"""
tutorial.py — 新手引导系统 (v3.2)
7 步引导: 开局 → 诏书 → 战役 → 科技 → 后果 → 存档 → 统计
高亮目标元素 + 步骤提示 + 强制等待
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
TUTORIAL_FILE = CONTENT_DIR / "tutorial_steps.json"


@dataclass
class TutorialStep:
    """单步引导"""
    id: str
    order: int
    title: str
    description: str
    target: str  # 高亮目标元素 (CSS selector)
    position: str = "bottom"  # 提示框位置
    required_action: Optional[str] = None  # 强制等待动作
    highlight_color: str = "#3b82f6"
    can_skip: bool = True
    icon: str = ""  # 不用 emoji, 用实色标识符


@dataclass
class TutorialState:
    """玩家引导状态"""
    current_step: int = 0
    completed: List[str] = field(default_factory=list)
    skipped: bool = False
    started_at: int = 0
    completed_at: Optional[int] = 0


class TutorialEngine:
    """引导引擎"""

    def __init__(self, defs_path: Path = TUTORIAL_FILE):
        self.steps: Dict[str, TutorialStep] = {}
        self._load_definitions(defs_path)

    def _load_definitions(self, path: Path):
        if not path.exists():
            self._init_defaults()
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for s in data.get("steps", []):
                step = TutorialStep(
                    id=s["id"], order=s["order"], title=s["title"],
                    description=s["description"], target=s["target"],
                    position=s.get("position", "bottom"),
                    required_action=s.get("required_action"),
                    highlight_color=s.get("highlight_color", "#3b82f6"),
                    can_skip=s.get("can_skip", True),
                    icon=s.get("icon", "")
                )
                self.steps[step.id] = step
        except Exception:
            self._init_defaults()

    def _init_defaults(self):
        """默认 7 步引导"""
        defaults = [
            ("welcome", 0, "欢迎来到汉献帝", "陛下, 您的王朝由您主宰。本教程将引导您掌握核心玩法。", ".app-header", "bottom", None),
            ("issue_decree", 1, "颁布诏书", "点击「诏书」按钮, 颁布第一道圣旨。", "[data-tutorial='decree']", "right", "issue_decree"),
            ("view_battle", 2, "指挥战役", "查看「战役」, 调兵遣将。", "[data-tutorial='battle']", "right", "view_battle"),
            ("unlock_tech", 3, "解锁科技", "打开「科技树」, 累计声望后解锁节点。", "[data-tutorial='tech-tree']", "left", "unlock_tech"),
            ("view_consequence", 4, "后果链", "查看「后果链」, 您的决策会产生长期影响。", "[data-tutorial='consequence']", "left", "view_consequence"),
            ("save_game", 5, "存档", "点击「存档」, 保存您的进度。", "[data-tutorial='save']", "right", "save_game"),
            ("view_stats", 6, "回放", "查看「决策回放」, 复盘您的治理。", "[data-tutorial='replay']", "left", "view_stats"),
        ]
        for d in defaults:
            step = TutorialStep(id=d[0], order=d[1], title=d[2], description=d[3], target=d[4],
                                position=d[5], required_action=d[6], highlight_color="#3b82f6",
                                can_skip=True, icon="")
            self.steps[step.id] = step

    def init_state(self) -> TutorialState:
        return TutorialState(current_step=0, completed=[], skipped=False, started_at=0, completed_at=None)

    def get_step(self, order: int) -> Optional[TutorialStep]:
        for s in self.steps.values():
            if s.order == order:
                return s
        return None

    def get_all_steps(self) -> List[TutorialStep]:
        return sorted(self.steps.values(), key=lambda s: s.order)

    def advance(self, state: TutorialState) -> bool:
        """前进一步"""
        current = self.get_step(state.current_step)
        if current:
            state.completed.append(current.id)
        if state.current_step >= len(self.steps) - 1:
            state.completed_at = 1
            return False  # 已完成
        state.current_step += 1
        return True

    def skip(self, state: TutorialState) -> None:
        """跳过"""
        state.skipped = True
        state.completed_at = 1

    def is_completed(self, state: TutorialState) -> bool:
        return state.completed_at is not None

    def get_progress(self, state: TutorialState) -> Dict[str, Any]:
        return {
            "current_step": state.current_step,
            "total_steps": len(self.steps),
            "completed_count": len(state.completed),
            "is_completed": self.is_completed(state),
            "skipped": state.skipped,
            "percent": (state.current_step / max(len(self.steps), 1)) * 100,
        }

    def to_dict(self, state: TutorialState) -> Dict[str, Any]:
        return {
            "current_step": state.current_step,
            "completed": state.completed,
            "skipped": state.skipped,
            "started_at": state.started_at,
            "completed_at": state.completed_at,
        }

    def from_dict(self, data: Dict[str, Any]) -> TutorialState:
        return TutorialState(
            current_step=data.get("current_step", 0),
            completed=data.get("completed", []),
            skipped=data.get("skipped", False),
            started_at=data.get("started_at", 0),
            completed_at=data.get("completed_at"),
        )


_engine: Optional[TutorialEngine] = None


def get_tutorial_engine() -> TutorialEngine:
    global _engine
    if _engine is None:
        _engine = TutorialEngine()
    return _engine
