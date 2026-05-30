"""LLM 契约：检查文本是否含错误标记。L2。"""

from han_sim.exceptions import LLMUnavailable


def fail_if_llm_error(text: str, stage: str) -> None:
    markers = ("ERROR", "Traceback", "Exception", " traceback ", "PANIC")
    upper = text.upper()
    for m in markers:
        if m.upper() in upper:
            raise LLMUnavailable(f"{stage}失败：{text[:200]}", code="llm_output_error", provider_message=text[:300])