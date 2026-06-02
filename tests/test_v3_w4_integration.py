"""v3.0 W4: server.py 11 新端点 + save_system + usage_tracker 测试"""
import sys, os
sys.path.insert(0, '/home/admin/.openclaw/workspace/han-empire')

def test_save_system():
    from han_sim.save_system import (
        build_save_meta, list_saves, read_save_meta, delete_save,
        cleanup_old_saves, MAX_SLOTS, get_save_path, write_save_meta,
    )
    cid = "test_w4"
    # 0) 先清场
    for slot in range(1, MAX_SLOTS + 1):
        delete_save(cid, slot)
    
    # 1) 构造 meta
    meta = build_save_meta(turn=10, year=200, month=3, summary='测试存档')
    assert meta['turn'] == 10
    assert meta['year'] == 200
    assert '汉献帝' in meta['emperor']
    print(f"  ✓ build_save_meta: 回合{meta['turn']}, 年{meta['year']}, 月{meta['month']}")
    
    # 2) list_saves 空 (清场后)
    saves = list_saves(cid)
    assert saves == []
    print(f"  ✓ list_saves 清场空: {saves}")
    
    # 3) 写测试存档
    for slot in range(1, 4):
        p = get_save_path(cid, slot)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f'{{"test": true, "slot": {slot}}}', encoding='utf-8')
        write_meta = dict(meta, slot=slot)
        write_meta['summary'] = f'槽{slot}'
        write_save_meta(cid, slot, write_meta)
    
    # 4) list_saves 3 个
    saves = list_saves(cid)
    assert len(saves) == 3
    print(f"  ✓ list_saves 3 个: slots={[s['slot'] for s in saves]}")
    
    # 5) read_save_meta
    m1 = read_save_meta(cid, 1)
    assert m1['slot'] == 1
    assert m1['summary'] == '槽1'  # 我们的写入是 '槽1'
    print(f"  ✓ read_save_meta slot 1: {m1['summary']}")
    
    # 6) cleanup (keep=2, 删 1 个)
    n = cleanup_old_saves(cid, keep=2)
    assert n == 1
    saves = list_saves(cid)
    assert len(saves) == 2
    print(f"  ✓ cleanup_old_saves(keep=2): 删 {n}, 剩 {len(saves)}")
    
    # 7) 清理
    for s in saves:
        delete_save(cid, s['slot'])
    saves = list_saves(cid)
    assert saves == []
    print(f"  ✓ 全清: {saves}")


def test_usage_tracker():
    from han_sim.usage_tracker import (
        record_usage, get_stats, get_recent, COST_PER_MILLION_TOKENS_USD,
    )
    # 1) 记录
    record_usage('decree', 'minimax', 'MiniMax-Text-01', 1000, 500)
    record_usage('court_debate', 'minimax', 'MiniMax-Text-01', 2000, 1000)
    
    # 2) stats
    stats = get_stats()
    assert stats['today'] >= 4500
    assert stats['currency'] == 'USD'
    assert stats['rate_per_million'] == COST_PER_MILLION_TOKENS_USD
    print(f"  ✓ stats: today={stats['today']}, week={stats['week']}, cost=${stats['cost']}")
    
    # 3) recent
    recent = get_recent(5)
    assert len(recent) >= 2
    print(f"  ✓ recent: {len(recent)} 条")


