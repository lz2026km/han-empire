"""诏书系统：拟旨 → LLM生成 → 效果结算。L5。

天子回合的 issued 阶段使用：
  decree.py 负责"天子拟旨"这一核心行动。

核心流程：
  1. 拟定诏书意图（intent + 可选大臣意见）
  2. 调用 LLM 将意图扩展为完整诏书文本
  3. 根据诏书类型执行数值效果结算
  4. 将诏书记录写入 db
"""



import json
import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from agno.agent import Agent

from han_sim.db import GameDB
from han_sim.llm_config import load_llm_config
from han_sim.llm_model import create_chat_model, extract_agent_text
from han_sim.models import GameState


# ── 诏书类型 ────────────────────────────────────────────────────────────────

@dataclass
class DecreeEffect:
    metric: str
    delta: int
    description: str


# 诏书效果模板（intent → 效果列表）
DECREE_EFFECT_TEMPLATES: Dict[str, List[Dict]] = {
    "赈济灾民": [
        {"metric": "汉室库", "delta": -20, "description": "拨付赈灾银20万两"},
        {"metric": "声望", "delta": +10, "description": "民心稍安"},
    ],
    "犒赏三军": [
        {"metric": "汉室库", "delta": -30, "description": "犒赏军士30万两"},
        {"metric": "声望", "delta": +5, "description": "军中感念皇恩"},
    ],
    "颁布新政": [
        {"metric": "声望", "delta": +15, "description": "新政得人心"},
        {"metric": "威权", "delta": +5, "description": "天子振作朝纲"},
    ],
    "招降叛将": [
        {"metric": "威权", "delta": +10, "description": "招抚有功"},
        {"metric": "声望", "delta": +5, "description": "天下知天子仁义"},
    ],
    "清剿黄巾": [
        {"metric": "声望", "delta": +10, "description": "剿贼安民"},
        {"metric": "威权", "delta": +5, "description": "威权略振"},
    ],
    "迁都": [
        {"metric": "威权", "delta": -20, "description": "迁都动摇人心"},
        {"metric": "声望", "delta": -10, "description": "百官疲于奔命"},
    ],
    "征召人才": [
        {"metric": "声望", "delta": +8, "description": "求贤令一出，人心归附"},
        {"metric": "威权", "delta": +3, "description": "朝廷有新血注入"},
    ],
    "废除苛政": [
        {"metric": "声望", "delta": +12, "description": "百姓感荷皇恩"},
        {"metric": "威权", "delta": -5, "description": "触动藩镇利益"},
    ],
    "与藩镇会盟": [
        {"metric": "威权", "delta": +8, "description": "会盟暂稳局面"},
        {"metric": "藩镇", "delta": -5, "description": "藩镇暂时服从"},
    ],
    "讨伐董卓": [
        {"metric": "威权", "delta": +15, "description": "天子下诏讨贼，民心大快"},
        {"metric": "声望", "delta": +10, "description": "天下知汉室未亡"},
        {"metric": "藩镇", "delta": -10, "description": "各镇响应讨伐"},
    ],
    "衣带密诏": [
        {"metric": "威权", "delta": +8, "description": "密诏已下，忠臣暗通款曲"},
        {"metric": "威权", "delta": -5, "description": "秘密外泄风险"},
        {"metric": "声望", "delta": +3, "description": "忠义之心天下知"},
    ],
    "东归诏": [
        {"metric": "威权", "delta": +5, "description": "颁布东归诏令，人心振奋"},
        {"metric": "声望", "delta": +5, "description": "天下望天子归正朔"},
    ],
}


# 诏书类型枚举（含特殊诏书）
DECREE_KINDS = {
    "normal_edict": "普通诏书",
    "secret_edict": "衣带密诏",
    "moving_edict": "迁都诏书",
    "campaign_edict": "讨伐诏书",
    "east_return_edict": "东归诏书",
}


@dataclass
class Decree:
    intent: str           # 诏书意图（用户输入）
    full_text: str        # LLM 生成的完整诏书文本
    decree_type: str      # 诏书类型
    effects: List[Dict]   # 效果列表
    cost: int             # 耗费（万两）
    narrative: str        # 推行后的叙事


