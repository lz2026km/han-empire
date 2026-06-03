"""v1.16.0 乾坤大挪移 Phase E · 候选情势判选官模块。

功能：
- judge_candidates：程序内 quick_check → LLM 软筛 → 越界校验 → 返回 fire 列表
- 退避机制：连续 hold 3 次 → 强制 fire
- 缓存：同盘面 24h 复用判选结果
- 降级：LLM 失败 → 全量 fire（保守）

底册依据：docs/game-bible-localization-plan.md §2 (115-238 行)
"""

import json
import hashlib
import time
from typing import List, Dict, Optional, Tuple, Set

from han_sim.models import Event, GameState
from han_sim.db import GameDB


_CACHE: Dict[str, Tuple[float, List[str]]] = {}  # cache_key -> (ts, fired_ids)
_CACHE_TTL_SECONDS = 24 * 3600
_MAX_HOLD_BEFORE_FORCE_FIRE = 3  # 底册 §2.4 退避


# ════════════════════════════════════════════════════════════════
# 程序内 quick_check（毫秒级，0 LLM 调用）
# ════════════════════════════════════════════════════════════════

def _quick_check(state: GameState, candidate: Event, db: GameDB) -> bool:
    """程序内快筛：返回 True 表示通过因果预判，False 表示明显该 hold。

    判据：
    1. active_issues ≥ 8 → 任何非 severity≥5 的候选都 hold
    2. urgency=0 → hold
    3. 汉末节点：董卓未死时王允相关 hold；曹操未控许时迎帝相关 hold
    """
    # 1. 喘息窗口
    try:
        active = db.list_active_issues()
        if len(active) >= 8 and candidate.severity < 5:
            return False
    except Exception:
        pass

    # 2. urgency=0
    if candidate.urgency <= 0:
        return False

    # 3. 汉末节点（最简版本 — 完整规则交给 LLM 软筛）
    cid = candidate.id.lower()
    if "dongzhuo" in cid and state.year < 192:
        return False  # 董卓未死
    if "caocao" in cid and "y..." in cid and state.year < 196:
        return False  # 曹操未控许

    return True


# ════════════════════════════════════════════════════════════════
# LLM 软筛
# ════════════════════════════════════════════════════════════════

def _build_input_json(state: GameState, db: GameDB, candidates: List[Event]) -> Dict:
    """构造 6 字段输入（底册 §2.2）。"""
    # period
    period = {
        "year": getattr(state, "year", 190),
        "month": getattr(state, "month", 1),
        "turn": getattr(state, "turn", 1),
    }

    # metrics
    metrics = getattr(state, "metrics", {}) or {}

    # active_issues（最多 10 条，简化）
    active_issues = []
    try:
        for row in db.list_active_issues()[:10]:
            active_issues.append({
                "id": row.get("id", row.get("issue_id", "")),
                "title": row.get("title", ""),
                "bar": row.get("bar", 0),
                "stage": row.get("stage", ""),
                "urgency": row.get("urgency", 0),
                "severity": row.get("severity", 0),
            })
    except Exception:
        pass

    # powers（势力态势 - 简化）
    powers = []
    try:
        warlord_keys = ["董卓", "袁绍", "曹操", "孙权", "刘备", "公孙", "吕布"]
        for name in warlord_keys:
            try:
                w = db.get_warlord(name)
                if w:
                    powers.append({
                        "name": name,
                        "controlled_regions": w.get("controlled_regions", []),
                        "military_strength": w.get("military_strength", 0),
                        "relation_to_emperor": w.get("relation_to_emperor", "未知"),
                    })
            except Exception:
                pass
    except Exception:
        pass

    # regions_hot（最危险的 5 州郡）
    regions_hot = []
    try:
        for r in db.list_regions()[:5]:
            regions_hot.append({
                "region": r.get("name", r.get("id", "")),
                "unrest": r.get("unrest", 0),
                "grain_security": r.get("grain_security", 0),
                "gentry_resistance": r.get("gentry_resistance", 0),
            })
    except Exception:
        pass

    # candidates
    cand_list = []
    for ev in candidates:
        cand_list.append({
            "id": ev.id,
            "title": ev.title,
            "kind": ev.kind,
            "summary": ev.summary,
            "interests": getattr(ev, "interests", []) or [],
            "urgency": ev.urgency,
            "severity": ev.severity,
        })

    return {
        "period": period,
        "metrics": metrics,
        "active_issues": active_issues,
        "powers": powers,
        "regions_hot": regions_hot,
        "candidates": cand_list,
    }


