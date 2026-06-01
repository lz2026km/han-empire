# -*- mode: python ; coding: utf-8 -*-
"""
汉献帝之末路 - 公共工具函数
v2.0.0 Phase 2.2: 从 tools.py / flows.py / decree.py 抽公共函数

统一收口"字符串处理 / 角色查找 / 职责地点"等跨模块复用逻辑。
"""
from __future__ import annotations

import difflib
import re
from typing import Dict, List, Optional


def normalize_person_name(text: str) -> str:
    """去除所有空白，便于人物名模糊匹配。

    v2.0.0 Phase 2.2: 抽自 tools.py:51
    """
    return re.sub(r"\s+", "", str(text or "").strip())


def match_character_by_name(name: str, characters: List[Dict]) -> Optional[Dict]:
    """三级匹配人物名：精确 → 包含 → 模糊（difflib）。

    v2.0.0 Phase 2.2: 抽自 tools.py:55
    返回命中的角色 dict，或 None。
    """
    key = normalize_person_name(name)
    if not key:
        return None
    # 精确匹配
    for c in characters:
        names = [c.get("name", ""), *(c.get("aliases", []) or [])]
        if any(normalize_person_name(n) == key for n in names):
            return c
    # 包含匹配
    for c in characters:
        names = [c.get("name", ""), *(c.get("aliases", []) or [])]
        if any(
            key in normalize_person_name(n) or normalize_person_name(n) in key
            for n in names
        ):
            return c
    # 模糊匹配
    choices = {c.get("name", ""): c for c in characters}
    match = difflib.get_close_matches(key, list(choices.keys()), n=1, cutoff=0.6)
    return choices[match[0]] if match else None


def duty_location(office: str, office_type: str, status: str) -> str:
    """根据官职/官职类型/状态推导人物当下应在的"职责地点"。

    v2.0.0 Phase 2.2: 抽自 tools.py:75
    规则：
      - dead → "已故，不在任事。"
      - imprisoned → "系狱待勘。"
      - dismissed/exiled/retired/offstage → "不在朝任事。"
      - office 含州名 → "按现职在X州任事。"
      - 三公/九卿/尚书等 → "按现职在朝。"
      - 太守 → "按现职为X。"
      - 刺史 → "按现职刺X。"
    """
    if status == "dead":
        return "已故，不在任事。"
    if status == "imprisoned":
        return "系狱待勘。"
    if status in {"dismissed", "exiled", "retired", "offstage"}:
        return "不在朝任事。"
    text = office or office_type
    if not text:
        return "在朝但现职未明。"
    region_markers = [
        "司隶", "豫州", "兖州", "徐州", "扬州", "荆州", "益州",
        "凉州", "并州", "幽州", "冀州", "青州",
    ]
    for marker in region_markers:
        if marker in text:
            return f"按现职在{marker}任事。"
    if office_type in {
        "三公", "九卿", "尚书", "御史", "太尉", "司徒", "司空",
        "大将军", "侍中", "散骑",
    }:
        return "按现职在朝。"
    if office_type == "太守":
        return f"按现职为{office}。"
    if office_type == "刺史":
        return f"按现职刺{office}。"
    return "按现职任事。"
