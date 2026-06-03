"""游戏内容加载：人物/省份/事件/初始数据。L2。"""



import json
import os
from typing import Dict, List

from han_sim.paths import content_path, user_data_path


class GameContent:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.dirname(content_path(""))
        # ── 提示词缓存（v1.13.0 乾坤大挪移 Phase B 新增）──
        # 让 agents.create_*_agent() 的 ctx.xxx_prompt hasattr 检查通过
        self.game_world_prompt: str = self.load_prompt("game_world")
        self.season_simulator_prompt: str = self.load_prompt("season_simulator")
        self.simulator_prompt: str = self.load_prompt("simulator")
        self.minister_agent_prompt: str = self.load_prompt("minister_agent")
        self.memory_extractor_prompt: str = self.load_prompt("memory_extractor")
        self.extractor_prompt: str = self.load_prompt("extractor")
        self.score_extractor_prompt: str = self.load_prompt("score_extractor")
        self.decree_writer_prompt: str = self.load_prompt("decree_writer")
        self.opening_gazette_prompt: str = self.load_prompt("opening_gazette")
        self.chat_memory_extractor_prompt: str = self.load_prompt("chat_memory_extractor")

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

    # ── 后宫（v1.15.0 Phase D） ─────────────────────────────────

    def load_consorts(self) -> List[Dict]:
        """v1.15.0 乾坤大挪移 Phase D · 加载后宫人物画像（consorts.json）。

        与 characters.json 解耦，独立文件避免触发 characters.json 4097 行损坏 BUG。
        """
        path = content_path("consorts.json")
        if not os.path.isfile(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return []
        if isinstance(data, dict) and "consorts" in data:
            return data["consorts"]
        if isinstance(data, list):
            return data
        return []

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


def seed_consort_candidates(db: "GameDB") -> None:
    """将 content/consorts.json 的候选秀女数据灌入数据库。"""
    from pathlib import Path
    import json
    path = Path(__file__).parent.parent / "content" / "consorts.json"
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # v1.15.0 兼容：consorts.json 可能是 list 也可能是 {"consorts": [...]}
    if isinstance(data, dict) and "consorts" in data:
        candidates = data["consorts"]
    elif isinstance(data, list):
        candidates = data
    else:
        candidates = [data]
    for c in candidates:
        # v1.15.0 兼容：人物对象可能是 {name:..., ...} 或 {canonical_name:..., ...}
        nm = c.get("name") or c.get("canonical_name", "")
        if not nm:
            continue
        existing = db.conn.execute(
            "SELECT id FROM consort_candidates WHERE name=?", (nm,)
        ).fetchone()
        if existing:
            continue
        db.add_consort_candidate(
            name=nm,
            age=c.get("age", 18),
            background=c.get("background", "") or c.get("summary", ""),
            appearance=c.get("appearance", 50),
            talent=c.get("talent", 50),
            temperament=c.get("temperament", "温婉"),
            skills=c.get("skills", []),
            traits=c.get("traits", []),
            portrait_id=c.get("portrait_id", ""),
        )