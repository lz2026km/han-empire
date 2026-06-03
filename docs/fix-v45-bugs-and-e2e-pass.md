# v4.5 真 Bug 修复 + E2E 跑通 (2026-06-03)

## 一、v4.5 范围发现的真 Bug

### Bug 1: issues.py:1039 - ongoing_effects 重复 json.loads
**症状**:
```
TypeError: the JSON object must be str, bytes or bytearray, not dict
```

**根因**:
SQLite Python 驱动对 JSON 字段已自动反序列化为 dict, 代码再 `json.loads` 一次.

**修复** (han_sim/issues.py:1039-1047):
```python
_raw = row.get("ongoing_effects")
if isinstance(_raw, dict):
    ongoing = _raw
elif isinstance(_raw, (str, bytes, bytearray)):
    ongoing = json.loads(_raw or "{}")
else:
    ongoing = {}
```

### Bug 2: db.py:1116 - SQLite bind 不支持 list
**症状**:
```
sqlite3.ProgrammingError: Error binding parameter 2: type 'list' is not supported
```

**根因**:
`state.metrics` 字典的 value 可能是 list/dict 复合值, SQL bind 不能直接传 list.

**修复** (han_sim/db.py:1115-1126):
```python
for key, value in state.metrics.items():
    if isinstance(value, (list, dict)):
        import json as _json
        bind_value = _json.dumps(value, ensure_ascii=False)
    else:
        bind_value = value
    self.conn.execute(...)
```

## 二、E2E 验证

```
1. POST /api/campaigns (创朝) → 200, campaign_id=c3ae445f9
2. POST /api/campaigns/<id>/next_turn → 200
   返回 SimulationResult:
   - fiscal: tax=158, expense=23, net=135, treasury=335
   - provinces: 51 个州郡
   - faction_delta: 6 派系权威变动
   - warlord_changes: 董卓 整军经武
3. GET /portraits/main/{xundi,yuan_shu,han_su,dongcheng}.jpg → 200
4. GET /api/health → 200
```

## 三、结论
v4.5 范围游戏跑通无错, 可在 retry 补图完成后出 v4.9.
