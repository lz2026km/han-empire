"""游戏内容加载：人物/省份/事件/初始数据。L2。"""



import json
import os
from typing import Dict, List

from han_sim.paths import content_path, user_data_path


class GameContent:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.dirname(content_path(""))

    # ── 人物 ─────────────────────────────────────────────────

    def load_characters(self) -> List[Dict]:
        return self._load_json("characters.json")

    # ── 省份 ─────────────────────────────────────────────────

    def load_regions(self) -> List[Dict]:
        return self._load_json("regions.json")

    # ── 军队 ─────────────────────────────────────────────────

    def load_armies(self) -> List[Dict]:
        return self._load_json("armies.json")

    # ── 势力 ─────────────────────────────────────────────────

    def load_powers(self) -> List[Dict]:
        return self._load_json("powers.json")

    # ── 事件 ─────────────────────────────────────────────────

    def load_events(self) -> List[Dict]:
        return self._load_json("events.json")

    def load_seed_events(self) -> List[Dict]:
        return self._load_json("seed_events.json")

    def load_opening_crises(self) -> List[Dict]:
        return self._load_json("opening_crises.json")

    # ── 技能 ─────────────────────────────────────────────────

    def load_skills(self) -> List[Dict]:
        return self._load_json("skills.json")

    def load_skill_tools(self) -> List[Dict]:
        return self._load_json("skill_tools.json")

    def load_emperor_skills(self) -> List[Dict]:
        return self._load_json("emperor_skills.json")

    # ── 建筑 ─────────────────────────────────────────────────

    def load_buildings(self) -> List[Dict]:
        return self._load_json("buildings.json")

    # ── 提示词 ───────────────────────────────────────────────

    def load_prompt(self, name: str) -> str:
        path = os.path.join(self.data_dir, "prompts", f"{name}.md")
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    # ── 工具 ─────────────────────────────────────────────────

    def _load_json(self, filename: str) -> List[Dict]:
        path = content_path(filename)
        if not os.path.isfile(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []

    def _load_dict(self, filename: str) -> Dict:
        path = content_path(filename)
        if not os.path.isfile(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def load_game_content() -> GameContent:
    return GameContent()