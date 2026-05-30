"""回合展示与变更报告纯函数（返回 str / 打印）。L7。

回合末总结奏章格式，用于 Gradio 界面和日志输出。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from han_sim.assets import format_money, format_money_delta, wrap
from han_sim.constants import TURN_UNIT
from han_sim.models import GameState
from han_sim.context import format_metric_delta, state_context, historical_anchor_for_month


def metric_bar(value: int, max_val: int = 100) -> str:
    """绘制数值进度条（10格）。"""
    filled = max(0, min(max_val, value)) * 10 // max_val
    return "█" * filled + "░" * (10 - filled)


def print_header(state: GameState) -> None:
    """打印回合开始时的状态头。"""
    print("\n" + "=" * 60)
    print(f"汉献帝之末路 | {state.year}年{state.period}月 | 第 {state.turn} 回合")
    print("=" * 60)
    for key, value in state.metrics.items():
        if key in ("汉室库", "内库"):
            print(f"{key}: {format_money(value)}")
        elif key == "藩镇" or key == "威权" or key == "声望":
            print(f"{key}: {value} {metric_bar(value)}")
    print()


def format_region_changes(changes: List[Dict[str, object]]) -> str:
    """格式化地区变化报告。"""
    if not changes:
        return f"本{TURN_UNIT}未见明确地区盘面变化。"
    parts = []
    for change in changes:
        delta = change.get("delta")
        if delta is None:
            parts.append(f"{change['region']}{change['label']}改为{change['new']}（{change['reason']}）")
        else:
            sign = "+" if int(delta) > 0 else ""
            parts.append(f"{change['region']}{change['label']}{sign}{int(delta)}（{change['reason']}）")
    return "；".join(parts) + "。"


def format_army_changes(changes: List[Dict[str, object]]) -> str:
    """格式化军队变化报告。"""
    if not changes:
        return f"本{TURN_UNIT}未见明确军队盘面变化。"
    parts = []
    for change in changes:
        delta = change.get("delta")
        field_name = str(change.get("field", ""))
        if delta is None:
            parts.append(f"{change['army']}{change['label']}改为{change['new']}（{change['reason']}）")
        elif field_name == "manpower":
            sign = "+" if int(delta) > 0 else ""
            parts.append(f"{change['army']}{change['label']}{sign}{int(delta)}人（{change['reason']}）")
        elif field_name == "maintenance_per_turn":
            parts.append(f"{change['army']}{change['label']}{format_money_delta(int(delta))}（{change['reason']}）")
        else:
            sign = "+" if int(delta) > 0 else ""
            parts.append(f"{change['army']}{change['label']}{sign}{int(delta)}（{change['reason']}）")
    return "；".join(parts) + "。"


def format_power_changes(changes: List[Dict[str, object]]) -> str:
    """格式化势力变化报告。"""
    if not changes:
        return f"本{TURN_UNIT}未见明确势力盘面变化。"
    parts = []
    for change in changes:
        delta = change.get("delta")
        if delta is None:
            parts.append(f"{change['power']}{change['label']}改为{change['new']}（{change['reason']}）")
        else:
            sign = "+" if int(delta) > 0 else ""
            parts.append(f"{change['power']}{change['label']}{sign}{int(delta)}（{change['reason']}）")
    return "；".join(parts) + "。"


def metric_delta_summary(before: Dict[str, int], after: Dict[str, int]) -> Dict[str, int]:
    """计算两个状态快照之间的差值。"""
    keys = list(before.keys())
    for key in after:
        if key not in before:
            keys.append(key)
    return {key: after.get(key, 0) - before.get(key, 0) for key in keys if after.get(key, 0) != before.get(key, 0)}


def format_period_report(
    event_title: str,
    executor_name: str,
    executor_office: str,
    result_level: str,
    public_report: str,
    delta: Dict[str, int],
    region_changes: List[Dict[str, object]],
    army_changes: List[Dict[str, object]],
    anchor_note: str = "",
) -> str:
    """构建回合末总结奏章完整文本。"""
    lines = [
        f"\n{TURN_UNIT}末总结奏章：",
        f"奏事：{event_title}",
        f"主办：{executor_name}（{executor_office}）",
        f"奉旨结果：{result_level}。{public_report}",
    ]

    # 钱粮流水（如有）
    money_moves = [(k, v) for k, v in delta.items() if k in ("汉室库", "内库")]
    if money_moves:
        money_str = "；".join(
            f"{key}{format_money_delta(value)}" for key, value in money_moves
        )
        lines.append(f"钱粮流水：{money_str}。")
    else:
        lines.append(f"钱粮流水：本{TURN_UNIT}未形成新入账或出账。")

    # 地区/军队变化
    lines.append("地区变化：" + format_region_changes(region_changes))
    lines.append("军队变化：" + format_army_changes(army_changes))

    # 数值变化
    non_money = {k: v for k, v in delta.items() if k not in ("汉室库", "内库")}
    if non_money:
        lines.append(format_metric_delta(non_money))

    # 历史锚点（若有重要事件）
    if anchor_note:
        lines.append(f"历史背景：{anchor_note}")

    return "\n".join(lines)


def format_decree_summary(decree_text: str, effects: List[Dict]) -> str:
    """格式化诏书执行摘要。"""
    parts = [f"诏书已下：{decree_text[:60]}..." if len(decree_text) > 60 else f"诏书已下：{decree_text}"]
    effect_parts = []
    for e in effects:
        if e.get("metric") in ("汉室库", "内库"):
            effect_parts.append(f"{e['metric']}{format_money_delta(e['delta'])}：{e['description']}")
        else:
            sign = "+" if e.get("delta", 0) > 0 else ""
            effect_parts.append(f"{e['metric']}{sign}{e['delta']}：{e['description']}")
    if effect_parts:
        parts.append("效果：" + "；".join(effect_parts))
    return "\n".join(parts)


def build_turn_intro(state: GameState) -> str:
    """构建回合开始时的引导文本。"""
    anchor = historical_anchor_for_month(state.year, state.period)
    ctx = state_context(state)
    lines = [
        f"【第 {state.turn} 回合】{state.year}年{state.period}月",
        f"当前局势：{ctx}",
    ]
    if anchor.get("must_respect"):
        lines.append(f"【历史护栏】{anchor['note']}")
    lines.append("陛下，该下决断了。")
    return "\n".join(lines)


def build_event_brief(event: Dict) -> str:
    """格式化事件简报（用于召对界面）。"""
    return (
        f"【{event.get('title', '未知') if isinstance(event, dict) else event}】\n"
        f"类型：{event.get('kind', 'unknown') if isinstance(event, dict) else ''}。"
        f"奏报：{event.get('summary', '') if isinstance(event, dict) else ''}\n"
        f"紧急度：{event.get('urgency', 0)} | 严重度：{event.get('severity', 0)} | 可信度：{event.get('credibility', 0)}\n"
        f"牵涉：{', '.join(event.get('interests', [])) if isinstance(event, dict) else ''}"
    )