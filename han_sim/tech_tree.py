"""
tech_tree.py — 科技树核心引擎 (v3.1)
3 主线 (农本/王权/军备) × 15 节点 DAG
玩家累计声望 → 消耗解锁下一节点 → 触发永久 buff
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
TECH_DEFS_FILE = CONTENT_DIR / "tech_definitions.json"


@dataclass
class TechNode:
    """单个科技节点"""
    id: str
    name: str
    line: str  # 农本/王权/军备
    tier: int  # 0-4 层级
    cost: int  # 声望消耗
    description: str
    effects: Dict[str, Any] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)  # 前置节点 id
    unlocks: List[str] = field(default_factory=list)  # 解锁后能买的节点 id


@dataclass
class TechState:
    """玩家科技状态"""
    unlocked: List[str] = field(default_factory=list)
    available: List[str] = field(default_factory=list)  # 可解锁
    locked: List[str] = field(default_factory=list)
    reputation: int = 0  # 累计声望


class TechTreeEngine:
    """科技树核心引擎"""

    def __init__(self, defs_path: Path = TECH_DEFS_FILE):
        self.nodes: Dict[str, TechNode] = {}
        self._load_definitions(defs_path)

    def _load_definitions(self, path: Path):
        """从 tech_definitions.json 加载"""
        if not path.exists():
            # 默认 15 节点
            self._init_defaults()
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for n in data.get("techs", []):
                node = TechNode(
                    id=n["id"], name=n["name"], line=n["line"],
                    tier=n["tier"], cost=n["cost"],
                    description=n["description"],
                    effects=n.get("effects", {}),
                    prerequisites=n.get("prerequisites", []),
                    unlocks=n.get("unlocks", [])
                )
                self.nodes[node.id] = node
        except Exception as e:
            print(f"[tech_tree] 加载失败: {e}, 用默认")
            self._init_defaults()

    def _init_defaults(self):
        """默认 15 节点 (3 主线 × 5 节点)"""
        defaults = [
            # 农本线
            ("agri_basic", "初农", "农本", 0, 0, "开垦基本农田, 每年粮食产量 +10%", {"grain_output": 0.10}, [], ["agri_water"]),
            ("agri_water", "水利", "农本", 1, 30, "兴修水利, 农田旱涝保收", {"grain_output": 0.20, "disaster_resist": 0.10}, ["agri_basic"], ["agri_tuntian"]),
            ("agri_tuntian", "屯田", "农本", 2, 80, "募民屯田, 充实边郡", {"grain_output": 0.30, "border_garrison": 5}, ["agri_water"], ["agri_tools"]),
            ("agri_tools", "曲辕犁", "农本", 3, 150, "改进农具, 精耕细作", {"grain_output": 0.40, "population_growth": 0.05}, ["agri_tuntian"], ["agri_reform"]),
            ("agri_reform", "土改新政", "农本", 4, 300, "授田于民, 国泰民安", {"grain_output": 0.50, "peasant_loyalty": 0.30}, ["agri_tools"], []),
            # 王权线
            ("law_basic", "律法", "王权", 0, 0, "颁布汉律, 纲常有序", {"legal_clarity": 0.10}, [], ["law_wen"]),
            ("law_wen", "文书", "王权", 1, 30, "设尚书台, 公文通达", {"admin_efficiency": 0.15}, ["law_basic"], ["law_math"]),
            ("law_math", "算学", "王权", 2, 80, "兴算学, 户籍田亩皆可核", {"tax_collection": 0.20, "census_accuracy": 0.30}, ["law_wen"], ["law_central"]),
            ("law_central", "中央集权", "王权", 3, 150, "推恩令, 削藩集权", {"vassal_loyalty": 0.25, "imperial_authority": 0.30}, ["law_math"], ["law_legitimacy"]),
            ("law_legitimacy", "法统正统", "王权", 4, 300, "定鼎之功, 万世法统", {"imperial_authority": 0.50, "succession_stability": 0.40}, ["law_central"], []),
            # 军备线
            ("mil_basic", "冶铁", "军备", 0, 0, "冶铁成兵, 装备初成", {"unit_attack": 0.10}, [], ["mil_tactic"]),
            ("mil_tactic", "兵法", "军备", 1, 30, "研习兵法, 阵法初成", {"unit_attack": 0.15, "unit_defense": 0.10}, ["mil_basic"], ["mil_intel"]),
            ("mil_intel", "间谍", "军备", 2, 80, "遣间探敌, 知己知彼", {"intel_quality": 0.30, "sabotage_chance": 0.20}, ["mil_tactic"], ["mil_elite"]),
            ("mil_elite", "精兵", "军备", 3, 150, "百战精兵, 以一当十", {"unit_attack": 0.30, "unit_defense": 0.20, "morale": 0.30}, ["mil_intel"], ["mil_legend"]),
            ("mil_legend", "百战雄狮", "军备", 4, 300, "百战之师, 威震天下", {"unit_attack": 0.50, "unit_defense": 0.40, "morale": 0.50, "intimidation": 0.30}, ["mil_elite"], []),
        ]
        for d in defaults:
            node = TechNode(
                id=d[0], name=d[1], line=d[2], tier=d[3], cost=d[4],
                description=d[5], effects=d[6], prerequisites=d[7], unlocks=d[8]
            )
            self.nodes[node.id] = node

    def init_state(self) -> TechState:
        """初始化玩家科技状态 (tier=0 默认解锁)"""
        unlocked = [n.id for n in self.nodes.values() if n.tier == 0]
        available = [n.id for n in self.nodes.values() if n.tier == 1]
        locked = [n.id for n in self.nodes.values() if n.tier >= 2]
        return TechState(unlocked=unlocked, available=available, locked=locked, reputation=0)

    def can_unlock(self, node_id: str, state: TechState) -> tuple[bool, str]:
        """检查节点是否可解锁"""
        node = self.nodes.get(node_id)
        if not node:
            return False, f"科技节点 {node_id} 不存在"
        if node_id in state.unlocked:
            return False, f"科技 {node.name} 已解锁"
        if node_id not in state.available:
            return False, f"科技 {node.name} 前置条件未满足"
        if state.reputation < node.cost:
            return False, f"声望不足 (需 {node.cost}, 当前 {state.reputation})"
        return True, "ok"

    def unlock(self, node_id: str, state: TechState) -> tuple[bool, str, Optional[TechNode]]:
        """解锁科技节点"""
        ok, reason = self.can_unlock(node_id, state)
        if not ok:
            return False, reason, None
        node = self.nodes[node_id]
        state.reputation -= node.cost
        state.unlocked.append(node_id)
        state.available.remove(node_id)
        # 找出新可解锁
        for next_id in node.unlocks:
            if next_id in state.locked:
                state.locked.remove(next_id)
                state.available.append(next_id)
        return True, f"已解锁 {node.name}", node

    def add_reputation(self, amount: int, state: TechState):
        """增加声望 (回合结算/事件奖励)"""
        state.reputation += amount

    def get_total_effects(self, state: TechState) -> Dict[str, float]:
        """汇总所有已解锁节点的效果"""
        total: Dict[str, float] = {}
        for uid in state.unlocked:
            node = self.nodes.get(uid)
            if not node:
                continue
            for k, v in node.effects.items():
                if isinstance(v, (int, float)):
                    total[k] = total.get(k, 0) + v
        return total

    def get_tree_view(self, state: TechState) -> Dict[str, Any]:
        """获取科技树视图 (给前端 DAG)"""
        nodes_view = []
        for node in self.nodes.values():
            status = "unlocked" if node.id in state.unlocked else (
                "available" if node.id in state.available else "locked"
            )
            nodes_view.append({
                "id": node.id, "name": node.name, "line": node.line,
                "tier": node.tier, "cost": node.cost,
                "description": node.description,
                "effects": node.effects,
                "prerequisites": node.prerequisites,
                "unlocks": node.unlocks,
                "status": status
            })
        return {
            "nodes": nodes_view,
            "reputation": state.reputation,
            "lines": ["农本", "王权", "军备"]
        }

    def to_dict(self, state: TechState) -> Dict[str, Any]:
        """状态序列化 (存档)"""
        return {
            "unlocked": state.unlocked,
            "available": state.available,
            "locked": state.locked,
            "reputation": state.reputation
        }

    def from_dict(self, data: Dict[str, Any]) -> TechState:
        """状态反序列化"""
        return TechState(
            unlocked=data.get("unlocked", []),
            available=data.get("available", []),
            locked=data.get("locked", []),
            reputation=data.get("reputation", 0)
        )


# === 单例 ===
_engine: Optional[TechTreeEngine] = None


def get_tech_engine() -> TechTreeEngine:
    global _engine
    if _engine is None:
        _engine = TechTreeEngine()
    return _engine
