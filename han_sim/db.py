"""SQLite 游戏数据库。L3。"""



import json
import os
import sqlite3
from typing import Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from han_sim.models import GameState

from han_sim.paths import user_data_path


class GameDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY,
                name TEXT, office TEXT, office_type TEXT, faction TEXT,
                aliases TEXT, personal_skills TEXT, loyalty INT, ability INT,
                integrity INT, courage INT, style TEXT, power_id TEXT,
                location TEXT, birth_year INT, historical_death_year INT,
                historical_death_month INT, debut_year INT, debut_month INT,
                status TEXT, summary TEXT, portrait_id TEXT
            );
            CREATE TABLE IF NOT EXISTS regions (
                id TEXT PRIMARY KEY, name TEXT, kind TEXT, population INT,
                public_support INT, unrest INT, natural_disaster TEXT,
                human_disaster TEXT, registered_land INT, hidden_land INT,
                tax_per_turn INT, grain_security INT, gentry_resistance INT,
                military_pressure INT, status TEXT, controlled_by TEXT,
                fiscal TEXT, on_restore TEXT
            );
            CREATE TABLE IF NOT EXISTS armies (
                id TEXT PRIMARY KEY, name TEXT, station TEXT, theater TEXT,
                commander TEXT, controller TEXT, troop_type TEXT, manpower INT,
                maintenance_per_turn INT, supply INT, morale INT, training INT,
                equipment INT, arrears INT, mobility INT, loyalty INT,
                status TEXT, owner_power TEXT
            );
            CREATE TABLE IF NOT EXISTS powers (
                id TEXT PRIMARY KEY, name TEXT, kind TEXT, leader TEXT,
                stance TEXT, leverage INT, satisfaction INT, military_strength INT,
                cohesion INT, supply INT, agenda TEXT, status TEXT,
                last_action TEXT, aliases TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY, title TEXT, kind TEXT, summary TEXT,
                urgency INT, severity INT, credibility INT, interests TEXT,
                audiences TEXT, resolve_condition TEXT, fail_condition TEXT,
                trigger_year INT, trigger_month INT, trigger_end_year INT,
                trigger_end_month INT, precondition TEXT, event_type TEXT,
                trigger_gate TEXT, trigger_condition TEXT
            );
            CREATE TABLE IF NOT EXISTS game_log (id INTEGER PRIMARY KEY AUTOINCREMENT, turn INT, phase TEXT, entry TEXT);
            CREATE TABLE IF NOT EXISTS event_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_type TEXT, subject_id TEXT,
                event_type TEXT, title TEXT,
                cause TEXT, process TEXT, outcome TEXT,
                sentiment TEXT DEFAULT 'neutral',
                importance INT DEFAULT 3,
                tags TEXT DEFAULT '[]',
                source_kind TEXT DEFAULT 'system',
                source_id TEXT,
                expires_turn INT,
                turn INT, year INT, period INT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS event_memory_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INT, source_kind TEXT, source_id TEXT,
                excerpt TEXT, locator TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_memories_expires ON event_memories(expires_turn);
            CREATE INDEX IF NOT EXISTS idx_memories_subject ON event_memories(subject_type, subject_id);
            CREATE INDEX IF NOT EXISTS idx_memories_turn ON event_memories(turn);
            CREATE INDEX IF NOT EXISTS idx_memories_sources_memory ON event_memory_sources(memory_id);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_dedup
                ON event_memories(subject_type, subject_id, event_type, source_kind, source_id);
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL, description TEXT,
                status TEXT DEFAULT 'active',
                proposed_by TEXT, progress INT DEFAULT 0,
                total_steps INT DEFAULT 1, current_step INT DEFAULT 0,
                deadline_turn INT, created_turn INT,
                closed_turn INT, success INT,
                origin_kind TEXT, origin_ref TEXT,
                tags TEXT DEFAULT '[]',
                cancellable TEXT DEFAULT 'never',
                ongoing_effects TEXT DEFAULT '{}',
                effect_on_resolve TEXT DEFAULT '{}',
                effect_on_fail TEXT DEFAULT '{}',
                resolve_condition TEXT, fail_condition TEXT,
                last_updated_turn INT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # ── 状态读写 ─────────────────────────────────────────────

    def save_state(self, key: str, value) -> None:
        self.conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
                         (key, json.dumps(value, ensure_ascii=False)))

    def load_state(self, key: str, default=None):
        row = self.conn.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    # ── 角色 CRUD ─────────────────────────────────────────────

    def upsert_character(self, c: dict) -> None:
        sql = (
            "INSERT OR REPLACE INTO characters VALUES ("
            ":id,:name,:office,:office_type,:faction,:aliases,:personal_skills,"
            ":loyalty,:ability,:integrity,:courage,:style,:power_id,"
            ":location,:birth_year,:historical_death_year,:historical_death_month,"
            ":debut_year,:debut_month,:status,:summary,:portrait_id"
            ")"
        )
        params = {**c,
                  "aliases": json.dumps(c.get("aliases", []), ensure_ascii=False),
                  "personal_skills": json.dumps(c.get("personal_skills", []), ensure_ascii=False)}
        self.conn.execute(sql, params)

    def list_characters(self, status: str = "") -> List[Dict]:
        if status:
            rows = self.conn.execute("SELECT * FROM characters WHERE status=?", (status,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM characters").fetchall()
        return self._rows_to_dicts(rows)

    def get_character(self, char_id: str) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM characters WHERE id=?", (char_id,)).fetchone()
        return dict(row) if row else None

    # ── 省份 CRUD ─────────────────────────────────────────────

    def upsert_region(self, r: dict) -> None:
        sql = (
            "INSERT OR REPLACE INTO regions VALUES ("
            ":id,:name,:kind,:population,:public_support,:unrest,"
            ":natural_disaster,:human_disaster,:registered_land,:hidden_land,"
            ":tax_per_turn,:grain_security,:gentry_resistance,:military_pressure,"
            ":status,:controlled_by,:fiscal,:on_restore"
            ")"
        )
        params = {**r,
                  "fiscal": json.dumps(r.get("fiscal", {}), ensure_ascii=False),
                  "on_restore": json.dumps(r.get("on_restore", {}), ensure_ascii=False)}
        self.conn.execute(sql, params)

    def list_regions(self) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM regions").fetchall()
        return self._rows_to_dicts(rows)

    # ── 军队 CRUD ─────────────────────────────────────────────

    def upsert_army(self, a: dict) -> None:
        sql = (
            "INSERT OR REPLACE INTO armies VALUES ("
            ":id,:name,:station,:theater,:commander,:controller,:troop_type,"
            ":manpower,:maintenance_per_turn,:supply,:morale,:training,:equipment,"
            ":arrears,:mobility,:loyalty,:status,:owner_power)"
        )
        self.conn.execute(sql, a)

    def list_armies(self) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM armies").fetchall()
        return self._rows_to_dicts(rows)

    # ── 势力 CRUD ─────────────────────────────────────────────

    def upsert_power(self, p: dict) -> None:
        sql = (
            "INSERT OR REPLACE INTO powers VALUES ("
            ":id,:name,:kind,:leader,:stance,:leverage,:satisfaction,"
            ":military_strength,:cohesion,:supply,:agenda,:status,"
            ":last_action,:aliases)"
        )
        self.conn.execute(sql, p)

    def list_powers(self) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM powers").fetchall()
        return self._rows_to_dicts(rows)

    # ── 事件 ─────────────────────────────────────────────────

    def upsert_event(self, e: dict) -> None:
        sql = (
            "INSERT OR REPLACE INTO events VALUES ("
            ":id,:title,:kind,:summary,:urgency,:severity,:credibility,"
            ":interests,:audiences,:resolve_condition,:fail_condition,"
            ":trigger_year,:trigger_month,:trigger_end_year,:trigger_end_month,"
            ":precondition,:event_type,:trigger_gate,:trigger_condition)"
        )
        params = {**e,
                  "interests": json.dumps(e.get("interests", []), ensure_ascii=False),
                  "audiences": json.dumps(e.get("audiences", []), ensure_ascii=False),
                  "trigger_gate": json.dumps(e.get("trigger_gate", {}), ensure_ascii=False),
                  "trigger_condition": json.dumps(e.get("trigger_condition", {}), ensure_ascii=False)}
        self.conn.execute(sql, params)

    def list_events(self) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM events").fetchall()
        return self._rows_to_dicts(rows)

    # ── 事件记忆（Event Memories）────────────────────────────────

    def upsert_event_memory(
        self,
        state: "GameState",
        subject_type: str,
        subject_id: str,
        event_type: str,
        title: str,
        cause: str = "",
        process: str = "",
        outcome: str = "",
        sentiment: str = "neutral",
        importance: int = 3,
        tags: Optional[List[str]] = None,
        source_kind: str = "system",
        source_id: str = "",
        expires_turn: Optional[int] = None,
    ) -> int:
        """写入/更新一张事件记忆摘要卡，按主体+类型+来源去重。"""
        subject_type = (subject_type or "").strip()
        subject_id = (subject_id or "").strip()
        event_type = (event_type or "").strip()
        source_kind = (source_kind or "system").strip()
        source_id = str(source_id or "").strip()
        if not subject_type or not subject_id or not event_type or not source_id:
            return 0
        importance = max(1, min(5, int(importance or 3)))
        if expires_turn is None:
            _ttl = {1: 6, 2: 12, 3: 24, 4: 48}
            ttl = _ttl.get(importance)
            if ttl is not None:
                expires_turn = int(state.turn) + ttl
        clean_tags = []
        for tag in tags or []:
            t = str(tag).strip()
            if t and t not in clean_tags:
                clean_tags.append(t[:40])
        existed = self.conn.execute(
            """
            SELECT id FROM event_memories
            WHERE subject_type=? AND subject_id=? AND event_type=? AND source_kind=? AND source_id=?
            """,
            (subject_type, subject_id, event_type, source_kind, source_id),
        ).fetchone()
        self.conn.execute(
            """
            INSERT INTO event_memories
                (subject_type, subject_id, turn, year, period, event_type, title,
                 cause, process, outcome, sentiment, importance, tags,
                 source_kind, source_id, expires_turn)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(subject_type, subject_id, event_type, source_kind, source_id)
            DO UPDATE SET
                turn = excluded.turn,
                year = excluded.year,
                period = excluded.period,
                title = excluded.title,
                cause = excluded.cause,
                process = excluded.process,
                outcome = excluded.outcome,
                sentiment = excluded.sentiment,
                importance = excluded.importance,
                tags = excluded.tags,
                expires_turn = excluded.expires_turn,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                subject_type, subject_id, state.turn, state.year, state.period,
                event_type, str(title or "")[:40], str(cause or "")[:80],
                str(process or "")[:80], str(outcome or "")[:80],
                sentiment if sentiment in {"positive", "neutral", "negative", "mixed"} else "neutral",
                importance, json.dumps(clean_tags, ensure_ascii=False),
                source_kind, source_id, expires_turn,
            ),
        )
        row = self.conn.execute(
            """
            SELECT id FROM event_memories
            WHERE subject_type=? AND subject_id=? AND event_type=? AND source_kind=? AND source_id=?
            """,
            (subject_type, subject_id, event_type, source_kind, source_id),
        ).fetchone()
        self.conn.commit()
        return int(row["id"]) if row else 0

    def add_event_memory_source(
        self,
        memory_id: int,
        source_kind: str,
        source_id: str,
        excerpt: str = "",
        locator: Optional[Dict] = None,
    ) -> None:
        if not memory_id:
            return
        locator_json = json.dumps(locator or {}, ensure_ascii=False, sort_keys=True)
        self.conn.execute(
            """
            INSERT INTO event_memory_sources
                (memory_id, source_kind, source_id, excerpt, locator)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(memory_id, source_kind, source_id, locator)
            DO UPDATE SET
                excerpt = excluded.excerpt,
                updated_at = CURRENT_TIMESTAMP
            """,
            (int(memory_id), str(source_kind or "system"), str(source_id or ""),
             str(excerpt or "")[:200], locator_json),
        )
        self.conn.commit()

    def prune_event_memories_for_turn(self, turn: int, per_subject: int = 3) -> None:
        """同一主体同回合只保留若干高价值摘要卡，避免记忆膨胀。"""
        rows = self.conn.execute(
            """
            SELECT id, subject_type, subject_id, importance, updated_at
            FROM event_memories
            WHERE turn = ?
            ORDER BY subject_type, subject_id, importance DESC, id DESC
            """,
            (int(turn),),
        ).fetchall()
        seen: Dict[tuple, int] = {}
        delete_ids: List[int] = []
        for row in rows:
            key = (row["subject_type"], row["subject_id"])
            seen[key] = seen.get(key, 0) + 1
            if seen[key] > per_subject:
                delete_ids.append(int(row["id"]))
        if delete_ids:
            placeholders = ",".join("?" for _ in delete_ids)
            self.conn.execute(
                f"DELETE FROM event_memory_sources WHERE memory_id IN ({placeholders})",
                delete_ids,
            )
            self.conn.execute(
                f"DELETE FROM event_memories WHERE id IN ({placeholders})",
                delete_ids,
            )
            self.conn.commit()

    def get_relevant_event_memories(
        self,
        character_name: str,
        faction: str,
        office_type: str,
        turn: int,
        limit: int = 5,
        ignore_expiry: bool = False,
    ) -> List[Dict]:
        """召见前取少量相关旧事摘要；纯结构化检索。"""
        active_issues: List[Dict] = []
        try:
            active_issues = self.list_active_issues() if hasattr(self, "list_active_issues") else []
        except Exception:
            pass
        active_issue_tags: List[str] = []
        for issue in active_issues[:12]:
            active_issue_tags.append(f"#{int(issue['id'])}")
            if issue.get("title"):
                active_issue_tags.append(str(issue["title"])[:20])
        tag_needles = [character_name, faction, office_type] + active_issue_tags
        expiry_clause = "" if ignore_expiry else "AND (expires_turn IS NULL OR expires_turn >= ?)"
        params: List = [int(turn)]
        if not ignore_expiry:
            params.append(int(turn))
        params += [
            character_name, faction,
            f"%{character_name}%", f"%{faction}%", f"%{office_type}%",
        ]
        rows = self.conn.execute(
            f"""
            SELECT * FROM event_memories
            WHERE turn <= ?
              {expiry_clause}
              AND (
                (subject_type='character' AND subject_id=?)
                OR (subject_type='faction' AND subject_id=?)
                OR (subject_type='court' AND importance>=4)
                OR tags LIKE ?
                OR tags LIKE ?
                OR tags LIKE ?
              )
            """,
            params,
        ).fetchall()
        scored: List[tuple] = []
        for row in rows:
            age = max(0, int(turn) - int(row["turn"]))
            if int(row["importance"]) <= 1 and not (
                row["subject_type"] == "character"
                and row["subject_id"] == character_name
                and age <= 3
            ):
                continue
            try:
                tags_list = json.loads(row["tags"] or "[]")
            except Exception:
                tags_list = []
            tag_matches = [
                t for t in tag_needles
                if t and any(str(t) in str(tag) or str(tag) in str(t) for tag in tags_list)
            ]
            exact = row["subject_type"] == "character" and row["subject_id"] == character_name
            active_hit = any(
                str(t).startswith("#") or t in active_issue_tags for t in tag_matches
            )
            score = (
                int(row["importance"]) * 10
                + (20 if exact else 0)
                + len(tag_matches) * 4
                + max(0, 10 - age)
                + (12 if active_hit else 0)
            )
            scored.append((score, row, tag_matches))
        scored.sort(key=lambda item: (item[0], int(item[1]["turn"]), int(item[1]["id"])), reverse=True)
        result: List[Dict] = []
        for _score, row, _matches in scored[:limit]:
            d = dict(row)
            d["id"] = int(row["id"])
            d["turn"] = int(row["turn"])
            d["year"] = int(row["year"])
            d["period"] = int(row["period"])
            d["importance"] = int(row["importance"])
            try:
                d["tags"] = json.loads(row["tags"] or "[]")
            except Exception:
                d["tags"] = []
            result.append(d)
        return result

    def get_memories_by_keywords(self, keywords: List[str], turn: int, limit: int = 8) -> List[Dict]:
        """关键词检索记忆。"""
        if not keywords:
            return []
        tag_conditions = " OR ".join([f"tags LIKE :kw{i}" for i in range(len(keywords))])
        named_params = {"kw%d" % i: f"%{kw}%" for i, kw in enumerate(keywords)}
        all_params = {"turn": int(turn), "limit": int(limit), **named_params}
        all_params["exp_turn"] = int(turn)
        sql = (
            "SELECT * FROM event_memories "
            "WHERE (expires_turn IS NULL OR expires_turn >= :exp_turn) "
            "AND turn <= :turn "
            "AND (" + tag_conditions + ") "
            "ORDER BY importance DESC, turn DESC "
            "LIMIT :limit"
        )
        rows = self.conn.execute(sql, all_params).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["id"] = int(row["id"])
            d["turn"] = int(row["turn"])
            d["year"] = int(row["year"])
            d["period"] = int(row["period"])
            d["importance"] = int(row["importance"])
            try:
                d["tags"] = json.loads(row["tags"] or "[]")
            except Exception:
                d["tags"] = []
            result.append(d)
        return result

    # ── 日志 ─────────────────────────────────────────────────

    def append_log(self, turn: int, phase: str, entry: str) -> None:
        self.conn.execute("INSERT INTO game_log (turn, phase, entry) VALUES (?, ?, ?)",
                          (turn, phase, entry))

    def get_recent_log(self, limit: int = 20) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT * FROM game_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return self._rows_to_dicts(rows)

    # ── 事项追踪（Issues）──────────────────────────────

    def insert_issue(
        self,
        state: GameState,
        title: str,
        description: str = "",
        origin_kind: str = "",
        origin_ref: str = "",
        progress: int = 0,
        proposed_by: str = "",
        tags: Optional[List[str]] = None,
        ongoing_effects: Optional[Dict] = None,
        cancellable: str = "never",
        effect_on_resolve: Optional[Dict] = None,
        effect_on_fail: Optional[Dict] = None,
        resolve_condition: str = "",
        fail_condition: str = "",
        total_steps: int = 1,
        deadline_turn: Optional[int] = None,
    ) -> int:
        """新建事项，返回 issue id。"""
        tags = tags or []
        self.conn.execute(
            """INSERT INTO issues
            (title,description,status,proposed_by,progress,total_steps,deadline_turn,
             created_turn,origin_kind,origin_ref,tags,cancellable,
             ongoing_effects,effect_on_resolve,effect_on_fail,
             resolve_condition,fail_condition,last_updated_turn)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                title, description, "active", proposed_by, progress, total_steps,
                deadline_turn, state.turn, origin_kind, origin_ref,
                json.dumps(tags, ensure_ascii=False),
                cancellable,
                json.dumps(ongoing_effects or {}, ensure_ascii=False),
                json.dumps(effect_on_resolve or {}, ensure_ascii=False),
                json.dumps(effect_on_fail or {}, ensure_ascii=False),
                resolve_condition, fail_condition, state.turn,
            ),
        )
        self.commit()
        row = self.conn.execute("SELECT last_insert_rowid()").fetchone()
        return row[0] if row else 0

    def advance_issue(self, issue_id: int, steps: int = 1, state: Optional[GameState] = None) -> None:
        """推进事项 steps 步。"""
        turn = state.turn if state else self.load_state("turn", 1)
        self.conn.execute(
            "UPDATE issues SET current_step=current_step+?, progress=progress+?, "
            "last_updated_turn=? WHERE id=?",
            (steps, steps * (100 // max(1, self._issue_total_steps(issue_id))), turn, issue_id),
        )
        self.commit()

    def _issue_total_steps(self, issue_id: int) -> int:
        row = self.conn.execute("SELECT total_steps FROM issues WHERE id=?", (issue_id,)).fetchone()
        return row["total_steps"] if row else 1

    def close_issue(self, issue_id: int, success: bool, state: Optional[GameState] = None) -> None:
        """结案，success=True为解决，False为失败。"""
        turn = state.turn if state else self.load_state("turn", 1)
        self.conn.execute(
            "UPDATE issues SET status='closed', closed_turn=?, success=? WHERE id=?",
            (turn, 1 if success else 0, issue_id),
        )
        self.commit()

    def get_active_issues(self, tag: str = "") -> List[Dict]:
        """查询进行中事项，可按 tag 过滤。"""
        if tag:
            rows = self.conn.execute(
                "SELECT * FROM issues WHERE status='active' AND tags LIKE ? ORDER BY id",
                (f"%{tag}%",),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM issues WHERE status='active' ORDER BY id"
            ).fetchall()
        return self._rows_to_dicts(rows)

    def get_issues_by_tag(self, tag: str) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT * FROM issues WHERE tags LIKE ? ORDER BY id", (f"%{tag}%",)
        ).fetchall()
        return self._rows_to_dicts(rows)

    def find_any_issue_by_origin(self, origin_kind: str, origin_ref: str) -> Optional[Dict]:
        """按 origin 查询是否已立项。"""
        row = self.conn.execute(
            "SELECT * FROM issues WHERE origin_kind=? AND origin_ref=?",
            (origin_kind, origin_ref),
        ).fetchone()
        return dict(row) if row else None

    # ── 工具 ─────────────────────────────────────────────────

    def _rows_to_dicts(self, rows) -> List[Dict]:
        result = []
        for row in rows:
            d = dict(row)
            for field in ("aliases", "personal_skills", "interests", "audiences",
                          "trigger_gate", "trigger_condition", "fiscal", "on_restore"):
                if field in d and d[field]:
                    try:
                        d[field] = json.loads(d[field])
                    except Exception:
                        pass
            result.append(d)
        return result

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    @staticmethod
    def new(db_path: str) -> "GameDB":
        db = GameDB(db_path)
        return db
