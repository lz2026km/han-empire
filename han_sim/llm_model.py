# v2.0.0 Phase 4.1: LLM 模型工厂与 agent 输出提取
# 统一 han-empire 的 LLM 入口
# 解决 3 个痛点：
# 1. 5 个 agent 0 个 tool_calls (Phase 4.3 解决)
# 2. 3 处 LLM 静默失败 (本文件 + llm_contract 解决)
# 3. 0 个 token 统计
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

# v2.0.0 Phase 4.1: 仿 agents.py:8 模式软导入 agno，无 agno 时降级
try:
    from agno.models.openai import OpenAIChat
except ImportError:
    OpenAIChat = None  # type: ignore

from han_sim.llm_config import (
    is_dashscope_base_url,
    is_deepseek_base_url,
    is_minimax_base_url,
    provider_extra_body,
    supports_openai_reasoning_effort,
)
from han_sim.llm_contract import fail_if_llm_error
from han_sim.models import LLMConfig

logger = logging.getLogger(__name__)

# v2.0.0 Phase 4.1: token 统计
_TOKEN_STATS: Dict[str, int] = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "call_count": 0,
    "error_count": 0,
}


def get_token_stats() -> Dict[str, int]:
    """返回当前会话的 token 统计快照。"""
    return dict(_TOKEN_STATS)


def reset_token_stats() -> None:
    """重置 token 统计（测试/多 campaign 切换用）。"""
    _TOKEN_STATS.update(
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        call_count=0,
        error_count=0,
    )


def _accumulate_tokens(response: Any) -> None:
    """从 agno response 提取 tokens 累加。"""
    try:
        usage = getattr(response, "metrics", None) or getattr(response, "usage", None)
        if usage is None:
            return
        if hasattr(usage, "prompt_tokens"):
            _TOKEN_STATS["prompt_tokens"] += int(usage.prompt_tokens or 0)
            _TOKEN_STATS["completion_tokens"] += int(usage.completion_tokens or 0)
            _TOKEN_STATS["total_tokens"] += int(
                (usage.prompt_tokens or 0) + (usage.completion_tokens or 0)
            )
    except Exception as e:  # noqa: BLE001
        logger.debug("token 统计跳过: %s", e)


def create_chat_model(
    llm_config: LLMConfig,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    enable_thinking: bool = False,
    thinking_budget: Optional[int] = None,
    top_p: Optional[float] = None,
    force_json_output: bool = False,
) -> OpenAIChat:
    """统一 LLM 模型工厂。

    用途：所有 5 个 agent（minister/season_simulator/score_extractor/memory/chat/
    consort/sanitizer）应统一调用此函数，避免每处重复 base_url/temperature
    /extra_body 处理。
    """
    extra_body = provider_extra_body(llm_config.base_url)
    if enable_thinking and is_dashscope_base_url(llm_config.base_url):
        extra_body = {"enable_thinking": True}
        if thinking_budget is not None:
            extra_body["thinking_budget"] = int(thinking_budget)
    elif enable_thinking and is_deepseek_base_url(llm_config.base_url):
        extra_body = {}
    elif enable_thinking and is_minimax_base_url(llm_config.base_url):
        extra_body = {}

    kwargs: Dict[str, object] = {
        "id": llm_config.model,
        "api_key": llm_config.api_key,
        "base_url": llm_config.base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": getattr(llm_config, "timeout_seconds", 60),
        "max_retries": 1,
        "role_map": {"system": "system", "user": "user", "assistant": "assistant", "tool": "tool"},
        "extra_body": extra_body,
    }
    if top_p is not None:
        kwargs["top_p"] = top_p
    if force_json_output:
        if extra_body is None:
            extra_body = {}
        extra_body["response_format"] = {"type": "json_object"}
        kwargs["extra_body"] = extra_body
    if supports_openai_reasoning_effort(llm_config.model):
        kwargs["reasoning_effort"] = "medium" if enable_thinking else "minimal"
    return OpenAIChat(**kwargs) if OpenAIChat is not None else None  # type: ignore[return-value]


def extract_agent_text(run_output: Any) -> str:
    """统一提取 agno agent 输出文本。

    关键改进（修复 P1-3 处 LLM 静默失败）：提取后立即调用
    fail_if_llm_error()，确保 ERROR/Traceback/PANIC 等错误标记不会被
    当成"成功返回"继续向下走。
    """
    content = getattr(run_output, "content", None)
    if content is not None:
        text = str(content).strip()
    else:
        text = str(run_output).strip()
    fail_if_llm_error(text, "LLM 调用")
    _accumulate_tokens(run_output)
    _TOKEN_STATS["call_count"] += 1
    return text


def safe_extract_agent_text(run_output: Any, default: str = "") -> str:
    """安全版 - 失败不抛异常，返回 default。

    适用于不阻塞主流程的 LLM 调用（如天子日记、背景叙事）。
    """
    try:
        return extract_agent_text(run_output)
    except Exception as e:  # noqa: BLE001
        _TOKEN_STATS["error_count"] += 1
        logger.warning("LLM 调用降级返回默认文本: %s", e)
        return default


def verify_llm_available(llm_config: LLMConfig) -> bool:
    """启动时健康检查。

    返回 True=可用, False=不可用（不抛异常，让上层决定是否继续）。
    """
    try:
        from agno.agent import Agent
    except ImportError:
        logger.warning("agno 未安装，跳过 LLM 连通性检查")
        return False
    if OpenAIChat is None:
        return False

    try:
        agent = Agent(
            name="LLM连通性检查",
            id="llm-smoke-test",
            session_id="llm-smoke-test",
            model=create_chat_model(llm_config, temperature=0, max_tokens=8),
            instructions=["只输出 ok。"],
            markdown=False,
        )
        text = extract_agent_text(agent.run("输出 ok"))
        return text.lower().strip() == "ok"
    except Exception as e:  # noqa: BLE001
        logger.error("LLM 连通性检查失败: %s", e)
        return False
