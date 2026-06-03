"""
v3.0-BE-2: LLM KV Cache 优化 (调研 P0-2)
========================================

设计依据: 智谱 GLM-5 + 青干《崇祯模拟器》联合白皮书
  "GLM-5 凭借 200K 上下文 + 高效稀疏注意力, 配合阿里云缓存命中方案,
   让它能记住玩家几十回合前下过的诏书. KV cache 避免重复计费."

实现:
  1. system prompt 中"静态部分" (角色档案/规则/格式) → system 前缀 (缓存命中)
  2. user message 中"动态部分" (玩家诏书/当前状态) → user 消息 (每次重算)
  3. 缓存键: 静态部分 SHA256
  4. 命中率统计: 按 (purpose, model) 分桶

注意: MiniMax/Qwen/DeepSeek/OpenAI 都支持 OpenAI 兼容的 prompt cache,
      通过把"不变内容"放 system 开头实现.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """KV cache 命中率统计"""
    total_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    by_purpose: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {"hits": 0, "misses": 0}))

    @property
    def hit_rate(self) -> float:
        return self.cache_hits / max(self.total_calls, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{self.hit_rate:.2%}",
            "by_purpose": {k: dict(v) for k, v in self.by_purpose.items()},
        }


_STATS = CacheStats()


# 静态部分缓存: key = (purpose, model, sha256(content)) -> hits
_STATIC_HASH_CACHE: Dict[Tuple[str, str, str], int] = {}


def make_static_block(content: str) -> str:
    """生成静态块 (供 system prompt 头部). 不带时间戳/动态值, 利于 KV cache."""
    return content.strip()


def static_hash(content: str) -> str:
    """算静态内容 SHA256 (用于 cache key)."""
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()[:16]


def split_prompt_for_cache(
    purpose: str,
    model: str,
    static_part: str,
    dynamic_part: str,
) -> Tuple[str, str]:
    """
    把 prompt 拆为 (system_static, user_dynamic) 利于 KV cache.

    参数:
      purpose: 用途 (decree/court_debate/diary/...)
      model: 模型名 (Qwen/DeepSeek/GLM-5/MiniMax)
      static_part: 不变部分 (角色档案/规则/格式说明)
      dynamic_part: 变化部分 (玩家诏书/当前状态/历史摘要)

    返回:
      (system_prefix_with_static, user_message_with_dynamic)

    实现:
      - 静态部分放在 system 开头 (模型会缓存)
      - 动态部分放 user message (每次重算)
      - 记录 cache hit/miss
    """
    key = (purpose, model, static_hash(static_part))
    _STATS.total_calls += 1
    if key in _STATIC_HASH_CACHE:
        _STATS.cache_hits += 1
        _STATS.by_purpose[purpose]["hits"] += 1
    else:
        _STATIC_HASH_CACHE[key] = _STATS.total_calls
        _STATS.cache_misses += 1
        _STATS.by_purpose[purpose]["misses"] += 1

    # 拼 system 头: 静态 + 动态标记
    system = (
        f"[STATIC-CACHE:{static_hash(static_part)}]\n"
        f"{static_part}\n"
        f"[/STATIC-CACHE]\n"
        f"--- 以下为每回合变化内容, 勿缓存 ---\n"
    )
    user = dynamic_part
    return system, user


def get_cache_stats() -> Dict[str, Any]:
    """返回 KV cache 命中统计 (供 API 暴露)."""
    return _STATS.to_dict()


def reset_cache_stats() -> None:
    """测试/重置用."""
    global _STATS
    _STATS = CacheStats()
    _STATIC_HASH_CACHE.clear()


def estimate_cache_savings(tokens_saved: int = 0) -> Dict[str, Any]:
    """
    估算缓存节省的 token 数 (按静态内容 token 数 × hit 次数).
    实际节省依赖模型 (MiniMax/Qwen/DeepSeek cache 价 = 0.1x 输入价).
    """
    if not tokens_saved:
        # 默认静态 system prompt 约 2000 tokens
        tokens_saved = 2000
    saved_per_hit = tokens_saved * 0.9  # cache 价 = 0.1x, 节省 0.9
    total_saved = saved_per_hit * _STATS.cache_hits
    return {
        "cache_hits": _STATS.cache_hits,
        "tokens_saved_estimate": total_saved,
        "cost_saved_estimate_usd": f"${total_saved * 0.11 / 1_000_000:.4f}",
    }
