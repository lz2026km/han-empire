"""
Flask REST API Server for han-empire
Replaces Gradio with a REST API + React frontend
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request
from flask_cors import CORS
from han_sim.session import GameSession
from han_sim.simulation import run_monthly_simulation
from han_sim.decree import issue_secret_edict
import json

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
    sim_result = run_monthly_simulation(session)
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    app.run(host='0.0.0.0', port=port, debug=False)