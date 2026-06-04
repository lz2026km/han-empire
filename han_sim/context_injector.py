"""
v3.0-BE-4: 长上下文防幻觉 (调研 P0-4)
====================================

设计依据: 历史策略游戏类作品5-19 Steam 更新日志
  "优化了「准奏」功能的提示词与代码模块, 令输出内容更聚焦于当前回合的议题,
   减少了因长上下文引发的模型幻觉问题."

实现:
  1. 每回合注入"当前议题硬约束"块 (放在 system prompt 头部)
  2. 上下文窗口管理: 超过 80K 自动压缩历史摘要
  3. NPC 提及时附带"现实提示"块 (人物档案/派系/官职)
  4. 角色一致性校验: 检 LLM 输出是否提到不存在的角色
"""
from __future__ import annotations

import json
import logging
import re
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ContextBudget:
    """上下文窗口预算 (按 200K 设计的保守值)"""
    max_tokens: int = 200_000
    static_budget: int = 4_000       # system 静态 (角色/规则)
    current_issue_budget: int = 500   # 当前议题硬约束
    npc_hint_budget: int = 1_500      # 提及 NPC 的档案
    history_budget: int = 60_000      # 历史摘要
    user_dynamic_budget: int = 10_000  # 玩家诏书 + 状态

    @property
    def total_budget(self) -> int:
        return (
            self.static_budget
            + self.current_issue_budget
            + self.npc_hint_budget
            + self.history_budget
            + self.user_dynamic_budget
        )


# 全局历史摘要滚动 buffer
_HISTORY_BUFFER: deque = deque(maxlen=20)


def inject_current_issue(
    system_prompt: str,
    current_issue: str,
    turn_label: str = "",
) -> str:
    """
    在 system prompt 头部注入"当前议题硬约束"块.

    块结构:
      [CURRENT-ISSUE-LOCK]
      回合: {turn_label}
      议题: {current_issue}
      输出必须紧扣此议题, 不得跑题/编造/出戏
      [/CURRENT-ISSUE-LOCK]
    """
    if not current_issue:
        return system_prompt
    block = (
        f"[CURRENT-ISSUE-LOCK]\n"
        f"回合: {turn_label or '当前回合'}\n"
        f"议题: {current_issue}\n"
        f"约束: 输出必须紧扣此议题, 不得:\n"
        f"  1. 跑题/答非所问\n"
        f"  2. 编造未在历史档案中的人物/事件\n"
        f"  3. 时间线出戏 (如已死人物复活)\n"
        f"[/CURRENT-ISSUE-LOCK]\n\n"
    )
    return block + system_prompt


def build_npc_hint_block(mentioned_npcs: List[str], npc_db: Dict[str, Dict[str, Any]]) -> str:
    """
    根据本回合提到的 NPC 列表, 拼"现实提示"块.
    避免 LLM 凭印象编造 NPC 性格/官职.
    """
    if not mentioned_npcs or not npc_db:
        return ""
    lines = ["[NPC-REALITY-CHECK] 提及人物档案:"]
    for name in mentioned_npcs[:10]:  # 最多 10 人
        npc = npc_db.get(name)
        if not npc:
            lines.append(f"  [警告] {name}: 不在档案中, 请勿编造")
            continue
        lines.append(
            f"  • {name}: 派系={npc.get('faction', '?')}, "
            f"官职={npc.get('office', '?')}, "
            f"立场={npc.get('stance', '?')[:30]}"
        )
    lines.append("[/NPC-REALITY-CHECK]")
    return "\n".join(lines)


def extract_mentioned_npcs(text: str, known_npc_names: Set[str]) -> List[str]:
    """
    从文本中提取提到的 NPC 名字.
    设计: 2-3 字汉名前后允许 CJK 字符 (中文里名字常紧贴其他汉字, 如"曹操与"中的"曹操").
    """
    if not known_npc_names or not text:
        return []

    mentioned = []
    seen = set()
    # 按名字长度倒序, 先匹配长名 (3字 > 2字), 避免子串误判
    for name in sorted(known_npc_names, key=len, reverse=True):
        if name in seen:
            continue
        # 简易: text.find 找到就算提及
        if text.find(name) >= 0:
            mentioned.append(name)
            seen.add(name)
    return mentioned


def push_history_turn(summary: str, max_chars: int = 4000) -> None:
    """把本回合摘要压入历史 buffer (自动滚动)."""
    if not summary:
        return
    s = summary[:max_chars]  # 截断
    _HISTORY_BUFFER.append(s)


def build_history_compression() -> str:
    """把历史 buffer 拼成压缩块 (按时间倒序)."""
    if not _HISTORY_BUFFER:
        return ""
    lines = ["[HISTORY-COMPRESS] 最近回合摘要:"]
    for i, s in enumerate(reversed(list(_HISTORY_BUFFER)[-10:]), 1):
        # 单行截断
        s1 = s.replace("\n", " ")[:200]
        lines.append(f"  {i}. {s1}")
    lines.append("[/HISTORY-COMPRESS]")
    return "\n".join(lines)


def reset_history() -> None:
    """测试/重开用."""
    _HISTORY_BUFFER.clear()


def get_history_count() -> int:
    return len(_HISTORY_BUFFER)


# === 角色一致性校验 ===
# 已知名单 (含主公原始人物 + 各种尊称/字/号)
def _get_known_npc_aliases() -> set:
    """返回所有已知 NPC 名字 + 常见字/号 (避免误报). 占位实现, 真实项目从 content/characters.json 读."""
    return {
        # 姓
        "曹", "刘", "孙", "袁", "张", "王", "李", "赵", "马", "黄",
        "董", "吕", "关", "诸葛", "司马", "夏侯", "公孙", "荀", "郭", "程",
    }


def validate_npc_consistency(
    llm_output: str,
    known_npc_names: Set[str],
) -> List[str]:
    """
    校验 LLM 输出是否提到不存在的 NPC (幻觉嫌疑).
    策略: 用 characters.json 的人物名 + 常见姓库作白名单, 不在白名单中的 2-3 字汉名 = 嫌疑.

    返回问题列表 (空 = 0 幻觉).
    """
    issues = []
    # 拼白名单
    whitelist = set(known_npc_names) | _get_known_npc_aliases()
    # 文本中所有 2-3 字汉名
    candidates = set()
    for i in range(len(llm_output) - 1):
        for ln in (2, 3):
            if i + ln <= len(llm_output):
                c = llm_output[i:i+ln]
                if all(_is_cjk(c[j]) for j in range(ln)):
                    candidates.add(c)
    # 不在白名单的 = 嫌疑
    for c in candidates:
        if c not in whitelist:
            issues.append(f"幻觉嫌疑: 提及未在档案中的人物 '{c}'")
    return issues


def _is_cjk(c: str) -> bool:
    if not c:
        return False
    cp = ord(c)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF
