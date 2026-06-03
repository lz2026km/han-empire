"""
Flask REST API Server for han-empire
Replaces Gradio with a REST API + React frontend
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import os
from functools import lru_cache, wraps
import gzip
import io
from han_sim.session import GameSession
from han_sim.simulation import run_monthly_simulation
from han_sim.decree import issue_secret_edict
from han_sim.portraits import save_custom_portrait, delete_custom_portrait, list_custom_portraits
from han_sim.content import load_game_content
from han_sim import agents as _agents
from han_sim.tech_tree import get_tech_engine, TechState
from han_sim.consequence_chain import get_consequence_chain, ConsequenceType
from han_sim.decision_log import DecisionLog
from han_sim.tutorial import get_tutorial_engine
from han_sim.dag_query import get_dag_query
from han_sim.auto_save import get_auto_save_manager

# ── v1.13.0 乾坤大挪移 Phase B：注入 GameContent 到 agents 模块 ──
# 让 create_chat_memory_agent / create_minister_agent 等能拿到 prompt 字段
_agents.bind_content(load_game_content())
import json
from typing import List, Dict, Any

# v2.0.0 Phase 5.5: 简单 LRU 缓存 + 全局 gzip 响应
_CACHE: Dict = {}  # key -> (timestamp, data), key 可以是 tuple
_CACHE_TTL = 60  # 60 秒 (regions/health 等静态端点)
def cached_json(ttl: int = _CACHE_TTL):
    """装饰器: 缓存 JSON 响应 N 秒。Phase 5.5 性能优化。"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # 缓存键 = (函数名, args, kwargs)
            key = (fn.__name__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in _CACHE:
                ts, data = _CACHE[key]
                if now - ts < ttl:
                    return jsonify(data)
            # 不在缓存: 调用并缓存
            resp = fn(*args, **kwargs)
            # resp 是 Flask Response 对象, 解析 JSON 再缓存
            try:
                payload = resp.get_json()
                _CACHE[key] = (now, payload)
            except Exception:
                pass
            return resp
        return wrapper
    return decorator

app = Flask(__name__)
CORS(app)

DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
GAMES: dict = {}


def _state_to_dict(state):
    """Convert GameState to dict for JSON serialization."""
    return {
        'campaign_id': getattr(state, 'campaign_id', ''),
        'year': getattr(state, 'year', 189),
        'month': getattr(state, 'month', 1),
        'emperor_name': getattr(state, 'emperor_name', '刘协'),
        'emperor_authority': getattr(state, 'emperor_authority', 100),
        'emperor_loyalty': getattr(state, 'emperor_loyalty', 50),
        'faction_influence': getattr(state, 'faction_influence', {}),
        'available_decree_types': getattr(state, 'available_decree_types', ['edict', 'inspect', 'recruit', 'grant', 'appoint']),
        'turn_count': getattr(state, 'turn_count', 0),
        'game_over': getattr(state, 'game_over', False),
        'victory': getattr(state, 'victory', False),
    }


# v2.0.0 Phase 5.5: 全局 after_request 钩子, 自动 gzip 响应
@app.after_request
def gzip_response_hook(response):
    """对 > 1KB 的 JSON 响应自动 gzip 压缩 (Accept-Encoding: gzip 时)。"""
    if (response.status_code < 200 or response.status_code >= 300
        or 'gzip' not in request.headers.get('Accept-Encoding', '')
        or len(response.get_data()) < 1024
        or 'Content-Encoding' in response.headers):
        return response
    data = response.get_data()
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb') as f:
        f.write(data)
    response.set_data(buf.getvalue())
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = len(buf.getvalue())
    response.headers['Vary'] = 'Accept-Encoding'
    return response


# v2.0.0 Phase 5.5: 缓存清理端点 (开发用, 防止开发期数据陈旧)
@app.route('/api/_cache/clear', methods=['POST'])
def clear_cache_api():
    """清理服务器缓存 (仅在开发时使用)。"""
    _CACHE.clear()
    return jsonify({'cleared': True, 'remaining': 0})


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'game': 'han-empire'})


@app.route('/')
def serve_index():
    dist_path = os.path.join(os.path.dirname(__file__), 'web', 'dist')
    return send_from_directory(dist_path, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    dist_path = os.path.join(os.path.dirname(__file__), 'web', 'dist')
    return send_from_directory(dist_path, filename)


# ---- Campaign Management ----

@app.route('/api/campaigns', methods=['GET'])
def list_campaigns():
    saves = GameSession.list_saves()
    campaigns = []
    for s in saves:
        campaigns.append({
            'id': s['campaign_id'],
            'year': 189,
            'emperor_authority': 100,
            'created': s.get('modified', ''),
        })
    return jsonify({'campaigns': campaigns})


@app.route('/api/campaigns', methods=['POST'])
def create_campaign():
    data = request.get_json() or {}
    emperor_name = data.get('emperor_name', '刘协')

    from han_sim.content import load_game_content
    content = load_game_content()
    content.emperor_name = emperor_name

    session = GameSession.new(campaign_id=None, content=content)
    GAMES[session.campaign_id] = session

    return jsonify({
        'campaign_id': session.campaign_id,
        'message': f'新朝建立：{emperor_name}'
    })


@app.route('/api/campaigns/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    # v2.0.0 Phase 6: try/except 避免 GameSession.load 抛异常 500
    if campaign_id not in GAMES:
        try:
            GAMES[campaign_id] = GameSession.load(campaign_id)
        except Exception as e:
            import logging
            logging.warning(f"GameSession.load failed for {campaign_id}: {e}")
            return jsonify({'error': f'Campaign {campaign_id} not found', 'detail': str(e)}), 404

    session = GAMES[campaign_id]
    state = _state_to_dict(session.state)
    ministers = session.get_active_ministers()
    factions = []

    # v2.0.0 Phase 6.2: FACTION_DATA → FACTION_META (修正 v1.x 时代 import 错)
    # v2.0.0 Phase 6.2: faction_influence 在 state.metrics 而非 state 属性
    from han_sim.models import FACTION_META
    faction_influence = session.state.metrics.get('faction_influence', {})
    for fid, fdata in FACTION_META.items():
        influence = faction_influence.get(fid, 50)
        factions.append({
            'id': fid,
            'name': fid,
            'leader_name': '',  # v1.x FACTION_DATA 有 leader, v2.0.0 FACTION_META 不含
            'influence': influence,
            'color': fdata.get('color', '#6b7280'),
            'description': fdata.get('description', ''),
            'dominant_ministers': len([m for m in ministers if m.get('faction') == fid]),
        })

    return jsonify({
        'campaign_id': campaign_id,
        'state': state,
        'ministers': ministers,
        'factions': factions,
    })


# ---- Game Actions ----

@app.route('/api/campaigns/<campaign_id>/issue_decree', methods=['POST'])
def issue_decree(campaign_id):
    data = request.get_json() or {}
    decree_type = data.get('decree_type', 'edict')

    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]

    # 根据 decree_type 分发到正确的诏书处理函数
    if decree_type == 'secret_edict':
        result = issue_secret_edict(session.state, session.db)
    else:
        intent = data.get('intent', '')
        result = issue_decree(intent, session.state, session.db, campaign_id)

    return jsonify({
        'result': {
            'success': result.decree is not None and result.decree.decree_type != 'failed',
            'message': result.decree.narrative if result.decree else (result.log_entries[0] if result.log_entries else ''),
            'metrics_delta': result.metrics_delta,
        },
        'game_state': _state_to_dict(session.state)
    })


@app.route('/api/campaigns/<campaign_id>/receive_minister', methods=['POST'])
def receive_minister(campaign_id):
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    result = session.summon_minister("", "")
    GAMES[campaign_id] = session

    return jsonify({'result': result.narrative if hasattr(result, 'narration') else str(result)})


@app.route('/api/campaigns/<campaign_id>/next_turn', methods=['POST'])
def next_turn(campaign_id):
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    sim_result = run_monthly_simulation(session.state, session.db)
    session.save()
    GAMES[campaign_id] = session

    return jsonify({
        'result': sim_result.narration if hasattr(sim_result, 'narration') else str(sim_result)
    })


@app.route('/api/campaigns/<campaign_id>/check_events', methods=['GET'])
def check_events(campaign_id):
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)
    session = GAMES[campaign_id]
    events = []
    return jsonify({'events': events})


@app.route('/api/campaigns/<campaign_id>/trigger_event', methods=['POST'])
def trigger_event(campaign_id):
    data = request.get_json() or {}
    return jsonify({'result': {'success': True, 'message': '事件已执行'}})


# ---- Skill Tree ----

@app.route('/api/campaigns/<campaign_id>/skill_tree', methods=['GET'])
def skill_tree(campaign_id):
    return jsonify({'skill_tree': {'branches': {}, 'authority_required': 0, 'unlocked_skills': []}})


@app.route('/api/campaigns/<campaign_id>/unlock_skill', methods=['POST'])
def unlock_skill(campaign_id):
    return jsonify({'result': {'success': True, 'message': '技能已解锁'}})


# ---- Buildings ----

@app.route('/api/campaigns/<campaign_id>/buildings', methods=['GET'])
def buildings(campaign_id):
    return jsonify({'buildings': {'buildings': [], 'total_slots': 5, 'used_slots': 0}})


@app.route('/api/campaigns/<campaign_id>/construct', methods=['POST'])
def construct(campaign_id):
    return jsonify({'result': {'success': True, 'message': '建筑已建造'}})


# ---- Factions ----

@app.route('/api/campaigns/<campaign_id>/faction_info', methods=['GET'])
def faction_info(campaign_id):
    # v2.1.0 Phase 5: 加派系深度 (密谋/外交/目标链)
    from han_sim.flows_faction import (
        get_faction_goals, calc_faction_diplomacy, generate_faction_conspiracy
    )
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)
    session = GAMES[campaign_id]
    state = session.state

    # 4 派系目标链
    goals = {f: get_faction_goals(f) for f in ("忠汉派", "务实派", "离心派", "叛逆派")}
    # 派系外交
    diplomacy = calc_faction_diplomacy(state)
    # 当回合密谋
    conspiracies = generate_faction_conspiracy(state, session.db)

    return jsonify({
        'factions': [],
        'goals': goals,
        'diplomacy': diplomacy,
        'conspiracies': conspiracies,
    })


@app.route('/api/campaigns/<campaign_id>/faction_influence', methods=['POST'])
def faction_influence(campaign_id):
    return jsonify({'result': {'success': True, 'message': '影响力已调整'}})


# ---- Save/Load ----

@app.route('/api/campaigns/<campaign_id>/save', methods=['POST'])
def save_game(campaign_id):
    if campaign_id not in GAMES:
        return jsonify({'error': 'Session not in memory'}), 400
    session = GAMES[campaign_id]
    session.save()
    return jsonify({'message': '存档成功', 'campaign_id': campaign_id})


@app.route('/api/campaigns/<campaign_id>/load', methods=['POST'])
def load_game(campaign_id):
    session = GameSession.load(campaign_id)
    GAMES[campaign_id] = session
    return jsonify({'message': '读档成功', 'campaign_id': campaign_id})


