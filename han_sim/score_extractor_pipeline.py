"""v5.0 P0-1: 5 档房串联抽取 Pipeline

把 v4.9 的 311 行单体 score_extractor 拆为 4 个专项档房, 通过 4 次 LLM 调用
分别抽取 4 类字段, 合并为 20 字段 JSON.

设计要点:
1. 4 档房串行调用 (避免 LLM 速率限制 + 上下文污染)
2. 任意档房失败 → 重试 1 次 → 仍失败用 v4 backup
3. 字段所有权清晰, 4 档房输出不冲突
4. 支持 4 档房并行 (asyncio.gather) 用于降低延迟

调用入口:
    from han_sim.score_extractor_pipeline import extract_score
    result = extract_score(narrative, decree_text, ctx)
    # result: dict with 20 fields, or {"_error": "..."} on total failure
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
# 20 字段契约定义
# ════════════════════════════════════════════════════════════════

# 4 档房各负责的字段 (字段所有权)
TIER_FIELDS: Dict[str, List[str]] = {
    "internal": [
        "metric_delta", "economy_moves", "fiscal_changes",
        "faction_delta", "class_delta", "region_delta",
    ],
    "issues": [
        "issue_advances", "new_issues", "cancels", "close_issues",
    ],
    "military_external": [
        "army_delta", "new_armies", "power_updates", "world_advance",
    ],
    "personnel_secret": [
        "office_changes", "appointments", "character_status_changes",
        "character_power_changes", "secret_order_updates",
        "secret_order_closes",
    ],
}

# 4 档房 prompt 文件名
TIER_PROMPTS: Dict[str, str] = {
    "internal": "score_extractor_internal",
    "issues": "score_extractor_issues",
    "military_external": "score_extractor_military_external",
    "personnel_secret": "score_extractor_personnel_secret",
}

# v4 backup prompt (失败回退用)
V4_BACKUP_PROMPT = "score_extractor_v4_backup"

# 档房执行顺序 (按依赖: 内部 → 局势 → 军外 → 人事)
TIER_ORDER = ["internal", "issues", "military_external", "personnel_secret"]


# ════════════════════════════════════════════════════════════════
# 20 字段 JSON 骨架
# ════════════════════════════════════════════════════════════════

def make_empty_20_field() -> Dict[str, Any]:
    """创建 20 字段空骨架 (供合并用)"""
    result: Dict[str, Any] = {}
    for tier in TIER_ORDER:
        for field_name in TIER_FIELDS[tier]:
            # 标量字段 → {}; 列表字段 → []
            if field_name in ("metric_delta", "faction_delta", "class_delta",
                              "region_delta", "army_delta", "power_updates",
                              "world_advance"):
                result[field_name] = {}
            else:
                result[field_name] = []
    return result


# ════════════════════════════════════════════════════════════════
# 5 档房 Agent 工厂 (含 tier 参数)
# ════════════════════════════════════════════════════════════════

def _create_tier_agent(tier: str, game_content: Any) -> Any:
    """为指定档房创建 Agent (使用对应 prompt + tier 标识)

    Args:
        tier: "internal" / "issues" / "military_external" / "personnel_secret"
        game_content: GameContent 实例 (含 load_prompt)

    Returns:
        Agno Agent 实例
    """
    import os as _os
    from han_sim.llm_config import load_llm_config
    from han_sim.llm_model import create_chat_model
    from agno.agent import Agent

    _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
    cfg = load_llm_config(
        base_url="https://api.minimaxi.com/v1",
        model="MiniMax-M2.5",
        api_key=_api_key,
        timeout_seconds=120.0,
    )

    # 加载档房 prompt + 共享规则 + game_world
    tier_prompt_name = TIER_PROMPTS[tier]
    if hasattr(game_content, "load_prompt"):
        tier_prompt = game_content.load_prompt(tier_prompt_name)
        shared_prompt = game_content.load_prompt("score_extractor_shared")
        game_world = (game_content.load_prompt("game_world")
                      if hasattr(game_content, "load_prompt") else "")
    else:
        tier_prompt = ""
        shared_prompt = ""
        game_world = ""

    full_prompt_parts = [p for p in [game_world, shared_prompt, tier_prompt] if p]

    return Agent(
        name=f"档房书办-{tier}",
        id=f"score-extractor-{tier}",
        session_id=f"score-extractor-{tier}",
        model=create_chat_model(cfg, temperature=0.1, top_p=0.7,
                                enable_thinking=False, force_json_output=True),
        instructions=full_prompt_parts,
        add_history_to_context=False,
        markdown=False,
    )


# ════════════════════════════════════════════════════════════════
# 档房 LLM 调用 + JSON 解析
# ════════════════════════════════════════════════════════════════

def _call_tier_and_parse(
    tier: str,
    narrative: str,
    decree_text: str,
    ctx: Dict[str, Any],
    game_content: Any,
    max_retries: int = 1,
) -> Dict[str, Any]:
    """调用指定档房 LLM, 解析输出 JSON

    Args:
        tier: 档房名
        narrative: 月末奏章原文
        decree_text: 皇帝本回合诏书全文
        ctx: 上下文 dict (含 regions/armies/active_issues/secret_orders 等)
        game_content: GameContent 实例
        max_retries: 失败重试次数 (默认 1)

    Returns:
        dict: 该档房负责的字段; 失败时返回 {"_error": "...", "_tier": tier}
    """
    user_input = {
        "tier": tier,
        "narrative": narrative,
        "decree_text": decree_text,
        "context": ctx,
    }
    user_prompt = json.dumps(user_input, ensure_ascii=False, indent=2)

    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            agent = _create_tier_agent(tier, game_content)
            from han_sim.agents import extract_agent_text
            text = extract_agent_text(agent.run(user_prompt))
            data = _parse_json_safely(text, tier)
            if "_error" not in data:
                return _filter_to_tier_fields(data, tier)
            last_error = data["_error"]
            logger.warning(f"[{tier}] 档房 LLM 返回错误: {last_error} (尝试 {attempt+1}/{max_retries+1})")
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning(f"[{tier}] 档房异常: {last_error} (尝试 {attempt+1}/{max_retries+1})")

    return {
        "_error": last_error or f"{tier} 档房失败",
        "_tier": tier,
        "_fallback": True,
    }


def _parse_json_safely(text: str, tier: str) -> Dict[str, Any]:
    """安全解析 LLM 输出为 JSON

    错误处理:
    - 空字符串 → {"_error": "empty"}
    - 非 dict → {"_error": "not_dict"}
    - 缺字段 → 自动补默认 (空 dict / 空 list)
    - 字段所有权外字段 → 删除 (不混入)
    """
    if not text or not text.strip():
        return {"_error": f"{tier}: LLM 输出为空"}

    # 尝试剥 ```json ``` 包裹
    cleaned = text.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(1).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {"_error": f"{tier}: JSON 解析失败 - {e}"}

    if not isinstance(data, dict):
        return {"_error": f"{tier}: 输出不是 dict"}

    return data


def _filter_to_tier_fields(data: Dict[str, Any], tier: str) -> Dict[str, Any]:
    """过滤: 只保留该档房负责的字段 (字段所有权铁律)"""
    allowed = set(TIER_FIELDS[tier])
    return {k: v for k, v in data.items() if k in allowed}


# ════════════════════════════════════════════════════════════════
# v4 Backup 回退 (单体 311 行 prompt 一次性抽全部 20 字段)
# ════════════════════════════════════════════════════════════════

def _fallback_v4_extract(
    narrative: str,
    decree_text: str,
    ctx: Dict[str, Any],
    game_content: Any,
) -> Dict[str, Any]:
    """v4 backup 模式: 用旧 311 行单体 prompt 一次性抽 20 字段"""
    import os as _os
    from han_sim.llm_config import load_llm_config
    from han_sim.llm_model import create_chat_model
    from han_sim.agents import extract_agent_text
    from agno.agent import Agent

    _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
    cfg = load_llm_config(
        base_url="https://api.minimaxi.com/v1",
        model="MiniMax-M2.5",
        api_key=_api_key,
        timeout_seconds=120.0,
    )

    if hasattr(game_content, "load_prompt"):
        v4_prompt = game_content.load_prompt(V4_BACKUP_PROMPT)
        game_world = game_content.load_prompt("game_world")
    else:
        v4_prompt = ""
        game_world = ""

    user_input = {
        "narrative": narrative,
        "decree_text": decree_text,
        "context": ctx,
    }
    user_prompt = json.dumps(user_input, ensure_ascii=False, indent=2)

    try:
        agent = Agent(
            name="档房书办-v4backup",
            id="score-extractor-v4backup",
            session_id="score-extractor-v4backup",
            model=create_chat_model(cfg, temperature=0.1, top_p=0.7,
                                    enable_thinking=False, force_json_output=True),
            instructions=[p for p in [game_world, v4_prompt] if p],
            add_history_to_context=False,
            markdown=False,
        )
        text = extract_agent_text(agent.run(user_prompt))
        data = _parse_json_safely(text, "v4backup")
        if "_error" in data:
            return data
        # v4 backup 输出应该是 20 字段, 验证
        return _ensure_all_20_fields(data)
    except Exception as e:
        return {
            "_error": f"v4backup 也失败: {type(e).__name__}: {e}",
            "_fallback": True,
        }


def _ensure_all_20_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """确保 20 字段都出现, 缺则填默认值"""
    empty = make_empty_20_field()
    for k, v in empty.items():
        if k not in data:
            data[k] = v
    return data


# ════════════════════════════════════════════════════════════════
# 4 档房串行串联 + 合并 + 失败回退 (主入口)
# ════════════════════════════════════════════════════════════════

def extract_score(
    narrative: str,
    decree_text: str = "",
    ctx: Optional[Dict[str, Any]] = None,
    game_content: Any = None,
    parallel: bool = False,
) -> Dict[str, Any]:
    """5 档房串联抽取主入口 (v5.0 P0-1)

    Args:
        narrative: 月末奏章原文 (推演官写的邸报)
        decree_text: 皇帝本回合诏书全文
        ctx: 上下文 dict (含 regions/armies/active_issues/secret_orders 等)
        game_content: GameContent 实例 (含 load_prompt)
        parallel: 是否并行调用 4 档房 (默认 False 串行)

    Returns:
        dict: 20 字段 JSON, 字段所有权严格分离; 失败回退后字段可能混合
        失败时: {"_error": "...", "_fallback": true}
    """
    ctx = ctx or {}

    # 获取 game_content (如未传, 尝试从 context 获取)
    if game_content is None:
        try:
            from han_sim.agents import _ctx
            game_content = _ctx()
        except Exception:
            game_content = None

    if game_content is None:
        return {"_error": "无法获取 game_content (load_prompt 来源)", "_fallback": True}

    t0 = time.time()
    tier_results: Dict[str, Dict[str, Any]] = {}

    if parallel:
        # 并行模式 (asyncio)
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                async def _run_all():
                    return await asyncio.gather(*[
                        asyncio.to_thread(_call_tier_and_parse, tier,
                                          narrative, decree_text, ctx, game_content)
                        for tier in TIER_ORDER
                    ])
                results = loop.run_until_complete(_run_all())
                for tier, res in zip(TIER_ORDER, results):
                    tier_results[tier] = res
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"并行模式失败, 降级为串行: {e}")
            parallel = False

    if not parallel:
        # 串行模式
        for tier in TIER_ORDER:
            tier_results[tier] = _call_tier_and_parse(
                tier, narrative, decree_text, ctx, game_content,
            )

    # 检查哪些档房失败
    failed_tiers = [t for t, r in tier_results.items() if "_error" in r]
    success_tiers = [t for t, r in tier_results.items() if "_error" not in r]

    # 合并 20 字段
    merged = make_empty_20_field()
    for tier, result in tier_results.items():
        if "_error" not in result:
            for k, v in result.items():
                if k in merged:
                    merged[k] = v

    elapsed = time.time() - t0
    logger.info(
        f"score_pipeline: 成功 {len(success_tiers)}/4 档房, "
        f"失败 {failed_tiers or '无'}, 耗时 {elapsed:.2f}s"
    )

    # 全部失败 → 完整 v4 backup 回退
    if len(failed_tiers) == 4:
        logger.warning("4 档房全部失败, 启用 v4 backup 回退")
        v4_result = _fallback_v4_extract(narrative, decree_text, ctx, game_content)
        if "_error" in v4_result:
            v4_result["_all_failed"] = True
        return v4_result

    # 部分失败 → 标记 partial, 仍返回成功部分
    if failed_tiers:
        merged["_partial"] = True
        merged["_failed_tiers"] = failed_tiers

    return merged


# ════════════════════════════════════════════════════════════════
# 兼容 v4.9 API: extract_score_simple (单 prompt 模式, 等价旧版)
# ════════════════════════════════════════════════════════════════

def extract_score_simple(
    narrative: str,
    decree_text: str = "",
    ctx: Optional[Dict[str, Any]] = None,
    game_content: Any = None,
) -> Dict[str, Any]:
    """v4.9 兼容: 直接调 v4 backup prompt 抽 20 字段 (旧版行为)"""
    ctx = ctx or {}
    if game_content is None:
        try:
            from han_sim.agents import _ctx
            game_content = _ctx()
        except Exception:
            game_content = None
    if game_content is None:
        return {"_error": "无法获取 game_content"}
    return _fallback_v4_extract(narrative, decree_text, ctx, game_content)


# ════════════════════════════════════════════════════════════════
# 调试辅助
# ════════════════════════════════════════════════════════════════

def get_tier_summary() -> Dict[str, Any]:
    """返回 4 档房配置摘要 (调试用)"""
    return {
        "tier_order": TIER_ORDER,
        "tier_fields": TIER_FIELDS,
        "tier_prompts": TIER_PROMPTS,
        "v4_backup_prompt": V4_BACKUP_PROMPT,
        "total_fields": sum(len(v) for v in TIER_FIELDS.values()),
    }


if __name__ == "__main__":
    # 自测: 打印配置
    import json as _json
    print(_json.dumps(get_tier_summary(), ensure_ascii=False, indent=2))
