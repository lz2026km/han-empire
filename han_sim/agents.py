"""LLM Agent 工厂与文本解析。L4。"""



import json
import re
from typing import Any, Callable, Dict, List, Optional

try:
    from agno.agent import Agent
except ImportError:
    Agent = None  # type: ignore

from han_sim.llm_config import load_llm_config
from han_sim.llm_model import create_chat_model, extract_agent_text, verify_llm_available
from han_sim.models import GameState


def _tlog(msg: str) -> None:
    """简单的日志输出"""
    import time
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def create_minister_agent(minister: Dict, state: GameState, memory_brief: str = "", loyalty_ctx: str = "") -> Agent:
    """创建大臣对话 agent。memory_brief 会注入到 system prompt 末尾。"""
    import os as _os
    _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
    llm_cfg = load_llm_config(
        base_url="https://api.minimaxi.com/v1",
        model="MiniMax-M2.5",
        api_key=_api_key,
        timeout_seconds=180.0,
    )
    if Agent is None:
        raise LLMUnavailable("agno未安装，无法创建大臣Agent")
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
        "【忠诚度说明】" + loyalty_ctx + "\n\n"
        "你是一个三国时期的历史人物，以符合你人物性格的方式与天子（汉献帝刘协）对话。\n"
        "天子此时被曹操控制在许昌，名为天子实为阶下囚。\n"
        "你要根据你的忠诚度和人物性格来决定如何回应天子。\n\n"
        "当前局势：\n"
        "- 年份：" + str(state.year) + "年\n"
        "- 汉室库：" + str(state.metrics.get("汉室库", 0)) + "万两\n"
        "- 声望：" + str(state.metrics.get("声望", 0)) + "\n"
        "- 威权：" + str(state.metrics.get("威权", 0)) + "\n"
        "- 藩镇：" + str(state.metrics.get("藩镇", 0)) + "\n"
        "- 都城：" + state.capital + "\n\n"
        "【威权影响】威权决定天子诏书效力：\n"
        "  威权≥80：诏书如山，大臣俯首听命\n"
        "  威权≥50：诏书有效，大臣谨慎遵从\n"
        "  威权≥20：诏书无力，大臣阳奉阴违\n"
        "  威权<20：天子的声音无人理会\n\n"
    )
    if memory_brief:
        system_prompt += memory_brief + "\n\n"

    system_prompt += "请用符合你人物身份的方式回应天子。"

    if Agent is None:
        raise LLMUnavailable("agno未安装，无法创建大臣Agent")
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


# ── 多策略 JSON 解析 ────────────────────────────────────────────────────────


def parse_agent_json_full(text: str) -> Optional[Dict]:
    """多策略 JSON 解析：
    - 策略0：剥离 ```json ... ``` 或 ``` ... ``` 代码块包裹（v1.13.1 修）
    - 策略1：原文直解
    - 策略2：截取最外层{...}
    - 策略3：净化控制字符
    - 策略4：首个合法平衡子串
    """
    import json as _json
    text = text.strip()
    # 策略0：剥离 ```json ... ``` 或 ``` ... ``` 代码块包裹
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        candidate = m.group(1).strip()
        try:
            return _json.loads(candidate)
        except Exception:
            pass  # 落入策略1
    # 策略1：原文直解
    try:
        return _json.loads(text)
    except Exception:
        pass
    # 策略2：截取{...}最外层
    m = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if m:
        try:
            return _json.loads(m.group(0))
        except Exception:
            pass
    # 策略3：净化控制字符
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    try:
        return _json.loads(cleaned)
    except Exception:
        pass
    # 策略4：首个合法平衡子串
    depth = 0
    start = None
    for i, c in enumerate(text):
        if c == '{':
            if depth == 0:
                start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return _json.loads(text[start:i+1])
                except Exception:
                    pass
    return None


def run_agent_stream_text(
    agent: Agent,
    prompt: str,
    on_thinking: Optional[Callable[[str], None]] = None,
    on_text: Optional[Callable[[str], None]] = None,
) -> str:
    """流式执行 Agent，带推理回调。"""
    pieces: List[str] = []
    reasoning_buf: List[str] = []
    try:
        stream = agent.run(prompt, stream=True, stream_events=True)
    except TypeError:
        # fallback：不支持流式
        text = extract_agent_text(agent.run(prompt))
        if on_text:
            on_text(text)
        return text

    for event in stream:
        ev_type = type(event).__name__
        # 工具调用
        if ev_type == "ToolCallStartedEvent":
            tool = getattr(event, "tool", None)
            tname = getattr(tool, "tool_name", "?") if tool else "?"
            _tlog(f"[工具] 调用 {tname}")
            if on_thinking:
                on_thinking(f"\n〔查阅 {tname}〕\n")
            continue
        # 思考内容
        rdelta = getattr(event, "reasoning_content", None)
        if isinstance(rdelta, str) and rdelta:
            reasoning_buf.append(rdelta)
            if on_thinking:
                on_thinking(rdelta)
        # 正文内容
        is_terminal = (
            (hasattr(event, "is_final") and getattr(event, "is_final", False))
            or ev_type in ("RunOutput", "RunCompletedEvent")
        )
        if is_terminal:
            continue
        delta = getattr(event, "content", None)
        if isinstance(delta, str) and delta:
            pieces.append(delta)
            if on_text:
                on_text(delta)

    if reasoning_buf and on_thinking:
        on_thinking("".join(reasoning_buf))

    return "".join(pieces).strip()


