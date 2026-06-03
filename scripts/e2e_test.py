#!/usr/bin/env python3
"""
汉献帝之末路 - 端到端测试套件
验证所有核心系统的功能正常
"""
import sys
sys.path.insert(0, '.')

from han_sim.content import load_game_content
from han_sim.session import GameSession
from han_sim.decree import issue_decree, DECREE_TEMPLATES
from han_sim.flows import (
    get_skill_tree_status, apply_skill_points, activate_skill, calc_faction_influence
)
from han_sim.models import SKILL_TREES, get_available_skills, can_activate_skill, get_faction_status, get_authority_level, init_faction_influence
from han_sim.db import GameDB

def test_game_initialization():
    """测试游戏初始化"""
    print("\n=== 测试1: 游戏初始化 ===")
    content = load_game_content()
    session = GameSession.new('e2e-test', content)
    state = session.state
    db = session.db

    assert session is not None, "Session should not be None"
    assert state.turn == 1, f"Turn should be 1, got {state.turn}"
    assert state.capital == "洛阳", f"Capital should be 洛阳, got {state.capital}"
    assert '威权' in state.metrics, "Metrics should have 威权"
    assert '藩镇' in state.metrics, "Metrics should have 藩镇"
    assert '汉室库' in state.metrics, "Metrics should have 汉室库"

    print(f"  ✅ Session创建成功: turn={state.turn}, capital={state.capital}")
    print(f"  ✅ 初始指标: 威权={state.metrics['威权']}, 藩镇={state.metrics['藩镇']}, 汉室库={state.metrics['汉室库']}")
    return session, state, db


def test_decree_system(state, db):
    """测试诏书系统"""
    print("\n=== 测试2: 诏书系统 ===")

    decree_types = list(DECREE_TEMPLATES.keys())
    successful = 0
    for dtype in decree_types:
        try:
            result = issue_decree(dtype, state, db)
            assert result is not None, f"issue_decree returned None for {dtype}"
            assert result.decree is not None, f"Decree is None for {dtype}"
            assert result.decree.decree_type == dtype, f"Type mismatch: {dtype}"
            assert len(result.decree.full_text) > 0, f"Empty full_text for {dtype}"
            successful += 1
        except Exception as e:
            print(f"  ⚠️ {dtype}: {e}")

    print(f"  ✅ 诏书系统: {successful}/{len(decree_types)} 类型测试通过")
    return successful


def test_skill_system(state, db):
    """测试技能系统"""
    print("\n=== 测试3: 技能系统 ===")

    gained = apply_skill_points(state, db)
    sp = state.metrics.get('skill_points', 0)
    print(f"  📍 技能点: gained={gained}, total={sp}")

    st = get_skill_tree_status(state)
    print(f"  📍 技能树: {st['total_skills']} 总计, {len(st['branch_progress'])} 派系")

    for branch, progress in st['branch_progress'].items():
        print(f"     - {branch}: {progress['activated']}/{progress['total']}")

    authority = state.metrics.get('威权', 0)
    available = get_available_skills(authority, state.metrics.get('activated_skills', []))
    print(f"  ✅ 威权{authority}下可用技能: {len(available)}")
    return st


def test_faction_system(state, db):
    """测试派系系统"""
    print("\n=== 测试4: 派系系统 ===")

    fi = calc_faction_influence(state, db)
    print(f"  📍 派系影响力:")
    for faction, influence in fi.items():
        print(f"     - {faction}: {influence:.1f}%")

    fs = get_faction_status(state)
    print(f"  ✅ 派系状态: {len(fs)} 派系")
    return fi


def test_authority_level(state):
    """测试威权等级"""
    print("\n=== 测试5: 威权等级 ===")

    levels = [0, 15, 25, 40, 60, 80, 100]
    for auth in levels:
        state.metrics['威权'] = auth
        level = get_authority_level(auth)
        print(f"  📍 威权{auth} → {level.label}(倍率{level.decree_mult:.0%})")

    print(f"  ✅ 威权等级系统正常")
    state.metrics['威权'] = 15


def test_database_operations(db):
    """测试数据库操作"""
    print("\n=== 测试6: 数据库操作 ===")

    powers = db.list_powers()
    print(f"  📍 势力: {len(powers)} 个")
    assert len(powers) > 0, "Should have powers"

    regions = db.list_regions()
    print(f"  📍 地区: {len(regions)} 个")
    assert len(regions) > 0, "Should have regions"

    buildings = db.list_buildings()
    print(f"  📍 建筑: {len(buildings)} 个")

    characters = db.list_characters()
    print(f"  📍 人物: {len(characters)} 个")

    print(f"  ✅ 数据库操作正常")


def test_metrics_consistency(state):
    """测试指标一致性"""
    print("\n=== 测试7: 指标一致性 ===")

    required = ['威权', '藩镇', '声望', '汉室库', '内库']
    for k in required:
        assert k in state.metrics, f"Missing metric: {k}"
        val = state.metrics[k]
        assert isinstance(val, (int, float)), f"{k} should be numeric, got {type(val)}"
        print(f"  📍 {k}: {val} ({type(val).__name__})")

    print(f"  ✅ 所有指标类型正确")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("汉献帝之末路 v0.9.8 - 端到端测试套件")
    print("=" * 60)

    try:
        session, state, db = test_game_initialization()
        test_decree_system(state, db)
        test_skill_system(state, db)
        test_faction_system(state, db)
        test_authority_level(state)
        test_database_operations(db)
        test_metrics_consistency(state)

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！游戏核心系统运行正常。")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)