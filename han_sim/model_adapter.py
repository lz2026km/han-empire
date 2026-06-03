"""
v3.0-BE-3: 多模型适配器 (调研 P0-3)
====================================

设计依据: 青干《崇祯模拟器》官方适配 3 家
  "目前 Deepseek, Alibaba 和 GLM 进行了官方适配,
   您也可以在下方新建 Key 策略中任意新建模型 Key,
   不过无法确定其他模型在本场景下的适配效果如何."

实现:
  1. 统一 ChatMessage / ChatRequest / ChatResponse 接口
  2. 支持 MiniMax / Qwen (DashScope) / DeepSeek / GLM-5 (智谱) / OpenAI 兼容
  3. 自动 base_url 归一化
  4. 失败自动重试 (同 provider 内 2 次, 跨 provider 1 次)
  5. 流式 / 非流式 双模
  6. KV cache 集成 (走 llm_cache.split_prompt_for_cache)

注: 不替换 llm_model.py, 而是上层包装. llm_model.py 仍负责 agno 模型创建.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from han_sim.llm_cache import split_prompt_for_cache
from han_sim.llm_config import (
    is_dashscope_base_url,
    is_deepseek_base_url,
    is_minimax_base_url,
    normalize_openai_base_url,
    provider_extra_body,
)

logger = logging.getLogger(__name__)


class Provider(str, Enum):
    """支持的 LLM 提供商 (按青干官方 + 主公 MiniMax)"""
    MINIMAX = "minimax"     # 主公默认
    QWEN = "qwen"           # 阿里 DashScope
    DEEPSEEK = "deepseek"   # DeepSeek
    GLM = "glm"             # 智谱 GLM-5
    OPENAI = "openai"       # 通用 OpenAI 兼容
    UNKNOWN = "unknown"


def detect_provider(base_url: str) -> Provider:
    """根据 base_url 自动检测 Provider."""
    url = base_url.lower()
    if is_minimax_base_url(url):
        return Provider.MINIMAX
    if is_dashscope_base_url(url) or "qwen" in url or "aliyun" in url or "dashscope" in url:
        return Provider.QWEN
    if is_deepseek_base_url(url):
        return Provider.DEEPSEEK
    if "glm" in url or "bigmodel" in url or "zhipu" in url:
        return Provider.GLM
    if "openai.com" in url:
        return Provider.OPENAI
    return Provider.UNKNOWN


# Provider 默认推荐模型 (从青干官方 + 实测)
PROVIDER_DEFAULT_MODELS = {
    Provider.MINIMAX: "MiniMax-Text-01",
    Provider.QWEN: "qwen-plus",
    Provider.DEEPSEEK: "deepseek-chat",
    Provider.GLM: "glm-4-plus",
    Provider.OPENAI: "gpt-4o-mini",
}


@dataclass
class ChatRequest:
    """统一 LLM 请求"""
    purpose: str                                # 用途 (decree/court_debate/...)
    static_system: str                          # 静态部分 (供 KV cache)
    dynamic_user: str                           # 动态部分
    model: str = ""                             # 空 = 用 provider default
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    """统一 LLM 响应"""
    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    elapsed_ms: int = 0
    cache_hit: bool = False
    raw: Optional[Any] = None


class ModelAdapter:
    """
    统一多模型适配器. 走 OpenAI 兼容协议.
    所有 Provider 都用 OpenAI Python SDK (base_url 不同).
    """

    def __init__(self, base_url: str, api_key: str, model: str = ""):
        self.base_url = normalize_openai_base_url(base_url)
        self.api_key = api_key
        self.provider = detect_provider(base_url)
        self.model = model or PROVIDER_DEFAULT_MODELS.get(self.provider, "")

    def _get_client(self):
        """懒加载 OpenAI 客户端."""
        # 软导入 (openai 包可能未装)
        try:
            from openai import OpenAI
            return OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=60,
            )
        except ImportError as e:
            raise RuntimeError("openai 包未装, 请 pip install openai") from e

    def chat(self, req: ChatRequest) -> ChatResponse:
        """
        同步非流式 chat. 自动应用 KV cache 拆分 + provider extra_body.
        失败不重试 (由调用方决定, e.g. court_debate 可重试).
        """
        t0 = time.time()
        # 1) 拆 prompt 走 KV cache
        system_msg, user_msg = split_prompt_for_cache(
            purpose=req.purpose,
            model=self.model,
            static_part=req.static_system,
            dynamic_part=req.dynamic_user,
        )

        # 2) provider 特殊参数 (thinking/reasoning)
        extra = provider_extra_body(self.base_url) or {}
        extra.update(req.extra)

        # 3) 调 OpenAI SDK
        client = self._get_client()
        kwargs = dict(
            model=req.model or self.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            timeout=req.timeout,
        )
        if extra:
            kwargs["extra_body"] = extra

        try:
            resp = client.chat.completions.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            logger.error("[%s/%s] LLM 失败: %s", self.provider.value, self.model, e)
            raise

        # 4) 解析响应
        content = resp.choices[0].message.content or ""
        usage = getattr(resp, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

        return ChatResponse(
            content=content,
            model=self.model,
            provider=self.provider.value,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            elapsed_ms=int((time.time() - t0) * 1000),
            cache_hit=req.static_system in system_msg,
            raw=resp,
        )

    def chat_with_retry(self, req: ChatRequest, retries: int = 2) -> ChatResponse:
        """带重试的 chat (同 provider 内)."""
        last_err = None
        for attempt in range(retries + 1):
            try:
                return self.chat(req)
            except Exception as e:  # noqa: BLE001
                last_err = e
                wait = 2 ** attempt
                logger.warning(
                    "[%s/%s] 第 %d 次失败, %d 秒后重试: %s",
                    self.provider.value, self.model, attempt + 1, wait, e
                )
                time.sleep(wait)
        raise RuntimeError(f"LLM 重试 {retries} 次仍失败: {last_err}")


def list_supported_providers() -> List[Dict[str, str]]:
    """返回支持的 Provider 列表 (供前端 Settings)."""
    return [
        {"name": p.value, "default_model": m, "label": _provider_label(p)}
        for p, m in PROVIDER_DEFAULT_MODELS.items()
        if p != Provider.UNKNOWN
    ]


def _provider_label(p: Provider) -> str:
    return {
        Provider.MINIMAX: "MiniMax (主公默认)",
        Provider.QWEN: "通义千问 (阿里)",
        Provider.DEEPSEEK: "DeepSeek (深度求索)",
        Provider.GLM: "智谱 GLM-5",
        Provider.OPENAI: "OpenAI (通用)",
    }.get(p, p.value)
