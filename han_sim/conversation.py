"""对话历史管理：多轮上下文持久化。L4。

为每个 campaign 的每次召见维护完整对话历史，
使大臣能够在多轮对话中记住之前的上下文。

表设计：
  conversation_history(campaign_id, minister_name, role, content, turn, period)
  — role: 'emperor' | 'minister'
"""

from dataclasses import dataclass
from typing import List, Optional

from han_sim.db import GameDB


@dataclass
class ChatMessage:
    role: str          # 'emperor' | 'minister'
    content: str
    turn: int
    period: int


# ── 表初始化 ────────────────────────────────────────────────────────────────

INIT_SQL = """
CREATE TABLE IF NOT EXISTS conversation_history(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT    NOT NULL,
    minister_name TEXT  NOT NULL,
    role        TEXT    NOT NULL,   -- 'emperor' | 'minister'
    content     TEXT    NOT NULL,
    turn        INTEGER NOT NULL,
    period      INTEGER NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conv_campaign
    ON conversation_history(campaign_id, minister_name, turn);
"""


def init_conv_table(db: GameDB) -> None:
    db.conn.executescript(INIT_SQL)
    db.conn.commit()


# ── 读写 ──────────────────────────────────────────────────────────────────

def save_message(
    db: GameDB,
    campaign_id: str,
    minister_name: str,
    role: str,
    content: str,
    turn: int,
    period: int,
) -> None:
    db.conn.execute(
        """
        INSERT INTO conversation_history
            (campaign_id, minister_name, role, content, turn, period)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (campaign_id, minister_name, role, content, turn, period),
    )
    db.conn.commit()


def load_conversation(
    db: GameDB,
    campaign_id: str,
    minister_name: str,
    limit: int = 20,
) -> List[ChatMessage]:
    rows = db.conn.execute(
        """
        SELECT role, content, turn, period
          FROM conversation_history
         WHERE campaign_id=? AND minister_name=?
         ORDER BY id ASC
         LIMIT ?
        """,
        (campaign_id, minister_name, limit),
    ).fetchall()
    return [
        ChatMessage(role=r[0], content=r[1], turn=r[2], period=r[3])
        for r in rows
    ]


def clear_conversation(
    db: GameDB,
    campaign_id: str,
    minister_name: str,
) -> None:
    db.conn.execute(
        "DELETE FROM conversation_history WHERE campaign_id=? AND minister_name=?",
        (campaign_id, minister_name),
    )
    db.conn.commit()


def build_context_prompt(messages: List[ChatMessage]) -> str:
    """从历史消息构建上下文 prompt，供 agent system prompt 使用。"""
    if not messages:
        return ""
    lines = []
    for m in messages:
        speaker = "天子" if m.role == "emperor" else "大臣"
        lines.append(f"{speaker}：{m.content}")
    return "\n".join(lines) + "\n"


def get_recent_exchanges(
    db: GameDB,
    campaign_id: str,
    minister_name: str,
    n: int = 6,
) -> List[ChatMessage]:
    """获取最近 N 轮对话（每轮包含天子+大臣两条）。"""
    rows = db.conn.execute(
        """
        SELECT role, content, turn, period
          FROM conversation_history
         WHERE campaign_id=? AND minister_name=?
         ORDER BY id DESC
         LIMIT ?
        """,
        (campaign_id, minister_name, n * 2),
    ).fetchall()
    # 反转回来，按时间正序
    result = [
        ChatMessage(role=r[0], content=r[1], turn=r[2], period=r[3])
        for r in reversed(rows)
    ]
    return result