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

# ── v1.13.0 乾坤大挪移 Phase B：注入 GameContent 到 agents 模块 ──
# 让 create_chat_memory_agent / create_minister_agent 等能拿到 prompt 字段
_agents.bind_content(load_game_content())
import json
from typing import List, Dict

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
    return jsonify({'factions': []})


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


@app.route('/api/campaigns/<campaign_id>/cheat', methods=['POST'])
def execute_cheat(campaign_id):
    """执行作弊命令"""
    data = request.get_json() or {}
    command = data.get('command', '')
    args = data.get('args', {})

    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    state = session.state

    output = ''
    success = True

    if command == 'status':
        output = f"""当前状态：
年份：{state.year}年 {state.period}月
威权：{state.metrics.get('威权', 0)}
声望：{state.metrics.get('声望', 0)}
藩镇：{state.metrics.get('藩镇', 0)}
汉室库：{state.metrics.get('汉室库', 0)}万两
回合：{state.turn}"""
    elif command == 'add-authority':
        n = int(args.get('n', 10))
        state.metrics['威权'] = state.metrics.get('威权', 0) + n
        output = f'威权 +{n}，当前：{state.metrics.get("威权", 0)}'
    elif command == 'set-authority':
        n = int(args.get('n', 50))
        state.metrics['威权'] = n
        output = f'威权已设置为：{n}'
    elif command == 'add-loyalty':
        n = int(args.get('n', 10))
        state.metrics['声望'] = state.metrics.get('声望', 0) + n
        output = f'声望 +{n}，当前：{state.metrics.get("声望", 0)}'
    elif command == 'unlock-skills':
        output = '技能已解锁（模拟）'
    elif command == 'skip-month':
        state.next_period()
        output = f'进入{state.year}年{state.period}月'
    else:
        output = f'未知命令: {command}'
        success = False

    session.save()
    GAMES[campaign_id] = session

    return jsonify({'success': success, 'output': output})


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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    app.run(host='0.0.0.0', port=port, debug=False)