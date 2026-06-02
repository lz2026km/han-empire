# v2.0.0 Phase 4.3: 大臣对话可调用的 tool_call 工具集
# 兼容 agno_skills/decree-drafting 协议
# 主公原则: 召对 = LLM 自由对话 + 可调用 tool 行动
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def query_state_tool(state: Dict[str, Any]) -> str:
    """查询当前国家状态。

    Tool Call 描述：大臣在召对中想了解国势时调用。
    返回：精炼的国势摘要（汉风"尚书台"口吻）。
    """
    lines = [
        "【尚书台报】",
        f"  年份：建安{state.get('year', '?')}年",
        f"  国库：{state.get('metrics', {}).get('汉室库', 0)}万两",
        f"  威权：{state.get('metrics', {}).get('威权', 0)} / 100",
        f"  声望：{state.get('metrics', {}).get('声望', 0)} / 100",
        f"  藩镇：{state.get('metrics', {}).get('藩镇', 0)} / 100",
        f"  民心：{state.get('metrics', {}).get('民心', 0)} / 100",
        f"  兵力：{state.get('metrics', {}).get('兵力', 0)}万",
        f"  都城：{state.get('capital', '许昌')}",
    ]
    return "\n".join(lines)


def propose_decree_tool(draft: str) -> Dict[str, Any]:
    """拟旨入档：起草一份诏书草案。

    Tool Call 描述：天子明示采纳某方案时调用，生成"尚书台"草拟的诏书。
    参数：
      draft: 完整诏书文本（含"奉天承运皇帝诏曰"开头，"钦此"结尾）
    返回：
      {"status": "drafted", "text": draft, "review": "请陛下御览"}
    """
    # 校验格式
    if "诏曰" not in draft and "制曰" not in draft:
        draft = f"奉天承运皇帝诏曰：{draft}。钦此。"
    elif "钦此" not in draft:
        draft = f"{draft}钦此。"

    return {
        "status": "drafted",
        "text": draft,
        "review": "臣已拟旨入档，请陛下御览草案。",
        "warning": "此为草案，未经天子朱批不得颁行。",
    }


def estimate_resistance_tool(target: str) -> str:
    """估阻力：评估执行某事的反弹。

    Tool Call 描述：大臣想了解实施某政策的党争阻力时调用。
    参数：target - 政策/事项名（如"削藩"、"迁都"、"杀董卓"）
    返回：汉风"廷尉"估的阻力等级。
    """
    # v2.0.0 Phase 4.3: 简单规则表（Phase 4.5 升级 LLM 裁判）
    high_resistance = ["削藩", "废相", "清君侧", "诛宦", "废后", "迁都"]
    medium_resistance = ["加税", "征兵", "检田", "案验大臣"]
    if any(k in target for k in high_resistance):
        return f"【廷尉报】'{target}' 阻力极大：牵涉外戚/宦官/士族根本利益，若无绝对威权(≥80)恐激反。"
    if any(k in target for k in medium_resistance):
        return f"【廷尉报】'{target}' 中等阻力：需三公九卿半数以上连署方可行。"
    return f"【廷尉报】'{target}' 阻力轻微：按例行即可。"


def suggest_audience_tool(topic: str) -> str:
    """建议召对人选：就某事推荐应召见的大臣。

    Tool Call 描述：天子想就某事找人商量时调用。
    返回：汉风"侍中"建议（带人物性格匹配）。
    """
    advice = {
        "军事": "【侍中荐】当召骠骑将军、卫将军，辅以中郎将。",
        "财政": "【侍中荐】当召大司农，兼问少府。",
        "吏治": "【侍中荐】当召尚书令、侍御史。",
        "礼制": "【侍中荐】当召太常、光禄勋。",
        "刑狱": "【侍中荐】当召廷尉、御史中丞。",
        "外戚": "【侍中荐】当召太傅，密问中常侍。",
        "边患": "【侍中荐】当召护匈奴中郎将、度辽将军。",
    }
    for k, v in advice.items():
        if k in topic:
            return v
    return f"【侍中荐】'{topic}' 事体重大，当先问尚书台，再召相关九卿议之。"


# v2.0.0 Phase 4.3: 大臣 Agent 可用 tool 列表（注入到 Agent(tools=[...])）
MINISTER_TOOLS: List[Any] = [
    {
        "name": "query_state",
        "description": "查询当前国势（国库、威权、藩镇、民心、兵力、都城）。"
                       "大臣想了解当下盘面时调用。",
        "func": query_state_tool,
    },
    {
        "name": "propose_decree",
        "description": "拟旨入档。天子明示采纳、强命拟旨、下旨、写旨时调用。"
                       "调用时必须含完整诏书文本（含'奉天承运'和'钦此'）。"
                       "调用后回：'臣已拟旨入档，请陛下御览草案。'",
        "func": propose_decree_tool,
    },
    {
        "name": "estimate_resistance",
        "description": "估阻力。评估执行某政策/事项的党争反弹程度。"
                       "返回廷尉估的阻力等级（大/中/小）及原因。",
        "func": estimate_resistance_tool,
    },
    {
        "name": "suggest_audience",
        "description": "建议召对人选。提供某事推荐召见的官员（汉风侍中口吻）。",
        "func": suggest_audience_tool,
    },
]


def build_minister_session_id(campaign_id: str, minister_name: str) -> str:
    """构建稳定 session_id - 多轮对话依赖此键。"""
    return f"han-empire:minister:{campaign_id}:{minister_name}"


def build_audience_session_id(campaign_id: str, topic: str) -> str:
    """群臣廷议 session_id - 多大臣共同讨论。"""
    return f"han-empire:audience:{campaign_id}:{topic[:20]}"