@dataclass
class DecreeResult:
    decree: Decree
    metrics_delta: Dict[str, int]
    log_entries: List[str]


def issue_secret_edict(state: GameState, db: GameDB) -> DecreeResult:
    """发布衣带密诏。威权≥30且忠诚大臣≥3人时可发布，
    成功率=威权/100，失败则威权额外-10。"""
    authority = state.metrics.get("威权", 0)
    if authority < 30:
        return _decree_fail_result("威权不足30，衣带诏外泄风险过大，不宜发布")

    loyal_count = db.conn.execute(
        "SELECT COUNT(*) FROM characters WHERE loyalty>=70 AND status='active'").fetchone()[0]
    if loyal_count < 3:
        return _decree_fail_result(f"忠诚大臣仅{loyal_count}人，不足三人，密诏难以推行")

    intent = "衣带密诏：密召忠义之臣，暗图除贼"
    decree_type = "衣带密诏"
    effects = _get_decree_effects(intent)

    # 成功与否由威权决定
    success = random.random() < (authority / 100)
    if success:
        state.metrics["威权"] = min(100, authority + 8)
        # 在 issues 中建立高优先权"密谋讨贼"事项
        db.insert_issue(
            state,
            title="密谋讨贼",
            description="忠臣暗通款曲，共谋除贼大计",
            origin_kind="decree",
            origin_ref="secret_edict",
            severity=80,
            kind="political",
            bar_value=30,
            tags=["衣带诏", "除贼"],
            resolve_condition="董卓伏诛",
            ongoing_effects={"metrics": {"威权": -1}},
            effect_on_resolve={"metrics": {"威权": 15, "声望": 10}},
            effect_on_fail={"metrics": {"威权": -10, "声望": -5}},
        )
        full_text = _generate_decree_text(intent, decree_type, state)
        decree = Decree(intent=intent, full_text=full_text, decree_type=decree_type,
                       effects=effects, cost=0, narrative="衣带密诏已下，忠臣暗通款曲。")
        db.append_log(state.turn, "issued", "衣带密诏成功，密谋讨贼进行中")
        return DecreeResult(decree=decree, metrics_delta={"威权": +8}, log_entries=["衣带密诏成功，忠臣暗通款曲"])
    else:
        state.metrics["威权"] = max(0, authority - 10)
        decree = Decree(intent=intent, full_text="", decree_type=decree_type,
                       effects=[{"metric": "威权", "delta": -10, "description": "密谋外泄"}],
                       cost=0, narrative="衣带密诏外泄，帝威权大损")
        db.append_log(state.turn, "issued", "衣带密诏外泄，威权受损")
        return DecreeResult(decree=decree, metrics_delta={"威权": -10}, log_entries=["衣带密诏外泄，帝威权大损"])


def _decree_fail_result(reason: str) -> DecreeResult:
    """返回一个表示失败的 DecreeResult（不生成诏书文本）。"""
    decree = Decree(intent=reason, full_text="", decree_type="failed",
                   effects=[], cost=0, narrative=reason)
    return DecreeResult(decree=decree, metrics_delta={}, log_entries=[reason])


def _resolve_decree_type(intent: str) -> str:
    """从意图文本推断诏书类型。"""
    for key in DECREE_EFFECT_TEMPLATES:
        if key in intent:
            return key
    return "颁布诏书"  # 默认类型


def _get_decree_effects(intent: str) -> List[Dict]:
    """按诏书类型获取效果模板，找不到则用默认。"""
    decree_type = _resolve_decree_type(intent)
    return DECREE_EFFECT_TEMPLATES.get(decree_type, [
        {"metric": "威权", "delta": +5, "description": "诏令已下"},
        {"metric": "声望", "delta": +3, "description": "天下闻风而动"},
    ])


def _apply_decree_effects(
    effects: List[Dict],
    state: GameState,
    db: GameDB,
) -> tuple[Dict[str, int], List[str]]:
    """应用诏书效果，返回 (delta_dict, log_entries)。"""
    delta: Dict[str, int] = {}
    logs: List[str] = []
    for e in effects:
        metric = e["metric"]
        d = e["delta"]
        state.metrics[metric] = max(0, state.metrics.get(metric, 0) + d)
        delta[metric] = delta.get(metric, 0) + d
        logs.append(e["description"])
    state.clamp()
    db.append_log(state.turn, "issued", f"拟旨：{effects[0]['description'] if effects else '诏令已下'}")
    return delta, logs


