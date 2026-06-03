"""
decision_log.py — 决策日志系统 (v3.1)
记录所有玩家决策, 支持回放
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = DATA_DIR / "decision_log.json"


@dataclass
class DecisionEntry:
    """单个决策记录"""
    id: str
    turn: int
    decision_type: str  # 诏书/任免/调兵/外交/科技
    action: str  # 具体动作
    description: str
    effects: Dict[str, float] = field(default_factory=dict)
    timestamp: int = 0  # unix time
    game_year: str = ""  # 游戏内年号 (如 "初平元年")
    consequence_ids: List[str] = field(default_factory=list)


class DecisionLog:
    """决策日志"""

    def __init__(self, log_path: Path = LOG_FILE):
        self.log_path = log_path
        self.entries: List[DecisionEntry] = []
        self._load()

    def _load(self):
        if not self.log_path.exists():
            return
        try:
            data = json.loads(self.log_path.read_text(encoding="utf-8"))
            for e in data.get("entries", []):
                self.entries.append(DecisionEntry(**e))
        except Exception as ex:
            print(f"[decision_log] 加载失败: {ex}")

    def _save(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"entries": [asdict(e) for e in self.entries]}
        self.log_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def record(
        self,
        turn: int,
        decision_type: str,
        action: str,
        description: str = "",
        effects: Optional[Dict[str, float]] = None,
        game_year: str = "",
        consequence_ids: Optional[List[str]] = None,
    ) -> DecisionEntry:
        """记录决策"""
        entry = DecisionEntry(
            id=f"dec_{int(time.time() * 1000)}_{turn}",
            turn=turn,
            decision_type=decision_type,
            action=action,
            description=description,
            effects=effects or {},
            timestamp=int(time.time()),
            game_year=game_year,
            consequence_ids=consequence_ids or [],
        )
        self.entries.append(entry)
        self._save()
        return entry

    def get_entries(self, turn: Optional[int] = None) -> List[DecisionEntry]:
        """获取决策记录, 可按回合过滤"""
        if turn is None:
            return list(self.entries)
        return [e for e in self.entries if e.turn == turn]

    def get_timeline(self) -> List[Dict[str, Any]]:
        """获取时间线 (供前端回放)"""
        timeline = []
        for e in sorted(self.entries, key=lambda x: (x.turn, x.timestamp)):
            timeline.append({
                "id": e.id,
                "turn": e.turn,
                "game_year": e.game_year,
                "decision_type": e.decision_type,
                "action": e.action,
                "description": e.description,
                "effects": e.effects,
                "consequence_count": len(e.consequence_ids),
            })
        return timeline

    def get_stats(self) -> Dict[str, Any]:
        """统计"""
        if not self.entries:
            return {
                "total": 0, "by_type": {}, "by_turn": {},
                "first_turn": 0, "last_turn": 0
            }
        by_type: Dict[str, int] = {}
        by_turn: Dict[int, int] = {}
        for e in self.entries:
            by_type[e.decision_type] = by_type.get(e.decision_type, 0) + 1
            by_turn[e.turn] = by_turn.get(e.turn, 0) + 1
        return {
            "total": len(self.entries),
            "by_type": by_type,
            "by_turn": by_turn,
            "first_turn": min(e.turn for e in self.entries),
            "last_turn": max(e.turn for e in self.entries),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"entries": [asdict(e) for e in self.entries]}

    def from_dict(self, data: Dict[str, Any]):
        self.entries = [DecisionEntry(**e) for e in data.get("entries", [])]
