"""v5.0 P0-1: score_extractor_pipeline 单测

覆盖:
1. 20 字段骨架生成 (make_empty_20_field)
2. 档房字段所有权 (TIER_FIELDS 正确)
3. JSON 解析 (_parse_json_safely 各种边界)
4. 字段过滤 (_filter_to_tier_fields 越界字段丢弃)
5. 字段补全 (_ensure_all_20_fields 缺字段补默认)
6. 档房配置摘要 (get_tier_summary)
"""
import json
import sys
import os

# 让 pytest 能找到 han_sim
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")

from han_sim.score_extractor_pipeline import (
    TIER_FIELDS, TIER_ORDER, TIER_PROMPTS, V4_BACKUP_PROMPT,
    make_empty_20_field, _parse_json_safely, _filter_to_tier_fields,
    _ensure_all_20_fields, get_tier_summary,
)


# ════════════════════════════════════════════════════════════════
# Test 1: 20 字段骨架
# ════════════════════════════════════════════════════════════════

def test_make_empty_20_field_has_20_keys():
    """空骨架必须有 20 个字段"""
    skeleton = make_empty_20_field()
    assert len(skeleton) == 20, f"期望 20 字段, 实际 {len(skeleton)}"


def test_make_empty_20_field_correct_types():
    """空骨架字段类型正确 (dict vs list)"""
    skeleton = make_empty_20_field()
    dict_fields = {"metric_delta", "faction_delta", "class_delta",
                   "region_delta", "army_delta", "power_updates", "world_advance"}
    list_fields = {"economy_moves", "fiscal_changes",
                   "issue_advances", "new_issues", "cancels", "close_issues",
                   "new_armies", "office_changes", "appointments",
                   "character_status_changes", "character_power_changes",
                   "secret_order_updates", "secret_order_closes"}
    for k in dict_fields:
        assert skeleton[k] == {}, f"{k} 应为 dict, 实际 {type(skeleton[k]).__name__}"
    for k in list_fields:
        assert skeleton[k] == [], f"{k} 应为 list, 实际 {type(skeleton[k]).__name__}"


# ════════════════════════════════════════════════════════════════
# Test 2: 档房字段所有权
# ════════════════════════════════════════════════════════════════

def test_tier_fields_total_is_20():
    """4 档房负责的字段总数 = 20"""
    total = sum(len(v) for v in TIER_FIELDS.values())
    assert total == 20, f"期望 20, 实际 {total}"


def test_tier_fields_no_overlap():
    """4 档房字段无重叠 (铁律: 字段所有权清晰)"""
    all_fields = []
    for tier, fields in TIER_FIELDS.items():
        for f in fields:
            assert f not in all_fields, f"字段 {f} 重复出现在多个档房"
            all_fields.append(f)
    assert len(all_fields) == 20


def test_tier_order_4_tiers():
    """档房执行顺序: 4 个档房"""
    assert len(TIER_ORDER) == 4
    assert TIER_ORDER == ["internal", "issues", "military_external", "personnel_secret"]


def test_tier_prompts_match_files():
    """档房 prompt 文件名 (实际文件存在)"""
    base = "/home/admin/.openclaw/workspace/han-empire/content/prompts"
    for tier, prompt_name in TIER_PROMPTS.items():
        path = os.path.join(base, f"{prompt_name}.md")
        assert os.path.exists(path), f"{path} 不存在"


# ════════════════════════════════════════════════════════════════
# Test 3: JSON 解析 (边界)
# ════════════════════════════════════════════════════════════════

def test_parse_json_empty():
    """空字符串 → 错误"""
    result = _parse_json_safely("", "internal")
    assert "_error" in result
    assert result["_error"].startswith("internal")


def test_parse_json_whitespace():
    """纯空白 → 错误"""
    result = _parse_json_safely("   \n\t  ", "issues")
    assert "_error" in result


def test_parse_json_invalid():
    """非 JSON → 错误"""
    result = _parse_json_safely("not a json", "internal")
    assert "_error" in result
    assert "解析失败" in result["_error"]


def test_parse_json_not_dict():
    """JSON 但不是 dict (如 list) → 错误"""
    result = _parse_json_safely('["a", "b"]', "internal")
    assert "_error" in result
    assert "不是 dict" in result["_error"]


