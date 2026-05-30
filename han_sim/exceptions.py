"""自定义异常。L0。"""


class GameError(Exception):
    pass


class LLMUnavailable(GameError):
    def __init__(self, message: str, code: str = "error", provider_message: str = "", status_code: int = None):
        super().__init__(message)
        self.code = code
        self.provider_message = provider_message
        self.status_code = status_code


class LLMContractError(GameError):
    """LLM 返回内容不符合契约规范（如 JSON 解析失败、字段缺失等）。"""
    pass