# ── Agent 工厂函数 ─────────────────────────────────────────────────────────


_CONTENT: Optional[Any] = None


def bind_content(content: Any) -> None:
    global _CONTENT
    _CONTENT = content


def _ctx():
    if _CONTENT is None:
        raise RuntimeError("agents.bind_content() 未调用")
    return _CONTENT


def create_season_simulator_agent(
    game_content: Any,
    state: Optional[GameState] = None,
    simulator_payload: Optional[Dict[str, Any]] = None,
) -> Agent:
    """月末推演官 Agent。"""
    import os as _os
    from han_sim.llm_config import load_llm_config
    _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
    cfg = load_llm_config(
        base_url="https://api.minimaxi.com/v1",
        model="MiniMax-M2.5",
        api_key=_api_key,
        timeout_seconds=180.0,
    )
    turn_header = ""
    if state is not None:
        turn_header = (
            f"【本回合年月】{state.year} 年 {state.period} 月（第 {state.turn} 回合）。\n"
        )
    simulator_context = (
        turn_header
        + "【本回合推演输入】\n"
        + json.dumps(simulator_payload or {}, ensure_ascii=False, sort_keys=False)
    )
    ctx = _ctx()
    return Agent(
        name="月末推演日讲官",
        id="season-simulator",
        session_id="season-simulator",
        model=create_chat_model(cfg, temperature=0.9, top_p=0.95, enable_thinking=True),
        instructions=[ctx.game_world_prompt if hasattr(ctx, "game_world_prompt") else "",
                      ctx.season_simulator_prompt if hasattr(ctx, "season_simulator_prompt") else "",
                      simulator_context],
        add_history_to_context=False,
        markdown=False,
    )


def create_score_extractor_agent(game_content: Any) -> Agent:
    """档房书办 Agent（打分提取）。"""
    import os as _os
    from han_sim.llm_config import load_llm_config
    _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
    cfg = load_llm_config(
        base_url="https://api.minimaxi.com/v1",
        model="MiniMax-M2.5",
        api_key=_api_key,
        timeout_seconds=120.0,
    )
    ctx = _ctx()
    return Agent(
        name="档房书办",
        id="score-extractor",
        session_id="score-extractor",
        model=create_chat_model(cfg, temperature=0.1, top_p=0.7, enable_thinking=False, force_json_output=True),
        instructions=[ctx.game_world_prompt if hasattr(ctx, "game_world_prompt") else "",
                      ctx.score_extractor_prompt if hasattr(ctx, "score_extractor_prompt") else ""],
        add_history_to_context=False,
        markdown=False,
    )


_MEMORY_RETRIEVAL_PROMPT = (
    "你是记忆检索助手。从给定文本（诏书、对话、奏报均可）中提取关键实体、操作词与时间信息，用于检索历史记忆。\n"
    "输出严格 JSON，不加任何解释：\n"
    "{\n"
    '  "characters": ["人名", ...],\n'
    '  "regions": ["地名/省份", ...],\n'
    '  "keywords": ["核心动词或操作名词", ...],\n'
    "}\n"
    "规则：只提取文本中实际出现的词；keywords 限 5 个以内最核心的；所有列表可为空数组。"
)


def create_memory_retrieval_agent() -> Agent:
    """记忆检索 Agent（提取实体用于记忆检索）。"""
    import os as _os
    from han_sim.llm_config import load_llm_config
    _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
    cfg = load_llm_config(
        base_url="https://api.minimaxi.com/v1",
        model="MiniMax-M2.5",
        api_key=_api_key,
        timeout_seconds=60.0,
    )
    return Agent(
        name="记忆检索员",
        id="memory-retrieval",
        session_id="memory-retrieval",
        model=create_chat_model(cfg, temperature=0.0, top_p=0.7, enable_thinking=False, force_json_output=True),
        instructions=[_MEMORY_RETRIEVAL_PROMPT],
        add_history_to_context=False,
        markdown=False,
    )


JSON_SANITIZER_PROMPT = (
    "你是 JSON 修复匠。下面给你一段被污染的 JSON（可能混了思考过程、```json fence、注释、尾随逗号等），"
    "请只输出修复后的合法 JSON 字符串，不要加任何解释、前后缀或 fence。"
)