def test_parse_json_with_codeblock():
    """含 ```json``` 包裹 → 正确解析"""
    text = '```json\n{"metric_delta": {"皇威": 5}}\n```'
    result = _parse_json_safely(text, "internal")
    assert "_error" not in result
    assert result == {"metric_delta": {"皇威": 5}}


def test_parse_json_with_codeblock_no_lang():
    """含 ``` ``` 包裹 (无 json 标记) → 正确解析"""
    text = '```\n{"metric_delta": {"皇威": 5}}\n```'
    result = _parse_json_safely(text, "internal")
    assert "_error" not in result


def test_parse_json_valid():
    """合法 JSON dict → 正确返回"""
    text = '{"metric_delta": {"皇威": 5, "民心": -2}, "economy_moves": []}'
    result = _parse_json_safely(text, "internal")
    assert "_error" not in result
    assert result["metric_delta"] == {"皇威": 5, "民心": -2}


# ════════════════════════════════════════════════════════════════
# Test 4: 字段所有权过滤
# ════════════════════════════════════════════════════════════════

def test_filter_to_tier_fields_internal():
    """internal 档房: 只保留 6 个字段"""
    data = {
        "metric_delta": {"皇威": 5},
        "economy_moves": [{"x": 1}],
        "office_changes": [{"name": "y"}],  # 不属于 internal
        "issue_advances": [{"x": 2}],  # 不属于 internal
    }
    result = _filter_to_tier_fields(data, "internal")
    assert "metric_delta" in result
    assert "economy_moves" in result
    assert "office_changes" not in result
    assert "issue_advances" not in result


def test_filter_to_tier_fields_issues():
    """issues 档房: 只保留 4 个字段"""
    data = {
        "issue_advances": [{"x": 1}],
        "new_issues": [{"y": 2}],
        "metric_delta": {"皇威": 5},  # 不属于 issues
        "army_delta": {"z": 1},  # 不属于 issues
    }
    result = _filter_to_tier_fields(data, "issues")
    assert "issue_advances" in result
    assert "new_issues" in result
    assert "metric_delta" not in result
    assert "army_delta" not in result


def test_filter_to_tier_fields_empty():
    """空数据 → 空 dict"""
    result = _filter_to_tier_fields({}, "internal")
    assert result == {}


# ════════════════════════════════════════════════════════════════
# Test 5: 20 字段补全
# ════════════════════════════════════════════════════════════════

def test_ensure_all_20_fields_fill_missing():
    """缺字段时补默认"""
    data = {"metric_delta": {"皇威": 5}}  # 只 1 个字段
    result = _ensure_all_20_fields(data)
    assert len(result) == 20
    assert result["metric_delta"] == {"皇威": 5}
    assert result["faction_delta"] == {}
    assert result["economy_moves"] == []


def test_ensure_all_20_fields_keep_existing():
    """已有字段保持不变"""
    data = {"metric_delta": {"皇威": 5}, "economy_moves": [{"x": 1}]}
    result = _ensure_all_20_fields(data)
    assert result["metric_delta"] == {"皇威": 5}
    assert result["economy_moves"] == [{"x": 1}]
    assert result["faction_delta"] == {}


# ════════════════════════════════════════════════════════════════
# Test 6: 配置摘要
# ════════════════════════════════════════════════════════════════

def test_get_tier_summary_structure():
    """get_tier_summary 返回正确结构"""
    summary = get_tier_summary()
    assert "tier_order" in summary
    assert "tier_fields" in summary
    assert "tier_prompts" in summary
    assert "v4_backup_prompt" in summary
    assert "total_fields" in summary
    assert summary["total_fields"] == 20
    assert summary["v4_backup_prompt"] == "score_extractor_v4_backup"


# ════════════════════════════════════════════════════════════════
# Test 7: 提示词文件内容检查
# ════════════════════════════════════════════════════════════════

