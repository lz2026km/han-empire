"""游戏会话：回合流转层。L8。"""



import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from han_sim.agents import create_minister_agent
from han_sim.constants import PHASE_ISSUED, PHASE_REVIEWING, PHASE_SUMMONING
from han_sim.content import GameContent
from han_sim.conversation import (
    build_context_prompt,
    get_recent_exchanges,
    init_conv_table,
    save_message,
)
from han_sim.db import GameDB
from han_sim.flows import apply_monthly_flow
from han_sim.models import Character, CourtContext, GameState
from han_sim.paths import user_data_path
from han_sim.registry import build_memory_brief, build_context_for_minister


AUTO_SAVE_PREFIX = "auto_"
AUTO_SAVE_KEEP_TURNS = 3


class TurnPhase(Enum):
    SUMMONING = PHASE_SUMMONING
    REVIEWING = PHASE_REVIEWING
    ISSUED = PHASE_ISSUED


@dataclass
class SummonResult:
    chat_text: str
    refresh_ministers: List[str] = field(default_factory=list)


@dataclass
class ReviewResult:
    summary: str
    new_events: List[Dict] = field(default_factory=list)
    metrics_delta: Dict[str, int] = field(default_factory=dict)
    log_entries: List[str] = field(default_factory=list)


@dataclass
class GameSession:
    campaign_id: str
    state: GameState
    db: GameDB
    content: GameContent
    turn_phase: str = PHASE_SUMMONING

    @staticmethod
    def new(campaign_id: str, content: GameContent) -> "GameSession":
        db_path = user_data_path(f"campaign_{campaign_id}.db")
        db = GameDB.new(db_path)
        state = GameState()
        session = GameSession(
            campaign_id=campaign_id,
            state=state,
            db=db,
            content=content,
            turn_phase=PHASE_SUMMONING,
        )
        session._init_db(content)
        init_conv_table(session.db)
        return session

    def _init_db(self, content: GameContent) -> None:
        for c in content.load_characters():
            self.db.upsert_character(c)
        for r in content.load_regions():
            self.db.upsert_region(r)
        for a in content.load_armies():
            self.db.upsert_army(a)
        for p in content.load_powers():
            self.db.upsert_power(p)
        for e in content.load_seed_events():
            self.db.upsert_event(e)
        self.db.commit()

    # ── 召见大臣 ─────────────────────────────────────────────

    def summon_minister(self, minister_name: str, instruction: str) -> SummonResult:
        """天子召见大臣，大臣回应（记忆召回注入 + 召对记忆提取）。"""
        minister = self.db.get_character(minister_name)
        if not minister:
            return SummonResult(chat_text=f"找不到大臣：{minister_name}")

        # ── 召见前：记忆召回 ───────────────────────────────────
        memory_brief = build_memory_brief(
            character_name=minister["name"],
            faction=minister.get("faction", ""),
            office_type=minister.get("office_type", ""),
            turn=self.state.turn,
            db=self.db,
            limit=5,
        )

        # 加载历史对话，构建上下文
        recent = get_recent_exchanges(self.db, self.campaign_id, minister_name, n=6)
        context = build_context_prompt(recent)

        agent = create_minister_agent(minister, self.state, memory_brief=memory_brief)

        prompt = (
            f"{context}\n"
            f"【天子此次询问】{instruction}\n\n"
            f"请以{minister['name']}的身份回应天子。"
        )
        response = agent.run(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        if not isinstance(text, str):
            text = str(text)

        # 持久化对话历史
        save_message(self.db, self.campaign_id, minister_name,
                    "emperor", instruction, self.state.turn, self.state.period)
        save_message(self.db, self.campaign_id, minister_name,
                    "minister", text, self.state.turn, self.state.period)

        self.db.append_log(self.state.turn, "summoning",
                           f"召见 {minister['name']}：{instruction[:50]}")
        self.db.commit()
        return SummonResult(chat_text=text)

    # ── 月末推演 ─────────────────────────────────────────────

    def run_review(self) -> ReviewResult:
        """月末推演：数值结算 + 事件生成。"""
        fiscal = apply_monthly_flow(self.state, self.db)
        log_entries = [f"【{self.state.year}年{self.state.period}月结算】{fiscal['net']:+d}万两"]

        self.state.next_period()
        self.turn_phase = PHASE_SUMMONING

        self.db.save_state("turn", self.state.turn)
        self.db.save_state("year", self.state.year)
        self.db.save_state("period", self.state.period)
        self.db.save_state("metrics", self.state.metrics)
        self.db.commit()

        return ReviewResult(
            summary=f"{self.state.year}年{self.state.period}月结束，进入{self.state.year}年{self.state.period+1}月",
            new_events=[],
            metrics_delta={"汉室库": fiscal["net"]},
            log_entries=log_entries,
        )

    # ── 存档 ─────────────────────────────────────────────────

    def save(self) -> str:
        path = user_data_path(f"campaign_{self.campaign_id}_save.db")
        return path

    def export_state(self) -> Dict:
        return {
            "campaign_id": self.campaign_id,
            "year": self.state.year,
            "period": self.state.period,
            "turn": self.state.turn,
            "metrics": self.state.metrics,
            "phase": self.turn_phase,
        }

    def get_active_ministers(self) -> List[Dict]:
        return self.db.list_characters(status="active")