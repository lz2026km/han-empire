"""
consequence_chain.py — 后果链 DAG 系统 (v3.1)
玩家每个决策 (诏书/任免/调兵/外交) → 1-N 个后果节点
后果类型: 即时 (1 回合) / 短期 (5 回合) / 长期 (30 回合) / 永久
后果指标: 民心/财政/军力/威望/继承/法统
"""
from __future__ import annotations
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ConsequenceType(str, Enum):
    IMMEDIATE = "immediate"  # 1 回合
    SHORT = "short"  # 5 回合
    LONG = "long"  # 30 回合
    PERMANENT = "permanent"  # 永久


# 颜色映射 (实色, 无 emoji, 主色 #3b82f6 蓝调)
TYPE_COLORS = {
    ConsequenceType.IMMEDIATE: "#10b981",   # 绿
    ConsequenceType.SHORT: "#3b82f6",        # 蓝
    ConsequenceType.LONG: "#f59e0b",         # 橙
    ConsequenceType.PERMANENT: "#ef4444",    # 红
}


@dataclass
class ConsequenceNode:
    """单个后果节点"""
    id: str
    decision_id: str  # 关联的决策
    decision_type: str  # 诏书/任免/调兵/外交
    description: str
    consequence_type: ConsequenceType
    effects: Dict[str, float] = field(default_factory=dict)  # 指标变化
    target: str = "全国"  # 影响范围
    created_at: int = 0  # 回合数
    expires_at: Optional[int] = None  # 过期回合
    triggered: bool = False  # 是否已触发
    depends_on: List[str] = field(default_factory=list)  # 前置后果

    def is_expired(self, current_turn: int) -> bool:
        if self.expires_at is None:
            return False
        return current_turn >= self.expires_at