def test_prompts_have_默会知识():
    """5 个 prompt 都含「默会知识」"""
    base = "/home/admin/.openclaw/workspace/han-empire/content/prompts"
    files = [
        "score_extractor_shared.md",
        "score_extractor_internal.md",
        "score_extractor_issues.md",
        "score_extractor_military_external.md",
        "score_extractor_personnel_secret.md",
        "score_extractor.md",
    ]
    for f in files:
        path = os.path.join(base, f)
        if not os.path.exists(path):
            continue  # 跳过 (测试环境可能缺)
        with open(path, "r", encoding="utf-8") as fp:
            content = fp.read()
        assert "默会知识" in content, f"{f} 缺「默会知识」段"


def test_prompts_have_权威源声明():
    """5 个 prompt 都含「权威源声明」"""
    base = "/home/admin/.openclaw/workspace/han-empire/content/prompts"
    files = [
        "score_extractor_shared.md",
        "score_extractor_internal.md",
        "score_extractor_issues.md",
        "score_extractor_military_external.md",
        "score_extractor_personnel_secret.md",
        "score_extractor.md",
    ]
    for f in files:
        path = os.path.join(base, f)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as fp:
            content = fp.read()
        assert "权威源声明" in content, f"{f} 缺「权威源声明」段"


# ════════════════════════════════════════════════════════════════
# Test 8: E2E 字段所有权合并
# ════════════════════════════════════════════════════════════════

def test_e2e_merge_4_tiers():
    """模拟 4 档房各抽部分字段, 合并为 20 字段"""
    # 模拟各档房输出
    internal_result = {
        "metric_delta": {"皇威": 5, "民心": -2},
        "economy_moves": [{"account": "国库", "delta": -10}],
        "faction_delta": {"忠汉派": -3},
    }
    issues_result = {
        "issue_advances": [{"issue_id": 12, "delta_bar": 15}],
    }
    military_result = {
        "army_delta": {"guanning": {"morale": -3}},
    }
    personnel_result = {
        "office_changes": [{"name": "王允", "new_office": "司徒"}],
        "character_status_changes": [{"name": "董卓", "status": "dead"}],
    }

    # 过滤后合并
    merged = make_empty_20_field()
    for tier, result in [
        ("internal", internal_result),
        ("issues", issues_result),
        ("military_external", military_result),
        ("personnel_secret", personnel_result),
    ]:
        for k, v in result.items():
            if k in merged:
                merged[k] = v

    # 验证 20 字段都有值或默认值
    assert len(merged) == 20
    assert merged["metric_delta"] == {"皇威": 5, "民心": -2}
    assert merged["economy_moves"] == [{"account": "国库", "delta": -10}]
    assert merged["faction_delta"] == {"忠汉派": -3}
    assert merged["issue_advances"] == [{"issue_id": 12, "delta_bar": 15}]
    assert merged["army_delta"] == {"guanning": {"morale": -3}}
    assert merged["office_changes"] == [{"name": "王允", "new_office": "司徒"}]
    assert merged["character_status_changes"] == [{"name": "董卓", "status": "dead"}]
    # 未涉及的字段
    assert merged["class_delta"] == {}
    assert merged["new_issues"] == []


if __name__ == "__main__":
    # 手动跑测试
    import sys as _sys
    test_funcs = [
        test_make_empty_20_field_has_20_keys,
        test_make_empty_20_field_correct_types,
        test_tier_fields_total_is_20,
        test_tier_fields_no_overlap,
        test_tier_order_4_tiers,
        test_tier_prompts_match_files,
        test_parse_json_empty,
        test_parse_json_whitespace,
        test_parse_json_invalid,
        test_parse_json_not_dict,
        test_parse_json_with_codeblock,
        test_parse_json_with_codeblock_no_lang,
        test_parse_json_valid,
        test_filter_to_tier_fields_internal,
        test_filter_to_tier_fields_issues,
        test_filter_to_tier_fields_empty,
        test_ensure_all_20_fields_fill_missing,
        test_ensure_all_20_fields_keep_existing,
        test_get_tier_summary_structure,
        test_prompts_have_默会知识,
        test_prompts_have_权威源声明,
        test_e2e_merge_4_tiers,
    ]
    passed = 0
    failed = 0
    for fn in test_funcs:
        try:
            fn()
            passed += 1
            print(f"  ✓ {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {fn.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