def create_json_sanitizer_agent() -> Agent:
    """JSON 修复 Agent。"""
    import os as _os
    from han_sim.llm_config import load_llm_config
    _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
    cfg = load_llm_config(
        base_url="https://api.minimaxi.com/v1",
        model="MiniMax-M2.5",
        api_key=_api_key,
        timeout_seconds=60.0,
    )
    return Agent(
        name="JSON修复匠",
        id="json-sanitizer",
        session_id="json-sanitizer",
        model=create_chat_model(cfg, temperature=0.0, top_p=0.7, enable_thinking=False, force_json_output=True),
        instructions=[JSON_SANITIZER_PROMPT],
        add_history_to_context=False,
        markdown=False,
    )


def create_chat_memory_agent() -> Agent:
    """对话记忆提取 Agent（从召对聊天提取承诺/建议/情报）。"""
    import os as _os
    from han_sim.llm_config import load_llm_config
    _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
    cfg = load_llm_config(
        base_url="https://api.minimaxi.com/v1",
        model="MiniMax-M2.5",
        api_key=_api_key,
        timeout_seconds=60.0,
    )
    ctx = _ctx()
    prompt = ctx.chat_memory_extractor_prompt if hasattr(ctx, "chat_memory_extractor_prompt") else (
        "从当月召对聊天中提取承诺/建议/情报，写入结构化记忆卡。闲聊跳过。"
    )
    return Agent(
        name="对话记忆档房",
        id="chat-memory-extractor",
        session_id="chat-memory-extractor",
        model=create_chat_model(cfg, temperature=0.1, top_p=0.7, enable_thinking=False, force_json_output=True),
        instructions=[ctx.game_world_prompt if hasattr(ctx, "game_world_prompt") else "", prompt],
        add_history_to_context=False,
        markdown=False,
    )


def create_consort_agent(consort_id: str, db, state):
    """v1.15.0 乾坤大挪移 Phase D 后宫妃嫔 agent。

    工厂函数，与现有 create_*_agent 同款风格。
    输入：consort_id（对应 consorts.json 里的 id，如 "consort_fu_shou"）。
    返：一个 Agno Agent 实例，prompt 注入 consort_agent.md + 7. 当前被召妃嫔画像。
    """
    import json as _json
    from agno.agent import Agent
    from han_sim.content import _ctx as content_ctx
    from han_sim.llm_config import load_runtime_llm, create_chat_model

    cfg = load_runtime_llm() or {}
    ctx = content_ctx()
    # 加载 prompt
    prompt = ctx.load_prompt("consort_agent") if ctx else ""

    # 加载当前妃嫔画像（优先 consorts.json → fallback db.consorts）
    consort_obj: Dict = {}
    if ctx:
        try:
            consorts = ctx.load_consorts()
            for c in consorts:
                if c.get("id") == consort_id:
                    consort_obj = c
                    break
        except Exception:
            pass
    if not consort_obj:
        try:
            ci = consort_id.replace("consort_", "")
            consort_obj = db.get_consort(state.campaign_id, ci) or {}
        except Exception:
            consort_obj = {}

    # 加载调教记录（取最近 3 条）
    recent_records: List[Dict] = []
    try:
        ci = consort_id.replace("consort_", "")
        recent_records = db.list_consort_events(state.campaign_id, ci)[:3]
    except Exception:
        pass

    consort_block = _json.dumps({
        "consort": consort_obj,
        "recent_cultivate_records": recent_records,
    }, ensure_ascii=False, indent=2)

    full_instructions = [
        ctx.game_world_prompt if hasattr(ctx, "game_world_prompt") else "",
        prompt,
        f"---\n## 7. 当前被召妃嫔\n{consort_block}",
    ]

    return Agent(
        name=f"ConsortAgent({consort_id})",
        model=create_chat_model(cfg, temperature=0.7, top_p=0.8, enable_thinking=False),
        instructions=full_instructions,
        add_history_to_context=True,
        markdown=False,
    )


def create_event_selector_agent() -> Agent:
    """v1.16.0 乾坤大挪移 Phase E · 候选情势判选 agent。

    工厂函数，与现有 create_*_agent 同款风格。
    加载 content/prompts/event_selector.md + game_world 双层 prompt。
    """
    from agno.agent import Agent
    from han_sim.content import _ctx as content_ctx
    from han_sim.llm_config import load_runtime_llm, create_chat_model

    cfg = load_runtime_llm() or {}
    ctx = content_ctx()
    prompt = ctx.load_prompt("event_selector") if ctx else ""

    full_instructions = [
        ctx.game_world_prompt if hasattr(ctx, "game_world_prompt") else "",
        prompt,
        "\n\n你只输出合法 JSON object, 严禁输出其他文字。",
    ]

    return Agent(
        name="候选情势判选官",
        id="event-selector",
        session_id="event-selector",
        model=create_chat_model(
            cfg, temperature=0.2, top_p=0.7, enable_thinking=False, max_tokens=600,
            force_json_output=True,
        ),
        instructions=full_instructions,
        add_history_to_context=False,
        markdown=False,
    )
