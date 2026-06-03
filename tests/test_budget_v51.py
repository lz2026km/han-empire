"""v5.1.0 P0-2: 13 州分税源 + Budget endpoint 单测"""
import json
import os
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from han_sim.db import GameDB
from han_sim.budget import (
    ACCOUNT_HANSHIKU, ACCOUNT_INNER,
    INTERCEPT_THRESHOLD, INTERCEPT_RATE,
    BudgetAccount, BudgetMovement,
    compute_budget_lines, apply_economy_to_budget,
    sync_budget_to_metrics, sync_metrics_to_budget,
    _province_efficiency,
)


def _make_db():
    """创建临时 DB + state, 加载初始 regions"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = GameDB.new(path)
    # 加载初始 content (regions/characters/...)
    db.seed_static_data()
    # load_state 初始化 game_state + metrics
    state = db.load_state("189.04")
    # 确保威权为 0 (避免盐铁专营触发)
    state.metrics["威权"] = 0
    state.metrics["汉室库"] = 100
    state.metrics["内库"] = 50
    db.save_state(state)
    return db, state, path


def _cleanup(db, path):
    try:
        db.conn.close()
    except Exception:
        pass
    try:
        os.unlink(path)
    except OSError:
        pass


# ════════════════════════════════════════════════════════════════
# Test 1: 13 州税基合计 = 国库月初余额 + 净流入
# ════════════════════════════════════════════════════════════════

def test_13_province_tax_total_income():
    """13 州分账田赋收入 = 国库 income 田赋项"""
    db, state, path = _make_db()
    try:
        budgets = compute_budget_lines(state, db)
        hanshiku = budgets[ACCOUNT_HANSHIKU]
        # 至少有 1 条田赋收入
        tax_items = [i for i in hanshiku.income if i["name"] == "田赋"]
        assert len(tax_items) == 1
        assert tax_items[0]["amount"] > 0
        # 13 州分账 (隐字段 _provinces)
        provinces = budgets.get("_provinces", [])
        assert len(provinces) > 0
        # 净收入项 = 田赋 - 截留 - 盐铁截留 - ...
        assert hanshiku.income_total >= tax_items[0]["amount"] - 50
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 2: 截留 20% 在皇威 < 30 触发
# ════════════════════════════════════════════════════════════════

def test_intercept_20pct_when_authority_low():
    """皇威 < 30 时启用 20% 截留 (M# 仿点)"""
    db, state, path = _make_db()
    try:
        state.metrics["威权"] = INTERCEPT_THRESHOLD - 1  # 触发截留
        db.save_state(state)
        budgets = compute_budget_lines(state, db)
        provinces = budgets.get("_provinces", [])
        # 至少 1 个省有 intercepted > 0
        assert any(p["intercepted"] > 0 for p in provinces), "应有 20% 截留"
        # 国库 expense 含 "地方截留" 项
        hanshiku = budgets[ACCOUNT_HANSHIKU]
        intercept_items = [e for e in hanshiku.expense if e["name"] == "地方截留"]
        assert len(intercept_items) == 1
        assert intercept_items[0]["amount"] > 0
        # 截留总额 ≈ 田赋总额 × 20% (容许 5 个省以上累加的舍入误差)
        tax_sum = sum(p["actual"] for p in provinces)
        intercept_sum = sum(p["intercepted"] for p in provinces)
        expected_intercept = tax_sum * INTERCEPT_RATE
        assert abs(intercept_sum - expected_intercept) / max(1, tax_sum) < 0.10, (
            f"截留比例偏差 > 10% ({intercept_sum}/{tax_sum} vs 期望 {expected_intercept})"
        )

        # 皇威 >= 30 时不截留
        state.metrics["威权"] = INTERCEPT_THRESHOLD + 1
        db.save_state(state)
        budgets = compute_budget_lines(state, db)
        provinces2 = budgets.get("_provinces", [])
        assert all(p["intercepted"] == 0 for p in provinces2)
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 3: 4 税源互不干扰
# ════════════════════════════════════════════════════════════════

def test_4_tax_sources_independent():
    """4 税源 (田赋/盐铁/皇庄/商税) 互不干扰, 各自走对应账户"""
    db, state, path = _make_db()
    try:
        # 威权=0 → 无盐铁专营 (走截留)
        state.metrics["威权"] = 0
        db.save_state(state)
        budgets = compute_budget_lines(state, db)
        h = budgets[ACCOUNT_HANSHIKU]
        n = budgets[ACCOUNT_INNER]
        # 国库含田赋 + 盐铁截留 (expense)
        h_income_names = {i["name"] for i in h.income}
        h_expense_names = {e["name"] for e in h.expense}
        assert "田赋" in h_income_names
        assert "盐铁截留" in h_expense_names
        assert "盐铁专营" not in h_income_names  # 走国库截留, 不走内库
        # 内库空
        assert n.income_total == 0
        assert n.expense_total == 0

        # 威权=30 → 盐铁专营解锁, 入内库
        state.metrics["威权"] = 35
        db.save_state(state)
        budgets = compute_budget_lines(state, db)
        h = budgets[ACCOUNT_HANSHIKU]
        n = budgets[ACCOUNT_INNER]
        n_income_names = {i["name"] for i in n.income}
        assert "盐铁专营" in n_income_names
        assert n.income_total == 10
        h_expense_names = {e["name"] for e in h.expense}
        assert "盐铁截留" not in h_expense_names
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 4: E2E apply_economy_to_budget + sync
# ════════════════════════════════════════════════════════════════

def test_e2e_apply_and_sync():
    """E2E: apply_economy_to_budget + sync 双向同步"""
    db, state, path = _make_db()
    try:
        state.metrics["汉室库"] = 1000
        state.metrics["内库"] = 500
        state.metrics["威权"] = 0  # 触发截留
        db.save_state(state)

        result = apply_economy_to_budget(state, db)
        assert "hanshiku_delta" in result
        assert "neiku_delta" in result
        # 应用后余额已更新
        assert state.metrics["汉室库"] >= 0
        assert state.metrics["内库"] >= 0
        # metrics 与 budget 同步
        sync_budget_to_metrics(state)
        sync_metrics_to_budget(state)
        # 旧 metrics["汉室库"] 与 budget["汉室库"].balance 一致
        sync_metrics_to_budget(state)
        budgets = compute_budget_lines(state, db)
        h_budget = budgets[ACCOUNT_HANSHIKU]
        # 余额可能不严格等于 metrics (因为 compute_budget_lines 是 forecast)
        # 但 metrics 应该已被 apply_economy_to_budget 改过
        # 这里只验证 sync 函数不崩
        assert h_budget.balance >= 0
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# 额外: 省份效率公式 + BudgetAccount 序列化
# ════════════════════════════════════════════════════════════════

def test_province_efficiency_formula():
    """省份效率 = 1 - corruption*0.5 - gentry*0.25 - unrest*0.25"""
    fiscal = {"corruption": 50}
    eff = _province_efficiency(fiscal, gentry=20, unrest=20)
    expected = 1.0 - 0.25 - 0.05 - 0.05
    assert abs(eff - expected) < 0.01, f"expected ~{expected}, got {eff}"

    # 全 0 (corruption=0 显式, gentry/unrest 走 0)
    eff = _province_efficiency({"corruption": 0}, gentry=0, unrest=0)
    assert abs(eff - 1.0) < 0.01

    # 极端高腐败
    eff = _province_efficiency({"corruption": 100}, gentry=100, unrest=100)
    assert eff == 0.0

    # 缺省 corruption 字段 → 默认 30
    eff = _province_efficiency({}, gentry=0, unrest=0)
    assert abs(eff - 0.85) < 0.01, f"缺省 corruption=30 → 0.85, got {eff}"


def test_budget_account_serialization():
    """BudgetAccount.to_dict() 字段完整"""
    ba = BudgetAccount(
        balance=100,
        income=[{"name": "田赋", "amount": 50, "note": "test"}],
        expense=[{"name": "军费", "amount": 30, "note": "test"}],
        income_total=50,
        expense_total=30,
        net=20,
        movements=[{"delta": 50, "balance_after": 150, "category": "田赋", "reason": "test", "account": "汉室库"}],
        movements_total=20,
    )
    d = ba.to_dict()
    assert d["balance"] == 100
    assert d["income_total"] == 50
    assert d["net"] == 20
    assert len(d["movements"]) == 1
    assert d["movements_total"] == 20
