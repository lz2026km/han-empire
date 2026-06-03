"""v5.0 P0-2: 模型分级路由 (按用途分配 model)

4 个 tier:
- SIMULATE: 推演 (量大, 用 flash/快速模型降本)
- ROLEPLAY: 角色扮演 (大臣/妃嫔, 用 plus/高质量模型提质)
- BRIEFING: 简报 (中等质量)
- SANITIZE: JSON 清洗 (用 flash 即可)

支持 4 个独立 model 槽位, 全部从 runtime_llm.json 读取.

调用入口:
    from han_sim.llm_router import get_router, ModelTier
    router = get_router()
    cfg = router.get_config(ModelTier.SIMULATE)  # 返回推演用的 LLMConfig
"""
from __future__ import annotations

import json
import logging
import os
from enum import Enum
from typing import Dict, Optional

from han_sim.models import LLMConfig
from han_sim.paths import user_data_path

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """模型分级 (4 tier)"""
    SIMULATE = "simulate"    # 推演 (量大, flash 降本)
    ROLEPLAY = "roleplay"    # 角色 (大臣/妃嫔, plus 提质)
    BRIEFING = "briefing"    # 简报 (中等)
    SANITIZE = "sanitize"    # JSON 清洗 (flash)


# 4 tier 默认 model 映射 (可被 runtime_llm.json 覆盖)
DEFAULT_TIER_MODELS: Dict[ModelTier, Dict[str, str]] = {
    ModelTier.SIMULATE: {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
    },
    ModelTier.ROLEPLAY: {
        "base_url": "https://api.minimaxi.com/v1",
        "model": "MiniMax-M2.5",
    },
    ModelTier.BRIEFING: {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
    },
    ModelTier.SANITIZE: {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
    },
}

# tier 持久化文件路径
TIER_CONFIG_PATH = user_data_path("model_tiers.json")

# v4.9 role 到 tier 映射 (向后兼容)
_V4_ROLE_TO_TIER: Dict[str, ModelTier] = {
    "simulator": ModelTier.SIMULATE,
    "extractor": ModelTier.SIMULATE,  # 5 档房用 SIMULATE
    "minister": ModelTier.ROLEPLAY,
    "consort": ModelTier.ROLEPLAY,
    "memory": ModelTier.SANITIZE,
    "chat_memory": ModelTier.BRIEFING,
    "default": ModelTier.ROLEPLAY,
}


class LLMRouter:
    """模型分级路由器 (单例)

    提供:
    - get_config(tier): 返回该 tier 的 LLMConfig
    - get_model_name(tier): 返回该 tier 的 model 名
    - 4 tier × N model 持久化
    """

    def __init__(self):
        self._tier_configs: Dict[ModelTier, Dict[str, str]] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        """从 model_tiers.json 加载 4 tier 配置"""
        for tier in ModelTier:
            self._tier_configs[tier] = dict(DEFAULT_TIER_MODELS[tier])

        if not os.path.exists(TIER_CONFIG_PATH):
            return

        try:
            with open(TIER_CONFIG_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                return
            for tier_name, cfg in data.items():
                try:
                    tier = ModelTier(tier_name)
                except ValueError:
                    continue
                if isinstance(cfg, dict):
                    if "base_url" in cfg and cfg["base_url"]:
                        self._tier_configs[tier]["base_url"] = cfg["base_url"]
                    if "model" in cfg and cfg["model"]:
                        self._tier_configs[tier]["model"] = cfg["model"]
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"加载 model_tiers.json 失败, 用默认: {e}")

    def save(self) -> None:
        """持久化 4 tier 配置"""
        os.makedirs(os.path.dirname(TIER_CONFIG_PATH), exist_ok=True)
        payload = {
            tier.value: dict(self._tier_configs[tier])
            for tier in ModelTier
        }
        with open(TIER_CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

    def get_config(self, tier: ModelTier) -> LLMConfig:
        """返回该 tier 的 LLMConfig

        从 environment 变量读 api_key (顺序: MINIMAX_API_KEY → OPENAI_API_KEY → DEEPSEEK_API_KEY)
        """
        tier_cfg = self._tier_configs.get(tier, DEFAULT_TIER_MODELS[tier])
        base_url = tier_cfg.get("base_url", "")
        model = tier_cfg.get("model", "")

        # 读 api_key
        api_key = (
            os.environ.get("MINIMAX_API_KEY", "").strip()
            or os.environ.get("OPENAI_API_KEY", "").strip()
            or os.environ.get("DEEPSEEK_API_KEY", "").strip()
        )
        if not api_key:
            raise RuntimeError(
                f"未提供 API key (tier={tier.value}). "
                f"请设置 MINIMAX_API_KEY/OPENAI_API_KEY/DEEPSEEK_API_KEY 环境变量"
            )

        return LLMConfig(
            api_key=api_key,
            base_url=_normalize_url(base_url),
            model=model,
            timeout_seconds=180.0,
        )

    def get_model_name(self, tier: ModelTier) -> str:
        """返回该 tier 的 model 名 (快捷接口)"""
        return self._tier_configs.get(tier, DEFAULT_TIER_MODELS[tier]).get("model", "")

    def get_base_url(self, tier: ModelTier) -> str:
        """返回该 tier 的 base_url (快捷接口)"""
        return self._tier_configs.get(tier, DEFAULT_TIER_MODELS[tier]).get("base_url", "")

    def set_tier(self, tier: ModelTier, base_url: str = "", model: str = "") -> None:
        """动态设置 tier 配置"""
        if base_url:
            self._tier_configs[tier]["base_url"] = base_url
        if model:
            self._tier_configs[tier]["model"] = model

    def get_all_tiers(self) -> Dict[str, Dict[str, str]]:
        """返回所有 tier 当前配置 (调试用)"""
        return {
            tier.value: dict(self._tier_configs[tier])
            for tier in ModelTier
        }


def _normalize_url(base_url: str) -> str:
    """规范化 base_url (确保 /v1 后缀)"""
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


# ════════════════════════════════════════════════════════════════
# 单例 + v4 兼容
# ════════════════════════════════════════════════════════════════

_router_instance: Optional[LLMRouter] = None


def get_router() -> LLMRouter:
    """获取 router 单例"""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance


def reset_router() -> None:
    """重置 router (测试用)"""
    global _router_instance
    _router_instance = None


def get_config_for_tier(tier: ModelTier) -> LLMConfig:
    """便捷函数: 直接拿 tier 的 LLMConfig"""
    return get_router().get_config(tier)


def get_config_for_v4_role(role: str) -> LLMConfig:
    """v4.9 兼容: 根据 role 字符串返回 LLMConfig

    role ∈ "simulator" / "extractor" / "minister" / "consort" / "memory" / "chat_memory"
    """
    tier = _V4_ROLE_TO_TIER.get(role, ModelTier.ROLEPLAY)
    return get_router().get_config(tier)


def get_tier_summary() -> Dict[str, Dict[str, str]]:
    """返回所有 tier 配置摘要 (调试用)"""
    return get_router().get_all_tiers()


if __name__ == "__main__":
    # 自测: 打印配置
    import json as _json
    print(_json.dumps(get_tier_summary(), ensure_ascii=False, indent=2))