@app.route('/api/campaigns/<campaign_id>/saves', methods=['GET'])
def list_saves(campaign_id):
    saves = GameSession.list_saves()
    return jsonify({'saves': saves})


@app.route('/api/campaigns/<campaign_id>/saves/<int:slot>', methods=['DELETE'])
def delete_save(campaign_id, slot):
    return jsonify({'message': f'存档 slot {slot} 已删除'})


@app.route('/api/portraits/custom/<character_name>', methods=['POST'])
def upload_custom_portrait(character_name):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'Empty filename'}), 400
    image_data = file.read()
    path = save_custom_portrait(character_name, image_data, file.filename)
    return jsonify({'message': 'Portrait uploaded', 'path': path})


@app.route('/api/portraits/custom/<character_name>', methods=['DELETE'])
def delete_custom_portrait_api(character_name):
    deleted = delete_custom_portrait(character_name)
    if deleted:
        return jsonify({'message': f'Portrait for {character_name} deleted'})
    return jsonify({'error': 'Portrait not found'}), 404


@app.route('/api/portraits/custom', methods=['GET'])
def list_custom_portraits_api():
    portraits = list_custom_portraits()
    return jsonify({'portraits': portraits})


# ---- Directives (Draft Decree System) ----

@app.route('/api/directives', methods=['GET'])
def list_directives():
    campaign_id = request.args.get('campaign_id', '')
    turn = request.args.get('turn', type=int, default=0)

    if campaign_id not in GAMES:
        try:
            GAMES[campaign_id] = GameSession.load(campaign_id)
        except Exception as e:
            # v2.0.0 Phase 5.7: 显式记录加载失败 (之前静默 pass)
            import logging
            logging.warning(f"Campaign load failed: {campaign_id} → {e}")
            return jsonify({'directives': [], 'error': 'Campaign not found'})

    session = GAMES[campaign_id]
    db = session.db

    try:
        rows = db.conn.execute(
            """SELECT * FROM directives
               WHERE (? = 0 OR issued_turn = ?) AND campaign_id = ?
               ORDER BY issued_turn DESC, id DESC""",
            (turn, turn, campaign_id),
        ).fetchall()
    except Exception:
        rows = []

    directives = []
    for row in rows:
        d = dict(row)
        directives.append({
            'id': d.get('id'),
            'turn': d.get('issued_turn', 0),
            'year': session.state.year,
            'period': session.state.period,
            'text': d.get('content', ''),
            'source': d.get('kind', ''),
            'actor': '',
            'status': d.get('status', 'draft'),
            'notes': '',
            'created_at': d.get('created_at', ''),
        })

    return jsonify({'directives': directives})


@app.route('/api/directives', methods=['POST'])
def create_directive():
    data = request.get_json() or {}
    campaign_id = data.get('campaign_id', '')
    text = data.get('text', '')
    actor = data.get('actor', '')
    source = data.get('source', '')
    status = data.get('status', 'draft')

    if campaign_id not in GAMES:
        try:
            GAMES[campaign_id] = GameSession.load(campaign_id)
        except Exception:
            return jsonify({'error': 'Campaign not found'}), 404

    session = GAMES[campaign_id]
    db = session.db

    turn = session.state.turn
    issued_turn = turn
    expires_turn = turn + 3

    kind = source or 'manual'

    cursor = db.conn.execute(
        """INSERT INTO directives (campaign_id, type, kind, status, content, issued_turn, expires_turn)
           VALUES (?, 'decree', ?, ?, ?, ?, ?)""",
        (campaign_id, kind, status, text, issued_turn, expires_turn),
    )
    db.conn.commit()
    directive_id = cursor.lastrowid

    return jsonify({
        'id': directive_id,
        'turn': turn,
        'year': session.state.year,
        'period': session.state.period,
        'text': text,
        'source': source,
        'actor': actor,
        'status': status,
        'message': 'Directive created'
    })


@app.route('/api/directives/<int:directive_id>/confirm', methods=['PUT'])
def confirm_directive(directive_id):
    data = request.get_json() or {}
    campaign_id = data.get('campaign_id', '')

    if campaign_id not in GAMES:
        return jsonify({'error': 'Campaign not found'}), 404

    session = GAMES[campaign_id]
    db = session.db

    db.conn.execute(
        "UPDATE directives SET status = 'confirmed', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND campaign_id = ?",
        (directive_id, campaign_id),
    )
    db.conn.commit()

    return jsonify({'message': 'Directive confirmed', 'id': directive_id})


@app.route('/api/directives/<int:directive_id>/reject', methods=['PUT'])
def reject_directive(directive_id):
    data = request.get_json() or {}
    campaign_id = data.get('campaign_id', '')

    if campaign_id not in GAMES:
        return jsonify({'error': 'Campaign not found'}), 404

    session = GAMES[campaign_id]
    db = session.db

    db.conn.execute(
        "UPDATE directives SET status = 'rejected', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND campaign_id = ?",
        (directive_id, campaign_id),
    )
    db.conn.commit()

    return jsonify({'message': 'Directive rejected', 'id': directive_id})


@app.route('/api/directives/<int:directive_id>', methods=['DELETE'])
def delete_directive(directive_id):
    campaign_id = request.args.get('campaign_id', '')

    if campaign_id not in GAMES:
        return jsonify({'error': 'Campaign not found'}), 404

    session = GAMES[campaign_id]
    db = session.db

    db.conn.execute("DELETE FROM directives WHERE id = ? AND campaign_id = ?", (directive_id, campaign_id))
    db.conn.commit()

    return jsonify({'message': 'Directive deleted', 'id': directive_id})


@app.route('/api/decree/write', methods=['POST'])
def write_decree():
    data = request.get_json() or {}
    campaign_id = data.get('campaign_id', '')

    if campaign_id not in GAMES:
        try:
            GAMES[campaign_id] = GameSession.load(campaign_id)
        except Exception:
            return jsonify({'error': 'Campaign not found'}), 404

    session = GAMES[campaign_id]
    db = session.db

    rows = db.conn.execute(
        "SELECT * FROM directives WHERE campaign_id = ? AND status = 'confirmed' ORDER BY issued_turn DESC",
        (campaign_id,),
    ).fetchall()

    if not rows:
        return jsonify({'error': 'No confirmed directives', 'decree_text': ''})

    directives = [dict(row) for row in rows]
    decree_text = _generate_formal_decree(directives, session.state)

    return jsonify({
        'message': 'Decree generated',
        'decree_text': decree_text,
        'directives_count': len(directives),
    })


def _generate_formal_decree(directives: List[Dict], state) -> str:
    """Generate formal decree text from confirmed directives."""
    lines = ["奉天承运，皇帝诏曰："]

    for i, d in enumerate(directives, 1):
        text = d.get('content', '')
        if text:
            lines.append(f"其一：{text}。")

    lines.append("")
    lines.append("布告天下，咸使闻知。")

    return "\n".join(lines)


@app.route('/api/campaigns/<campaign_id>/stream_settlement', methods=['POST'])
def stream_settlement(campaign_id):
    """SSE流式月末结算端点"""
    from han_sim.simulation import run_monthly_simulation
    from han_sim.flows import apply_monthly_flow, calc_faction_delta

    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    db = session.db

    def generate():
        try:
            yield f"event: stage\ndata: stage:settling\n\n"

            fiscal = apply_monthly_flow(session.state, db)
            yield f"event: stage\ndata: stage:fiscal_done\ndata: text:财政结算完成\n\n"

            faction_delta = calc_faction_delta(session.state, db)
            yield f"event: stage\ndata: stage:faction_done\ndata: text:藩镇变化完成\n\n"

            yield f"event: stage\ndata: stage:thinking\ndata: text:推演中...\n\n"

            sim_result = run_monthly_simulation(session.state, session.db)

            yield f"event: stage\ndata: stage:events\ndata: text:事件结算完成\n\n"

            yield f"event: stage\ndata: stage:writing\ndata: text:撰写叙事...\n\n"

            yield f"event: thinking\ndata: text:生成月末叙事...\n\n"

            yield f"event: text\ndata: {sim_result.narration}\n\n"

            session.save()
            GAMES[campaign_id] = session

            yield f"event: done\ndata: done:true\n\n"

        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/campaigns/<campaign_id>/chat/<minister_name>', methods=['POST'])
def chat_with_minister(campaign_id, minister_name):
    """大臣召对聊天端点"""
    data = request.get_json() or {}
    message = data.get('message', '')

    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    db = session.db

    ministers = session.get_active_ministers()
    minister = next((m for m in ministers if m.get('name') == minister_name), None)

    if not minister:
        return jsonify({'result': f'未找到大臣{minister_name}'})

    from han_sim.agents import create_minister_agent
    from han_sim.memories import extract_chat_memories_for_minister

    try:
        # v2.0.0 Phase 4.3: 传 campaign_id 让多轮对话 session 持久化
        agent = create_minister_agent(minister, session.state, "", "", campaign_id=campaign_id)
        response = agent.run(message)
        text = response.content if hasattr(response, 'content') else str(response)

        # ── v1.13.0 乾坤大挪移 Phase B：召对结束 → chat_memory 实时抽取 ──
        # 失败 graceful（不阻断主流程），不抛错给前端
        chat_memory_count = 0
        try:
            from han_sim.agents import create_chat_memory_agent
            chat_memory_agent = create_chat_memory_agent()
            chat_history_for_memory = [
                {'role': 'user', 'content': message},
                {'role': 'assistant', 'content': text},
            ]
            chat_memory_count = extract_chat_memories_for_minister(
                chat_memory_agent, db, session.state, minister_name, chat_history_for_memory
            )
            if chat_memory_count:
                print(f"[chat_memory] {minister_name}:{session.state.turn} 抽取 {chat_memory_count} 条记忆")
        except Exception as chat_err:
            # 失败不阻断召对主流程
            print(f"[chat_memory] 抽取失败 (不阻断召对): {chat_err}")

        return jsonify({
            'result': text,
            'chat_history': [
                {'role': 'emperor', 'text': message},
                {'role': 'minister', 'text': text}
            ],
            'chat_memory_extracted': chat_memory_count,  # v1.13.0 新增字段
        })
    except Exception as e:
        return jsonify({'result': f'召对失败: {str(e)}'})


