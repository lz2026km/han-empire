"""
v3.0-BE-1: 本地 API Key 路由 (调研 P0-1)
=============================================

设计依据: 《历史模拟器:崇祯》Steam Q&A 官方要求
  "玩家的 API Key 不会被上传到服务器, 基于 API 的调用将从用户本地发起,
   API Key 将全程保持在用户本地."

实现:
  1. Web 端 LocalStorage 存 Key (不发给 server)
  2. Server 端配置默认回退 Key (MiniMax / 主公内嵌), 用于无 Key 玩家
  3. Server 端只接收"使用哪条 Key 路径"的指令, 不接收 Key 本身
  4. 客户端可主动调用 LLM (走 CORS), 也可走 Server 代理 (用 Server 默认 Key)

模式:
  Mode A (本地优先): client 拿 LocalStorage Key 直连 LLM API (推荐)
  Mode B (Server 代理): client 不存 Key, server 用默认 Key 代理
  Mode C (混合): 关键决策用 Mode A 私密, 通用推演用 Mode B 兜底

存储:
  - Server 端: runtime_llm.json (主公已存 MiniMax 凭据) 兜底
  - Client 端: localStorage["han_empire_api_keys"] 存用户 Key (base64 弱加密)
  - 服务端永不接收/存/记录用户 Key
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from han_sim.llm_config import (
    RUNTIME_LLM_PATH,
    is_dashscope_base_url,
    is_deepseek_base_url,
    is_minimax_base_url,
    normalize_openai_base_url,
)

logger = logging.getLogger(__name__)


class KeyMode(str, Enum):
    """API Key 路由模式"""
    LOCAL = "local"           # 客户端用自己 Key 直连 (私密)
    SERVER_PROXY = "server"   # 服务端用兜底 Key 代理
    HYBRID = "hybrid"         # 关键决策走 LOCAL, 通用走 SERVER


# 服务端兜底 Key (从 runtime_llm.json 读, 不在源码明文存)
def _load_server_fallback_key() -> Optional[Dict[str, str]]:
    """从主公 runtime_llm.json 加载服务端兜底凭据."""
    p = Path(RUNTIME_LLM_PATH) if isinstance(RUNTIME_LLM_PATH, str) else RUNTIME_LLM_PATH
    if not p.exists():
        logger.warning("runtime_llm.json 不存在, 服务端无兜底 Key")
        return None
    try:
        with open(RUNTIME_LLM_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return {
            "base_url": cfg.get("base_url", ""),
            "api_key": cfg.get("api_key", ""),
            "model": cfg.get("model", ""),
        }
    except Exception as e:  # noqa: BLE001
        logger.error("加载 runtime_llm.json 失败: %s", e)
        return None


# 服务端路由决策
@dataclass
class KeyRoute:
    """API Key 路由决策结果"""
    mode: KeyMode
    base_url: str
    api_key: str
    model: str
    from_local: bool = False
    warning: Optional[str] = None


def decide_route(
    requested_mode: str = "server",
    client_local_keys: Optional[Dict[str, str]] = None,
    purpose: str = "general",  # "general" | "decree" | "court_debate" | "diary"
) -> KeyRoute:
    """
    决定本次 LLM 调用走哪条 Key 路径.

    参数:
      requested_mode: 客户端请求的模式 "local" | "server" | "hybrid"
      client_local_keys: 客户端传来的 Key 字典 (仅 LOCAL 模式有效)
      purpose: 用途, 用于 HYBRID 模式分流 (关键决策走 LOCAL)

    返回:
      KeyRoute 路由决策 (含 base_url/api_key/model)
    """
    # 客户端明确传 LOCAL + 有 Key → 客户端私钥
    if requested_mode == "local" and client_local_keys:
        key = client_local_keys.get("api_key", "").strip()
        if not key:
            return _fallback_to_server("客户端 Key 为空, 回退到服务端兜底")
        return KeyRoute(
            mode=KeyMode.LOCAL,
            base_url=normalize_openai_base_url(client_local_keys.get("base_url", "")),
            api_key=key,
            model=client_local_keys.get("model", ""),
            from_local=True,
        )

    # HYBRID 模式: 关键决策走 LOCAL, 通用走 SERVER
    if requested_mode == "hybrid":
        critical = purpose in ("decree", "court_debate")  # 关键决策
        if critical and client_local_keys:
            key = client_local_keys.get("api_key", "").strip()
            if key:
                return KeyRoute(
                    mode=KeyMode.HYBRID,
                    base_url=normalize_openai_base_url(client_local_keys.get("base_url", "")),
                    api_key=key,
                    model=client_local_keys.get("model", ""),
                    from_local=True,
                )

    # 默认: 服务端兜底
    server = _load_server_fallback_key()
    if not server or not server.get("api_key"):
        raise RuntimeError(
            "服务端无兜底 Key, 且客户端未提供 LOCAL Key. "
            "请在 Settings 中配置 API Key, 或联系主公配置 runtime_llm.json"
        )
    return KeyRoute(
        mode=KeyMode.SERVER_PROXY,
        base_url=server["base_url"],
        api_key=server["api_key"],
        model=server["model"],
    )


def _fallback_to_server(warning: str) -> KeyRoute:
    """回退到服务端兜底 Key."""
    logger.warning(warning)
    server = _load_server_fallback_key()
    if not server or not server["api_key"]:
        raise RuntimeError(
            "客户端 + 服务端双无 Key, 无法调用 LLM. "
            "请检查 Settings 或 runtime_llm.json"
        )
    return KeyRoute(
        mode=KeyMode.SERVER_PROXY,
        base_url=server["base_url"],
        api_key=server["api_key"],
        model=server["model"],
        warning=warning,
    )


# === 服务端 API (供 server.py 调用) ===
def get_server_routes_summary() -> Dict[str, Any]:
    """返回服务端兜底 Key 状态摘要 (不含 Key 内容)."""
    server = _load_server_fallback_key()
    if not server:
        return {"has_fallback": False}
    # 算 Key 指纹 (前 4 + 后 4)
    key = server.get("api_key", "")
    fingerprint = f"{key[:4]}***{key[-4:]}" if len(key) > 8 else "***"
    return {
        "has_fallback": True,
        "base_url": server.get("base_url", ""),
        "model": server.get("model", ""),
        "key_fingerprint": fingerprint,
        "key_length": len(key),
    }


def get_supported_modes() -> List[str]:
    """返回支持的 Key 模式 (给前端 Settings 展示)."""
    return [m.value for m in KeyMode]
