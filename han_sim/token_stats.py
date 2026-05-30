"""Token 用量统计：monkey-patch openai client 抓取每次 completion 的 usage。L1。

TOKEN_STATS 是进程级遥测，留模块级单例。
_TOKEN_PATCH_INSTALLED 守卫保证补丁只打一次。
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict

TOKEN_STATS: Dict[str, Dict[str, int]] = {}
_TOKEN_PATCH_INSTALLED = False


def ts() -> str:
    now = datetime.now()
    return now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"


def tlog(msg: str) -> None:
    print(f"[{ts()}] {msg}", flush=True)


def _guess_caller_tag(kwargs: Dict[str, object]) -> str:
    """从 messages 的所有 system 段拼合后猜哪个 agent 在调用。"""
    messages = kwargs.get("messages") or []
    sys_text = ""
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") != "system":
            continue
        c = msg.get("content")
        if isinstance(c, str):
            sys_text += c
        elif isinstance(c, list):
            for item in c:
                if isinstance(item, dict):
                    sys_text += str(item.get("text", ""))
    if "召对" in sys_text or "模拟" in sys_text:
        return "minister"
    if "拟旨" in sys_text or "诏书" in sys_text:
        return "decree-writer"
    if "推演" in sys_text or "日讲" in sys_text:
        return "simulator"
    if "记忆" in sys_text or "档房" in sys_text:
        return "memory-extractor"
    if "评分" in sys_text or "抽取" in sys_text:
        return "extractor"
    return "?"


def _record_usage(model_id: str, usage: object, caller_tag: str = "?") -> None:
    if usage is None:
        return
    bucket = TOKEN_STATS.setdefault(
        model_id,
        {"calls": 0, "prompt": 0, "completion": 0, "cached": 0, "reasoning": 0, "total": 0},
    )
    prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion = int(getattr(usage, "completion_tokens", 0) or 0)
    total = int(getattr(usage, "total_tokens", prompt + completion) or 0)
    prompt_details = getattr(usage, "prompt_tokens_details", None)
    cached = int(getattr(prompt_details, "cached_tokens", 0) or 0) if prompt_details else 0
    completion_details = getattr(usage, "completion_tokens_details", None)
    reasoning = int(getattr(completion_details, "reasoning_tokens", 0) or 0) if completion_details else 0
    bucket["calls"] += 1
    bucket["prompt"] += prompt
    bucket["completion"] += completion
    bucket["cached"] += cached
    bucket["reasoning"] += reasoning
    bucket["total"] += total
    print(
        f"[TOKEN] caller={caller_tag} model={model_id} prompt={prompt} cached={cached} "
        f"completion={completion} reasoning={reasoning} total={total}",
        flush=True,
    )


def _get_client_base_url(self_client_holder: object) -> str:
    """从 openai Completions self 拿 client.base_url。"""
    try:
        client = getattr(self_client_holder, "_client", None)
        if client is None:
            return ""
        base = getattr(client, "base_url", "")
        return str(base) if base else ""
    except Exception:
        return ""


def _inject_cache_mark(kwargs: Dict[str, object]) -> None:
    """对请求注入 cache_control 显式缓存标记。"""
    messages = kwargs.get("messages")
    if not isinstance(messages, list):
        return
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        if msg.get("role") != "system":
            continue
        content = msg.get("content")
        if isinstance(content, str) and len(content) >= 800:
            msg["content"] = [{
                "type": "text",
                "text": content,
                "cache_control": {"type": "ephemeral"},
            }]
        elif isinstance(content, list) and content:
            last = content[-1]
            if isinstance(last, dict) and "cache_control" not in last:
                last["cache_control"] = {"type": "ephemeral"}
        break  # 只标第一条 system


def install_token_stats_patch() -> None:
    """Monkey-patch openai client to capture usage on every chat completion."""
    global _TOKEN_PATCH_INSTALLED
    if _TOKEN_PATCH_INSTALLED:
        return
    try:
        from openai.resources.chat.completions import Completions, AsyncCompletions  # type: ignore
    except Exception:
        return
    orig_create = Completions.create
    orig_acreate = AsyncCompletions.create

    def patched_create(self, *args, **kwargs):
        base_url = _get_client_base_url(self)
        caller_tag = _guess_caller_tag(kwargs)
        if "minimax" in base_url.lower() or "ark" in base_url.lower():
            _inject_cache_mark(kwargs)
        resp = orig_create(self, *args, **kwargs)
        try:
            model_id = getattr(resp, "model", kwargs.get("model", "unknown"))
            _record_usage(model_id, getattr(resp, "usage", None), caller_tag)
        except Exception:
            pass
        return resp

    async def patched_acreate(self, *args, **kwargs):
        base_url = _get_client_base_url(self)
        caller_tag = _guess_caller_tag(kwargs)
        if "minimax" in base_url.lower() or "ark" in base_url.lower():
            _inject_cache_mark(kwargs)
        resp = await orig_acreate(self, *args, **kwargs)
        try:
            model_id = getattr(resp, "model", kwargs.get("model", "unknown"))
            _record_usage(model_id, getattr(resp, "usage", None), caller_tag)
        except Exception:
            pass
        return resp

    Completions.create = patched_create  # type: ignore
    AsyncCompletions.create = patched_acreate  # type: ignore
    _TOKEN_PATCH_INSTALLED = True


def print_token_summary() -> None:
    if not TOKEN_STATS:
        print("[TOKEN-SUMMARY] no LLM calls captured")
        return
    print("\n========== TOKEN USAGE SUMMARY ==========")
    grand: Dict[str, int] = {}
    for model_id, bucket in TOKEN_STATS.items():
        hit_rate = (bucket["cached"] / bucket["prompt"] * 100) if bucket["prompt"] else 0
        print(
            f"  {model_id}: calls={bucket['calls']} prompt={bucket['prompt']} "
            f"cached={bucket['cached']} ({hit_rate:.1f}%) completion={bucket['completion']} "
            f"reasoning={bucket['reasoning']} total={bucket['total']}"
        )
        for key, value in bucket.items():
            grand[key] = grand.get(key, 0) + int(value)
    grand_hit = (grand.get("cached", 0) / grand.get("prompt", 0) * 100) if grand.get("prompt") else 0
    print(
        f"  TOTAL: calls={grand.get('calls',0)} prompt={grand.get('prompt',0)} "
        f"cached={grand.get('cached',0)} ({grand_hit:.1f}%) completion={grand.get('completion',0)} "
        f"reasoning={grand.get('reasoning',0)} total={grand.get('total',0)}"
    )
    print("=========================================")