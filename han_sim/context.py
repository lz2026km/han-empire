"""上下文生成与文本匹配：历史锚点、胜负判定、地区/军队/人物模糊匹配、
人物/事件上下文串、给 LLM 的 state_context。L4。

通过 bind_content() 注入 GameContent（过渡期）。
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from han_sim.assets import format_money, format_money_delta
from han_sim.exceptions import LLMContractError

if TYPE_CHECKING:
    from han_sim.content import GameContent
    from han_sim.models import GameState, Character, Event

_content: Optional["GameContent"] = None


def bind_content(content: "GameContent") -> None:
    global _content
    _content = content


def _ctx() -> "GameContent":
    if _content is None:
        raise RuntimeError("context.bind_content() 未调用：GameContent 未注入。")
    return _content


# ── 历史锚点 ──────────────────────────────────────────────────────────────

def historical_anchor_for_month(year: int, month: int) -> Dict[str, object]:
    """给 LLM 的历史护栏：关键历史事变必须出现，但玩家可改变走向和结果。"""
    anchors = {
        (189, 1): "中平六年正月，灵帝病重，何进与蹇硕争权，何皇后所生刘辩为皇子，陈留王刘协为董太后所养。灵帝遗命以刘协为嗣，但何进杀蹇硕，辩即帝位，是为少帝，何太后临朝。",
        (189, 3): "董卓进京历史窗口：董卓率西凉兵自陇右入京途中，何进已被宦官诱杀，少帝流落北邙。董卓驰援救驾，迎帝还宫，废刘辩为弘农王，改立刘协，是为献帝。",
        (189, 4): "董卓已掌控京畿，迁都长安，焚毁洛阳宫阙、陵墓。袁绍、袁术、曹操等出逃，诸侯开始串联。",
        (189, 12): "诸侯讨董历史窗口开启：袁绍据冀州、袁术据南阳、曹操据陈留、袁绍盟主号召天下诸侯会盟酸枣，讨伐董卓。",
        (190, 1): "诸侯联军与董卓军对峙于汜水关、虎牢关。董卓焚洛阳迁都，长沙太守孙坚率先破洛，联军内部开始争权夺利。",
        (190, 3): "诸侯内讧，联军解散。董卓退守长安，天下进入群雄割据时代。",
        (191, 4): "孙坚攻入洛阳，得传国玉玺，旋被袁术算计，驻军鲁阳。",
        (192, 4): "王允设连环计，吕布杀董卓于长安北掖门。董卓死，其部将李傕、郭汜攻入长安，杀王允，献帝再次落入军阀之手。",
        (192, 6): "董卓伏诛后，西凉军内部火拼，李傕、郭汜互攻，献帝在乱军中辗转。",
        (195, 1): "献帝东归历史窗口：趁李傕、郭汜互攻，献帝在杨奉、董承护送下逃出长安，东归洛阳。",
        (196, 7): "曹操迎奉献帝至许昌，改元建元，挟天子以令诸侯。汉室威权开始部分恢复，但实质仍由曹操掌控。",
        (197, 1): "袁术在寿春称帝，僭号仲氏。曹操、刘备、吕布、孙策联军讨伐。",
        (199, 12): "曹操破袁术，袁术败亡。曹操基本统一北方中原地区。",
        (200, 1): "官渡之战历史窗口：袁绍率十万大军南渡黄河，与曹操对峙于官渡。曹操兵少粮尽，坚守待机。",
        (200, 10): "曹操奇袭乌巢，烧袁绍军粮，袁绍大败。官渡之战曹操以少胜多，奠定统一北方基础。",
        (202, 9): "袁绍病亡，子弟争权，曹操陆续平定河北。",
        (207, 8): "曹操北征乌桓，白狼山之战大破乌桓骑兵，北方边境基本安定。",
        (208, 7): "荆州牧刘表病死，曹操南征荆州，刘琮投降。刘备败走夏口，孙权决定联刘抗曹。",
        (208, 12): "赤壁之战：周瑜、黄盖以火攻大破曹操水军，刘备、孙权联军以少胜多，三分天下格局初步形成。",
        (209, 1): "赤壁战后，曹操退回北方，刘备占据荆州南部，孙权保有江东，三国鼎立局面正式形成。",
        (211, 3): "曹操征马超、韩遂，关中之战爆发。渭南之战后曹操平定关中。",
        (214, 5): "刘备入蜀，夺取益州牧刘璋地盘，汉中成为争夺焦点。",
        (215, 11): "曹操征张鲁，取汉中，但未继续南下，留守合肥的张辽威震逍遥津。",
        (219, 5): "刘备夺取汉中，进位汉中王，关羽北伐水淹七军，威震华夏。",
        (219, 12): "吕蒙白衣渡江，关羽败走麦城，被擒杀。孙权夺回荆州。",
        (220, 1): "曹操病亡，子曹丕继魏王位。汉室气数已尽，禅让压力逼近。",
        (220, 12): "曹丕篡汉，废献帝为山阳公，汉朝正式灭亡，三国时代开始。",
    }
    note = anchors.get((year, month), "")
    return {
        "date": f"{year}年{month}月",
        "note": note or f"本月无硬性历史锚点，但天下大势由陛下与诸侯共同书写。",
        "must_respect": bool(note),
    }


# ── 胜负判定 ───────────────────────────────────────────────────────────────

def victory_status(state: "GameState", db) -> Dict[str, object]:
    """汉末版胜负判定：
    - 汉室中兴：威权≥85 且 声望≥80 且 董卓已诛 且 藩镇≤30
    - 献帝东归：皇帝已至许昌 且 威权≥60
    - 董卓伏诛：dong_zhuo_killed_turn > 0 且 state.dong_zhuo_killed_turn < state.turn - 6
    - 三分天下：存在3个以上独立强权，无人能统一
    - 汉室覆灭：藩镇≥95 且 威权≤5
    - 禅让：state.metrics.get("禅让标志", 0) >= 100
    """
    authority = state.metrics.get("威权", 0)
    prestige = state.metrics.get("声望", 0)
    warlords = state.metrics.get("藩镇", 0)
    treasury = state.metrics.get("汉室库", 0)

    # 汉室中兴
    if authority >= 85 and prestige >= 80 and state.dong_zhuo_killed_turn > 0 and warlords <= 30:
        return {
            "status": "total_restoration",
            "summary": "汉室威权与声望鼎盛，董卓已除，藩镇归心，天下重归一统有望。",
        }

    # 献帝东归（完成）
    if state.emperor_safe_turn > 0 and authority >= 60:
        return {
            "status": "partition",
            "summary": "献帝已幸许昌，汉室法统存续，但三分天下格局已成。",
        }

    # 董卓伏诛（刚发生）
    if 0 < state.dong_zhuo_killed_turn <= state.turn:
        return {
            "status": "ongoing",
            "summary": "董卓伏诛，京畿初定，但李傕、郭汜余部尚在，天下未定。",
        }

    # 董卓伏诛（余波）
    if state.dong_zhuo_killed_turn > 0 and (state.turn - state.dong_zhuo_killed_turn) <= 6:
        return {
            "status": "ongoing",
            "summary": "董卓伏诛不久，余部未平，陛下当安抚西凉，招揽人才，重建朝纲。",
        }

    # 禅让
    abdication = state.metrics.get("禅让标志", 0)
    if abdication >= 100:
        return {
            "status": "abdication",
            "summary": "汉室气数已尽，曹丕或他人将逼迫禅让，兴复之望断绝。",
        }

    # 汉室覆灭
    if warlords >= 95 and authority <= 5:
        return {
            "status": "downfall",
            "summary": "藩镇割据彻底失控，威权荡然，汉室名存实亡。",
        }

    # 三分天下（僵局）
    if authority >= 40 and authority <= 60 and warlords >= 50:
        return {
            "status": "partition",
            "summary": f"三分天下格局已成：汉室威权{authority}、声望{prestige}、藩镇{warlords}，天下呈均势。",
        }

    return {
        "status": "ongoing",
        "summary": f"天下未定：威权{authority}、声望{prestige}、藩镇{warlords}、汉室库{treasury}万两。",
    }


# ── 地区/军队/人物匹配 ────────────────────────────────────────────────────

from han_sim.matching import army_aliases, compact_name, region_aliases  # noqa: E402,F401
from han_sim.matching import match_army_id_from_text as _match_army
from han_sim.matching import match_region_id_from_text as _match_region
from han_sim.matching import match_character_from_text as _match_character


def match_region_id_from_text(text: str) -> Optional[str]:
    return _match_region(text, _ctx().regions)


def match_army_id_from_text(text: str) -> Optional[str]:
    return _match_army(text, _ctx().armies)


def match_character_from_text(text: str, current: Optional[Dict] = None) -> Optional[Dict]:
    return _match_character(text, _ctx().characters, current)


# ── 状态上下文 ─────────────────────────────────────────────────────────────

def state_context(state: "GameState") -> str:
    """生成给 LLM 的状态摘要字符串。"""
    parts = []
    for key, value in state.metrics.items():
        if key in ("汉室库", "内库"):
            parts.append(f"{key}{format_money(value)}")
        else:
            parts.append(f"{key}{value}")
    return "，".join(parts)


# ── JSON 解析 ──────────────────────────────────────────────────────────────

def parse_json_dict(raw: str) -> Dict[str, int]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise LLMContractError(f"数据库中的数值变化 JSON 已损坏：{raw[:200]}") from error
    if not isinstance(data, dict):
        raise LLMContractError(f"数据库中的数值变化不是 object：{raw[:200]}")
    parsed: Dict[str, int] = {}
    for key, value in data.items():
        try:
            parsed[str(key)] = int(value)
        except (TypeError, ValueError) as error:
            raise LLMContractError(f"数据库中的数值变化字段不是整数：{key}={value}") from error
    return parsed


def format_metric_delta(delta: Dict[str, int]) -> str:
    """格式化数值变化（用于回合末报告）。"""
    if not delta:
        return "核心数值无明显变化。"
    parts = []
    for key, value in delta.items():
        if key in ("汉室库", "内库"):
            parts.append(f"{key}{format_money_delta(value)}")
        else:
            sign = "+" if value > 0 else ""
            parts.append(f"{key}{sign}{value}")
    return "数值变化：" + "；".join(parts) + "。"


# ── 人物/事件上下文 ───────────────────────────────────────────────────────

def character_context(character: Dict) -> str:
    """生成人物的完整描述字符串。"""
    return (
        f"{character.get('name', '未知')}，{character.get('office', '无官')}，"
        f"职位类型：{character.get('office_type', 'unknown')}，派系：{character.get('faction', '无')}，"
        f"别名：{', '.join(character.get('aliases', [])) or '无'}，"
        f"人物标签：{', '.join(character.get('personal_skills', []))}，"
        f"忠诚{character.get('loyalty', 0)}，能力{character.get('ability', 0)}，"
        f"清廉{character.get('integrity', 0)}，胆略{character.get('courage', 0)}，"
        f"风格：{character.get('style', '未知')}"
    )


def event_context(event: Dict) -> str:
    """生成事件的完整描述字符串。"""
    return (
        f"{event.get('title', '未知')}。类型：{event.get('kind', 'unknown')}。"
        f"奏报：{event.get('summary', '')} "
        f"紧急{event.get('urgency', 0)}，严重{event.get('severity', 0)}，可信{event.get('credibility', 0)}。 "
        f"牵涉利益：{', '.join(event.get('interests', []))}。"
    )


# ── 快捷工具 ──────────────────────────────────────────────────────────────

def first_character() -> Dict:
    try:
        return next(iter(_ctx().characters.values()))
    except StopIteration as error:
        raise SystemExit("characters.json 至少需要一个人物。") from error


def first_character_name() -> str:
    return first_character().get("name", "")


def character_from_name(name: object) -> Dict:
    value = str(name or "")
    character = _ctx().characters.get(value)
    if character is None:
        raise LLMContractError(f"人物未建档：{value}")
    return character


def region_from_id(region_id: str) -> Optional[Dict]:
    return _ctx().regions.get(region_id)


def army_from_id(army_id: str) -> Optional[Dict]:
    return _ctx().armies.get(army_id)


def power_from_id(power_id: str) -> Optional[Dict]:
    return _ctx().powers.get(power_id)