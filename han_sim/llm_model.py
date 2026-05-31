"""LLM 模型与 Agno DB 工厂、agent 输出文本提取。L2。"""



from typing import Dict, Optional

try:
    from agno.agent import Agent
    from agno.db.sqlite import SqliteDb
    from agno.models.openai import OpenAIChat
except ImportError:
    Agent = None  # type: ignore
    SqliteDb = None  # type: ignore
    OpenAIChat = None  # type: ignore
try:
    from openai import APIConnectionError, APIStatusError, APITimeoutError
except ImportError:
    APIConnectionError = Exception  # type: ignore
    APIStatusError = Exception      # type: ignore
    APITimeoutError = Exception     # type: ignore

from han_sim.exceptions import LLMUnavailable
from han_sim.llm_config import (
    is_dashscope_base_url,
    is_deepseek_base_url,
    is_minimax_base_url,
    provider_extra_body,
    supports_openai_reasoning_effort,
)
from han_sim.llm_contract import fail_if_llm_error
from han_sim.models import LLMConfig


def _extract_provider_error(error: Exception) -> tuple:
    code = getattr(error, "code", None) or type(error).__name__
    message = str(error)
    status_code = getattr(error, "status_code", None)
    response = getattr(error, "response", None)
    if response is not None:
        try:
            payload = response.json()
        except Exception:
            payload = None
        if isinstance(payload, dict):
            inner = payload.get("error")
            if isinstance(inner, dict):
                code = inner.get("code") or inner.get("type") or code
                message = inner.get("message") or message
            else:
                code = payload.get("code") or payload.get("type") or code
                message = payload.get("message") or payload.get("detail") or message
    return str(code), str(message), int(status_code) if status_code is not None else None


def llm_unavailable_from_error(error: Exception, stage: str = "LLM 连通性检查") -> LLMUnavailable:
    provider_code, provider_message, status_code = _extract_provider_error(error)
    if isinstance(error, APITimeoutError):
        code = "llm_timeout"
    elif isinstance(error, APIConnectionError):
        code = "llm_connection_error"
    elif isinstance(error, APIStatusError):
        code = f"llm_http_{status_code or 'error'}"
    else:
        code = "llm_error"
    return LLMUnavailable(
        f"{stage}失败：{provider_message}",
        code=code,
        provider_message=provider_message,
        status_code=status_code,
    )


def create_chat_model(
    llm_config: LLMConfig,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    enable_thinking: bool = False,
    thinking_budget: Optional[int] = None,
    top_p: Optional[float] = None,
    force_json_output: bool = False,
) -> OpenAIChat:
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
        "timeout": llm_config.timeout_seconds,
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
    if OpenAIChat is None:
        raise LLMUnavailable("agno未安装，无法创建LLM模型")
    return OpenAIChat(**kwargs)


def create_agno_db(sqlite_path: str) -> SqliteDb:
    if SqliteDb is None:
        raise LLMUnavailable("agno未安装，无法创建Agno DB")
    return SqliteDb(
        db_file=sqlite_path,
        session_table="agno_sessions",
        memory_table="agno_memories",
    )


def extract_agent_text(run_output: object) -> str:
    content = getattr(run_output, "content", None)
    if content is not None:
        text = str(content).strip()
    else:
        text = str(run_output).strip()
    fail_if_llm_error(text, "LLM 调用")
    return text


def verify_llm_available(llm_config: LLMConfig) -> None:
    if Agent is None:
        raise LLMUnavailable("agno未安装，无法验证LLM")
    agent = Agent(
        name="LLM连通性检查",
        id="llm-smoke-test",
        session_id="llm-smoke-test",
        model=create_chat_model(llm_config, temperature=0, max_tokens=8),
        instructions=["只输出 ok。"],
        markdown=False,
    )
    try:
        text = extract_agent_text(agent.run("输出 ok"))
    except LLMUnavailable:
        raise
    except Exception as error:
        raise llm_unavailable_from_error(error) from error
    if text.strip().lower() != "ok":
        raise LLMUnavailable(
            f"LLM 连通性检查失败：期望返回 ok，实际返回：{text[:300]}",
            code="llm_validation_failed",
            provider_message=text[:300],
        )