def _extract_json(text: str) -> Optional[Dict]:
    """从 LLM 输出中提取 JSON dict。"""
    text = text.strip()
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return None


def _generate_decree_text(intent: str, decree_type: str, state: GameState) -> str:
    """调用 LLM 将意图扩展为完整诏书文本。"""
    prompt = (
        f"你是一位精通东汉末历史的宫廷文官，奉天子之命起草诏书。\n"
        f"\n"
        f"【诏书意图】{intent}\n"
        f"【诏书类型】{decree_type}\n"
        f"【当前时间】{state.year}年{state.period}月\n"
        f"【汉室现状】\n"
        f"  汉室库：{state.metrics.get('汉室库', 0)}万两\n"
        f"  声望：{state.metrics.get('声望', 0)}/100\n"
        f"  威权：{state.metrics.get('威权', 0)}/100\n"
        f"  藩镇：{state.metrics.get('藩镇', 0)}/100\n"
        f"\n"
        f"请撰写一份完整的汉帝诏书，要求：\n"
        f"1. 以「奉天承运，皇帝诏曰」开头\n"
        f"2. 300-500字，文言风格，庄重威严\n"
        f"3. 末尾以「布告天下，咸使闻知」收尾\n"
        f"4. 诏书内容须与【诏书意图】相符，体现天子忧心天下之心\n"
        f"5. 不要提及LLM或AI等字样\n"
        f"\n"
        f"直接输出诏书正文，不要解释。"
    )
    try:
        llm_cfg = load_llm_config(
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-M2.7-highspeed",
            api_key="",
        )
        agent = Agent(
            name="诏书起草",
            model=create_chat_model(llm_cfg, temperature=0.7, max_tokens=800),
            instructions=[prompt],
            markdown=False,
        )
        text = extract_agent_text(agent.run(prompt))
        return text.strip()
    except Exception:
        # LLM 失败时返回 fallback
        return (
            f"奉天承运，皇帝诏曰：\n"
            f"朕以凉薄，遭时多难，{intent}，实乃当务之急。\n"
            f"今下令天下，共襄盛举，咸使闻知。\n"
            f"布告天下，咸使闻知。"
        )


def issue_decree(
    intent: str,
    state: GameState,
    db: GameDB,
    minister_advice: Optional[str] = None,
) -> DecreeResult:
    """执行"拟旨"行动：生成诏书并结算效果。"""
    decree_type = _resolve_decree_type(intent)
    effects = _get_decree_effects(intent)
    cost = sum(abs(e["delta"]) for e in effects if e["metric"] in ("汉室库", "内库"))

    # 耗费汉室库（如果不够则记为亏损，效果减半）
    if cost > 0:
        if state.metrics.get("汉室库", 0) >= cost:
            state.metrics["汉室库"] -= cost
        else:
            # 钱不够，效果减半但不拒绝（天子处境艰难）
            effects = [
                {**e, "delta": e["delta"] // 2}
                for e in effects
            ]

    # LLM 生成诏书文本
    full_text = _generate_decree_text(intent, decree_type, state)

    # 应用效果
    metrics_delta, log_entries = _apply_decree_effects(effects, state, db)

    decree = Decree(
        intent=intent,
        full_text=full_text,
        decree_type=decree_type,
        effects=effects,
        cost=cost,
        narrative="",
    )
    decree.narrative = (
        f"{state.year}年{state.period}月，天子颁布《{decree_type}》诏，"
        f"{'；'.join(log_entries[:2]) or '已布告天下'}。"
    )

    # 写入 db
    db.save_state("last_decree", {
        "intent": intent,
        "type": decree_type,
        "turn": state.turn,
        "year": state.year,
        "period": state.period,
    })
    db.commit()

    return DecreeResult(
        decree=decree,
        metrics_delta=metrics_delta,
        log_entries=log_entries,
    )