class ConsequenceChain:
    """后果链 DAG 引擎"""

    # 后果类型 → 持续回合数
    TYPE_DURATION = {
        ConsequenceType.IMMEDIATE: 1,
        ConsequenceType.SHORT: 5,
        ConsequenceType.LONG: 30,
        ConsequenceType.PERMANENT: 9999,
    }

    def __init__(self):
        self.nodes: Dict[str, ConsequenceNode] = {}

    def record_decision(
        self,
        decision_id: str,
        decision_type: str,
        description: str,
        effects: Dict[str, float],
        target: str = "全国",
        consequence_type: ConsequenceType = ConsequenceType.SHORT,
        depends_on: Optional[List[str]] = None,
        current_turn: int = 0,
    ) -> List[ConsequenceNode]:
        """记录玩家决策, 自动派生 1-4 个后果节点"""
        # 主后果
        main_node = ConsequenceNode(
            id=f"csq_{decision_id}_main",
            decision_id=decision_id,
            decision_type=decision_type,
            description=f"{description} (即时效应)",
            consequence_type=ConsequenceType.IMMEDIATE,
            effects=effects,
            target=target,
            created_at=current_turn,
            expires_at=current_turn + self.TYPE_DURATION[ConsequenceType.IMMEDIATE],
        )
        self.nodes[main_node.id] = main_node
        created = [main_node]

        # 派生长期/永久后果 (基于决策类型)
        derivations = self._derive_consequences(decision_type, effects, decision_id, current_turn)
        for d in derivations:
            self.nodes[d.id] = d
            created.append(d)

        return created

    def _derive_consequences(
        self,
        decision_type: str,
        effects: Dict[str, float],
        decision_id: str,
        current_turn: int,
    ) -> List[ConsequenceNode]:
        """根据决策类型派生 1-3 个后续后果"""
        derived = []

        if decision_type == "诏书":
            # 诏书: 短期 (民心反馈) + 长期 (法统巩固)
            if "民心" in effects or "威望" in effects:
                short = ConsequenceNode(
                    id=f"csq_{decision_id}_short",
                    decision_id=decision_id,
                    decision_type=decision_type,
                    description="诏书颁布后, 朝野议论纷纷, 短期人心浮动",
                    consequence_type=ConsequenceType.SHORT,
                    effects={"民心": effects.get("民心", 0) * 0.5},
                    created_at=current_turn,
                    expires_at=current_turn + self.TYPE_DURATION[ConsequenceType.SHORT],
                    depends_on=[f"csq_{decision_id}_main"],
                )
                derived.append(short)
            if "法统" in effects:
                long = ConsequenceNode(
                    id=f"csq_{decision_id}_long",
                    decision_id=decision_id,
                    decision_type=decision_type,
                    description="诏书成为后世法统, 长期巩固",
                    consequence_type=ConsequenceType.LONG,
                    effects={"法统": effects.get("法统", 0) * 0.7},
                    created_at=current_turn,
                    expires_at=current_turn + self.TYPE_DURATION[ConsequenceType.LONG],
                    depends_on=[f"csq_{decision_id}_main"],
                )
                derived.append(long)

        elif decision_type == "任免":
            # 任免: 短期 (派系反应) + 永久 (长期忠诚)
            if "军力" in effects or "行政" in effects:
                short = ConsequenceNode(
                    id=f"csq_{decision_id}_faction",
                    decision_id=decision_id,
                    decision_type=decision_type,
                    description="朝中派系对新任命反应不一",
                    consequence_type=ConsequenceType.SHORT,
                    effects={"派系": -abs(effects.get("军力", 0) or effects.get("行政", 0)) * 0.3},
                    created_at=current_turn,
                    expires_at=current_turn + self.TYPE_DURATION[ConsequenceType.SHORT],
                    depends_on=[f"csq_{decision_id}_main"],
                )
                derived.append(short)
            perm = ConsequenceNode(
                id=f"csq_{decision_id}_loyalty",
                decision_id=decision_id,
                decision_type=decision_type,
                description="新臣效忠, 长期受益",
                consequence_type=ConsequenceType.PERMANENT,
                effects={"忠诚": effects.get("行政", 0) * 0.3},
                created_at=current_turn,
                depends_on=[f"csq_{decision_id}_main"],
            )
            derived.append(perm)

        elif decision_type == "调兵":
            # 调兵: 短期 (军心) + 长期 (边患)
            short = ConsequenceNode(
                id=f"csq_{decision_id}_morale",
                decision_id=decision_id,
                decision_type=decision_type,
                description="将士出征, 短期军心凝聚",
                consequence_type=ConsequenceType.SHORT,
                effects={"军力": effects.get("军力", 0) * 0.2},
                created_at=current_turn,
                expires_at=current_turn + self.TYPE_DURATION[ConsequenceType.SHORT],
                depends_on=[f"csq_{decision_id}_main"],
            )
            derived.append(short)

        elif decision_type == "外交":
            # 外交: 长期 (邦交)
            if "威望" in effects or "法统" in effects:
                long = ConsequenceNode(
                    id=f"csq_{decision_id}_diplomacy",
                    decision_id=decision_id,
                    decision_type=decision_type,
                    description="外交斡旋, 长期邦交稳固",
                    consequence_type=ConsequenceType.LONG,
                    effects={"威望": effects.get("威望", 0) * 0.5},
                    created_at=current_turn,
                    expires_at=current_turn + self.TYPE_DURATION[ConsequenceType.LONG],
                    depends_on=[f"csq_{decision_id}_main"],
                )
                derived.append(long)

        return derived

    def get_active_consequences(self, current_turn: int) -> List[ConsequenceNode]:
        """获取当前活跃后果 (未过期)"""
        return [n for n in self.nodes.values() if not n.is_expired(current_turn)]

    def get_consequences_by_decision(self, decision_id: str) -> List[ConsequenceNode]:
        """获取某决策的所有后果"""
        return [n for n in self.nodes.values() if n.decision_id == decision_id]

    def get_chain_view(self, current_turn: int) -> Dict[str, Any]:
        """获取后果链视图 (给前端 DAG)"""
        nodes_view = []
        for n in self.nodes.values():
            nodes_view.append({
                "id": n.id,
                "decision_id": n.decision_id,
                "decision_type": n.decision_type,
                "description": n.description,
                "type": n.consequence_type.value,
                "type_color": TYPE_COLORS[n.consequence_type],
                "effects": n.effects,
                "target": n.target,
                "created_at": n.created_at,
                "expires_at": n.expires_at,
                "expired": n.is_expired(current_turn),
                "depends_on": n.depends_on,
            })
        return {
            "nodes": nodes_view,
            "current_turn": current_turn,
            "type_legend": {
                "immediate": "即时 (1回合)",
                "short": "短期 (5回合)",
                "long": "长期 (30回合)",
                "permanent": "永久"
            },
            "type_colors": {k.value: v for k, v in TYPE_COLORS.items()},
        }

    def get_active_effects(self, current_turn: int) -> Dict[str, float]:
        """汇总当前活跃后果的指标变化"""
        total: Dict[str, float] = {}
        for n in self.get_active_consequences(current_turn):
            for k, v in n.effects.items():
                if isinstance(v, (int, float)):
                    total[k] = total.get(k, 0) + v
        return total

    def cleanup_expired(self, current_turn: int) -> int:
        """清理过期后果"""
        before = len(self.nodes)
        self.nodes = {k: v for k, v in self.nodes.items() if not v.is_expired(current_turn)}
        return before - len(self.nodes)

    def to_dict(self) -> Dict[str, Any]:
        """序列化"""
        return {
            "nodes": {
                k: {
                    "id": v.id, "decision_id": v.decision_id,
                    "decision_type": v.decision_type, "description": v.description,
                    "consequence_type": v.consequence_type.value, "effects": v.effects,
                    "target": v.target, "created_at": v.created_at,
                    "expires_at": v.expires_at, "triggered": v.triggered,
                    "depends_on": v.depends_on
                }
                for k, v in self.nodes.items()
            }
        }

    def from_dict(self, data: Dict[str, Any]):
        """反序列化"""
        self.nodes = {}
        for k, v in data.get("nodes", {}).items():
            self.nodes[k] = ConsequenceNode(
                id=v["id"], decision_id=v["decision_id"],
                decision_type=v["decision_type"], description=v["description"],
                consequence_type=ConsequenceType(v["consequence_type"]),
                effects=v.get("effects", {}), target=v.get("target", "全国"),
                created_at=v.get("created_at", 0),
                expires_at=v.get("expires_at"), triggered=v.get("triggered", False),
                depends_on=v.get("depends_on", [])
            )


# === 单例 ===
_chain: Optional[ConsequenceChain] = None


def get_consequence_chain() -> ConsequenceChain:
    global _chain
    if _chain is None:
        _chain = ConsequenceChain()
    return _chain
