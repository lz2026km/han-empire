"""LLM 提供商配置：base_url 规范化、提供商检测、LLMConfig 加载。L1。"""



import getpass
import json
import os
from typing import Dict, Optional

from han_sim.models import LLMConfig
from han_sim.paths import user_data_path

RUNTIME_LLM_PATH = user_data_path("runtime_llm.json")


def normalize_openai_base_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


def is_deepseek_base_url(base_url: str) -> bool:
    return "deepseek.com" in base_url.lower()


def is_dashscope_base_url(base_url: str) -> bool:
    return "dashscope" in base_url.lower() or "aliyuncs" in base_url.lower()


def is_minimax_base_url(base_url: str) -> bool:
    return "minimax" in base_url.lower() or "api.minimax.chat" in base_url.lower()


def provider_extra_body(base_url: str) -> Optional[Dict[str, object]]:
    if is_deepseek_base_url(base_url):
        return {"thinking": {"type": "disabled"}}
    if is_dashscope_base_url(base_url):
        return {"enable_thinking": False}
    if is_minimax_base_url(base_url):
        return None
    return None


def supports_openai_reasoning_effort(model: str) -> bool:
    model_id = model.lower()
    return model_id.startswith(("o1", "o3", "o4", "gpt-5"))


def load_llm_config(
    base_url: str = "",
    model: str = "",
    api_key: str = "",
    timeout_seconds: float = 180.0,
    advanced_model: str = "",
    advanced_base_url: str = "",
    advanced_api_key: str = "",
) -> LLMConfig:
    runtime = load_runtime_llm()
    api_key = (api_key or runtime.get("api_key", "") or os.environ.get("OPENAI_API_KEY", "")).strip()
    if not api_key:
        api_key = getpass.getpass("请输入 API key（不会保存，回车取消）：").strip()
    if not api_key:
        raise SystemExit("未提供 API key，无法使用 LLM。")
    cfg_base_url = (base_url or runtime.get("base_url", "") or "").strip()
    cfg_model = (model or runtime.get("model", "") or "").strip()
    if not cfg_base_url:
        cfg_base_url = "https://api.deepseek.com/v1"
    if not cfg_model:
        cfg_model = "deepseek-v4-flash"
    adv_base = (advanced_base_url or runtime.get("advanced_base_url", "") or "").strip()
    return LLMConfig(
        api_key=api_key,
        base_url=normalize_openai_base_url(cfg_base_url),
        model=cfg_model,
        timeout_seconds=timeout_seconds,
        advanced_model=(advanced_model or runtime.get("advanced_model", "") or "").strip(),
        advanced_base_url=normalize_openai_base_url(adv_base) if adv_base else "",
        advanced_api_key=(advanced_api_key or runtime.get("advanced_api_key", "") or "").strip(),
    )


_ADVANCED_ROLES = frozenset({"simulator", "extractor"})


def for_role(cfg: LLMConfig, role: str) -> LLMConfig:
    if role in _ADVANCED_ROLES and (cfg.advanced_model or "").strip():
        adv_base = (cfg.advanced_base_url or "").strip() or cfg.base_url
        adv_key = (cfg.advanced_api_key or "").strip() or cfg.api_key
        return LLMConfig(
            api_key=adv_key,
            base_url=adv_base,
            model=cfg.advanced_model.strip(),
            max_tokens=cfg.max_tokens,
            timeout_seconds=cfg.timeout_seconds,
            advanced_model=cfg.advanced_model,
            advanced_base_url=cfg.advanced_base_url,
            advanced_api_key=cfg.advanced_api_key,
        )
    return cfg


def save_llm_config(config: LLMConfig) -> None:
    save_runtime_llm(
        base_url=config.base_url,
        model=config.model,
        api_key=config.api_key,
        max_tokens=config.max_tokens,
        timeout_seconds=config.timeout_seconds,
        advanced_model=config.advanced_model,
        advanced_base_url=config.advanced_base_url,
        advanced_api_key=config.advanced_api_key,
    )


def load_runtime_llm() -> Dict[str, str]:
    """多路径回退读取 LLM 配置（v1.13.1 乾坤大挪移修小版本改）：
    1. RUNTIME_LLM_PATH（~/.hermes/han-empire/runtime_llm.json，标准路径）
    2. <工作目录>/runtime_llm.json（开发期常用）
    3. ~/.openclaw/agents/main/agent/auth-profiles.json 的 minimax:cn profile（兜底）
    任一找到后即停。若 api_key 仍空，自动从 auth-profiles.json 读取 minimax:cn.key。
    """
    candidates = [RUNTIME_LLM_PATH]
    cwd_rt = os.path.join(os.getcwd(), "runtime_llm.json")
    if cwd_rt not in candidates:
        candidates.append(cwd_rt)
    auth_path = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")

    data: Dict = {}
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    loaded = json.load(fh)
                if isinstance(loaded, dict):
                    data = loaded
                    break
            except (OSError, json.JSONDecodeError):
                pass

    # api_key 兜底：从 auth-profiles.json 的 minimax:cn profile 读
    if not data.get("api_key") and os.path.isfile(auth_path):
        try:
            with open(auth_path, "r", encoding="utf-8") as fh:
                auth_data = json.load(fh)
            profile = auth_data.get("profiles", {}).get("minimax:cn", {})
            if profile.get("key"):
                data["api_key"] = profile["key"]
                if not data.get("base_url"):
                    data["base_url"] = "https://api.minimaxi.com/v1"
                if not data.get("model"):
                    data["model"] = "MiniMax-Text-01"
        except (OSError, json.JSONDecodeError):
            pass

    if not isinstance(data, dict):
        return {}
    out = {
        k: str(data.get(k, "") or "")
        for k in ("base_url", "model", "api_key", "advanced_model", "advanced_base_url", "advanced_api_key")
    }
    if "max_tokens" in data:
        out["max_tokens"] = str(data["max_tokens"])
    if "timeout_seconds" in data:
        out["timeout_seconds"] = str(data["timeout_seconds"])
    return out


def save_runtime_llm(
    base_url: str,
    model: str,
    api_key: str,
    max_tokens: int = 8000,
    timeout_seconds: float = 180.0,
    advanced_model: str = "",
    advanced_base_url: str = "",
    advanced_api_key: str = "",
) -> None:
    os.makedirs(os.path.dirname(RUNTIME_LLM_PATH), exist_ok=True)
    payload = {
        "base_url": (base_url or "").strip(),
        "model": (model or "").strip(),
        "api_key": (api_key or "").strip(),
        "max_tokens": max_tokens,
        "timeout_seconds": timeout_seconds,
        "advanced_model": (advanced_model or "").strip(),
        "advanced_base_url": (advanced_base_url or "").strip(),
        "advanced_api_key": (advanced_api_key or "").strip(),
    }
    with open(RUNTIME_LLM_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)