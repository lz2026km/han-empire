# -*- mode: python ; coding: utf-8 -*-
"""v2.0.0 Phase 2.6: 阈值危机注入 + 事项级联

阈值触发新危机：
- 藩镇>70 → 诸侯坐大
- 威权<10 → 天子虚设
- 声望<15 → 民心尽失
- 财政<10 → 国库枯竭

事项级联：一个 issue 触发其他 issue 的反应链。
"""
from __future__ import annotations
import json
import sqlite3
from typing import Any, Dict, List, Optional, Union

from han_sim.db import GameDB
from han_sim.models import GameState, Event

# v2.0.0 Phase 2.6: 阈值危机注入 + 事项级联簇
# 原 issues.py:713-870 (157 行) 抽到本文件 ────────────────────────────────────────────────────────────


def _inject_crisis_by_metrics(state: GameState, db: GameDB) -> None:
    """根据指标阈值自动注入危机事项。

    - 藩镇 > 70 → "诸侯坐大"危机（severity=75，bar_value=20，resolve_condition="藩镇<50"）
    - 威权 < 10 → "天子形同虚设"危机（severity=90，威权归零则游戏失败）
    - 声望 < 15 → "民心尽失"危机
    """
    fanzhen = state.metrics.get("藩镇", 0)
    authority = state.metrics.get("威权", 0)
    reputation = state.metrics.get("声望", 0)

    # 藩镇 > 70 → 诸侯坐大
    if fanzhen > 70:
        # 检查是否已存在同名进行中事项
        existing = [r for r in db.list_active_issues() if "诸侯坐大" in r.get("title", "")]
        if not existing:
            db.insert_issue(
                state,
                title="诸侯坐大",
                description=f"藩镇值突破70（当前{fanzhen}），各地诸侯日益坐大，不奉朝命。",
                origin_kind="system",
                origin_ref="threshold_crisis_fanzhen",
                severity=75,
                kind="crisis",
                bar_value=20,
                tags=["危机", "藩镇", "诸侯"],
                ongoing_effects={"metrics": {"藩镇": +2, "威权": -1}},
                resolve_condition="藩镇<50",
                effect_on_resolve={"metrics": {"藩镇": -20, "威权": 5}},
                effect_on_fail={"metrics": {"藩镇": 15, "威权": -10}},
            )

    # 威权 < 10 → 天子形同虚设
    if authority < 10:
        existing = [r for r in db.list_active_issues() if "天子形同虚设" in r.get("title", "")]
        if not existing:
            db.insert_issue(
                state,
                title="天子形同虚设",
                description=f"威权跌破10（当前{authority}），朝廷大事实由权臣决断，天子沦为傀儡。",
                origin_kind="system",
                origin_ref="threshold_crisis_authority",
                severity=90,
                kind="crisis",
                bar_value=15,
                tags=["危机", "威权", "朝廷"],
                ongoing_effects={"metrics": {"威权": -2, "声望": -1}},
                resolve_condition="威权>=30",
                effect_on_resolve={"metrics": {"威权": 20, "声望": 10}},
                effect_on_fail={"metrics": {"威权": -100}},  # 威权归零 → 游戏失败
            )

    # 声望 < 15 → 民心尽失
    if reputation < 15:
        existing = [r for r in db.list_active_issues() if "民心尽失" in r.get("title", "")]
        if not existing:
            db.insert_issue(
                state,
                title="民心尽失",
                description=f"声望跌破15（当前{reputation}），民间已不再信任汉室，天下思乱。",
                origin_kind="system",
                origin_ref="threshold_crisis_reputation",
                severity=85,
                kind="crisis",
                bar_value=20,
                tags=["危机", "声望", "民心"],
                ongoing_effects={"metrics": {"声望": -2}},
                resolve_condition="声望>=40",
                effect_on_resolve={"metrics": {"声望": 25, "威权": 5}},
                effect_on_fail={"metrics": {"声望": -20, "威权": -10}},
            )


# ── 事项级联 ────────────────────────────────────────────────────────────────


def _cascade_issue(db: GameDB, state: GameState, issue_row: Union[sqlite3.Row, Dict]) -> None:
    """根据事项状态自动触发关联事项或副作用。

    - "密谋讨贼"(bar_value > 80) → 触发"董卓警觉"关联事项，威权 -5
    - "献帝东归" deadline_turn 到达且未完成 → 自动关闭并创建"东归失败"
    - "讨伐董卓" resolve_condition 达成 → 自动创建"重建朝纲"事项
    """
    title = str(issue_row.get("title", ""))
    bar_value = int(issue_row.get("bar_value", 0))
    status = str(issue_row.get("status", "active"))
    resolve_condition = str(issue_row.get("resolve_condition", ""))

    # "密谋讨贼" bar_value > 80 → 董卓警觉
    if title == "密谋讨贼" and bar_value > 80:
        existing = [r for r in db.list_active_issues() if "董卓警觉" in r.get("title", "")]
        if not existing:
            db.insert_issue(
                state,
                title="董卓警觉",
                description="密谋之事渐为董卓所知，贼将加意防备，局势危在旦夕。",
                origin_kind="cascade",
                origin_ref="密谋讨贼_alert",
                severity=70,
                kind="political",
                bar_value=50,
                tags=["董卓", "密谋", "危机"],
                ongoing_effects={"metrics": {"威权": -5}},
                resolve_condition="董卓伏诛",
                effect_on_resolve={"metrics": {"威权": 10}},
                effect_on_fail={"metrics": {"威权": -15}},
            )
        # 威权 -5
        state.metrics["威权"] = max(0, state.metrics.get("威权", 0) - 5)

    # "献帝东归" deadline_turn 到达且未完成 → 自动关闭并创建"东归失败"
    if title == "献帝东归" and status == "active":
        deadline_turn = int(issue_row.get("deadline_turn", 0))
        if deadline_turn > 0 and state.turn >= deadline_turn:
            # 关闭原事项
            db.close_issue(state, int(issue_row["id"]), reason="failed", narrative="东归逾期未成，献帝被困")
            # 创建"东归失败"事项
            db.insert_issue(
                state,
                title="东归失败",
                description="献帝东归未成，被李傕郭汜追回，局势更加恶劣。",
                origin_kind="cascade",
                origin_ref="献帝东归_failed",
                severity=80,
                kind="historical",
                bar_value=80,
                tags=["献帝", "东归", "失败"],
                ongoing_effects={"metrics": {"威权": -20, "声望": -10}},
                resolve_condition="",
                effect_on_resolve={},
                effect_on_fail={"metrics": {"威权": -20, "声望": -10}},
            )

    # "讨伐董卓" resolve_condition 达成 → 创建"重建朝纲"
    if title == "讨伐董卓" and resolve_condition:
        if "董卓伏诛" in resolve_condition:
            existing = [r for r in db.list_active_issues() if "重建朝纲" in r.get("title", "")]
            if not existing:
                db.insert_issue(
                    state,
                    title="重建朝纲",
                    description="董卓已伏诛，天子得以重新执政，重建汉室权威。",
                    origin_kind="cascade",
                    origin_ref="讨伐董卓_success",
                    severity=85,
                    kind="political",
                    bar_value=30,
                    tags=["董卓", "重建", "朝纲"],
                    ongoing_effects={"metrics": {"威权": 5, "声望": 5}},
                    resolve_condition="威权>=60",
                    effect_on_resolve={"metrics": {"威权": 30, "声望": 20, "藩镇": -10}},
                    effect_on_fail={"metrics": {"威权": -10}},
                )


