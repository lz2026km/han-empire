"""SQLite 游戏数据库。L3。"""



import json
import os
import sqlite3
from typing import Dict, List, Optional

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

    # ── 日志 ─────────────────────────────────────────────────

    def append_log(self, turn: int, phase: str, entry: str) -> None:
        self.conn.execute("INSERT INTO game_log (turn, phase, entry) VALUES (?, ?, ?)",
                          (turn, phase, entry))

    def get_recent_log(self, limit: int = 20) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT * FROM game_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return self._rows_to_dicts(rows)

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
