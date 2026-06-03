"""v2.1.0 Phase 8: 端到端 20 真路径测试

20 个真实路径覆盖 v2.1.0 全部新 API:
1. 战役: list / simulate (官渡/赤壁/夷陵)
2. 派系: faction_info (4 派系 12 目标)
3. 科举: subjects / ranks / exam (3 智力档)
4. 史记: historical / timeline / 4 史官 / record

每个测试 = 真 HTTP 请求 + 验证 200 + 验证字段
"""
import subprocess
import time
import urllib.request
import json
import sys

def http_get(url, timeout=5):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def http_post(url, data=None, timeout=5):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(url, data=body, method='POST',
                                  headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def run_tests():
    base = 'http://localhost:5555'
    passed = 0
    failed = 0
    results = []

    def check(name, ok, detail=''):
        nonlocal passed, failed
        if ok:
            passed += 1
            results.append(f'  ✓ {name}{": " + detail if detail else ""}')
        else:
            failed += 1
            results.append(f'  ✗ {name}: {detail}')

    # ---- 准备: 创建 campaign ----
    cid = http_post(f'{base}/api/campaigns').get('campaign_id')
    check('1. POST /api/campaigns', bool(cid), cid)

    # ---- 战役 API (Phase 4) ----
    battles = http_get(f'{base}/api/battles')['battles']
    check('2. GET /api/battles', len(battles) == 3, f'{len(battles)} 战役')

    for i, key in enumerate(['guandu', 'chibi', 'yiling'], 3):
        r = http_post(f'{base}/api/battles/simulate', {'battle_key': key})['report']
        check(f'{i}. POST /api/battles/simulate ({key})',
              r['battle_name'] and len(r['rounds']) > 0,
              f'{r["battle_name"]} {len(r["rounds"])} 回合')

    # ---- 派系 API (Phase 5) ----
    fi = http_get(f'{base}/api/campaigns/{cid}/faction_info')
    check('6. GET /faction_info (4 派系目标)',
          len(fi.get('goals', {})) == 4 and sum(len(v) for v in fi['goals'].values()) == 12,
          f'{len(fi.get("goals", {}))} 派系, {sum(len(v) for v in fi["goals"].values())} 目标')
    check('7. GET /faction_info (12 外交)',
          len(fi.get('diplomacy', {})) == 12, f'{len(fi.get("diplomacy", {}))} 关系')

    # ---- 科举 API (Phase 6) ----
    subjects = http_get(f'{base}/api/civil/subjects')['subjects']
    check('8. GET /api/civil/subjects', len(subjects) == 5, f'{subjects}')

    ranks = http_get(f'{base}/api/civil/ranks')['ranks']
    check('9. GET /api/civil/ranks', len(ranks) == 10, f'{len(ranks)} 级')

    # 科举 3 智力档
    for intel in [30, 60, 95]:
        r = http_post(f'{base}/api/civil/exam', {'candidate_name': f'应试者{intel}', 'intelligence': intel})['result']
        check(f'10-12. POST /api/civil/exam (智{intel})', r['score'] >= 0 and r['score'] <= 100, f'{r["score"]}分 {r["rank"]}')

    # 罢免 + 流放
    d = http_post(f'{base}/api/civil/dismiss', {'name': '董卓', 'reason': '专权'})['result']
    check('13. POST /api/civil/dismiss', d['action'] == '罢免', d['narrative'][:30])

    e = http_post(f'{base}/api/civil/exile', {'name': '李儒', 'reason': '助纣'})['result']
    check('14. POST /api/civil/exile', e['action'] == '流放' and '流放至' in e['narrative'], e['narrative'][:30])

    # ---- 史记 API (Phase 7) ----
    hist = http_get(f'{base}/api/chronicle/historical')
    check('15. GET /api/chronicle/historical', hist['total'] == 13, f'{hist["total"]} 件')

    tl = http_get(f'{base}/api/chronicle/timeline')['timeline']
    check('16. GET /api/chronicle/timeline', len(tl) == 12, f'{len(tl)} 年')

    historians = http_get(f'{base}/api/chronicle/historians')['historians']
    check('17. GET /api/chronicle/historians', len(historians) == 4, f'{list(historians.keys())}')

    for i, h in enumerate(['司马氏', '班氏', '范氏', '陈氏'], 18):
        c = http_post(f'{base}/api/chronicle/historian', {'historian': h, 'title': '曹丕代汉'})['comment']
        check(f'{i}. POST /api/chronicle/historian ({h})', len(c) > 5, c[:30])

    # 记录
    rec = http_post(f'{base}/api/chronicle/record', {'year': 200, 'title': '测试事件'})['event']
    check('20. POST /api/chronicle/record (已记录)', rec['title'] == '测试事件')

    return passed, failed, results


if __name__ == '__main__':
    # 启动 server
    p = subprocess.Popen(
        ['/home/admin/.hermes/hermes-agent/venv/bin/python', 'server.py'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    time.sleep(3)

    try:
        passed, failed, results = run_tests()
        print('=' * 60)
        print(f'v2.1.0 Phase 8 端到端 20 真路径测试')
        print('=' * 60)
        for r in results:
            print(r)
        print('=' * 60)
        print(f'通过: {passed} / 失败: {failed} / 总: {passed + failed}')
        print('=' * 60)
        sys.exit(0 if failed == 0 else 1)
    finally:
        subprocess.run(['pkill', '-f', 'python.*server.py'], capture_output=True)
        p.terminate()
