"""
auto_save.py — 自动存档系统 (v3.2)
每 N 回合自动存档 + 多档位 + 命名
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


SAVE_DIR = Path(__file__).resolve().parent.parent / "data" / "saves"
AUTO_SAVE_SLOT = "auto"  # 自动存档专用槽


@dataclass
class SaveSlot:
    """存档槽位"""
    slot_id: str  # 槽位 ID (0-9 或 auto)
    name: str
    turn: int
    campaign_id: str
    created_at: int
    updated_at: int
    game_year: str = ""
    thumbnail: str = ""  # 缩略图 (base64)
    file_path: str = ""  # 实际存档文件路径


class AutoSaveManager:
    """自动存档管理"""

    def __init__(self, save_dir: Path = SAVE_DIR, max_auto: int = 3, interval: int = 5):
        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.max_auto = max_auto  # 最多保留 3 个自动存档
        self.interval = interval  # 每 5 回合自动存档
        self._last_auto_turn: Dict[str, int] = {}  # campaign_id -> last_turn

    def should_auto_save(self, campaign_id: str, current_turn: int) -> bool:
        """是否应该自动存档"""
        last = self._last_auto_turn.get(campaign_id, -self.interval)
        return (current_turn - last) >= self.interval

    def auto_save(self, campaign_id: str, turn: int, state: Dict[str, Any],
                  game_year: str = "") -> Optional[SaveSlot]:
        """执行自动存档"""
        if not self.should_auto_save(campaign_id, turn):
            return None

        # 清理旧自动存档
        self._cleanup_auto_saves(campaign_id)

        # 保存到 auto_时间戳 槽
        timestamp = int(time.time())
        slot_id = f"auto_{timestamp}"
        file_path = self.save_dir / f"{campaign_id}_{slot_id}.json"
        try:
            file_path.write_text(
                json.dumps({"turn": turn, "state": state, "game_year": game_year,
                            "saved_at": timestamp, "auto": True}, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            self._last_auto_turn[campaign_id] = turn
            return SaveSlot(
                slot_id=slot_id, name=f"自动存档 · 回合{turn}",
                turn=turn, campaign_id=campaign_id,
                created_at=timestamp, updated_at=timestamp,
                game_year=game_year, file_path=str(file_path)
            )
        except Exception as e:
            print(f"[auto_save] 失败: {e}")
            return None

    def _cleanup_auto_saves(self, campaign_id: str):
        """清理旧自动存档, 保留 max_auto 个"""
        pattern = f"{campaign_id}_auto_*.json"
        files = sorted(self.save_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in files[self.max_auto:]:
            try:
                f.unlink()
            except Exception:
                pass

    def list_auto_saves(self, campaign_id: str) -> List[SaveSlot]:
        """列出某 campaign 的自动存档"""
        pattern = f"{campaign_id}_auto_*.json"
        saves = []
        for f in sorted(self.save_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                saves.append(SaveSlot(
                    slot_id=f.stem.split("_auto_")[-1],
                    name=f"自动存档 · 回合{data.get('turn', 0)}",
                    turn=data.get("turn", 0),
                    campaign_id=campaign_id,
                    created_at=data.get("saved_at", 0),
                    updated_at=data.get("saved_at", 0),
                    game_year=data.get("game_year", ""),
                    file_path=str(f)
                ))
            except Exception:
                continue
        return saves


_manager: Optional[AutoSaveManager] = None


def get_auto_save_manager() -> AutoSaveManager:
    global _manager
    if _manager is None:
        _manager = AutoSaveManager()
    return _manager
