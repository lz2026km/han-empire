"""大臣 system prompt 上下文构建：记忆注入、技能绑定。L6。"""

from typing import List

from han_sim.db import GameDB
from han_sim.models import Character, CourtContext, GameState


def build_memory_brief(
    character_name: str,
    faction: str,
    office_type: str,
    turn: int,
    db: GameDB,
    limit: int = 5,
) -> str:
    """召见前注入相关旧事记忆摘要。"""
    memories = db.get_relevant_event_memories(
        character_name=character_name,
        faction=faction,
        office_type=office_type,
        turn=turn,
        limit=limit,
    )
    if not memories:
        return ""
    lines = ["【上回合旧事记忆】"]
    for m in memories:
        lines.append(
            f"- {m['year']}年{m['period']}月：{m['title']}。\n"
            f"  因：{m['cause']}。经：{m['process']}。果：{m['outcome']}。"
        )
    return "\n".join(lines)


def build_context_for_minister(
    character_name: str,
    faction: str,
    office_type: str,
    turn: int,
    db: GameDB,
    recent_memory_brief: str = "",
    secret_order_brief: str = "",
) -> str:
    """构建注入大臣 system prompt 的全部上下文。"""
    parts = []
    if recent_memory_brief:
        parts.append(recent_memory_brief)
    if secret_order_brief:
        parts.append(secret_order_brief)
    return "\n\n".join(parts)