# v2.0.0 Phase 4.4: 自由对话 - 群臣廷议（多人同时发言 + 互相引用）
@app.route('/api/campaigns/<campaign_id>/free_chat', methods=['POST'])
def free_chat_endpoint(campaign_id):
    """群臣廷议端点 - 天子一句话，多大臣按立场轮流回应。

    请求体: {"topic": "迁都许昌是否可行", "ministers": ["曹操", "荀彧", "孔融"]}
    返回: {"rounds": [{"minister": "曹操", "text": "..."}, ...]}
    """
    data = request.get_json() or {}
    topic = data.get('topic', '').strip()
    minister_names = data.get('ministers', [])

    if not topic:
        return jsonify({'error': 'topic 必填'}), 400
    if not minister_names or len(minister_names) > 5:
        return jsonify({'error': 'ministers 1-5 人'}), 400

    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)
    session = GAMES[campaign_id]
    ministers = session.get_active_ministers()

    from han_sim.agents import create_minister_agent

    rounds = []
    prior_texts = []
    for name in minister_names:
        minister = next((m for m in ministers if m.get('name') == name), None)
        if not minister:
            rounds.append({"minister": name, "text": f"（{name}不在朝中）"})
            continue
        try:
            # 群臣廷议 session 共享
            from han_sim.agent_tools import build_audience_session_id
            sess_id = build_audience_session_id(campaign_id, topic)
            agent = create_minister_agent(
                minister, session.state, "",
                loyalty_ctx=f"廷议主题: {topic}",
                campaign_id=sess_id,
            )
            ctx = ""
            if prior_texts:
                ctx = "\n\n【前人已议】\n" + "\n".join(prior_texts[-3:])
            prompt = f"廷议主题：{topic}\n请以你的身份立场发表意见（200字内）。{ctx}"
            response = agent.run(prompt)
            text = response.content if hasattr(response, 'content') else str(response)
            rounds.append({"minister": name, "text": text})
            prior_texts.append(f"{name}: {text[:200]}")
        except Exception as e:
            rounds.append({"minister": name, "text": f"（{name} 奏对失败: {e}）"})

    return jsonify({"topic": topic, "rounds": rounds})


# v2.0.0 Phase 4.4: 重置对话 session
@app.route('/api/campaigns/<campaign_id>/chat/<minister_name>/reset', methods=['POST'])
def reset_chat_session(campaign_id, minister_name):
    """重置某大臣的对话历史（新朝会/新话题时用）。"""
    from han_sim.agent_tools import build_minister_session_id
    sess_id = build_minister_session_id(campaign_id, minister_name)
    try:
        from agno.memory import AgentMemory
        AgentMemory(session_id=sess_id).clear()
    except Exception as e:
        # v2.0.0 Phase 5.7: 显式记录, 不再静默 pass (agno 未装 / LLM 不在时常见)
        import logging
        logging.debug(f"AgentMemory clear skipped for {sess_id}: {e}")
        pass
    return jsonify({"status": "reset", "session_id": sess_id})


@app.route('/api/campaigns/<campaign_id>/secret_orders', methods=['GET'])
def get_secret_orders(campaign_id):
    """获取密令列表"""
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    db = session.db

    try:
        rows = db.conn.execute(
            "SELECT * FROM directives WHERE campaign_id = ? AND kind = 'secret' ORDER BY issued_turn DESC",
            (campaign_id,),
        ).fetchall()
    except Exception:
        rows = []

    orders = []
    for row in rows:
        d = dict(row)
        orders.append({
            'id': str(d.get('id', '')),
            'title': d.get('title', '密令'),
            'content': d.get('content', ''),
            'targetName': d.get('actor', ''),
            'issuedAt': f"{session.state.year}年{session.state.period}月",
            'status': d.get('status', 'pending'),
            'result': d.get('notes', ''),
        })

    return jsonify({'orders': orders})


@app.route('/api/campaigns/<campaign_id>/secret_orders', methods=['POST'])
def create_secret_order(campaign_id):
    """创建密令"""
    data = request.get_json() or {}
    title = data.get('title', '')
    content = data.get('content', '')
    assignee = data.get('assignee', '')
    deadline_months = data.get('deadline_months', 3)

    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    db = session.db

    turn = session.state.turn
    issued_turn = turn
    expires_turn = turn + deadline_months

    cursor = db.conn.execute(
        """INSERT INTO directives (campaign_id, type, kind, status, content, issued_turn, expires_turn, actor, title)
           VALUES (?, 'secret_order', 'secret', 'pending', ?, ?, ?, ?, ?)""",
        (campaign_id, content, issued_turn, expires_turn, assignee, title),
    )
    db.conn.commit()
    order_id = cursor.lastrowid

    return jsonify({
        'order': {
            'id': str(order_id),
            'title': title,
            'content': content,
            'targetName': assignee,
            'issuedAt': f"{session.state.year}年{session.state.period}月",
            'status': 'pending',
        }
    })


@app.route('/api/campaigns/<campaign_id>/secret_orders/<order_id>', methods=['DELETE'])
def cancel_secret_order(campaign_id, order_id):
    """取消密令"""
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    db = session.db

    db.conn.execute(
        "UPDATE directives SET status = 'cancelled' WHERE id = ? AND campaign_id = ?",
        (order_id, campaign_id),
    )
    db.conn.commit()

    return jsonify({'message': '密令已取消'})


DEBUG_PRESETS = {
    'caotang_ruin': {'威权': 15, '声望': 10, '藩镇': 80, '汉室库': 5, 'turn': 12, 'year': 196, 'period': 6,
                     'desc': '董卓焚洛阳 (中平六年 189 年 6 月, 威权 15, 藩镇 80)'},
    'yidai_200':    {'威权': 45, '声望': 35, '藩镇': 70, '汉室库': 12, 'turn': 132, 'year': 200, 'period': 4,
                     'desc': '衣带诏事发前夕 (建安五年 200 年 4 月)'},
    'guandu_202':   {'威权': 55, '声望': 50, '藩镇': 60, '汉室库': 18, 'turn': 156, 'year': 202, 'period': 9,
                     'desc': '官渡之战前夕 (建安七年 202 年 9 月)'},
    'chibi_208':    {'威权': 60, '声望': 60, '藩镇': 55, '汉室库': 30, 'turn': 228, 'year': 208, 'period': 11,
                     'desc': '赤壁之战前夕 (建安十三年 208 年 11 月)'},
    'caopi_220':    {'威权': 25, '声望': 15, '藩镇': 90, '汉室库': 8, 'turn': 372, 'year': 220, 'period': 10,
                     'desc': '曹丕篡汉 (延康元年 220 年 10 月, 汉室存亡)'},
}

DEBUG_COMMANDS = [
    {'cmd': 'help', 'cat': 'meta', 'desc': '显示所有可用命令'},
    {'cmd': 'status', 'cat': 'inspect', 'desc': '当前状态概要'},
    {'cmd': 'inspect', 'cat': 'inspect', 'desc': '完整状态 (metrics/factions/issues/directives)'},
    {'cmd': 'snapshot', 'cat': 'inspect', 'desc': '导出当前状态到 JSON'},
    {'cmd': 'list-scenarios', 'cat': 'scenario', 'desc': '列出预设场景'},
    {'cmd': 'scenario <name>', 'cat': 'scenario', 'desc': '加载预设 (caotang_ruin/yidai_200/guandu_202/chibi_208/caopi_220)'},
    {'cmd': 'add-authority <n>', 'cat': 'metric', 'desc': '增加威权值'},
    {'cmd': 'add-loyalty <n>', 'cat': 'metric', 'desc': '增加声望'},
    {'cmd': 'set-authority <n>', 'cat': 'metric', 'desc': '设置威权值'},
    {'cmd': 'add-metric <key> <n>', 'cat': 'metric', 'desc': '累加任意 metric'},
    {'cmd': 'set-metric <key> <n>', 'cat': 'metric', 'desc': '设置任意 metric'},
    {'cmd': 'set-turn <n>', 'cat': 'time', 'desc': '跳到指定回合 (仅修改 turn/year/period)'},
    {'cmd': 'unlock-skills', 'cat': 'meta', 'desc': '解锁所有技能 (模拟)'},
    {'cmd': 'skip-month', 'cat': 'time', 'desc': '推进一月'},
    {'cmd': 'skip-year', 'cat': 'time', 'desc': '推进一年 (12 月)'},
    {'cmd': 'inject-event <event_id>', 'cat': 'event', 'desc': '强制触发事件 (写入 issues)'},
    {'cmd': 'reveal-map', 'cat': 'meta', 'desc': '显示所有省份 (需后端联动)'},
    {'cmd': 'clear', 'cat': 'meta', 'desc': '清除控制台'},
    {'cmd': 'exit', 'cat': 'meta', 'desc': '关闭控制台'},
]


def _cmd_help() -> str:
    cats = {}
    for c in DEBUG_COMMANDS:
        cats.setdefault(c['cat'], []).append(c)
    lines = ['工程师调试命令 (按类别):', '']
    cat_name = {'meta': '元命令', 'inspect': '状态检视', 'scenario': '场景加载',
                'metric': '指标调控', 'time': '时间调控', 'event': '事件注入'}
    for cat, items in cats.items():
        lines.append(f'[{cat_name.get(cat, cat)}]')
        for it in items:
            lines.append(f"  {it['cmd'].ljust(28)} - {it['desc']}")
        lines.append('')
    return '\n'.join(lines).rstrip()


def _cmd_inspect(session) -> str:
    state = session.state
    scalar_metrics = [(k, v) for k, v in state.metrics.items() if isinstance(v, (int, float))]
    metrics = sorted(scalar_metrics, key=lambda kv: -kv[1])
    issues_count = session.db.conn.execute('SELECT COUNT(*) AS c FROM issues').fetchone()['c']
    directives = session.db.conn.execute(
        "SELECT id, kind, status FROM directives WHERE campaign_id=? ORDER BY id DESC LIMIT 5",
        (session.campaign_id,),
    ).fetchall()
    factions = session.db.conn.execute(
        'SELECT name, satisfaction, leverage FROM factions ORDER BY satisfaction DESC'
    ).fetchall()
    ministers_count = session.db.conn.execute(
        "SELECT COUNT(*) AS c FROM characters WHERE power_id='han' AND status='active'"
    ).fetchone()['c']
    faction_str = ', '.join(f"{f['name']}={f['satisfaction']}" for f in factions[:5])
    directive_str = ', '.join(f"#{d['id']}{d['kind'][:2]}/{d['status']}" for d in directives) or '无'
    lines = [
        '═' * 50,
        f'状态检视  {state.year}年{state.period}月  回合 {state.turn}  (campaign={session.campaign_id})',
        '─' * 50,
        '核心指标 (按值降序):',
    ]
    for k, v in metrics[:8]:
        lines.append(f'  {k:<10} = {v}')
    complex_count = sum(1 for v in state.metrics.values() if not isinstance(v, (int, float)))
    lines += [
        '─' * 50,
        f'派系 (top 5): {faction_str}',
        f'汉廷在任大臣: {ministers_count}',
        f'事项追踪: {issues_count} 条',
        f'近期诏令 (top 5): {directive_str}',
        f'(metrics 中另有 {complex_count} 个 dict/list 字段, 已跳过排序)',
        '═' * 50,
    ]
    return '\n'.join(lines)


def _cmd_scenario(session, name: str) -> tuple[str, bool]:
    if name == 'list':
        lines = ['预设场景:']
        for k, v in DEBUG_PRESETS.items():
            lines.append(f"  {k.ljust(14)} - {v['desc']}")
        return '\n'.join(lines), True
    if name not in DEBUG_PRESETS:
        return f'未知场景: {name}. 输入 list-scenarios 查看', False
    p = DEBUG_PRESETS[name]
    for k, v in p.items():
        if k == 'desc':
            continue
        if k in ('turn', 'year', 'period'):
            setattr(session.state, k, v)
        else:
            session.state.metrics[k] = v
    return f"已加载场景 [{name}]: {p['desc']}\n" + _cmd_inspect(session), True


