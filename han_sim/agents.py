"""LLM Agent 工厂与文本解析。L4。"""



import json
import re
from typing import Any, Dict, Optional

from agno.agent import Agent

from han_sim.llm_config import load_llm_config
from han_sim.llm_model import create_chat_model, extract_agent_text, verify_llm_available
from han_sim.models import GameState


def create_minister_agent(minister: Dict, state: GameState, memory_brief: str = "") -> Agent:
    """创建大臣对话 agent。memory_brief 会注入到 system prompt 末尾。"""
    llm_cfg = load_llm_config(
        base_url="https://api.minimax.chat/v1",
        model="MiniMax-M2.7-highspeed",
        api_key="",
    )
    verify_llm_available(llm_cfg)

    skills = ", ".join(minister.get("personal_skills", []))
    system_prompt = (
        "你是" + minister["name"] + "（" + minister["office"] + "）。\n\n"
        "人物档案：\n"
        "- 性格：" + minister["style"] + "\n"
        "- 能力：" + str(minister["ability"]) + " / 100\n"
        "- 忠诚：" + str(minister["loyalty"]) + " / 100\n"
        "- 简介：" + minister["summary"] + "\n"
        "- 特长：" + skills + "\n\n"
        "你是一个三国时期的历史人物，以符合你人物性格的方式与天子（汉献帝刘协）对话。\n"
        "天子此时被曹操控制在许昌，名为天子实为阶下囚。\n"
        "你要根据你的忠诚度和人物性格来决定如何回应天子。\n\n"
        "当前局势：\n"
        "- 年份：" + str(state.year) + "年\n"
        "- 汉室库：" + str(state.metrics.get("汉室库", 0)) + "万两\n"
        "- 声望：" + str(state.metrics.get("声望", 0)) + "\n"
        "- 威权：" + str(state.metrics.get("威权", 0)) + "\n"
        "- 藩镇：" + str(state.metrics.get("藩镇", 0)) + "\n\n"
    )
    if memory_brief:
        system_prompt += memory_brief + "\n\n"

    system_prompt += "请用符合你人物身份的方式回应天子。"

    return Agent(
        name="大臣-" + minister["name"],
        model=create_chat_model(llm_cfg, temperature=0.7),
        instructions=[system_prompt],
        markdown=True,
    )


def parse_agent_json(text: str, key: str) -> Optional[Any]:
    """从 agent 输出中提取 JSON。"""
    text = text.strip()
    # 尝试从 ```json ``` 块提取
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))[key]
        except Exception:
            pass
    # 尝试从 ``` ``` 块提取
    m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))[key]
        except Exception:
            pass
    # fallback: 整段
    try:
        return json.loads(text)[key]
    except Exception:
        return None


def run_agent_stream_text(agent: Agent, prompt: str):
    return agent.run(prompt)


def run_agent_text(agent: Agent, prompt: str) -> str:
    return extract_agent_text(agent.run(prompt))