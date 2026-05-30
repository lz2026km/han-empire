"""诏书系统：拟旨 → LLM生成 → 效果结算。L6。

天子回合的 issued 阶段使用：
  decree.py 负责"天子拟旨"这一核心行动。

核心流程：
  1. 拟定诏书意图（intent + 可选大臣意见）
  2. 调用 LLM 将意图扩展为完整诏书文本
  3. 根据诏书类型执行数值效果结算
  4. 将诏书记录写入 db

L6 升级：
  - parse_decree_intent() 支持自然语言意图理解
  - 诏书模板库扩充，每种意图 3-5 种风格变体
  - 融入历史典故，增加沉浸感
  - 保持向后兼容（下拉菜单方式仍可用）
"""



import json
import os
import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from agno.agent import Agent

from han_sim.db import GameDB
from han_sim.llm_config import load_llm_config
from han_sim.llm_model import create_chat_model, extract_agent_text
from han_sim.models import GameState, LLMConfig


# ── 诏书类型 ────────────────────────────────────────────────────────────────

@dataclass
class DecreeEffect:
    metric: str
    delta: int
    description: str


# ── 历史典故库 ────────────────────────────────────────────────────────────

HISTORICAL_REFERENCES = {
    # 先秦圣王典范
    "尧舜": "夫唐虞之世，禅让垂拱，天下为公。朕虽不德，尚思追步前圣。",
    "大禹": "昔大禹治水，三过家门而不入，以身殉职，今朕不敢安逸。",
    "周公": "周公吐哺，天下归心。朕思辅臣之谊，期于再睹成康之治。",
    "文武": "文王、武王以仁德取天下，朕虽中材，愿法文武之遗风。",

    # 汉室先帝典范
    "高祖": "高祖提三尺剑以定天下，创业维艰，朕敢忘荥阳之困？",
    "文帝": "孝文皇帝躬行节俭，政从宽简，海内富殷。朕用是知所勉。",
    "景帝": "孝景皇帝削藩定难，七国之乱遂平，朕心往之。",
    "武皇": "孝武皇帝北击匈奴，南通西域，华夏声威于斯为盛。",
    "宣帝": "孝宣皇帝励精为治，功光祖宗，业垂后裔。",
    "光武": "世祖光武皇帝起兵复兴，拨乱反正，天下重新。",

    # 忠臣义士典故
    "苌弘": "苌弘化碧，忠贞不回，朕重其节。",
    "苏武": "苏武牧羊，十九年而不改其志，朕感其忠。",
    "张骞": "张骞凿空，辟我丝路，朕用是知开拓之义。",
    "终军": "终军请缨，志在万里，朕嘉其勇。",
    "霍光": "霍光受托辅政，社稷之臣也。",
    "丙吉": "丙吉问牛，不忽寒微，宽仁之相也。",
    "魏相": "魏相好犯上之臣，正色立朝，朕用是知法度之重。",

    # 权臣祸国典故
    "王莽": "王莽篡汉，托古改制，海内鼎沸，此朕所深戒。",
    "梁冀": "梁冀专权，二十余年，天下侧目。",
    "窦宪": "窦宪怙宠，坐交通藩属，卒以诛灭。",
    "董卓": "董卓贼臣，废旧立新，焚烧宫阙，流毒四海。",
    "十常侍": "十常侍乱政，卖官鬻爵，汉室之疾也。",

    # 灾异与警惧
    "日食": "近日有日食之异，天象示警，朕甚惧焉。",
    "蝗灾": "蝗虫蔽天，赤地千里，朕心惄然。",
    "洪水": "洪水横流，没溺生民，朕夙夜忧惧。",
    "瘟疫": "瘟疫盛行，生民倒悬，朕何敢安。",

    # 经典引述
    "尚书": "《书》曰：「天命有德，五服五章哉。」",
    "诗经": "《诗》云：「普天之下，莫非王土；率土之滨，莫非王臣。」",
    "春秋": "《春秋》之法，责贤者详，朕敢不自律。",
    "论语": "《论语》云：「其身正，不令而行。」朕当自正。",
}


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


# ── 诏书模板库（多风格变体） ────────────────────────────────────────────
# 每种 intent 有 3-5 个风格变体，包含风格标识和历史典故标记

