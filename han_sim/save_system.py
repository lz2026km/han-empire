"""
v3.0-AP-2: 存档系统增强 (调研 P1-4)
====================================

设计依据: 青干《崇祯模拟器》5-19 Steam 更新日志
  "修复了部分玩家无法存档的问题. 优化了主动存档的数据逻辑,
   改为存档玩家的实时数据状态, 包括本回合推演前玩家与大臣的对话、
   快捷操作等."

实现:
  1. 5 槽位滚动 (auto + manual)
  2. 存档元数据 (时间/回合/皇帝年号/摘要)
  3. 存档恢复 (回到指定回合, 含对话上下文)
  4. 存档清理 (过期自动清)

注: server.py 已有 /api/campaigns/<id>/save /load /saves 基础端点.
    本模块增强存档元数据 + 摘要 + 清理.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


SAVE_DIR = Path("/home/admin/.openclaw/workspace/han-empire/data/saves")
MAX_SLOTS = 5  # 主公方案调研: 5 槽位


def ensure_save_dir() -> Path:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    return SAVE_DIR


def get_save_path(campaign_id: str, slot: int) -> Path:
    return ensure_save_dir() / f"{campaign_id}_slot{slot}.json"


def write_save_meta(campaign_id: str, slot: int, meta: Dict[str, Any]) -> None:
    """写存档元数据 (独立 .meta.json, 加快列表)."""
    p = get_save_path(campaign_id, slot).with_suffix(".meta.json")
    p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def read_save_meta(campaign_id: str, slot: int) -> Optional[Dict[str, Any]]:
    p = get_save_path(campaign_id, slot).with_suffix(".meta.json")
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        logger.warning("读存档 meta 失败 %s: %s", p, e)
        return None


def list_saves(campaign_id: str) -> List[Dict[str, Any]]:
    """列出 campaign 的所有存档 (含元数据)."""
    out = []
    for slot in range(1, MAX_SLOTS + 1):
        sp = get_save_path(campaign_id, slot)
        if not sp.exists():
            continue
        meta = read_save_meta(campaign_id, slot) or {}
        stat = sp.stat()
        out.append({
            "slot": slot,
            "size_bytes": stat.st_size,
            "modified_at": int(stat.st_mtime),
            **meta,
        })
    return sorted(out, key=lambda x: x["modified_at"], reverse=True)


def delete_save(campaign_id: str, slot: int) -> bool:
    """删指定槽位存档. 返回是否真删了."""
    sp = get_save_path(campaign_id, slot)
    mp = sp.with_suffix(".meta.json")
    deleted = False
    if sp.exists():
        sp.unlink()
        deleted = True
    if mp.exists():
        mp.unlink()
    return deleted


def cleanup_old_saves(campaign_id: str, keep: int = MAX_SLOTS) -> int:
    """清超出 keep 数量的旧存档. 返回清理数."""
    saves = list_saves(campaign_id)
    if len(saves) <= keep:
        return 0
    to_del = saves[keep:]  # 留 keep 个最新
    n = 0
    for s in to_del:
        if delete_save(campaign_id, s["slot"]):
            n += 1
    return n


def build_save_meta(
    turn: int,
    year: int,
    month: int,
    emperor_name: str = "汉献帝",
    summary: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """构造存档元数据."""
    return {
        "turn": turn,
        "year": year,
        "month": month,
        "emperor": emperor_name,
        "summary": summary or f"建安{year-196}年{month}月 · 第{turn}回合",
        "saved_at": int(time.time()),
        **((extra or {})),
    }