def _cmd_snapshot(session) -> str:
    import json as _json
    snap = {
        'campaign_id': session.campaign_id,
        'turn': session.state.turn,
        'year': session.state.year,
        'period': session.state.period,
        'metrics': dict(session.state.metrics),
    }
    return _json.dumps(snap, ensure_ascii=False, indent=2)


@app.route('/api/campaigns/<campaign_id>/cheat', methods=['POST'])
def execute_cheat(campaign_id):
    data = request.get_json() or {}
    command = (data.get('command', '') or '').strip()
    args = data.get('args', {}) or {}

    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)
    session = GAMES[campaign_id]
    state = session.state

    output = ''
    success = True

    if command in ('', 'help'):
        output = _cmd_help()
    elif command == 'status':
        m = state.metrics
        output = (
            f"年份 {state.year}年{state.period}月  回合 {state.turn}\n"
            f"威权 {m.get('威权', 0)}  声望 {m.get('声望', 0)}  藩镇 {m.get('藩镇', 0)}  "
            f"汉室库 {m.get('汉室库', 0)}万两"
        )
    elif command == 'inspect':
        output = _cmd_inspect(session)
    elif command == 'snapshot':
        output = _cmd_snapshot(session)
    elif command == 'list-scenarios':
        output = _cmd_scenario(session, 'list')[0]
    elif command.startswith('scenario '):
        name = command.split(' ', 1)[1].strip()
        output, success = _cmd_scenario(session, name)
    elif command == 'add-authority':
        n = int(args.get('n', 10))
        state.metrics['威权'] = state.metrics.get('威权', 0) + n
        output = f'威权 +{n}，当前: {state.metrics["威权"]}'
    elif command == 'set-authority':
        n = int(args.get('n', 50))
        state.metrics['威权'] = n
        output = f'威权已设置为: {n}'
    elif command == 'add-loyalty':
        n = int(args.get('n', 10))
        state.metrics['声望'] = state.metrics.get('声望', 0) + n
        output = f'声望 +{n}，当前: {state.metrics["声望"]}'
    elif command.startswith('add-metric '):
        parts = command.split()
        if len(parts) >= 3:
            key, delta = parts[1], int(parts[2])
            state.metrics[key] = state.metrics.get(key, 0) + delta
            output = f'{key} {delta:+d}，当前: {state.metrics[key]}'
        else:
            output = '用法: add-metric <key> <delta>'
            success = False
    elif command.startswith('set-metric '):
        parts = command.split()
        if len(parts) >= 3:
            key, val = parts[1], int(parts[2])
            state.metrics[key] = val
            output = f'{key} 已设置为: {val}'
        else:
            output = '用法: set-metric <key> <value>'
            success = False
    elif command.startswith('set-turn '):
        n = int(command.split()[1])
        delta_months = max(0, n - state.turn) * 1
        state.turn = n
        output = f'回合已设置为: {n}  (注: year/period 需按需调整, 当前 {state.year}/{state.period})'
    elif command == 'unlock-skills':
        output = '技能已解锁 (模拟)'
    elif command == 'skip-month':
        if hasattr(state, 'next_period'):
            state.next_period()
        else:
            state.period = (state.period % 12) + 1
            if state.period == 1:
                state.year += 1
            state.turn += 1
        output = f'进入 {state.year}年{state.period}月  回合 {state.turn}'
    elif command == 'skip-year':
        for _ in range(12):
            if hasattr(state, 'next_period'):
                state.next_period()
            else:
                state.period = (state.period % 12) + 1
                if state.period == 1:
                    state.year += 1
                state.turn += 1
        output = f'推进一年, 现在 {state.year}年{state.period}月  回合 {state.turn}'
    elif command.startswith('inject-event '):
        eid = command.split(' ', 1)[1].strip()
        try:
            session.db.conn.execute(
                "INSERT INTO issues (kind, status, title, origin_turn) VALUES (?, ?, ?, ?)",
                ('manual', 'open', f'工程师注入: {eid}', state.turn),
            )
            session.db.conn.commit()
            output = f'已注入事件占位: {eid} (写入了 issues 表)'
        except Exception as e:
            output = f'注入失败: {e}'
            success = False
    elif command == 'reveal-map':
        regions = session.db.conn.execute('SELECT COUNT(*) AS c FROM regions').fetchone()['c']
        output = f'全图已揭示 (regions 表共 {regions} 条, UI 联动待前端配合)'
    else:
        output = f'未知命令: {command}. 输入 help 查看'
        success = False

    session.save()
    GAMES[campaign_id] = session
    return jsonify({'success': success, 'output': output, 'command': command})


@app.route('/api/campaigns/<campaign_id>/debug/commands', methods=['GET'])
def debug_commands(campaign_id):
    return jsonify({'commands': DEBUG_COMMANDS, 'presets': list(DEBUG_PRESETS.keys())})


@app.route('/api/campaigns/<campaign_id>/debug/state', methods=['GET'])
def debug_state(campaign_id):
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)
    session = GAMES[campaign_id]
    state = session.state
    factions = [dict(r) for r in session.db.conn.execute(
        'SELECT name, satisfaction, leverage, agenda FROM factions ORDER BY satisfaction DESC'
    ).fetchall()]
    issues = [dict(r) for r in session.db.conn.execute(
        'SELECT id, kind, status, title, origin_turn FROM issues ORDER BY id DESC LIMIT 20'
    ).fetchall()]
    ministers = [dict(r) for r in session.db.conn.execute(
        "SELECT name, office, faction, loyalty, ability FROM characters WHERE power_id='han' AND status='active' ORDER BY name LIMIT 50"
    ).fetchall()]
    return jsonify({
        'campaign_id': session.campaign_id,
        'turn': state.turn,
        'year': state.year,
        'period': state.period,
        'metrics': dict(state.metrics),
        'factions': factions,
        'issues': issues,
        'ministers_count': len(ministers),
        'ministers_sample': ministers[:20],
    })


@app.route('/api/campaigns/<campaign_id>/debug/inspect/<table>', methods=['GET'])
def debug_inspect_table(campaign_id, table):
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)
    session = GAMES[campaign_id]
    allowed = {
        'characters', 'factions', 'powers', 'regions', 'armies', 'buildings',
        'events', 'issues', 'directives', 'secret_orders', 'consorts',
        'emperor_diary', 'minister_affection', 'imperial_events', 'memorials',
        'verdicts', 'faction_backlashes', 'court_debates',
    }
    if table not in allowed:
        return jsonify({'error': f'不允许的表: {table}. 允许: {sorted(allowed)}'}), 400
    try:
        rows = [dict(r) for r in session.db.conn.execute(
            f'SELECT * FROM {table} LIMIT 100'
        ).fetchall()]
        count = session.db.conn.execute(f'SELECT COUNT(*) AS c FROM {table}').fetchone()['c']
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'table': table, 'count': count, 'rows': rows})


# ---- Armies & Battle ----

@app.route('/api/campaigns/<campaign_id>/armies', methods=['GET'])
def list_armies(campaign_id):
    """获取所有军队列表"""
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    db = session.db

    rows = db.conn.execute(
        "SELECT * FROM armies WHERE owner_power = 'han' ORDER BY id"
    ).fetchall()

    armies = []
    for row in rows:
        armies.append({
            'id': row['id'],
            'name': row['name'],
            'station': row['station'],
            'theater': row['theater'],
            'commander': row['commander'],
            'troop_type': row['troop_type'],
            'manpower': row['manpower'],
            'morale': row['morale'],
            'training': row['training'],
            'equipment': row['equipment'],
            'status': row['status'],
        })

    return jsonify({'armies': armies})


@app.route('/api/campaigns/<campaign_id>/ministers', methods=['GET'])
def list_ministers(campaign_id):
    """获取大臣列表（含好感度）"""
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    db = session.db

    rows = db.conn.execute(
        "SELECT * FROM characters WHERE status = 'active' AND power_id = 'han' ORDER BY name"
    ).fetchall()

    ministers = []
    for row in rows:
        name = row['name']
        aff = db.get_minister_affection(name)
        ministers.append({
            'name': name,
            'office': row['office'],
            'office_type': row['office_type'],
            'faction': row['faction'],
            'loyalty': row['loyalty'],
            'ability': row['ability'],
            'integrity': row['integrity'],
            'courage': row['courage'],
            'portrait_id': row['portrait_id'],
            'affection': aff['affection'] if aff else 50,
            'interaction_count': aff['interaction_count'] if aff else 0,
            'last_interaction_turn': aff['last_interaction_turn'] if aff else 0,
        })

    return jsonify({'ministers': ministers})


@app.route('/api/campaigns/<campaign_id>/battle', methods=['POST'])
def trigger_battle(campaign_id):
    """触发战斗（随机骰子系统）"""
    import random

    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    data = request.get_json() or {}
    attacker_id = data.get('attacker_id', '')
    defender_id = data.get('defender_id', '')

    # 随机骰子投掷 (1-100)
    attacker_roll = random.randint(1, 100)
    defender_roll = random.randint(1, 100)

    # 基础胜率计算
    attacker_info = session.db.conn.execute(
        "SELECT morale, training FROM armies WHERE id = ?", (attacker_id,)
    ).fetchone()
    defender_info = session.db.conn.execute(
        "SELECT morale, training FROM armies WHERE id = ?", (defender_id,)
    ).fetchone()

    if not attacker_info or not defender_info:
        return jsonify({'error': 'Army not found'}), 404

    # 简单战斗力计算
    attacker_power = (attacker_info['morale'] + attacker_info['training']) * 2 + attacker_roll
    defender_power = (defender_info['morale'] + defender_info['training']) * 2 + defender_roll

    attacker_win = attacker_power > defender_power
    margin = abs(attacker_power - defender_power)

    result = '胜利' if attacker_win else '失败'
    return jsonify({
        'attacker_roll': attacker_roll,
        'defender_roll': defender_roll,
        'attacker_power': attacker_power,
        'defender_power': defender_power,
        'result': result,
        'margin': margin,
        'narrative': f'进攻方投出{attacker_roll}，防御方投出{defender_roll}，{result}！'
    })


# ════════════════════════════════════════════════════════════════
# v2.1.0 Phase 4.2: 历史战役推演 API (3 个东汉末年著名战役)
# ════════════════════════════════════════════════════════════════

@app.route('/api/battles', methods=['GET'])
def list_battles_api():
    """列出 3 个历史战役 (官渡/赤壁/夷陵)"""
    from han_sim.battle import list_battles
    return jsonify({"battles": list_battles()})


@app.route('/api/battles/simulate', methods=['POST'])
def simulate_battle_api():
    """推演指定战役 (返回完整战报)"""
    from han_sim.battle import simulate_battle
    data = request.get_json() or {}
    battle_key = data.get('battle_key', 'guandu')
    player_side_str = data.get('player_side')

    player_side = None
    if player_side_str:
        from han_sim.battle import Side
        try:
            player_side = Side(player_side_str)
        except ValueError:
            return jsonify({"error": f"无效 player_side: {player_side_str}"}), 400

    try:
        report = simulate_battle(battle_key, player_side)
        return jsonify({"report": report.to_dict()})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ════════════════════════════════════════════════════════════════
