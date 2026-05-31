"""
Flask REST API Server for han-empire
Replaces Gradio with a REST API + React frontend
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import os
from han_sim.session import GameSession
from han_sim.simulation import run_monthly_simulation
from han_sim.decree import issue_secret_edict
from han_sim.portraits import save_custom_portrait, delete_custom_portrait, list_custom_portraits
import json
from typing import List, Dict

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
    if campaign_id not in GAMES:
        GAMES[campaign_id] = GameSession.load(campaign_id)

    session = GAMES[campaign_id]
    state = _state_to_dict(session.state)
    ministers = session.get_active_ministers()
    factions = []

    from han_sim.models import FACTION_DATA
    for fid, fdata in FACTION_DATA.items():
        influence = session.state.faction_influence.get(fid, 50)
        factions.append({
            'id': fid,
            'name': fdata['name'],
            'leader_name': fdata['leader'],
            'influence': influence,
            'color': fdata['color'],
            'description': fdata['desc'],
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
    result = issue_secret_edict(session.state, session.db)

    return jsonify({
        'result': {
            'success': result.success,
            'message': result.narrative or result.reason,
            'authority_delta': result.authority_delta,
            'faction_delta': result.faction_delta,
            'minister_changes': result.minister_changes,
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
        except Exception:
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
        agent = create_minister_agent(minister, session.state, "", "")
        response = agent.run(message)
        text = response.content if hasattr(response, 'content') else str(response)

        return jsonify({
            'result': text,
            'chat_history': [
                {'role': 'emperor', 'text': message},
                {'role': 'minister', 'text': text}
            ]
        })
    except Exception as e:
        return jsonify({'result': f'召对失败: {str(e)}'})


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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    app.run(host='0.0.0.0', port=port, debug=False)