def test_api_routes_via_flask():
    """用 flask test_client 测 11 个新端点."""
    sys.path.insert(0, '/home/admin/.openclaw/workspace/han-empire')
    os.chdir('/home/admin/.openclaw/workspace/han-empire')
    from server import app
    
    client = app.test_client()
    
    # 1) /api/settings/api-key GET
    resp = client.get('/api/settings/api-key')
    data = resp.get_json()
    print(f"  ✓ GET /api/settings/api-key: status={resp.status_code}, has_fallback={data.get('has_fallback')}")
    assert resp.status_code == 200
    
    # 2) /api/settings/api-key POST (local 模式 + 假 client key)
    resp = client.post('/api/settings/api-key', json={
        'mode': 'local',
        'api_key': 'sk-fake-for-test',
        'base_url': 'https://api.deepseek.com/v1',
        'model': 'deepseek-chat',
        'purpose': 'decree',
    })
    data = resp.get_json()
    print(f"  ✓ POST /api/settings/api-key (local): ok={data.get('ok')}, mode={data.get('mode')}, from_local={data.get('from_local')}")
    assert data['ok'] is True
    assert data['mode'] == 'local'
    assert data['from_local'] is True
    
    # 3) /api/llm/test (local 模式)
    resp = client.post('/api/llm/test', json={
        'mode': 'local',
        'api_key': 'sk-fake-for-test',
        'base_url': 'https://api.deepseek.com/v1',
        'model': 'deepseek-chat',
    })
    data = resp.get_json()
    print(f"  ✓ POST /api/llm/test (local): ok={data.get('ok')}, message={data.get('message', '')[:60]}")
    assert data['ok'] is True
    
    # 4) /api/usage/stats
    resp = client.get('/api/usage/stats')
    data = resp.get_json()
    print(f"  ✓ GET /api/usage/stats: today={data.get('today')}, currency={data.get('currency')}")
    assert 'today' in data
    
    # 5) /api/usage/recent
    resp = client.get('/api/usage/recent?limit=5')
    data = resp.get_json()
    print(f"  ✓ GET /api/usage/recent: {len(data.get('records', []))} 条")
    
    # 6) /api/llm/models
    resp = client.get('/api/llm/models')
    data = resp.get_json()
    print(f"  ✓ GET /api/llm/models: {len(data.get('providers', []))} 家")
    assert len(data['providers']) >= 4
    
    # 7) /api/llm/cache-stats
    resp = client.get('/api/llm/cache-stats')
    data = resp.get_json()
    print(f"  ✓ GET /api/llm/cache-stats: hit_rate={data['cache_stats'].get('hit_rate', '0%')}")
    
    # 8) /api/saves/list
    resp = client.get('/api/saves/list?campaign_id=test')
    data = resp.get_json()
    print(f"  ✓ GET /api/saves/list: max_slots={data.get('max_slots')}")
    assert data['max_slots'] == 5
    
    # 9) /api/saves/meta (不存在的 campaign)
    resp = client.get('/api/saves/meta?campaign_id=nonexistent_xyz&slot=99')
    # campaign 不存在时, server.py 返回 400 (invalid args) 或 404
    print(f"  ✓ GET /api/saves/meta: status={resp.status_code}")
    assert resp.status_code in (400, 404)
    
    # 10) /api/saves/cleanup
    resp = client.post('/api/saves/cleanup', json={'campaign_id': 'test', 'keep': 5})
    data = resp.get_json()
    print(f"  ✓ POST /api/saves/cleanup: cleaned={data.get('cleaned')}")
    
    # 11) /api/health/full
    resp = client.get('/api/health/full')
    data = resp.get_json()
    print(f"  ✓ GET /api/health/full: status={data.get('status')}, checks={list(data.get('checks', {}).keys())}")


# === 跑全部 ===
print("=" * 60)
print("W4 阶段四: API + 存档 + 用量 集成测试")
print("=" * 60)
tests = [
    ("3.0-AP-2 存档系统 save_system", test_save_system),
    ("3.0-AP-3 Token 用量 usage_tracker", test_usage_tracker),
    ("3.0-AP-1/4 11 个新端点", test_api_routes_via_flask),
]
passed = 0
for name, fn in tests:
    print(f"\n[{name}]")
    try:
        fn()
        passed += 1
        print(f"  ✅ {name} PASSED")
    except Exception as e:
        print(f"  ❌ {name} FAILED: {e}")
        import traceback; traceback.print_exc()

print(f"\n{'='*60}\n结果: {passed}/{len(tests)} passed\n{'='*60}")
sys.exit(0 if passed == len(tests) else 1)