# v2.1.0 Phase 6.2: 科举征辟 + 罢免流放 API
# ════════════════════════════════════════════════════════════════

@app.route('/api/civil/ranks', methods=['GET'])
def civil_ranks_api():
    """列出 10 级官品"""
    from han_sim.civil_service import list_ranks
    return jsonify({"ranks": list_ranks()})


@app.route('/api/civil/subjects', methods=['GET'])
def civil_subjects_api():
    """列出科举科目"""
    from han_sim.civil_service import list_exam_subjects
    return jsonify({"subjects": list_exam_subjects()})


@app.route('/api/civil/exam', methods=['POST'])
def civil_exam_api():
    """举行科举"""
    from han_sim.civil_service import hold_exam
    data = request.get_json() or {}
    name = data.get('candidate_name', '天子')
    year = data.get('year', 200)
    month = data.get('month', 1)
    intelligence = data.get('intelligence', 50)
    result = hold_exam(name, year, month, intelligence)
    return jsonify({"result": result.to_dict()})


@app.route('/api/civil/dismiss', methods=['POST'])
def civil_dismiss_api():
    """罢免大臣"""
    from han_sim.civil_service import dismiss_minister
    data = request.get_json() or {}
    name = data.get('name', '某臣')
    reason = data.get('reason', '失职')
    year = data.get('year', 200)
    month = data.get('month', 1)
    faction = data.get('faction', '忠汉派')
    result = dismiss_minister(name, reason, year, month, faction)
    return jsonify({"result": result.to_dict()})


@app.route('/api/civil/exile', methods=['POST'])
def civil_exile_api():
    """流放大臣"""
    from han_sim.civil_service import exile_minister
    data = request.get_json() or {}
    name = data.get('name', '某臣')
    reason = data.get('reason', '谋反')
    year = data.get('year', 200)
    month = data.get('month', 1)
    faction = data.get('faction', '叛逆派')
    result = exile_minister(name, reason, year, month, faction)
    return jsonify({"result": result.to_dict()})


# ════════════════════════════════════════════════════════════════
# v2.1.0 Phase 7.2: 春秋史册 + 时间轴 API
# ════════════════════════════════════════════════════════════════

@app.route('/api/chronicle/historical', methods=['GET'])
def chronicle_historical_api():
    """列出东汉末年 13 件重大历史事件"""
    from han_sim.chronicle import list_historical_events
    year_min = int(request.args.get('year_min', 184))
    year_max = int(request.args.get('year_max', 280))
    return jsonify({
        "events": list_historical_events(year_min, year_max),
        "total": len(list_historical_events(year_min, year_max)),
    })


@app.route('/api/chronicle/timeline', methods=['GET'])
def chronicle_timeline_api():
    """生成时间轴 (按年分组)"""
    from han_sim.chronicle import get_timeline
    year_min = int(request.args.get('year_min', 184))
    year_max = int(request.args.get('year_max', 280))
    return jsonify({"timeline": get_timeline(year_min, year_max)})


@app.route('/api/chronicle/historian', methods=['POST'])
def chronicle_historian_api():
    """4 史官评语 (司马/班/范/陈)"""
    from han_sim.chronicle import generate_historian_comment
    data = request.get_json() or {}
    year = data.get('year', 220)
    title = data.get('title', '曹丕代汉')
    historian = data.get('historian', '司马氏')
    comment = generate_historian_comment(year, title, historian)
    return jsonify({"comment": comment, "historian": historian, "year": year, "title": title})


@app.route('/api/chronicle/historians', methods=['GET'])
def chronicle_historians_api():
    """4 史官立场"""
    from han_sim.chronicle import HISTORIAN_STANCES
    return jsonify({"historians": HISTORIAN_STANCES})


@app.route('/api/chronicle/record', methods=['POST'])
def chronicle_record_api():
    """记录游戏事件到史记"""
    from han_sim.chronicle import record_event
    data = request.get_json() or {}
    year = data.get('year', 200)
    month = data.get('month', 1)
    event_type = data.get('event_type', '诏书')
    title = data.get('title', '未知')
    description = data.get('description', '')
    impact = data.get('impact', {})
    source = data.get('source', 'player')
    event = record_event(year, month, event_type, title, description, impact, source)
    return jsonify({"event": event.to_dict()})


# ════════════════════════════════════════════════════════════════
# v1.15.0 乾坤大挪移 Phase D · 后宫 API
# ════════════════════════════════════════════════════════════════

@app.route('/api/campaigns/<campaign_id>/consorts', methods=['GET'])
def list_consorts_api(campaign_id):
    """后宫名册：返回已入宫妃嫔列表（按 rank 排序）。"""
    if campaign_id not in GAMES:
        return jsonify({'error': 'Campaign not found'}), 404
    session = GAMES[campaign_id]
    db = session.db
    rows = db.list_consorts(campaign_id)
    # rank 排序：皇后 > 贵妃 > 妃 > 嫔 > 贵人 > 常在 > 答应 > 采女
    rank_order = ['皇后', '贵妃', '妃', '嫔', '贵人', '常在', '答应', '采女']
    rows.sort(key=lambda r: rank_order.index(r['rank']) if r.get('rank') in rank_order else 99)
    return jsonify({'consorts': rows})


@app.route('/api/campaigns/<campaign_id>/consorts/<consort_id>', methods=['GET'])
def get_consort_detail_api(campaign_id, consort_id):
    """妃嫔详情：从 consorts.json 画像 + db consorts 表。"""
    if campaign_id not in GAMES:
        return jsonify({'error': 'Campaign not found'}), 404
    session = GAMES[campaign_id]
    db = session.db
    # 1. 画像（consorts.json）
    from han_sim.content import _ctx as content_ctx
    ctx = content_ctx()
    portrait = {}
    if ctx:
        try:
            for c in ctx.load_consorts():
                if c.get('id') == consort_id:
                    portrait = c
                    break
        except Exception:
            pass
    # 2. db 数据
    ci_short = consort_id.replace('consort_', '')
    db_row = db.get_consort(campaign_id, ci_short) or db.get_consort(campaign_id, consort_id) or {}
    # 3. 调教记录
    events = db.list_consort_events(campaign_id, ci_short) if ci_short else []
    return jsonify({
        'consort_id': consort_id,
        'portrait': portrait,
        'db': db_row,
        'events': events,
    })


@app.route('/api/campaigns/<campaign_id>/consorts/<consort_id>/audience', methods=['POST'])
def consort_audience_api(campaign_id, consort_id):
    """v1.15.0 Phase D 召幸对话端点（后宫妃嫔 agent）。"""
    if campaign_id not in GAMES:
        return jsonify({'error': 'Campaign not found'}), 404
    data = request.get_json() or {}
    message = (data.get('message', '') or '').strip()
    if not message:
        return jsonify({'result': '献帝陛下未发一言。'})

    session = GAMES[campaign_id]
    db = session.db

    try:
        from han_sim.agents import create_consort_agent
        agent = create_consort_agent(consort_id, db, session.state)
        response = agent.run(message)
        text = response.content if hasattr(response, 'content') else str(response)

        return jsonify({
            'result': text,
            'consort_id': consort_id,
            'chat_history': [
                {'role': 'emperor', 'text': message},
                {'role': 'consort', 'text': text},
            ],
        })
    except Exception as e:
        return jsonify({'result': f'召幸失败: {e}'})


@app.route('/api/campaigns/<campaign_id>/consorts/<consort_id>/records', methods=['GET'])
def list_consort_records_api(campaign_id, consort_id):
    """妃嫔调教记录（consort_events 事件流）。"""
    if campaign_id not in GAMES:
        return jsonify({'error': 'Campaign not found'}), 404
    session = GAMES[campaign_id]
    db = session.db
    ci_short = consort_id.replace('consort_', '')
    events = db.list_consort_events(campaign_id, ci_short)
    return jsonify({'records': events, 'consort_id': consort_id})


@app.route('/api/campaigns/<campaign_id>/consorts/<consort_id>/cultivate', methods=['POST'])
def cultivate_consort_api(campaign_id, consort_id):
    """调教妃嫔：学技能/改性格（后端接口，前端可单独调）。"""
    if campaign_id not in GAMES:
        return jsonify({'error': 'Campaign not found'}), 404
    data = request.get_json() or {}
    skill = (data.get('skill', '') or '').strip()
    trait = (data.get('trait', '') or '').strip()
    if not skill and not trait:
        return jsonify({'error': '调教失败：至少要填一个新技能或新性格。'}), 400

    session = GAMES[campaign_id]
    db = session.db
    try:
        result = db.cultivate_consort(
            campaign_id=campaign_id,
            name=consort_id,
            skill=skill,
            trait=trait,
        )
        return jsonify({'ok': True, 'consort': result})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/campaigns/<campaign_id>/consorts/<consort_id>/traits', methods=['GET'])
def get_consort_traits_api(campaign_id, consort_id):
    """妃嫔当前永久性情/技能（来自 consort_traits 表）。"""
    if campaign_id not in GAMES:
        return jsonify({'error': 'Campaign not found'}), 404
    session = GAMES[campaign_id]
    db = session.db
    ci_short = consort_id.replace('consort_', '')
    traits = db.get_consort_traits(ci_short) if ci_short else {'extra_skills': [], 'extra_traits': []}
    return jsonify({'consort_id': consort_id, **traits})


@app.route('/api/campaigns/<campaign_id>/consort_tab', methods=['GET'])
def consort_tab_api(campaign_id):
    """后宫 13 号 Tab 整体数据：名册 + 调教统计 + 当前提示。"""
    if campaign_id not in GAMES:
        return jsonify({'error': 'Campaign not found'}), 404
    session = GAMES[campaign_id]
    db = session.db
    consorts = db.list_consorts(campaign_id)
    # 6 候选人物（来自 consorts.json）
    from han_sim.content import _ctx as content_ctx
    ctx = content_ctx()
    candidates = ctx.load_consorts() if ctx else []
    # 妃嫔事件统计
    total_events = sum(len(db.list_consort_events(campaign_id)) for _ in [None])
    return jsonify({
        'consorts': consorts,
        'candidates': candidates,
        'stats': {
            'total_consorts': len(consorts),
            'total_candidates': len(candidates),
            'total_events': total_events,
        },
    })


# v2.0.0 Phase 5.2: 全局州郡数据 API (51 州郡 + 当前游戏快照叠加)
@app.route('/api/regions', methods=['GET'])
@cached_json(ttl=120)  # v2.0.0 Phase 5.5: 120 秒缓存 (51 州郡不变)
def regions_api():
    """返回所有州郡基础数据 (来自 content/regions.json)。
    不依赖 campaign_id — 州郡基础数据全局共享。
    gzip 压缩由全局 after_request 钩子自动处理。
    返回: {regions: [...], count: 51}
    """
    from han_sim.content import load_game_content
    content = load_game_content()
    regions = content.load_regions() if content else []
    return jsonify({'regions': regions, 'count': len(regions)})