DECREE_TEMPLATES: Dict[str, List[Dict]] = {
    "赈济灾民": [
        {
            "style": "凝重勤政",
            "template": "朕为一体，痛百姓之所痛。今闻{region}遭逢{disaster}，生民倒悬，朕心惄然。{historical_ref}今特颁此诏，着有司开仓赈济，免赋一年，务使天下苍生各安其业。布告天下，咸使闻知。",
            "effects": [("汉室库", -20), ("声望", +10)],
            "references": ["文帝", "诗经"],
        },
        {
            "style": "引咎罪己",
            "template": "天变屡现，{disaster}频仍，此皆朕一人之过也。{historical_ref}朕当深自刻责，减膳撤乐，以谢天下。今令州郡开仓仓赈济，蠲免租赋，务使百姓不失其所。布告天下，咸使闻知。",
            "effects": [("汉室库", -25), ("声望", +12)],
            "references": ["日食", "尚书"],
        },
        {
            "style": "仿古舜禹",
            "template": "朕为天子，当法尧舜之圣，忧民之忧。{historical_ref}今{region}灾荒，朕夙夜忧惧，思所以振救之策。着开常平仓，开仓赈民，免今年田租，务使天下生民各有依归。布告天下，咸使闻知。",
            "effects": [("汉室库", -20), ("声望", +8)],
            "references": ["尧舜", "大禹"],
        },
        {
            "style": "宽仁期许",
            "template": "天下之民，皆朕赤子。朕闻{region}有{disaster}之灾，心如刀割。{historical_ref}今特降罪己之诏，蠲租免税，开仓赈济，务使百姓得免于饥馑。朕以待天心，期于转祸为福。布告天下，咸使闻知。",
            "effects": [("汉室库", -18), ("声望", +10)],
            "references": ["文帝", "诗经", "尚书"],
        },
    ],
    "犒赏三军": [
        {
            "style": "慷慨激昂",
            "template": "朕以凉薄，遭时多难，仰赖三军用命，朝廷始得粗安。{historical_ref}今特颁此诏，犒赏三军，赐钱赐帛，以酬其勋。尔将校士卒，当感恩图报，务期扫除贼寇，还我河山。布告天下，咸使闻知。",
            "effects": [("汉室库", -30), ("声望", +5)],
            "references": ["高祖", "武皇"],
        },
        {
            "style": "庄重威仪",
            "template": "《春秋》之义，师以义动。朕嘉诸军忠勇，{historical_ref}今特颁犒赏之诏，赐钱三千万，绢布各万匹，犒赏三军。各将校当勉力报国，勿负朕意。布告天下，咸使闻知。",
            "effects": [("汉室库", -30), ("声望", +6)],
            "references": ["春秋", "高祖"],
        },
        {
            "style": "忆祖激励",
            "template": "高祖提三尺剑而定天下，今日朕亦赖诸军之用命。{historical_ref}今颁犒赏之诏，赐钱赐帛，务使三军饱暖。各将校当法高祖创业之艰，思今日之不易，勉力报国。布告天下，咸使闻知。",
            "effects": [("汉室库", -35), ("声望", +5)],
            "references": ["高祖", "武皇"],
        },
    ],
    "颁布新政": [
        {
            "style": "宏图远略",
            "template": "朕承汉室之业，思有以振之。{historical_ref}今颁新政之诏，改革吏治，整顿法度，务使朝廷清明，百官奉职，百姓乐业。朕以天下为公，思与天下共此太平。布告天下，咸使闻知。",
            "effects": [("声望", +15), ("威权", +5)],
            "references": ["宣帝", "论语"],
        },
        {
            "style": "正本清源",
            "template": "汉室中衰，政教不明，朕甚忧之。{historical_ref}今颁此诏，改革弊政，选用贤才，务使朝廷振作。朕当法宣帝之志，中兴汉室。布告天下，咸使闻知。",
            "effects": [("声望", +12), ("威权", +8)],
            "references": ["宣帝", "光武"],
        },
        {
            "style": "托古改制",
            "template": "夫天下之事，因时制宜。朕欲法古圣王之治，{historical_ref}今颁新政，改革吏治，选用贤能，以期刷新政治，中兴汉室。布告天下，咸使闻知。",
            "effects": [("声望", +10), ("威权", +6)],
            "references": ["王莽", "宣帝", "论语"],
        },
    ],
    "招降叛将": [
        {
            "style": "仁义怀柔",
            "template": "朕闻忠臣事君，义士事国，叛逆之徒，朕亦欲其归正。{historical_ref}今特颁此诏，凡有背离朝廷者，若能反正，朕皆宽宥之，予以自新。务使天下知朕仁义之心，不弃一人。布告天下，咸使闻知。",
            "effects": [("威权", +10), ("声望", +5)],
            "references": ["苏武", "文帝"],
        },
        {
            "style": "威德并施",
            "template": "今之藩镇，或有怙恶不悛者，朕思以威德并使之归化。{historical_ref}凡愿反正者，朕皆录其功，予以官爵，务使天下知朕赏罚分明。布告天下，咸使闻知。",
            "effects": [("威权", +8), ("声望", +6)],
            "references": ["宣帝", "光武"],
        },
        {
            "style": "圣王感化",
            "template": "夫唐虞之世，蛮夷率服，朕虽不德，窃慕其风。{historical_ref}今颁招降之诏，凡愿归正者，朕皆待以宽仁，务使天下知朕无弃人之心。布告天下，咸使闻知。",
            "effects": [("威权", +6), ("声望", +8)],
            "references": ["尧舜", "苏武"],
        },
    ],
    "清剿黄巾": [
        {
            "style": "雷霆万钧",
            "template": "黄巾贼众，扰乱天下，生民涂炭，朕甚痛之。{historical_ref}今颁讨贼之诏，大将军督各镇进兵，务期扫除贼寇，安定天下。朕不惜重赏，以酬有功。布告天下，咸使闻知。",
            "effects": [("声望", +10), ("威权", +5)],
            "references": ["武皇", "高祖"],
        },
        {
            "style": "安民除害",
            "template": "贼寇不除，天下不安。朕今颁此诏，{historical_ref}命有司进兵讨贼，务使百姓复安其业。凡斩贼有功者，朕不吝重赏。布告天下，咸使闻知。",
            "effects": [("声望", +8), ("威权", +6)],
            "references": ["武皇", "景帝"],
        },
        {
            "style": "吊民伐罪",
            "template": "今黄巾倡乱，生灵涂炭，朕吊民伐罪，不得不已。{historical_ref}各镇进兵讨贼，务使天下复见太平。布告天下，咸使闻知。",
            "effects": [("声望", +10), ("威权", +4)],
            "references": ["武皇", "尚书"],
        },
    ],
    "迁都": [
        {
            "style": "暂避锋芒",
            "template": "今京师变乱，不得不避其锋。{historical_ref}朕今决意迁都，以图后举。百官疲于奔命，朕亦知之，然此乃不得已之计，务使天下知朕暂避之由。布告天下，咸使闻知。",
            "effects": [("威权", -20), ("声望", -10)],
            "references": ["高祖"],
        },
        {
            "style": "东归图存",
            "template": "朕思祖宗之地，光武皇帝中兴之业，朕不敢忘。{historical_ref}今决意东归，迁都于东都，以图恢复。天下望天子归正朔，朕当勉力为之。布告天下，咸使闻知。",
            "effects": [("威权", -15), ("声望", -8)],
            "references": ["光武", "高祖"],
        },
        {
            "style": "审时度势",
            "template": "夫天下之势，审时度势，不可执一。{historical_ref}今京师不可居，朕决意迁都，以待天下之变。布告天下，咸使闻知。",
            "effects": [("威权", -18), ("声望", -10)],
            "references": ["光武"],
        },
    ],
    "征召人才": [
        {
            "style": "求贤若渴",
            "template": "朕闻贤才为国家之本，{historical_ref}今特颁求贤之诏，凡有才能者，皆可自荐或被荐，朕当破格擢用。务使天下知朕求贤之诚。布告天下，咸使闻知。",
            "effects": [("声望", +8), ("威权", +3)],
            "references": ["武帝", "诗经"],
        },
        {
            "style": "终军请缨",
            "template": "昔终军请缨，志在万里，朕嘉其勇。{historical_ref}今特颁此诏，征召天下贤才，凡有文武之才者，皆可应召。朕当择其优者，予以重任。布告天下，咸使闻知。",
            "effects": [("声望", +10), ("威权", +4)],
            "references": ["终军", "张骞"],
        },
        {
            "style": "复兴汉室",
            "template": "汉室中衰，人才凋零，朕甚忧之。{historical_ref}今颁求贤诏，征召天下英俊，务使朝廷新血注入，中兴汉室。布告天下，咸使闻知。",
            "effects": [("声望", +8), ("威权", +5)],
            "references": ["光武", "宣帝"],
        },
    ],
    "废除苛政": [
        {
            "style": "仁慈爱民",
            "template": "朕闻苛政害民，今欲废除之。{historical_ref}今特颁此诏，废除一切扰民之政，务使百姓得以休息。朕以天下为重，思与天下共享太平。布告天下，咸使闻知。",
            "effects": [("声望", +12), ("威权", -5)],
            "references": ["文帝", "诗经"],
        },
        {
            "style": "痛改前非",
            "template": "前此之政，或有不便于民者，朕甚悔之。{historical_ref}今颁此诏，痛改前非，废除苛政，务使天下百姓各安其业。朕当以此为戒，思所以利民之事。布告天下，咸使闻知。",
            "effects": [("声望", +10), ("威权", -3)],
            "references": ["文帝", "尚书"],
        },
        {
            "style": "正本清源",
            "template": "夫政者，正也。朕今欲正本清源，{historical_ref}废除一切扰民之政，务使朝廷清明，百姓乐业。布告天下，咸使闻知。",
            "effects": [("声望", +8), ("威权", -4)],
            "references": ["宣帝", "论语"],
        },
    ],
    "与藩镇会盟": [
        {
            "style": "怀柔制衡",
            "template": "今藩镇各据一方，朕思以怀柔制衡之策。{historical_ref}今颁会盟之诏，召各镇会盟，共辅汉室，务使天下暂安。布告天下，咸使闻知。",
            "effects": [("威权", +8), ("藩镇", -5)],
            "references": ["光武", "周公"],
        },
        {
            "style": "会盟稳定",
            "template": "朕思会盟之策，可以暂安天下。{historical_ref}今召各镇会盟，共商国事，务使天下知朕以德治国之志。布告天下，咸使闻知。",
            "effects": [("威权", +6), ("藩镇", -3)],
            "references": ["周公", "光武"],
        },
        {
            "style": "效法周公",
            "template": "昔周公会盟，安定周室，朕窃慕之。{historical_ref}今颁会盟之诏，召各镇会盟，共辅汉室，务使天下知朕以德治国之志。布告天下，咸使闻知。",
            "effects": [("威权", +10), ("藩镇", -6)],
            "references": ["周公", "诗经"],
        },
    ],
    "讨伐董卓": [
        {
            "style": "慷慨誓师",
            "template": "董卓贼臣，废旧立新，焚烧宫阙，流毒四海，天人共愤。{historical_ref}今朕以大义讨贼，告于天地祖宗，誓必诛灭此獠，以谢天下。布告天下，咸使闻知。",
            "effects": [("威权", +15), ("声望", +10), ("藩镇", -10)],
            "references": ["武皇", "高祖", "尚书"],
        },
        {
            "style": "吊民伐罪",
            "template": "董卓悖逆，人神共愤。朕今吊民伐罪，{historical_ref}大举讨贼，务使天下复见太平。凡斩贼立功者，朕不吝重赏。布告天下，咸使闻知。",
            "effects": [("威权", +12), ("声望", +10), ("藩镇", -8)],
            "references": ["武皇", "尚书"],
        },
        {
            "style": "激励忠义",
            "template": "今董卓肆逆，社稷危在旦夕。{historical_ref}朕特颁此诏，号召天下忠义之士，共讨贼臣，务使汉室复兴。凡有功者，朕当铭记不忘。布告天下，咸使闻知。",
            "effects": [("威权", +10), ("声望", +12), ("藩镇", -10)],
            "references": ["高祖", "苏武", "终军"],
        },
        {
            "style": "春秋大义",
            "template": "《春秋》之法，乱臣贼子必得诛讨。今董卓悖逆，{historical_ref}朕今大举讨伐，告于天地，誓必灭此国贼。布告天下，咸使闻知。",
            "effects": [("威权", +15), ("声望", +8), ("藩镇", -10)],
            "references": ["春秋", "武皇", "高祖"],
        },
        {
            "style": "中兴汉室",
            "template": "光武皇帝中兴汉室，朕虽不德，窃慕其志。{historical_ref}今董卓乱政，朕当法光武故事，大举讨贼，中兴汉室。布告天下，咸使闻知。",
            "effects": [("威权", +12), ("声望", +10), ("藩镇", -8)],
            "references": ["光武", "武皇", "高祖"],
        },
    ],
    "衣带密诏": [
        {
            "style": "肃穆机密",
            "template": "朕以微躯，遭时多难，贼臣窃柄，社稷将倾。{historical_ref}今密使此诏，交于忠义之臣，共图除贼大事。事成之后，朕当裂土封侯，以酬殊勋。此诏秘密，不得外泄。",
            "effects": [("威权", +8), ("威权", -5), ("声望", +3)],
            "references": ["霍光", "苏武", "苌弘"],
        },
        {
            "style": "临危托孤",
            "template": "今贼臣横逆，朕欲托孤于忠义之臣。{historical_ref}卿等受朕衣带密诏，当暗图除贼，务使社稷复兴。朕已备后事，若事不成，卿等当善自为计。",
            "effects": [("威权", +10), ("威权", -5), ("声望", +3)],
            "references": ["霍光", "苌弘"],
        },
        {
            "style": "忠义感召",
            "template": "朕以社稷为重，密使此诏于忠义之臣。{historical_ref}卿等当体朕之心，暗中联结，共除贼臣。事成之日，朕当厚报。布告天下，咸使闻知。",
            "effects": [("威权", +8), ("威权", -3), ("声望", +5)],
            "references": ["苏武", "终军", "苌弘"],
        },
        {
            "style": "泣血密诏",
            "template": "朕泣血书此诏，付于忠义之臣。{historical_ref}今贼臣当朝，社稷将亡，朕与卿等共约，务必除此大贼。事成则社稷安，不成则朕与卿等共赴国难。",
            "effects": [("威权", +6), ("威权", -5), ("声望", +3)],
            "references": ["苌弘", "苏武"],
        },
    ],
    "东归诏": [
        {
            "style": "东归复国",
            "template": "朕思祖宗之地，光武皇帝中兴之业，不敢忘也。{historical_ref}今决意东归，迁都东都，以图恢复汉室。天下望天子归正朔，朕当勉力为之。布告天下，咸使闻知。",
            "effects": [("威权", +5), ("声望", +5)],
            "references": ["光武", "高祖"],
        },
        {
            "style": "思归故土",
            "template": "朕本以洛阳为都，今东都光武之业，朕心往之。{historical_ref}今颁东归之诏，迁都东都，务使天下知朕恢复之志。布告天下，咸使闻知。",
            "effects": [("威权", +6), ("声望", +4)],
            "references": ["光武", "诗经"],
        },
        {
            "style": "重兴汉业",
            "template": "光武皇帝起兵复兴，拨乱反正，天下重新。{historical_ref}朕虽不德，窃慕光武之志，今决意东归，务使汉室复兴。布告天下，咸使闻知。",
            "effects": [("威权", +5), ("声望", +6)],
            "references": ["光武", "宣帝"],
        },
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

DECREE_TYPE_LABELS = {
    "secret_edict": "衣带密诏",
    "moving_edict": "迁都诏书",
    "campaign_edict": "讨伐董卓",
    "east_return_edict": "献帝东归",
}


# ── 意图类型关键词映射 ──────────────────────────────────────────────────
# 用于从自然语言中快速识别意图类型

INTENT_KEYWORDS: Dict[str, List[str]] = {
    "赈济灾民": ["赈灾", "赈济", "救济灾民", "开仓", "放粮", "免赋", "蠲免"],
    "犒赏三军": ["犒赏", "赏军", "三军", "赏赐", "军饷"],
    "颁布新政": ["新政", "改革", "变法", "维新", "新法"],
    "招降叛将": ["招降", "招抚", "招安", "纳降"],
    "清剿黄巾": ["剿贼", "清剿", "讨贼", "剿匪", "平贼"],
    "迁都": ["迁都", "迁都洛阳", "迁都长安", "迁都许昌", "移都"],
    "征召人才": ["求贤", "征召", "招贤", "人才", "贤才"],
    "废除苛政": ["废除", "免苛", "蠲免", "除苛", "减赋"],
    "与藩镇会盟": ["会盟", "结盟", "安抚", "藩镇"],
    "讨伐董卓": ["讨伐", "讨贼", "伐董", "诛董", "讨逆", "伐卓"],
    "衣带密诏": ["衣带诏", "密诏", "密旨", "密召", "暗中", "秘密"],
    "东归诏": ["东归", "东都", "归正朔", "回东", "归洛阳"],
}


@dataclass
class Decree:
    intent: str           # 诏书意图（用户输入）
    full_text: str        # LLM 生成的完整诏书文本
    decree_type: str      # 诏书类型
    effects: List[Dict]   # 效果列表
    cost: int             # 耗费（万两）
    narrative: str        # 推行后的叙事
    style: str = ""       # 诏书风格（新增）
    historical_refs: List[str] = field(default_factory=list)  # 历史典故（新增）


@dataclass
class DecreeResult:
    decree: Decree
    metrics_delta: Dict[str, int]
    log_entries: List[str]


# ── 意图解析 Prompt ──────────────────────────────────────────────────────

INTENT_EXTRACTION_PROMPT = """你是一位精通东汉末历史的宫廷谋士，奉天子之命分析诏书意图。

用户（天子）的输入可能是：
- 自然语言描述（如："朕欲令天下诸侯进贡粮草，该如何拟旨？"）
- 简短关键词（如："赈济灾民"、"讨伐董卓"）
- 混合形式

请提取结构化意图，返回 JSON 格式：

{
  "type": "诏书意图类型",
  "content": "具体内容描述（50字以内）",
  "decree_type": "诏书类型（normal_edict/secret_edict/moving_edict/campaign_edict/east_return_edict）",
  "target": "对象（如：天下/某藩镇/某臣）",
  "urgency": "紧急程度（high/normal/low）",
  "secrecy": "是否秘密（secret/normal）",
  "keywords": ["可作为检索关键词的词"],
  "fillers": {
    "region": "地区（如有）",
    "disaster": "灾异类型（如有）",
    "target_name": "对象名称（如有）"
  }
}

诏书类型映射：
- normal_edict：普通诏书（日常政令、赈灾、犒赏、征召人才、废除苛政等）
- secret_edict：衣带密诏（秘密行动，需要威权≥30）
- moving_edict：迁都诏书
- campaign_edict：讨伐诏书（军事行动，如讨伐董卓、清剿黄巾）
- east_return_edict：东归诏书

意图类型参考（type 字段值）：
- 赈济灾民、犒赏三军、颁布新政、招降叛将、清剿黄巾、迁都、征召人才、废除苛政、与藩镇会盟、讨伐董卓、衣带密诏、东归诏

注意：
1. 如果用户输入是简单关键词（如"赈济灾民"），直接推断 type，不要强行改写
2. content 应该概括诏书核心内容
3. 返回纯 JSON，不要解释
"""


def _parse_natural_language_intent(user_input: str, llm_cfg: Optional[LLMConfig] = None) -> Dict:
    """调用 LLM 从自然语言中提取结构化意图。失败时返回默认推断。"""
    if llm_cfg is None:
        import os as _os
        _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
        if not _api_key:
            return _infer_intent_fallback(user_input)
        llm_cfg = load_llm_config(
            base_url="https://api.minimaxi.com/v1",
            model="MiniMax-M2.5",
            api_key=_api_key,
            timeout_seconds=60.0,
        )

    try:
        agent = Agent(
            name="意图解析",
            model=create_chat_model(llm_cfg, temperature=0.3, max_tokens=600),
            instructions=[INTENT_EXTRACTION_PROMPT],
            markdown=False,
        )
        text = extract_agent_text(agent.run(user_input))
        parsed = _extract_json(text)
        if parsed and "type" in parsed:
            return parsed
    except Exception:
        pass

    return _infer_intent_fallback(user_input)


def _infer_intent_fallback(user_input: str) -> Dict:
    """无 LLM 时基于关键词规则推断意图（兼容旧下拉菜单方式）。"""
    text = user_input.strip()

    # 首先检查是否是已知意图关键词（精确匹配，支持部分匹配）
    for intent_type, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text or text in kw:
                return {
                    "type": intent_type,
                    "content": text,
                    "decree_type": _get_decree_type_by_intent(intent_type),
                    "target": "天下",
                    "urgency": "normal",
                    "secrecy": "normal",
                    "keywords": [kw],
                    "fillers": {},
                }

    # 默认普通诏书
    return {
        "type": "颁布新政",
        "content": text,
        "decree_type": "normal_edict",
        "target": "天下",
        "urgency": "normal",
        "secrecy": "normal",
        "keywords": [],
        "fillers": {},
    }


def _get_decree_type_by_intent(intent_type: str) -> str:
    """将意图类型映射为诏书类型枚举。"""
    mapping = {
        "衣带密诏": "secret_edict",
        "迁都": "moving_edict",
        "讨伐董卓": "campaign_edict",
        "东归诏": "east_return_edict",
    }
    return mapping.get(intent_type, "normal_edict")


def _get_intent_type_by_keywords(text: str) -> str:
    """从文本中匹配意图类型关键词。"""
    for intent_type, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return intent_type
    return "颁布新政"  # 默认


def parse_decree_intent(user_input: str, llm_client=None) -> Dict:
    """将自然语言转换为诏书意图（L6 新增核心函数）。

    参数：
        user_input: 玩家自由文本（如"朕欲令天下诸侯进贡粮草，该如何拟旨？"）
                   或下拉菜单值（如"赈济灾民"，向后兼容）
        llm_client: 可选，传入已配置的 LLMConfig 实例以加速

    返回：
        {
            "type": str,          # 意图类型（诏书效果模板的 key）
            "target": str,        # 诏书对象
            "content": str,       # 意图内容描述
            "decree_type": str,   # 诏书类型枚举
            "style": str,         # 选中的诏书风格（供模板填充用）
            "historical_refs": list,  # 选用典故列表
            "urgency": str,       # 紧急程度
            "secrecy": str,       # 是否秘密
            "fillers": dict,      # 模板填充字段（region/disaster/target_name）
        }

    示例：
        >>> parse_decree_intent("朕欲令天下诸侯进贡粮草，该如何拟旨？")
        {
            "type": "犒赏三军",
            "target": "天下诸侯",
            "content": "令天下诸侯进贡粮草",
            "decree_type": "normal_edict",
            "style": "慷慨激昂",
            "historical_refs": ["高祖", "武皇"],
            "urgency": "normal",
            "secrecy": "normal",
            "fillers": {},
        }
    """
    # 1. 尝试 LLM 解析自然语言
    parsed = _parse_natural_language_intent(user_input)

    # 2. 兼容旧的下拉菜单方式（精确匹配已知意图关键词）
    for intent_type, keywords in INTENT_KEYWORDS.items():
        if user_input.strip() in keywords or user_input.strip() == intent_type:
            decree_type = _get_decree_type_by_intent(intent_type)
            parsed = {
                "type": intent_type,
                "content": user_input.strip(),
                "decree_type": decree_type,
                "target": "天下",
                "urgency": "normal",
                "secrecy": "secret_edict" if decree_type == "secret_edict" else "normal",
                "keywords": [],
                "fillers": {},
            }
            break

    # 3. 选择诏书风格（3-5 种变体中随机选一个）
    intent_type = parsed.get("type", "颁布新政")
    templates = DECREE_TEMPLATES.get(intent_type, [])
    if templates:
        chosen = random.choice(templates)
        parsed["style"] = chosen.get("style", "")
        parsed["historical_refs"] = chosen.get("references", [])
    else:
        parsed["style"] = "常规"
        parsed["historical_refs"] = []

    return parsed


def _select_template(intent_type: str, style: str = "") -> Optional[Dict]:
    """根据意图类型和风格选择诏书模板。"""
    templates = DECREE_TEMPLATES.get(intent_type, [])
    if not templates:
        return None

    if style:
        for t in templates:
            if t.get("style") == style:
                return t

    # 随机选一个
    return random.choice(templates)


def _build_decree_text_from_template(intent_type: str, parsed: Dict, state: GameState) -> str:
    """使用模板生成诏书文本（不调用 LLM 的快速路径）。"""
    template_info = _select_template(intent_type, parsed.get("style", ""))
    if template_info is None:
        return _generate_decree_text_fallback(intent_type, state)

    tmpl = template_info["template"]
    refs = parsed.get("historical_refs", []) or template_info.get("references", [])
    fillers = parsed.get("fillers", {})

    # 填充典故
    historical_ref = ""
    if refs:
        chosen_refs = random.sample(refs, min(len(refs), 2))
        historical_ref = " ".join(HISTORICAL_REFERENCES.get(r, "") for r in chosen_refs)

    # 填充模板变量
    region = fillers.get("region", "天下各州")
    disaster = fillers.get("disaster", "灾荒")
    target_name = fillers.get("target_name", "天下")

    text = tmpl.format(
        region=region,
        disaster=disaster,
        target_name=target_name,
        historical_ref=historical_ref,
    )

    # 清理多余空白
    text = re.sub(r"\s+", " ", text)
    return text


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
    """应用诏书效果，返回 (delta_dict, log_entries)。

    派系修正：忠汉派大臣执行诏书效果×1.2，离心派×0.8。
    """
    # 获取当前派系影响力，用于计算修正系数
    from han_sim.flows import calc_faction_influence
    influences = calc_faction_influence(state, db)
    total_ministers = len(db.list_characters(status="active"))
    if total_ministers == 0:
        total_ministers = 1

    # 忠汉派大臣占比
    loyal_count = sum(1 for c in db.list_characters(status="active") if c.get("loyalty", 0) >= 70)
    离心_count = sum(1 for c in db.list_characters(status="active") if 10 <= c.get("loyalty", 0) < 40)

    # 忠汉派修正 1.2，离心派修正 0.8，叠加影响
    faction_mod = 1.0
    if loyal_count > 0:
        faction_mod *= 1.0 + 0.2 * (loyal_count / total_ministers)
    if 离心_count > 0:
        faction_mod *= 1.0 - 0.2 * (离心_count / total_ministers)

    delta: Dict[str, int] = {}
    logs: List[str] = []
    for e in effects:
        metric = e["metric"]
        d = int(e["delta"] * faction_mod)
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


def _get_llm_config() -> LLMConfig:
    """获取 LLM 配置（从环境变量读取 key，不打印）。"""
    api_key = os.environ.get("MINIMAX_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    if not api_key:
        raise RuntimeError("未配置 LLM API key（MINIMAX_API_KEY 或 OPENAI_API_KEY）")
    return load_llm_config(
        base_url="https://api.minimaxi.com/v1",
        model="MiniMax-M2.5",
        api_key=api_key,
        timeout_seconds=180.0,
    )


def _generate_decree_text(intent: str, decree_type: str, state: GameState) -> str:
    """调用 LLM 将意图扩展为完整诏书文本（含历史典故增强）。"""
    # 选择典故
    available_refs = list(HISTORICAL_REFERENCES.keys())
    chosen_refs = random.sample(available_refs, min(len(available_refs), 3))

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
        f"【可选历史典故】（选用其一或数个融入诏书正文）\n"
        + "\n".join(f"  ◆ {k}：{v}" for k, v in HISTORICAL_REFERENCES.items() if k in chosen_refs)
        + f"\n\n"
        f"请撰写一份完整的汉帝诏书，要求：\n"
        f"1. 以「奉天承运，皇帝诏曰」开头\n"
        f"2. 300-500字，文言风格，庄重威严\n"
        f"3. 自然融入 1-2 个上述历史典故（不拘泥原文）\n"
        f"4. 末尾以「布告天下，咸使闻知」收尾\n"
        f"5. 诏书内容须与【诏书意图】相符，体现天子忧心天下之心\n"
        f"6. 不要提及LLM或AI等字样\n"
        f"\n"
        f"直接输出诏书正文，不要解释。"
    )
    try:
        llm_cfg = _get_llm_config()
        agent = Agent(
            name="诏书起草",
            model=create_chat_model(llm_cfg, temperature=0.7, max_tokens=800),
            instructions=[prompt],
            markdown=False,
        )
        text = extract_agent_text(agent.run(prompt))
        return text.strip()
    except Exception:
        # LLM 失败时返回模板生成 fallback
        return _generate_decree_text_fallback(intent, state)


def _generate_decree_text_fallback(intent: str, state: GameState) -> str:
    """LLM 不可用时的模板化诏书文本生成。"""
    intent_type = _get_intent_type_by_keywords(intent)
    templates = DECREE_TEMPLATES.get(intent_type, [])
    if templates:
        chosen = random.choice(templates)
        tmpl = chosen["template"]
        refs = chosen.get("references", [])
        historical_ref = " ".join(HISTORICAL_REFERENCES.get(r, "") for r in refs[:2])
    else:
        tmpl = "朕以凉薄，遭时多难，{intent}，实乃当务之急。今下令天下，共襄盛举，咸使闻知。布告天下，咸使闻知。"
        historical_ref = ""
        refs = []

    text = tmpl.format(
        intent=intent,
        region="天下各州",
        disaster="灾荒",
        target_name="天下",
        historical_ref=historical_ref,
    )
    text = re.sub(r"\s+", " ", text)
    return text


def issue_decree(
    intent: str,
    state: GameState,
    db: GameDB,
    campaign_id: str = "",
    minister_advice: Optional[str] = None,
) -> DecreeResult:
    """执行"拟旨"行动：生成诏书并写入指令表（待批准/已发布）。

    L6 升级：支持自然语言 intent，自动选择模板并融入历史典故。
    旧的下拉菜单值（如"赈济灾民"）仍可直接传入，向后兼容。
    """
    # 解析意图（支持自然语言或旧式关键词）
    parsed = parse_decree_intent(intent)

    intent_type = parsed.get("type", "颁布新政")
    decree_type_name = intent_type  # 用于效果查找
    style = parsed.get("style", "")
    historical_refs = parsed.get("historical_refs", [])

    # 获取效果模板
    effects = DECREE_EFFECT_TEMPLATES.get(intent_type, [
        {"metric": "威权", "delta": +5, "description": "诏令已下"},
        {"metric": "声望", "delta": +3, "description": "天下闻风而动"},
    ])
    cost = sum(abs(e["delta"]) for e in effects if e["metric"] in ("汉室库", "内库"))

    # 耗费汉室库（如果不够则记为亏损，效果减半）
    if cost > 0:
        if state.metrics.get("汉室库", 0) >= cost:
            state.metrics["汉室库"] -= cost
        else:
            effects = [
                {**e, "delta": e["delta"] // 2}
                for e in effects
            ]

    # 生成诏书文本（优先模板，LLM 备用）
    full_text = _build_decree_text_from_template(intent_type, parsed, state)

    # 效果预计算（派系修正后，用于返回和记录）
    from han_sim.flows import calc_faction_influence
    influences = calc_faction_influence(state, db)
    total_ministers = len(db.list_characters(status="active")) or 1
    loyal_count = sum(1 for c in db.list_characters(status="active") if c.get("loyalty", 0) >= 70)
    离心_count = sum(1 for c in db.list_characters(status="active") if 10 <= c.get("loyalty", 0) < 40)
    faction_mod = 1.0
    if loyal_count > 0:
        faction_mod *= 1.0 + 0.2 * (loyal_count / total_ministers)
    if 离心_count > 0:
        faction_mod *= 1.0 - 0.2 * (离心_count / total_ministers)

    # 计算指标变化
    metrics_delta: Dict[str, int] = {}
    for e in effects:
        metric = e["metric"]
        d = int(e["delta"] * faction_mod)
        metrics_delta[metric] = metrics_delta.get(metric, 0) + d

    log_entries = [e["description"] for e in effects]

    decree = Decree(
        intent=intent,
        full_text=full_text,
        decree_type=decree_type_name,
        effects=effects,
        cost=cost,
        narrative="",
        style=style,
        historical_refs=historical_refs,
    )
    decree.narrative = (
        f"{state.year}年{state.period}月，天子颁布《{decree_type_name}》诏，"
        f"{'；'.join(log_entries[:2]) or '已布告天下'}。"
    )

    # 写入 directives 表（状态机：draft→issued→approved）
    if campaign_id:
        directive_id = db.create_directive(
            campaign_id=campaign_id,
            kind=decree_type_name,
            status="issued",
            content=full_text,
            issued_turn=state.turn,
            expires_turn=state.turn + 3,  # 3回合后过期
        )

    db.append_log(state.turn, "issued", f"拟旨：{effects[0]['description'] if effects else '诏令已下'}")
    db.commit()

    return DecreeResult(
        decree=decree,
        metrics_delta=metrics_delta,
        log_entries=log_entries,
    )