def _parse_judge_response(raw_text: str, candidate_ids: List[str]) -> Tuple[List[str], List[str]]:
    """解析 LLM JSON 输出，严格校验越界。

    返回：(fire_ids, hold_ids)。每条 candidate 必在 fire/hold 之一。
    """
    # 解析 JSON（防御性）
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # 尝试提取 {...}
        import re
        m = re.search(r'\{[\s\S]*\}', raw_text)
        if not m:
            raise ValueError("LLM 输出无法解析为 JSON")
        data = json.loads(m.group(0))

    fire = data.get("fire", [])
    hold = data.get("hold", [])

    fire_ids = []
    hold_ids = []

    cand_set = set(candidate_ids)
    seen = set()

    for item in fire:
        cid = item.get("id", "") if isinstance(item, dict) else str(item)
        if cid in cand_set and cid not in seen:
            fire_ids.append(cid)
            seen.add(cid)

    for item in hold:
        cid = item.get("id", "") if isinstance(item, dict) else str(item)
        if cid in cand_set and cid not in seen:
            hold_ids.append(cid)
            seen.add(cid)

    # 校验：每条 candidate 必在 fire/hold 之一
    missing = [c for c in candidate_ids if c not in seen]
    if missing:
        # 缺失的默认 hold（保守）
        hold_ids.extend(missing)

    return fire_ids, hold_ids


def _llm_judge(state: GameState, db: GameDB, candidates: List[Event]) -> Optional[List[str]]:
    """调 LLM 判选。失败返 None（外层 fallback 到全量 fire）。

    Returns:
        List of candidate.id that should fire. None 表示 LLM 失败。
    """
    try:
        from han_sim.agents import create_event_selector_agent
        from han_sim.content import _ctx as content_ctx

        agent = create_event_selector_agent()
        input_data = _build_input_json(state, db, candidates)
        input_text = json.dumps(input_data, ensure_ascii=False, indent=2)

        # Agno agent.run 是同步/异步双接口
        response = agent.run(input_text)
        # 提取文本
        if hasattr(response, "content"):
            raw = response.content
        elif isinstance(response, str):
            raw = response
        else:
            raw = str(response)

        fire_ids, hold_ids = _parse_judge_response(raw, [ev.id for ev in candidates])
        return fire_ids
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════
# 缓存 + 退避
# ════════════════════════════════════════════════════════════════

def _cache_key(state: GameState, candidate_ids: List[str]) -> str:
    """生成缓存 key（盘面状态指纹）。"""
    fingerprint = {
        "year": getattr(state, "year", 0),
        "period": getattr(state, "period", 0),
        "turn": getattr(state, "turn", 0),
        "metrics": getattr(state, "metrics", {}),
        "candidates": sorted(candidate_ids),
    }
    raw = json.dumps(fingerprint, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def _check_cache(key: str) -> Optional[List[str]]:
    if key in _CACHE:
        ts, fired = _CACHE[key]
        if time.time() - ts < _CACHE_TTL_SECONDS:
            return fired
        else:
            del _CACHE[key]
    return None


def _store_cache(key: str, fired: List[str]) -> None:
    _CACHE[key] = (time.time(), fired)


# ════════════════════════════════════════════════════════════════
# 公开 API
# ════════════════════════════════════════════════════════════════

def judge_candidates(state: GameState, db: GameDB, candidates: List[Event], campaign_id: str = "default") -> List[str]:
    """同步判选入口（内含 LLM 调用的同步包装）。

    Args:
        state: 当前游戏状态
        db: 数据库
        candidates: 程序硬筛后的候选情势
        campaign_id: 战役 ID（汉献帝版用 "default"，v1.18.0 多战役可扩展）

    Returns:
        List of candidate.id that should fire this round.
        LLM 失败时返全量（保守降级）。
    """
    if not candidates:
        return []

    candidate_ids = [ev.id for ev in candidates]

    # 1. 缓存检查
    key = _cache_key(state, candidate_ids)
    cached = _check_cache(key)
    if cached is not None:
        return cached

    # 2. 退避机制：连续 hold 3 次的强制 fire
    force_fire = []
    for ev in candidates:
        try:
            hold_count = db.get_hold_count(campaign_id, ev.id)
            if hold_count >= _MAX_HOLD_BEFORE_FORCE_FIRE:
                force_fire.append(ev.id)
        except Exception:
            pass

    if force_fire:
        # 全强制 fire
        _store_cache(key, force_fire)
        for ev_id in force_fire:
            try:
                db.reset_hold(campaign_id, ev_id)
            except Exception:
                pass
        return force_fire

    # 3. LLM 软筛
    fired = _llm_judge(state, db, candidates)
    if fired is None:
        # LLM 失败 → 全量 fire
        fired = candidate_ids

    # 4. 更新 hold 计数
    for ev in candidates:
        try:
            if ev.id in fired:
                db.reset_hold(campaign_id, ev.id)
            else:
                db.increment_hold(campaign_id, ev.id, getattr(state, "turn", 0))
        except Exception:
            pass

    # 5. 缓存
    _store_cache(key, fired)

    return fired


def clear_cache() -> int:
    """清空缓存（用于测试）。"""
    n = len(_CACHE)
    _CACHE.clear()
    return n
