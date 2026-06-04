"""v5.1.0 P0-2: 财政预算视图 (国库/内库 分账户)

v5.1 内部设计/models.py:113-114 BudgetAccount + v5.1 内部设计/web_app.py:700+ /api/budget
本模块提供只读视图, 不修改 state.metrics["汉室库"] / state.metrics["内库"]。
应用层仍走 flows.apply_monthly_flow / apply_graduated_fiscal。

设计目标:
  1. 双账户: 汉室库 (公帑) + 内库 (私帑)
  2. 收支分明: income[] / expense[] / movements[] 三段
  3. 截留机制: 皇威<30 时 20% 截留 (M# 仿点)
  4. 13 州分账: province 段列出每州明细
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from han_sim.constants import TURN_UNIT
from han_sim.db import GameDB
from han_sim.models import GameState


ACCOUNT_HANSHIKU = "汉室库"
ACCOUNT_INNER = "内库"

# 截留阈值: 皇威 < 此值时启用截留
INTERCEPT_THRESHOLD = 30
INTERCEPT_RATE = 0.20  # 20% 截留


@dataclass
class BudgetMovement:
    """单笔流水 (一笔收入或支出的记录)"""
    delta: int
    balance_after: int
    category: str           # 田赋/盐铁/俸禄/军费/...
    reason: str             # 人话描述
    account: str = ACCOUNT_HANSHIKU  # 汉室库 / 内库

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BudgetAccount:
    """单账户预算 (汉室库 或 内库)"""
    balance: int = 0
    income: List[Dict[str, Any]] = field(default_factory=list)
    expense: List[Dict[str, Any]] = field(default_factory=list)
    income_total: int = 0
    expense_total: int = 0
    net: int = 0
    movements: List[Dict[str, Any]] = field(default_factory=list)
    movements_total: int = 0  # 当前余额与上期差额

    def to_dict(self) -> Dict[str, Any]:
        return {
            "balance": self.balance,
            "income": self.income,
            "expense": self.expense,
            "income_total": self.income_total,
            "expense_total": self.expense_total,
            "net": self.net,
            "movements": self.movements,
            "movements_total": self.movements_total,
        }


# ── 收入项 (按 M# 仿点 4 税源) ────────────────────────────────────────────────

# v5.1.0 P0-2: 田赋基准 (按 province 简化估算, 单位: 万两/月)
# 实际值由 flows.calc_province_fiscal 计算, 这里仅作 fallback
_PROVINCE_TAX_FALLBACK = {
    "sili": 8, "jingzhou": 25, "yizhou": 20, "yanzhou": 18, "xuzhou": 12,
    "jizhou": 22, "qingzhou": 10, "bingzhou": 6, "yingchuan": 14, "nanyang": 16,
    "jiujiang": 12, "liangzhou": 5, "luoyang": 3, "youzhou": 8,
}


def _province_efficiency(fiscal: Dict, gentry: int, unrest: int) -> float:
    """省份税收效率 (0-1). v5.1 内部设计 公式.
    
    efficiency = 1 - corruption/100 * 0.6 - gentry/100 * 0.3 - unrest/100 * 0.3
    """
    if not isinstance(fiscal, dict):
        fiscal = {}
    corruption = float(fiscal.get("corruption", 30))
    base = 1.0
    base -= (corruption / 100.0) * 0.5  # 腐败扣 50%
    base -= (gentry / 100.0) * 0.25    # 士族阻力扣 25%
    base -= (unrest / 100.0) * 0.25    # 动乱扣 25%
    return max(0.0, min(1.0, base))


def _intercept_applies(state: GameState) -> bool:
    """皇威 < INTERCEPT_THRESHOLD 时启用 20% 截留"""
    return int(state.metrics.get("威权", 0)) < INTERCEPT_THRESHOLD


def _calc_province_tax(
    state: GameState,
    db: GameDB,
) -> Tuple[int, List[Dict]]:
    """计算本月 13 州分账田赋收入.
    
    Returns: (总收入, 各省摘要列表)
    """
    try:
        regions = db.list_regions()
    except Exception:
        regions = []
    if not regions:
        return 0, []

    intercept = _intercept_applies(state)
    total_tax = 0
    intercept_total = 0
    summaries = []

    for reg in regions:
        reg_id = reg.get("id", "")
        if reg.get("controlled_by") in ("han", "shiceng", "taoqian"):
            # 玩家实际控制 (简化判: shiceng/taoqian 是边远小势力, 不直接收税)
            pass

        fiscal = reg.get("fiscal", {}) if isinstance(reg.get("fiscal"), dict) else {}
        gentry = int(reg.get("gentry_resistance", 0))
        unrest = int(reg.get("unrest", 0))
        efficiency = _province_efficiency(fiscal, gentry, unrest)

        # 基础田赋
        tax_base = _PROVINCE_TAX_FALLBACK.get(
            reg_id, int(reg.get("tax_per_turn", 0) or 0)
        )
        # 隐田扣减
        hidden = int(reg.get("hidden_land", 0) or 0)
        registered = int(reg.get("registered_land", 1) or 1)
        hidden_ratio = min(0.5, hidden / max(1, registered + hidden))
        tax_base = int(tax_base * (1 - hidden_ratio * 0.5))

        actual = int(tax_base * efficiency)
        intercepted = int(actual * INTERCEPT_RATE) if intercept else 0
        net = actual - intercepted

        total_tax += net
        intercept_total += intercepted
        summaries.append({
            "region_id": reg_id,
            "region": reg.get("name", reg_id),
            "tax_base": tax_base,
            "efficiency": round(efficiency, 3),
            "actual": actual,
            "intercepted": intercepted,
            "net": net,
            "corruption": int(fiscal.get("corruption", 0)),
            "gentry_resistance": gentry,
            "unrest": unrest,
        })

    return total_tax, summaries


def _calc_army_expense(db: GameDB) -> Tuple[int, List[Dict]]:
    """军队维护费 (按 M# 仿点, 9 军维护费)"""
    try:
        armies = db.list_armies()
    except Exception:
        armies = []
    total = 0
    items = []
    for a in armies:
        if a.get("status") != "active":
            continue
        m = int(a.get("maintenance_per_turn", 0) or 0)
        total += m
        items.append({
            "name": a.get("name", a.get("id", "")),
            "amount": m,
            "note": f"{a.get('commander', '?')} 统率",
        })
    return total, items


def _calc_officials_expense(db: GameDB) -> Tuple[int, List[Dict]]:
    """百官俸 (简化估算)"""
    try:
        chars = db.list_characters()
    except Exception:
        chars = []
    active = [c for c in chars if c.get("status") == "active"]
    # 平均月俸 0.5 万两 (1-50 人: 10-30 万两/月)
    total = len(active) // 2 if active else 0
    return total, [{
        "name": "百官俸",
        "amount": total,
        "note": f"{len(active)} 位在朝臣工",
    }]


# ── 主入口 ────────────────────────────────────────────────────────────────

def compute_budget_lines(
    state: GameState,
    db: GameDB,
) -> Dict[str, BudgetAccount]:
    """v5.1.0 P0-2: 计算本月度预算 (国库/内库 双账户).
    
    不修改 state.metrics. 纯只读视图, 供 /api/budget 端点 + UI 弹窗使用.
    """
    # 国库 (汉室库) 月度预算
    hanshiku = BudgetAccount(
        balance=int(state.metrics.get(ACCOUNT_HANSHIKU, 0) or 0)
    )
    neiku = BudgetAccount(
        balance=int(state.metrics.get(ACCOUNT_INNER, 0) or 0)
    )

    # ── 田赋收入 (13 州分账) ──
    total_tax, province_summaries = _calc_province_tax(state, db)
    if total_tax > 0:
        hanshiku.income.append({
            "name": "田赋",
            "amount": total_tax,
            "note": f"{len(province_summaries)} 州月结 (按腐败/士族/动乱修正)",
        })
        hanshiku.income_total += total_tax

    # ── 截留项 (皇威<30 时 20% 截留) ──
    if _intercept_applies(state):
        intercept_sum = sum(s["intercepted"] for s in province_summaries)
        if intercept_sum > 0:
            hanshiku.expense.append({
                "name": "地方截留",
                "amount": intercept_sum,
                "note": f"皇威<{INTERCEPT_THRESHOLD}, 20% 截留",
            })
            hanshiku.expense_total += intercept_sum

    # ── 盐铁专营 (威权≥30 解锁, 仿 flows.apply_graduated_fiscal) ──
    authority = int(state.metrics.get("威权", 0))
    if authority >= 30:
        salt_iron = 10
        neiku.income.append({
            "name": "盐铁专营",
            "amount": salt_iron,
            "note": "威权≥30, 内库入账",
        })
        neiku.income_total += salt_iron
    else:
        hanshiku.expense.append({
            "name": "盐铁截留",
            "amount": 10,
            "note": f"威权<30, 截流入地方",
        })
        hanshiku.expense_total += 10

    # ── 军费 (国库支出) ──
    army_expense, army_items = _calc_army_expense(db)
    if army_expense > 0:
        hanshiku.expense.append({
            "name": "军费",
            "amount": army_expense,
            "note": f"{len(army_items)} 军在编",
        })
        hanshiku.expense_total += army_expense

    # ── 官俸 (国库支出) ──
    off_expense, off_items = _calc_officials_expense(db)
    if off_expense > 0:
        hanshiku.expense.append({
            "name": "百官俸",
            "amount": off_expense,
            "note": off_items[0]["note"] if off_items else "",
        })
        hanshiku.expense_total += off_expense

    # ── 暗探开支 (威权≥40 解锁, 仿 flows.apply_intel_expense) ──
    if authority >= 40:
        intel = 5
        hanshiku.expense.append({
            "name": "暗探开支",
            "amount": intel,
            "note": "威权≥40, 情报加成",
        })
        hanshiku.expense_total += intel

    # ── 净收 / 流水 ──
    hanshiku.net = hanshiku.income_total - hanshiku.expense_total
    neiku.net = neiku.income_total - neiku.expense_total

    # 写 movements (单笔流水)
    bal_h = hanshiku.balance
    for inc in hanshiku.income:
        bal_h += inc["amount"]
        hanshiku.movements.append({
            "delta": +inc["amount"],
            "balance_after": bal_h,
            "category": inc["name"],
            "reason": inc.get("note", ""),
            "account": ACCOUNT_HANSHIKU,
        })
    for exp in hanshiku.expense:
        bal_h -= exp["amount"]
        hanshiku.movements.append({
            "delta": -exp["amount"],
            "balance_after": bal_h,
            "category": exp["name"],
            "reason": exp.get("note", ""),
            "account": ACCOUNT_HANSHIKU,
        })
    hanshiku.movements_total = hanshiku.income_total - hanshiku.expense_total

    bal_n = neiku.balance
    for inc in neiku.income:
        bal_n += inc["amount"]
        neiku.movements.append({
            "delta": +inc["amount"],
            "balance_after": bal_n,
            "category": inc["name"],
            "reason": inc.get("note", ""),
            "account": ACCOUNT_INNER,
        })
    for exp in neiku.expense:
        bal_n -= exp["amount"]
        neiku.movements.append({
            "delta": -exp["amount"],
            "balance_after": bal_n,
            "category": exp["name"],
            "reason": exp.get("note", ""),
            "account": ACCOUNT_INNER,
        })
    neiku.movements_total = neiku.income_total - neiku.expense_total

    return {
        ACCOUNT_HANSHIKU: hanshiku,
        ACCOUNT_INNER: neiku,
        "_provinces": province_summaries,  # 隐藏字段, 上层 API 可选返
    }


def apply_economy_to_budget(state: GameState, db: GameDB) -> Dict[str, Any]:
    """v5.1.0 P0-3: 把 budget 计算结果应用到 state.metrics.
    
    等价于: 汉室库 += hanshiku.net, 内库 += neiku.net
    返字典含两个 net 值, 便于日志记录.
    """
    budgets = compute_budget_lines(state, db)
    hanshiku = budgets[ACCOUNT_HANSHIKU]
    neiku = budgets[ACCOUNT_INNER]

    state.metrics[ACCOUNT_HANSHIKU] = max(
        0, int(state.metrics.get(ACCOUNT_HANSHIKU, 0) or 0) + hanshiku.net
    )
    state.metrics[ACCOUNT_INNER] = max(
        0, int(state.metrics.get(ACCOUNT_INNER, 0) or 0) + neiku.net
    )
    state.clamp()

    return {
        "hanshiku_delta": hanshiku.net,
        "neiku_delta": neiku.net,
        "income_total": hanshiku.income_total,
        "expense_total": hanshiku.expense_total,
    }


# ── 兼容旧 metrics 双口径同步 ──────────────────────────────────────────────

def sync_budget_to_metrics(state: GameState) -> None:
    """v5.1.0 P0-3: 把 BudgetAccount 写回 state.metrics (兼容)."""
    budget = state.budget if isinstance(getattr(state, "budget", None), dict) else None
    if budget:
        for acc_name in (ACCOUNT_HANSHIKU, ACCOUNT_INNER):
            if acc_name in budget and hasattr(budget[acc_name], "balance"):
                state.metrics[acc_name] = budget[acc_name].balance


def sync_metrics_to_budget(state: GameState) -> None:
    """v5.1.0 P0-3: 启动时从旧 metrics 重建 BudgetAccount."""
    if not hasattr(state, "budget") or not isinstance(getattr(state, "budget", None), dict):
        state.budget = {}
    for acc_name in (ACCOUNT_HANSHIKU, ACCOUNT_INNER):
        bal = int(state.metrics.get(acc_name, 0) or 0)
        if acc_name not in state.budget:
            state.budget[acc_name] = BudgetAccount(balance=bal)
        else:
            state.budget[acc_name].balance = bal