# ════════════════════════════════════════════════════════════════
# v2.2.0: SSE 流式颁诏 (P0-1+P0-2+P0-3+P0-4+P0-5)
# ════════════════════════════════════════════════════════════════
@app.route('/api/decree/issue/stream', methods=['POST'])
def api_issue_decree_stream():
    """SSE 流式颁诏 - 主公实时看到 5 阶段推演 (拟诏/研判/推演/月结/完成)

    事件类型: stage / thinking / text / done / error
    """
    import queue
    import threading
    from han_sim.decree_stream import stream_issue_decree

    data = request.get_json() or {}
    campaign_id = data.get('campaign_id', '')
    # v5.1.1 P1-1: 天命控制台 cheat_directive 透传 (一次性, 不持久化)
    cheat_directive = (data.get('cheat') or '').strip()

    if campaign_id not in GAMES:
        try:
            GAMES[campaign_id] = GameSession.load(campaign_id)
        except Exception:
            return jsonify({'error': 'Campaign not found'}), 404

    session = GAMES[campaign_id]
    db = session.db
    state = session.state

    ev_queue = queue.Queue()

    def on_event(kind, content):
        ev_queue.put((kind, content))

    def worker():
        try:
            result = stream_issue_decree(
                state, db, campaign_id, on_event,
                cheat_directive=cheat_directive,
            )
            ev_queue.put(('__done__', result))
        except Exception as e:
            ev_queue.put(('__error__', str(e)))

    def generate():
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        while True:
            kind, content = ev_queue.get()
            if kind == '__done__':
                yield f"event: done\ndata: {json.dumps(content, ensure_ascii=False)}\n\n"
                break
            if kind == '__error__':
                yield f"event: error\ndata: {json.dumps({'message': content}, ensure_ascii=False)}\n\n"
                break
            # stage / thinking / text
            yield f"event: {kind}\ndata: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/decree/advance/stream', methods=['POST'])
def api_advance_stream():
    """SSE 流式退朝 - 不下旨, 仅推演月度结算 (P0-4)"""
    import queue
    import threading
    from han_sim.decree_stream import advance_without_edict

    data = request.get_json() or {}
    campaign_id = data.get('campaign_id', '')

    if campaign_id not in GAMES:
        try:
            GAMES[campaign_id] = GameSession.load(campaign_id)
        except Exception:
            return jsonify({'error': 'Campaign not found'}), 404

    session = GAMES[campaign_id]
    db = session.db
    state = session.state

    ev_queue = queue.Queue()

    def on_event(kind, content):
        ev_queue.put((kind, content))

    def worker():
        try:
            result = advance_without_edict(state, db, on_event)
            ev_queue.put(('__done__', result))
        except Exception as e:
            ev_queue.put(('__error__', str(e)))

    def generate():
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        while True:
            kind, content = ev_queue.get()
            if kind == '__done__':
                yield f"event: done\ndata: {json.dumps(content, ensure_ascii=False)}\n\n"
                break
            if kind == '__error__':
                yield f"event: error\ndata: {json.dumps({'message': content}, ensure_ascii=False)}\n\n"
                break
            yield f"event: {kind}\ndata: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


# ============================================
# v3.0 阶段四: 11 个新端点 (主公明令施工)
# ============================================

# --- 1) /api/settings/api-key (本地 Key CRUD) ---
@app.route('/api/settings/api-key', methods=['GET'])
def api_settings_get_key():
    """返回服务端兜底 Key 状态 (不暴露 Key 内容)."""
    from han_sim.api_key_router import get_server_routes_summary
    return jsonify(get_server_routes_summary())


@app.route('/api/settings/api-key', methods=['POST'])
def api_settings_post_key():
    """前端提交 (但服务端不存, 仅校验格式 + 模式决策)."""
    from han_sim.api_key_router import decide_route, KeyMode
    data = request.get_json() or {}
    mode = data.get('mode', 'server')
    client_keys = {
        'api_key': data.get('api_key', ''),
        'base_url': data.get('base_url', ''),
        'model': data.get('model', ''),
    }
    try:
        route = decide_route(mode, client_keys, purpose=data.get('purpose', 'general'))
        return jsonify({
            'ok': True,
            'mode': route.mode.value,
            'from_local': route.from_local,
            'warning': route.warning,
        })
    except RuntimeError as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


