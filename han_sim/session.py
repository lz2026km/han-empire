"""游戏会话：回合流转层。L8。"""



import uuid
import shutil
from pathlib import Path

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
from han_sim.flows import apply_monthly_flow, apply_skill_points
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
        # 初始化新增状态字段（Step4/5）
        from han_sim.models import init_faction_influence
        state.metrics["activated_skills"] = []
        state.metrics["built_buildings"] = []
        state.metrics["active_decrees"] = []
        init_faction_influence(state)
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
        # 初始化建筑（按简化版配置）
        initial_buildings = [
            {"id": "changan_weiyang", "region_id": "京兆尹", "name": "未央宫", "category": "内廷",
             "level": 4, "condition": 70, "maintenance": 10, "risk": 20,
             "output_metric": "威权", "output_amount": 3, "status": "正常"},
            {"id": "luoyang_wuku", "region_id": "河南尹", "name": "洛阳武库", "category": "军事",
             "level": 2, "condition": 15, "maintenance": 8, "risk": 70,
             "output_metric": "军备", "output_amount": 15, "status": "废墟"},
            {"id": "xuchang_palace", "region_id": "颍川郡", "name": "许昌行宫", "category": "内廷",
             "level": 3, "condition": 80, "maintenance": 12, "risk": 15,
             "output_metric": "威权", "output_amount": 2, "status": "正常"},
            {"id": "luoyang_taicang", "region_id": "河南尹", "name": "洛阳太仓", "category": "财政",
             "level": 2, "condition": 20, "maintenance": 5, "risk": 65,
             "output_metric": "汉室库", "output_amount": 3, "status": "残存"},
            {"id": "changan_taicang", "region_id": "京兆尹", "name": "长安太仓", "category": "财政",
             "level": 3, "condition": 65, "maintenance": 5, "risk": 25,
             "output_metric": "汉室库", "output_amount": 4, "status": "正常"},
            {"id": "xuchang_taicang", "region_id": "颍川郡", "name": "许昌太仓", "category": "财政",
             "level": 2, "condition": 75, "maintenance": 5, "risk": 20,
             "output_metric": "汉室库", "output_amount": 3, "status": "正常"},
            {"id": "jiujiang_taicang", "region_id": "豫章郡", "name": "九江粮仓", "category": "财政",
             "level": 1, "condition": 55, "maintenance": 5, "risk": 35,
             "output_metric": "汉室库", "output_amount": 2, "status": "正常"},
            {"id": "nanyang_taicang", "region_id": "南阳郡", "name": "南阳粮仓", "category": "财政",
             "level": 1, "condition": 55, "maintenance": 5, "risk": 40,
             "output_metric": "汉室库", "output_amount": 2, "status": "正常"},
            {"id": "jingzhou_taicang", "region_id": "南阳郡", "name": "荆州粮仓", "category": "财政",
             "level": 1, "condition": 60, "maintenance": 5, "risk": 30,
             "output_metric": "汉室库", "output_amount": 2, "status": "正常"},
        ]
        for b in initial_buildings:
            self.db.upsert_building(b)
        # 初始化后宫候选秀女
        from han_sim.content import seed_consort_candidates
        seed_consort_candidates(self.db)
        self.db.commit()

    # ── 召见大臣 ─────────────────────────────────────────────

    def summon_minister(self, minister_name: str, instruction: str) -> SummonResult:
        """天子召见大臣，大臣回应（记忆召回注入 + 召对记忆提取）。"""
        minister = self.db.get_character(minister_name)
        if not minister:
            return SummonResult(chat_text=f"找不到大臣：{minister_name}")

        # ── 召见前：忠诚度上下文注入 ─────────────────────────
        from han_sim.flows import get_minister_loyalty_context, calc_faction_influence
        loyalty_ctx = get_minister_loyalty_context(self.db, minister["name"])

        # ── 召见前：派系上下文注入 ─────────────────────────────
        influences = calc_faction_influence(self.state, self.db)
        faction_ctx = "当前各派系影响力：" + "、".join([f"{k}={v:.0f}" for k, v in influences.items()])

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

        # ── 召见前：威权等级上下文注入（Step2新增）─────────────────
        from han_sim.models import get_authority_level
        authority = self.state.metrics.get("威权", 0)
        auth_level = get_authority_level(authority)
        authority_ctx = f"当前天子威权：{authority}/100（{auth_level.label}），召对效果倍率：{auth_level.summon_mult:.0%}"

        agent = create_minister_agent(minister, self.state, memory_brief=memory_brief, loyalty_ctx=loyalty_ctx)

        prompt = (
            f"{context}\n"
            f"【天子此次询问】{instruction}\n\n"
            f"请以{minister['name']}的身份回应天子。\n"
            f"【忠诚度提示】{loyalty_ctx}\n"
            f"【派系态势】{faction_ctx}\n"
            f"【天子威权】{authority_ctx}"
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
        # 月末发放天子技能点：威权≥40每回合+1，威权≥60每回合+2，上限10点
        apply_skill_points(self.state, self.db)
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
        """保存当前进度到存档文件。返回存档文件路径。"""
        src = user_data_path(f"campaign_{self.campaign_id}.db")
        dst = user_data_path(f"campaign_{self.campaign_id}_save.db")
        shutil.copy2(src, dst)
        return dst

    @staticmethod
    def load(campaign_id: str) -> "GameSession":
        """从存档文件恢复游戏会话。"""
        save_path = user_data_path(f"campaign_{campaign_id}_save.db")
        if not Path(save_path).exists():
            raise FileNotFoundError(f"存档不存在：{save_path}")
        src = user_data_path(f"campaign_{campaign_id}.db")
        shutil.copy2(save_path, src)
        db = GameDB(src)
        state = db.load_state()
        from han_sim.content import load_game_content
        content = load_game_content()
        session = GameSession(
            campaign_id=campaign_id,
            state=state,
            db=db,
            content=content,
            turn_phase=getattr(state, 'turn_phase', PHASE_SUMMONING),
        )
        return session

    @staticmethod
    def list_saves() -> List[Dict]:
        """列出所有存档。"""
        base = user_data_path("")
        saves = []
        for f in Path(base).glob("campaign_*_save.db"):
            cid = f.stem.replace("campaign_", "").replace("_save", "")
            import time
            st = f.stat()
            saves.append({
                "campaign_id": cid,
                "path": str(f),
                "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
            })
        saves.sort(key=lambda x: x["modified"], reverse=True)
        return saves

    @staticmethod
    def delete_save(campaign_id: str) -> bool:
        """删除指定存档。"""
        save_path = user_data_path(f"campaign_{campaign_id}_save.db")
        if Path(save_path).exists():
            Path(save_path).unlink()
            return True
        return False

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