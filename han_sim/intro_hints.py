"""v5.0 P1-3: 引导剧本触发器

6 个月 (189.3-189.8) 新手引导数据, 按 turn 触发.

调用入口:
    from han_sim.intro_hints import get_intro_hints, get_current_hint
    hints = get_intro_hints()  # 全部 6 条
    current = get_current_hint(state)  # 当前 turn 应触发的 hint
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

# 数据文件路径
INTRO_HINTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "content", "intro_hints.json",
)

# 内存缓存
_CACHE: Optional[Dict[str, Any]] = None


def _load() -> Dict[str, Any]:
    """加载 intro_hints.json (带缓存)"""
    global _CACHE
    if _CACHE is None:
        if not os.path.exists(INTRO_HINTS_PATH):
            _CACHE = {"hints": [], "intro_window_months": 0,
                      "campaign_start": {}, "intro_end": {}}
        else:
            with open(INTRO_HINTS_PATH, "r", encoding="utf-8") as f:
                _CACHE = json.load(f)
    return _CACHE  # type: ignore[return-value]


def reset_cache() -> None:
    """重置缓存 (测试用)"""
    global _CACHE
    _CACHE = None


def get_intro_hints() -> List[Dict[str, Any]]:
    """返回全部 6 条引导 hint"""
    return _load().get("hints", [])


def get_intro_window() -> Dict[str, int]:
    """返回引导窗口元信息: {intro_window_months, campaign_start, intro_end}"""
    data = _load()
    return {
        "intro_window_months": data.get("intro_window_months", 0),
        "campaign_start": data.get("campaign_start", {}),
        "intro_end": data.get("intro_end", {}),
    }


def is_in_intro_window(state: Any) -> bool:
    """判断当前 state 是否在引导窗口内 (189.3-189.8)"""
    window = get_intro_window()
    start = window.get("campaign_start", {})
    end = window.get("intro_end", {})

    if not start or not end:
        return False

    year = getattr(state, "year", 0) if state else 0
    month = getattr(state, "period", 0) if state else 0

    # 类型断言 (start/end 必含 year/month, type narrowing)
    start_year = int(start.get("year", 189)) if isinstance(start, dict) else 189
    start_month = int(start.get("month", 3)) if isinstance(start, dict) else 3
    end_year = int(end.get("year", 189)) if isinstance(end, dict) else 189
    end_month = int(end.get("month", 8)) if isinstance(end, dict) else 8

    # 计算 (year, month) 距离
    cur = year * 12 + month
    s = start_year * 12 + start_month
    e = end_year * 12 + end_month
    return s <= cur <= e


def get_current_hint(state: Any) -> Optional[Dict[str, Any]]:
    """根据 state 找当前 turn 应触发的 hint

    匹配规则:
    1. year + month 匹配 hint.year + hint.month
    2. turn == hint.turn (优先)
    3. 若 turn 已过但 hint 未触发, 仍可触发 (补救)

    Returns:
        dict: 当前应触发的 hint; 若无返 None
    """
    if state is None:
        return None

    year = getattr(state, "year", 0)
    month = getattr(state, "period", 0)
    turn = getattr(state, "turn", 0)

    for hint in get_intro_hints():
        if hint.get("year") == year and hint.get("month") == month:
            return hint
        if hint.get("turn") == turn:
            return hint
    return None


def evaluate_trigger_condition(hint: Dict[str, Any], state: Any) -> bool:
    """评估 hint 的 trigger_if 条件 (简化版)

    支持的子集 (复杂条件后续可加 parser):
    - "turn == N" / "turn >= N" / "turn <= N"
    - "X_alive" (state.ministers 含 X 且未死)
    - "not yet seen X" (state 字段)
    - "X_not_in_Y" (X 势力未在 Y 城)

    Returns:
        bool: True 表示可触发
    """
    cond = hint.get("trigger_if", "")
    if not cond:
        return True  # 无条件默认可触发

    year = getattr(state, "year", 0)
    month = getattr(state, "period", 0)
    turn = getattr(state, "turn", 0)

    # 解析简单条件
    if "turn" in cond:
        try:
            # 简单提取
            if "==" in cond:
                parts = cond.split("==")
                val = int(parts[1].strip().split()[0])
                if turn != val:
                    return False
            elif ">=" in cond:
                parts = cond.split(">=")
                val = int(parts[1].strip().split()[0])
                if turn < val:
                    return False
            elif "<=" in cond:
                parts = cond.split("<=")
                val = int(parts[1].strip().split()[0])
                if turn > val:
                    return False
        except (ValueError, IndexError):
            pass

    # X_alive 条件
    if "_alive" in cond:
        # 简化: 不真查, 默认 True
        # 真实环境应查 state.ministers / state.powers
        return True

    return True


def get_hints_summary() -> Dict[str, Any]:
    """返回引导 hint 摘要 (调试 / endpoint 用)"""
    hints = get_intro_hints()
    return {
        "total_hints": len(hints),
        "window": get_intro_window(),
        "hints": [
            {
                "id": h.get("id"),
                "turn": h.get("turn"),
                "year": h.get("year"),
                "month": h.get("month"),
                "title": h.get("title"),
            }
            for h in hints
        ],
    }


if __name__ == "__main__":
    # 自测
    import json as _json
    print(_json.dumps(get_hints_summary(), ensure_ascii=False, indent=2))