# --- 2) /api/llm/test (测试连通) ---
@app.route('/api/llm/test', methods=['POST'])
def api_llm_test():
    """测试 LLM 连通. 不暴露 Key."""
    from han_sim.api_key_router import decide_route
    data = request.get_json() or {}
    mode = data.get('mode', 'server')
    client_keys = {
        'api_key': data.get('api_key', ''),
        'base_url': data.get('base_url', ''),
        'model': data.get('model', ''),
    }
    try:
        route = decide_route(mode, client_keys, purpose='general')
        # 仅校验路由可达, 不真发请求
        return jsonify({
            'ok': True,
            'message': f'路由可达: mode={route.mode.value}, model={route.model or "(default)"}',
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


# --- 3) /api/usage/stats (Token 用量统计) ---
@app.route('/api/usage/stats', methods=['GET'])
def api_usage_stats():
    from han_sim.usage_tracker import get_stats
    return jsonify(get_stats())


# --- 4) /api/usage/recent (最近 N 条记录) ---
@app.route('/api/usage/recent', methods=['GET'])
def api_usage_recent():
    from han_sim.usage_tracker import get_recent
    limit = int(request.args.get('limit', 20))
    return jsonify({'records': get_recent(limit)})


# --- 5) /api/llm/models (列出可用模型) ---
@app.route('/api/llm/models', methods=['GET'])
def api_llm_models():
    from han_sim.model_adapter import list_supported_providers
    return jsonify({'providers': list_supported_providers()})


# --- 6) /api/llm/cache-stats (KV cache 命中率) ---
@app.route('/api/llm/cache-stats', methods=['GET'])
def api_llm_cache_stats():
    from han_sim.llm_cache import get_cache_stats, estimate_cache_savings
    stats = get_cache_stats()
    saved = estimate_cache_savings()
    return jsonify({'cache_stats': stats, 'savings': saved})


# --- 6a) /api/token_stats (v5.0 P0-3: 仪表盘聚合) ---
@app.route('/api/token_stats', methods=['GET'])
def api_token_stats():
    """v5.0 P0-3: 仪表盘聚合 endpoint
    返回: token 用量 + 缓存命中率 + 按 model/tier 拆分
    """
    from han_sim.usage_tracker import get_stats
    from han_sim.llm_cache import get_cache_stats, estimate_cache_savings
    from han_sim.llm_router import get_tier_summary

    usage = get_stats()
    cache = get_cache_stats()
    savings = estimate_cache_savings()
    tiers = get_tier_summary()

    return jsonify({
        "usage": usage,
        "cache": cache,
        "savings": savings,
        "tier_config": tiers,
    })


# --- 6b) /api/score_extractor/tiers (v5.0 P0-1: 4 档房状态) ---
@app.route('/api/score_extractor/tiers', methods=['GET'])
def api_score_extractor_tiers():
    """v5.0 P0-1: 4 档房配置"""
    from han_sim.score_extractor_pipeline import get_tier_summary
    return jsonify(get_tier_summary())


# --- 6c) /api/intro_hints (v5.0 P1-3: 引导剧本) ---
@app.route('/api/intro_hints', methods=['GET'])
def api_intro_hints():
    """v5.0 P1-3: 返回 6 个月引导剧本 + 当前状态应触发的 hint

    Query params:
        year: 当前年份
        month: 当前月份
        turn: 当前回合
    """
    from han_sim.intro_hints import get_hints_summary, get_intro_hints
    from han_sim.intro_hints import is_in_intro_window

    data = get_hints_summary()
    in_window = False
    try:
        year = int(request.args.get("year", 0))
        month = int(request.args.get("month", 0))
        turn = int(request.args.get("turn", 0))
        from types import SimpleNamespace
        state = SimpleNamespace(year=year, period=month, turn=turn)
        in_window = is_in_intro_window(state)
    except (ValueError, TypeError):
        in_window = False

    return jsonify({
        "hints": data["hints"],
        "window": data["window"],
        "in_intro_window": in_window,
        "total_hints": data["total_hints"],
    })


# --- 6h) /api/issues/closed (v5.1.2 P2-1: ClosedIssuesModal 关案弹窗) ---
@app.route('/api/issues/closed', methods=['GET'])
def api_issues_closed():
    """v5.1.2 P2-1: 列本 turn 内结案的事项 (仿 ming_sim ClosedIssuesModal)

    Query params:
        campaign_id: 战役 ID (必需)
        turn: 当前 turn (缺省=state.turn)
    """
    from han_sim.paths import user_data_path

    campaign_id = (request.args.get("campaign_id") or "").strip()
    if not campaign_id:
        return jsonify({"error": "campaign_id required"}), 400

    db_path = user_data_path(f"campaign_{campaign_id}.db")
    if not os.path.exists(db_path):
        return jsonify({"error": f"campaign {campaign_id} not found"}), 404

    from han_sim.db import GameDB
    db = GameDB(db_path)

    try:
        turn = int(request.args.get("turn", 0))
    except (ValueError, TypeError):
        turn = 0
    if turn <= 0:
        # 从 state 拿当前 turn
        state = db.load_state()
        turn = state.turn if state else 0

    try:
        items = db.list_closed_issues_for_turn(turn)
        return jsonify({
            "issues": items,
            "total": len(items),
            "turn": turn,
        })
    except Exception as e:
        return jsonify({"error": f"closed issues query failed: {e}"}), 500


# --- 6g) /api/gazette (v5.1.1 P1-3: 月初邸报弹窗) ---
@app.route('/api/gazette', methods=['GET'])
def api_gazette():
    """v5.1.1 P1-3: 读 turn_reports 表 (仿 ming_sim /api/menu/status gazette)

    Query params:
        campaign_id: 战役 ID (必需)
        turn: 指定 turn (可选, 缺省=最新)
        recent: 返回最近 N 条 (缺省 0=单条, 12=12条)
    """
    from han_sim.paths import user_data_path

    campaign_id = (request.args.get("campaign_id") or "").strip()
    if not campaign_id:
        return jsonify({"error": "campaign_id required"}), 400

    db_path = user_data_path(f"campaign_{campaign_id}.db")
    if not os.path.exists(db_path):
        return jsonify({"error": f"campaign {campaign_id} not found"}), 404

    from han_sim.db import GameDB
    db = GameDB(db_path)

    try:
        recent = int(request.args.get("recent", 0))
    except (ValueError, TypeError):
        recent = 0
    try:
        turn = int(request.args.get("turn", 0))
    except (ValueError, TypeError):
        turn = 0

    if recent > 0:
        # 列表模式
        items = db.list_recent_reports(limit=recent)
        return jsonify({
            "gazettes": items,
            "total": len(items),
        })
    elif turn > 0:
        # 指定 turn
        item = db.get_turn_report(turn)
        if not item:
            return jsonify({"error": f"no report for turn {turn}"}), 404
        return jsonify({"gazette": item})
    else:
        # 最新一条
        items = db.list_recent_reports(limit=1)
        if not items:
            return jsonify({"error": "no reports yet"}), 404
        return jsonify({"gazette": items[0]})


# --- 6f) /api/legacies (v5.1.0 P0-4: Opening Legacies 开幕负担) ---
@app.route('/api/legacies', methods=['GET'])
def api_legacies():
    """v5.1.0 P0-4: 列当前战役的所有 active legacy (开幕负担)

    Query params:
        campaign_id: 战役 ID (必需)
        include_cleared: 是否含 cleared (默认 false)
    """
    from han_sim.paths import user_data_path
    from han_sim.legacies import get_active_legacy_summary

    campaign_id = (request.args.get("campaign_id") or "").strip()
    if not campaign_id:
        return jsonify({"error": "campaign_id required"}), 400

    db_path = user_data_path(f"campaign_{campaign_id}.db")
    if not os.path.exists(db_path):
        return jsonify({"error": f"campaign {campaign_id} not found"}), 404

    from han_sim.db import GameDB
    db = GameDB(db_path)

    include_cleared = (request.args.get("include_cleared", "false").lower() == "true")
    try:
        rows = db.list_active_legacies(turn=0) if not include_cleared else (
            db.conn.execute(
                "SELECT * FROM legacies WHERE status IN ('active', 'cleared') ORDER BY id"
            ).fetchall()
        )
        rows = [dict(r) for r in rows]
        from han_sim.legacies import format_legacy_for_display
        items = [format_legacy_for_display(r) for r in rows]
        return jsonify({
            "legacies": items,
            "total": len(items),
            "active_count": sum(1 for x in items if x["status"] == "active"),
            "cleared_count": sum(1 for x in items if x["status"] == "cleared"),
        })
    except Exception as e:
        return jsonify({"error": f"legacies query failed: {e}"}), 500


@app.route('/api/legacies/<legacy_key>/clear', methods=['POST'])
def api_clear_legacy(legacy_key):
    """v5.1.0 P0-4: 手动清除 legacy (作弊端点)"""
    from han_sim.paths import user_data_path
    from han_sim.legacies import get_active_legacy_summary

    campaign_id = (request.args.get("campaign_id") or "").strip()
    if not campaign_id:
        return jsonify({"error": "campaign_id required"}), 400

    db_path = user_data_path(f"campaign_{campaign_id}.db")
    if not os.path.exists(db_path):
        return jsonify({"error": f"campaign {campaign_id} not found"}), 404

    from han_sim.db import GameDB
    db = GameDB(db_path)
    try:
        ok = db.clear_legacy_by_key(legacy_key)
        if ok:
            return jsonify({"cleared": True, "key": legacy_key})
        return jsonify({"cleared": False, "error": "legacy not found or not active"}), 404
    except Exception as e:
        return jsonify({"error": f"clear legacy failed: {e}"}), 500


# --- 6e) /api/budget (v5.1.0 P0-2: 国库/内库 分账户预算视图) ---
@app.route('/api/budget', methods=['GET'])
def api_budget():
    """v5.1.0 P0-2: 财政预算视图 (仿 ming_sim /api/budget)

    Query params:
        campaign_id: 战役 ID (必需)
        include_provinces: 是否返 13 州分账 (默认 true)
    """
    from han_sim.budget import (
        ACCOUNT_HANSHIKU, ACCOUNT_INNER, compute_budget_lines,
    )
    from han_sim.paths import user_data_path

    campaign_id = (request.args.get("campaign_id") or "").strip()
    if not campaign_id:
        return jsonify({"error": "campaign_id required"}), 400

    db_path = user_data_path(f"campaign_{campaign_id}.db")
    if not os.path.exists(db_path):
        return jsonify({"error": f"campaign {campaign_id} not found"}), 404

    include_provinces = (request.args.get("include_provinces", "true").lower() == "true")

    from han_sim.db import GameDB
    db = GameDB(db_path)

    # 加载 state
    state = db.load_state()
    if state is None:
        return jsonify({"error": "no state"}), 404

    try:
        budgets = compute_budget_lines(state, db)
        hanshiku = budgets[ACCOUNT_HANSHIKU].to_dict()
        neiku = budgets[ACCOUNT_INNER].to_dict()
        provinces = budgets.get("_provinces", [])

        result = {
            ACCOUNT_HANSHIKU: hanshiku,
            ACCOUNT_INNER: neiku,
            "turn": {"year": state.year, "period": state.period, "turn": state.turn},
            "intercept_applies": int(state.metrics.get("威权", 0)) < 30,
        }
        if include_provinces:
            result["provinces"] = provinces
            result["province_count"] = len(provinces)
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({"error": f"budget compute failed: {e}", "trace": traceback.format_exc()}), 500


# --- 6d) /api/event_memories (v5.1.0 P0-1: 事件记忆) ---
@app.route('/api/event_memories', methods=['GET'])
def api_event_memories():
    """v5.1.0 P0-1: 事件记忆召回 (仿 ming_sim/memories.py:729)

    支持 3 种召回模式:
        1) subject 召回: ?campaign_id=&subject=曹操&subject_type=character&limit=10
        2) keyword 召回: ?campaign_id=&keywords=董卓,衣带诏&turn=50&limit=10
        3) time 召回: ?campaign_id=&year=200&period=3&keywords=曹操

    Query params:
        campaign_id: 战役 ID (必需)
        subject: 主体名 (可选, 与 subject_type 配套)
        subject_type: character/region/army/court/faction (可选)
        keywords: 逗号分隔关键词 (可选)
        year: 年份 (可选, time 召回用)
        period: 月份 (可选, time 召回用)
        turn: 当前回合 (用于 TTL 过滤)
        limit: 上限 (默认 10)
        ignore_expiry: True 时忽略 TTL (默认 False)
    """
    from han_sim.paths import user_data_path

    campaign_id = (request.args.get("campaign_id") or "").strip()
    if not campaign_id:
        return jsonify({"error": "campaign_id required"}), 400

    db_path = user_data_path(f"campaign_{campaign_id}.db")
    if not os.path.exists(db_path):
        return jsonify({"error": f"campaign {campaign_id} not found"}), 404

    from han_sim.db import GameDB
    db = GameDB(db_path)

    try:
        limit = int(request.args.get("limit", 10))
    except (ValueError, TypeError):
        limit = 10
    try:
        turn = int(request.args.get("turn", 0))
    except (ValueError, TypeError):
        turn = 0
    ignore_expiry = (request.args.get("ignore_expiry", "false").lower() == "true")

    # 模式 1: subject 召回
    subject = (request.args.get("subject") or "").strip()
    subject_type = (request.args.get("subject_type") or "").strip()
    if subject and subject_type:
        try:
            rows = db.conn.execute(
                """SELECT * FROM event_memories
                   WHERE subject_type = ? AND subject_id = ?
                   AND (expires_turn IS NULL OR expires_turn = -1 OR expires_turn >= ?)
                   ORDER BY importance DESC, turn DESC LIMIT ?""",
                (subject_type, subject, turn, limit),
            ).fetchall()
            memories = [dict(r) for r in rows]
            for m in memories:
                m["id"] = int(m["id"])
                m["turn"] = int(m["turn"])
                m["year"] = int(m["year"])
                m["period"] = int(m["period"])
                m["importance"] = int(m["importance"])
                if m.get("expires_turn") is not None:
                    m["expires_turn"] = int(m["expires_turn"])
                try:
                    m["tags"] = json.loads(m.get("tags") or "[]")
                except Exception:
                    m["tags"] = []
            return jsonify({
                "memories": memories,
                "total": len(memories),
                "mode": "subject",
                "subject": subject,
                "subject_type": subject_type,
                "ignore_expiry": ignore_expiry,
            })
        except Exception as e:
            return jsonify({"error": f"subject query failed: {e}"}), 500

    # 模式 2 & 3: keyword / time 召回
    keywords_raw = (request.args.get("keywords") or "").strip()
    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
    if not keywords:
        return jsonify({"error": "subject/subject_type OR keywords required"}), 400

    try:
        # 模式 3: time 召回 (ignore_expiry=True, 查该月历史)
        year = int(request.args.get("year", 0))
        period = int(request.args.get("period", 0))
        if year and period:
            memories = db.conn.execute(
                """SELECT * FROM event_memories
                   WHERE year = ? AND period = ?
                   AND (subject_id IN ({placeholders}) OR tags LIKE ? OR tags LIKE ? OR tags LIKE ?)
                   ORDER BY importance DESC, id DESC LIMIT ?""".format(
                    placeholders=",".join("?" for _ in keywords)
                ),
                (year, period, *keywords, f"%{keywords[0]}%",
                 f"%{keywords[0] if len(keywords) < 2 else keywords[1]}%",
                 f"%{keywords[-1]}%", limit),
            ).fetchall()
            memories = [dict(r) for r in memories]
            for m in memories:
                m["id"] = int(m["id"])
                m["turn"] = int(m["turn"])
                m["year"] = int(m["year"])
                m["period"] = int(m["period"])
                m["importance"] = int(m["importance"])
                if m.get("expires_turn") is not None:
                    m["expires_turn"] = int(m["expires_turn"])
                try:
                    m["tags"] = json.loads(m.get("tags") or "[]")
                except Exception:
                    m["tags"] = []
            return jsonify({
                "memories": memories,
                "total": len(memories),
                "mode": "time",
                "year": year,
                "period": period,
                "keywords": keywords,
            })
    except (ValueError, TypeError):
        pass

    # 模式 2: keyword 召回 (走 get_memories_by_keywords)
    try:
        memories = db.get_memories_by_keywords(
            keywords=keywords,
            turn=turn or 999,
            limit=limit,
            ignore_expiry=ignore_expiry,
        )
        return jsonify({
            "memories": memories,
            "total": len(memories),
            "mode": "keyword",
            "keywords": keywords,
            "turn": turn,
            "ignore_expiry": ignore_expiry,
        })
    except Exception as e:
        return jsonify({"error": f"keyword query failed: {e}"}), 500


# --- 7) /api/saves/list (存档列表含元数据) ---
@app.route('/api/saves/list', methods=['GET'])
def api_saves_list():
    from han_sim.save_system import list_saves
    campaign_id = request.args.get('campaign_id', '')
    if not campaign_id:
        return jsonify({'error': 'campaign_id required'}), 400
    return jsonify({'saves': list_saves(campaign_id), 'max_slots': 5})


# --- 8) /api/saves/meta (单槽位元数据) ---
@app.route('/api/saves/meta', methods=['GET'])
def api_saves_meta():
    from han_sim.save_system import read_save_meta
    campaign_id = request.args.get('campaign_id', '')
    slot = int(request.args.get('slot', 0))
    if not campaign_id or slot < 1 or slot > 5:
        return jsonify({'error': 'invalid args'}), 400
    meta = read_save_meta(campaign_id, slot)
    if not meta:
        return jsonify({'error': 'no such save'}), 404
    return jsonify({'meta': meta})


# --- 9) /api/saves/cleanup (清理超出槽位) ---
@app.route('/api/saves/cleanup', methods=['POST'])
def api_saves_cleanup():
    from han_sim.save_system import cleanup_old_saves
    data = request.get_json() or {}
    campaign_id = data.get('campaign_id', '')
    keep = int(data.get('keep', 5))
    if not campaign_id:
        return jsonify({'error': 'campaign_id required'}), 400
    n = cleanup_old_saves(campaign_id, keep)
    return jsonify({'cleaned': n})


# --- 10) /api/health/llm (LLM 健康检查) ---
@app.route('/api/health/llm', methods=['GET'])
def api_health_llm():
    from han_sim.llm_cache import get_cache_stats
    from han_sim.api_key_router import get_server_routes_summary
    return jsonify({
        'cache': get_cache_stats(),
        'server_key': get_server_routes_summary(),
    })


# --- 11) /api/health/full (综合健康, 含 DB) ---
@app.route('/api/health/full', methods=['GET'])
def api_health_full():
    """综合健康检查: DB + 服务端 Key + KV cache + 用量表."""
    out = {'status': 'ok', 'checks': {}}
    # 1) DB
    import sqlite3
    from pathlib import Path
    try:
        db_path = Path('/home/admin/.openclaw/workspace/han-empire/data/han_empire.db')
        if db_path.exists():
            with sqlite3.connect(str(db_path)) as conn:
                cnt = conn.execute('SELECT COUNT(*) FROM game_state').fetchone()[0]
            out['checks']['db'] = {'ok': True, 'campaigns': cnt}
        else:
            out['checks']['db'] = {'ok': False, 'error': 'db not found'}
    except Exception as e:
        out['checks']['db'] = {'ok': False, 'error': str(e)}
        out['status'] = 'degraded'

    # 2) 服务端 Key
    from han_sim.api_key_router import get_server_routes_summary
    out['checks']['server_key'] = get_server_routes_summary()

    # 3) KV cache
    from han_sim.llm_cache import get_cache_stats
    out['checks']['cache'] = get_cache_stats()

    # 4) 用量
    from han_sim.usage_tracker import get_stats
    out['checks']['usage'] = get_stats()

    return jsonify(out)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    app.run(host='0.0.0.0', port=port, debug=False)


# ═══════════════════════════════════════════════════════════════
# v3.1 新增 8 端点: 科技树 + 后果链 + 决策回放
# ═══════════════════════════════════════════════════════════════

# 全局状态 (per-process, 简化版)
_tech_states: Dict[str, Any] = {}  # session_id -> TechState
_consequence_chains: Dict[str, Any] = {}  # session_id -> ConsequenceChain
_decision_logs: Dict[str, Any] = {}  # session_id -> DecisionLog


def _get_tech_state(session_id: str):
    if session_id not in _tech_states:
        _tech_states[session_id] = get_tech_engine().init_state()
    return _tech_states[session_id]


def _get_consequence_chain(session_id: str):
    if session_id not in _consequence_chains:
        _consequence_chains[session_id] = get_consequence_chain()
    return _consequence_chains[session_id]


def _get_decision_log(session_id: str):
    if session_id not in _decision_logs:
        _decision_logs[session_id] = DecisionLog()
    return _decision_logs[session_id]


@app.route('/api/tech-tree', methods=['GET'])
def api_tech_tree():
    """获取科技树视图 (DAG)"""
    session_id = request.args.get('session_id', 'default')
    eng = get_tech_engine()
    state = _get_tech_state(session_id)
    return jsonify({
        'ok': True,
        'tree': eng.get_tree_view(state),
        'total_effects': eng.get_total_effects(state),
    })


@app.route('/api/tech-tree/unlock', methods=['POST'])
def api_tech_unlock():
    """解锁科技节点"""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    node_id = data.get('node_id')
    if not node_id:
        return jsonify({'ok': False, 'error': 'node_id 必填'}), 400
    eng = get_tech_engine()
    state = _get_tech_state(session_id)
    ok, reason, node = eng.unlock(node_id, state)
    return jsonify({
        'ok': ok, 'reason': reason,
        'node': {'id': node.id, 'name': node.name, 'effects': node.effects} if node else None,
        'reputation': state.reputation,
    })


@app.route('/api/tech-tree/reputation', methods=['POST'])
def api_tech_add_reputation():
    """增加声望 (回合结算/事件奖励)"""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    amount = int(data.get('amount', 0))
    eng = get_tech_engine()
    state = _get_tech_state(session_id)
    eng.add_reputation(amount, state)
    return jsonify({'ok': True, 'reputation': state.reputation})


@app.route('/api/consequence-chain', methods=['GET'])
def api_consequence_chain():
    """获取后果链 DAG 视图"""
    session_id = request.args.get('session_id', 'default')
    turn = int(request.args.get('turn', 0))
    chain = _get_consequence_chain(session_id)
    return jsonify({
        'ok': True,
        'chain': chain.get_chain_view(turn),
        'active_effects': chain.get_active_effects(turn),
    })


@app.route('/api/consequence-chain/record', methods=['POST'])
def api_consequence_record():
    """记录玩家决策, 派生后果"""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    decision_id = data.get('decision_id', f'dec_{len(_get_consequence_chain(session_id).nodes)}')
    decision_type = data.get('decision_type', '诏书')
    description = data.get('description', '')
    effects = data.get('effects', {})
    target = data.get('target', '全国')
    turn = int(data.get('turn', 0))
    ctype = ConsequenceType(data.get('consequence_type', 'short'))
    chain = _get_consequence_chain(session_id)
    created = chain.record_decision(
        decision_id=decision_id,
        decision_type=decision_type,
        description=description,
        effects=effects,
        target=target,
        consequence_type=ctype,
        current_turn=turn,
    )
    return jsonify({
        'ok': True,
        'consequence_count': len(created),
        'consequence_ids': [n.id for n in created],
    })


@app.route('/api/consequence-chain/effects', methods=['GET'])
def api_consequence_effects():
    """获取当前活跃后果总效果"""
    session_id = request.args.get('session_id', 'default')
    turn = int(request.args.get('turn', 0))
    chain = _get_consequence_chain(session_id)
    return jsonify({
        'ok': True,
        'turn': turn,
        'active_effects': chain.get_active_effects(turn),
        'active_count': len(chain.get_active_consequences(turn)),
    })


@app.route('/api/decision-log', methods=['GET'])
def api_decision_log():
    """获取决策日志 (回放时间线)"""
    session_id = request.args.get('session_id', 'default')
    turn = request.args.get('turn')
    turn = int(turn) if turn else None
    log = _get_decision_log(session_id)
    entries = log.get_entries(turn=turn)
    return jsonify({
        'ok': True,
        'entries': [e.__dict__ for e in entries],
        'timeline': log.get_timeline(),
        'stats': log.get_stats(),
    })


@app.route('/api/decision-log/record', methods=['POST'])
def api_decision_record():
    """记录玩家决策"""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    log = _get_decision_log(session_id)
    entry = log.record(
        turn=int(data.get('turn', 0)),
        decision_type=data.get('decision_type', ''),
        action=data.get('action', ''),
        description=data.get('description', ''),
        effects=data.get('effects', {}),
        game_year=data.get('game_year', ''),
        consequence_ids=data.get('consequence_ids', []),
    )
    return jsonify({
        'ok': True,
        'entry_id': entry.id,
        'entry': entry.__dict__,
    })


# ═══════════════════════════════════════════════════════════════
# v3.2 新增 6 端点: 教程 + DAG 性能 + 自动存档
# ═══════════════════════════════════════════════════════════════

# 全局状态
_tutorial_states: Dict[str, Any] = {}  # session_id -> TutorialState


def _get_tutorial_state(session_id: str):
    if session_id not in _tutorial_states:
        _tutorial_states[session_id] = get_tutorial_engine().init_state()
    return _tutorial_states[session_id]


@app.route('/api/tutorial', methods=['GET'])
def api_tutorial_state():
    """获取当前引导状态"""
    session_id = request.args.get('session_id', 'default')
    eng = get_tutorial_engine()
    state = _get_tutorial_state(session_id)
    return jsonify({
        'ok': True,
        'progress': eng.get_progress(state),
        'current_step': eng.get_step(state.current_step).__dict__ if eng.get_step(state.current_step) else None,
        'all_steps': [s.__dict__ for s in eng.get_all_steps()],
    })


@app.route('/api/tutorial/advance', methods=['POST'])
def api_tutorial_advance():
    """引导前进一步"""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    eng = get_tutorial_engine()
    state = _get_tutorial_state(session_id)
    has_next = eng.advance(state)
    return jsonify({
        'ok': True,
        'has_next': has_next,
        'progress': eng.get_progress(state),
    })


@app.route('/api/tutorial/skip', methods=['POST'])
def api_tutorial_skip():
    """跳过引导"""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    eng = get_tutorial_engine()
    state = _get_tutorial_state(session_id)
    eng.skip(state)
    return jsonify({'ok': True, 'progress': eng.get_progress(state)})


@app.route('/api/dag/optimize', methods=['POST'])
def api_dag_optimize():
    """DAG 性能优化 (剪枝 + LOD + 视口)"""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    eng = get_tech_engine()
    state = _get_tech_state(session_id)
    full_tree = eng.get_tree_view(state)
    nodes = full_tree['nodes']
    q = get_dag_query()
    # 应用剪枝
    visible_only = data.get('visible_only', False)
    nodes = q.prune_by_status(nodes, visible_only=visible_only)
    # LOD 简化
    simplified = q.lod_simplify(nodes, threshold=int(data.get('lod_threshold', 100)))
    # 统计
    stats = q.get_stats(nodes)
    # 视口过滤
    viewport = data.get('viewport')
    if viewport:
        nodes = q.get_viewport_nodes(nodes, viewport)
    return jsonify({
        'ok': True,
        'nodes': simplified if data.get('use_lod', False) else nodes,
        'stats': stats,
        'optimization': {
            'visible_only': visible_only,
            'lod_applied': data.get('use_lod', False),
            'viewport_filtered': viewport is not None,
            'original_count': len(full_tree['nodes']),
            'returned_count': len(simplified if data.get('use_lod', False) else nodes),
        }
    })


@app.route('/api/auto-save', methods=['POST'])
def api_auto_save():
    """自动存档 (每 5 回合触发)"""
    data = request.get_json() or {}
    campaign_id = data.get('campaign_id', 'default')
    turn = int(data.get('turn', 0))
    state = data.get('state', {})
    game_year = data.get('game_year', '')
    mgr = get_auto_save_manager()
    slot = mgr.auto_save(campaign_id, turn, state, game_year)
    if slot:
        return jsonify({
            'ok': True,
            'saved': True,
            'slot': slot.__dict__,
        })
    return jsonify({'ok': True, 'saved': False, 'reason': '间隔未到 (每5回合)'})


@app.route('/api/auto-save/list', methods=['GET'])
def api_auto_save_list():
    """列出自动存档"""
    campaign_id = request.args.get('campaign_id', 'default')
    mgr = get_auto_save_manager()
    saves = mgr.list_auto_saves(campaign_id)
    return jsonify({
        'ok': True,
        'saves': [s.__dict__ for s in saves],
        'count': len(saves),
    })