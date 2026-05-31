"""SQLite 游戏数据库。L3。

完整 schema + 种子数据初始化 + 状态持久化。启动时由 GameSession 注入 content。
"""



import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from han_sim.models import GameState

from han_sim.paths import user_data_path


# 汉末两账：汉室国库 + 皇帝内库
ECONOMY_ACCOUNTS = ("汉室库", "内库")


class GameDB:
    def __init__(self, path: str, content: Optional["GameContent"] = None):
        self.path = path
        self.content = content  # 过渡期可省略，seed_static_data 时自行加载
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.row_factory = sqlite3.Row
        self.init_schema()
        self.init_fiscal_config()
        if self.content is None:
            from han_sim.content import load_game_content
            self.content = load_game_content()

    @classmethod
    def new(cls, path: str) -> "GameDB":
        """工厂方法：创建新数据库实例（兼容 session.py 调用）"""
        return cls(path)

    # ── Schema ───────────────────────────────────────────────────────

    def init_schema(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS game_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                year INTEGER NOT NULL,
                period INTEGER NOT NULL,
                turn INTEGER NOT NULL,
                turn_phase TEXT NOT NULL DEFAULT 'summoning'
            );

            CREATE TABLE IF NOT EXISTS metrics (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS characters (
                name TEXT PRIMARY KEY,
                office TEXT NOT NULL DEFAULT '',
                office_type TEXT NOT NULL DEFAULT '',
                faction TEXT NOT NULL DEFAULT '中立',
                personal_skills TEXT NOT NULL DEFAULT '[]',
                loyalty INTEGER NOT NULL DEFAULT 50,
                ability INTEGER NOT NULL DEFAULT 50,
                integrity INTEGER NOT NULL DEFAULT 50,
                courage INTEGER NOT NULL DEFAULT 50,
                style TEXT NOT NULL DEFAULT '',
                birth_year INTEGER NOT NULL DEFAULT 0,
                historical_death_year INTEGER NOT NULL DEFAULT 0,
                historical_death_month INTEGER NOT NULL DEFAULT 0,
                debut_year INTEGER NOT NULL DEFAULT 0,
                debut_month INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                status_reason TEXT NOT NULL DEFAULT '',
                status_changed_turn INTEGER NOT NULL DEFAULT 0,
                power_id TEXT NOT NULL DEFAULT 'han',
                location TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                aliases TEXT NOT NULL DEFAULT '[]',
                portrait_id TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS character_offices (
                character_name TEXT PRIMARY KEY,
                office_title TEXT NOT NULL,
                office_type TEXT NOT NULL,
                source TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(character_name) REFERENCES characters(name)
            );

            CREATE TABLE IF NOT EXISTS factions (
                name TEXT PRIMARY KEY,
                satisfaction INTEGER NOT NULL,
                leverage INTEGER NOT NULL,
                agenda TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS classes (
                name TEXT NOT NULL,
                region_id TEXT NOT NULL DEFAULT '',
                population INTEGER NOT NULL,
                satisfaction INTEGER NOT NULL,
                leverage INTEGER NOT NULL,
                agenda TEXT NOT NULL,
                PRIMARY KEY (name, region_id)
            );
            CREATE INDEX IF NOT EXISTS idx_classes_region ON classes(region_id, name);

            CREATE TABLE IF NOT EXISTS powers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL,
                leader TEXT NOT NULL,
                stance TEXT NOT NULL,
                leverage INTEGER NOT NULL,
                satisfaction INTEGER NOT NULL,
                military_strength INTEGER NOT NULL DEFAULT 50,
                cohesion INTEGER NOT NULL DEFAULT 50,
                supply INTEGER NOT NULL DEFAULT 50,
                agenda TEXT NOT NULL,
                status TEXT NOT NULL,
                last_action TEXT NOT NULL DEFAULT '',
                aliases TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS power_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn INTEGER NOT NULL, year INTEGER NOT NULL, period INTEGER NOT NULL,
                power_id TEXT NOT NULL, field TEXT NOT NULL,
                old_value TEXT NOT NULL, new_value TEXT NOT NULL,
                delta INTEGER, reason TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(power_id) REFERENCES powers(id)
            );
            CREATE INDEX IF NOT EXISTS idx_power_logs_turn ON power_logs(turn, power_id);

            CREATE TABLE IF NOT EXISTS regions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL,
                population INTEGER NOT NULL,
                public_support INTEGER NOT NULL,
                unrest INTEGER NOT NULL,
                natural_disaster TEXT NOT NULL,
                human_disaster TEXT NOT NULL,
                registered_land INTEGER NOT NULL,
                hidden_land INTEGER NOT NULL,
                tax_per_turn INTEGER NOT NULL,
                grain_security INTEGER NOT NULL,
                gentry_resistance INTEGER NOT NULL,
                military_pressure INTEGER NOT NULL,
                status TEXT NOT NULL,
                controlled_by TEXT NOT NULL DEFAULT 'han',
                fiscal TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(controlled_by) REFERENCES powers(id)
            );

            CREATE TABLE IF NOT EXISTS region_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn INTEGER NOT NULL, year INTEGER NOT NULL, period INTEGER NOT NULL,
                region_id TEXT NOT NULL, field TEXT NOT NULL,
                old_value TEXT NOT NULL, new_value TEXT NOT NULL,
                delta INTEGER, reason TEXT NOT NULL,
                event_id TEXT, edict_id INTEGER, actor TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(region_id) REFERENCES regions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_region_logs_turn ON region_logs(turn, region_id);

            CREATE TABLE IF NOT EXISTS armies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                station TEXT NOT NULL,
                theater TEXT NOT NULL,
                commander TEXT NOT NULL,
                controller TEXT NOT NULL,
                troop_type TEXT NOT NULL,
                manpower INTEGER NOT NULL,
                maintenance_per_turn INTEGER NOT NULL,
                supply INTEGER NOT NULL,
                morale INTEGER NOT NULL,
                training INTEGER NOT NULL,
                equipment INTEGER NOT NULL,
                arrears INTEGER NOT NULL DEFAULT 0,
                mobility INTEGER NOT NULL,
                loyalty INTEGER NOT NULL,
                status TEXT NOT NULL,
                owner_power TEXT NOT NULL DEFAULT 'han',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(owner_power) REFERENCES powers(id)
            );

            CREATE TABLE IF NOT EXISTS army_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn INTEGER NOT NULL, year INTEGER NOT NULL, period INTEGER NOT NULL,
                army_id TEXT NOT NULL, field TEXT NOT NULL,
                old_value TEXT NOT NULL, new_value TEXT NOT NULL,
                delta INTEGER, reason TEXT NOT NULL,
                event_id TEXT, edict_id INTEGER, actor TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(army_id) REFERENCES armies(id)
            );
            CREATE INDEX IF NOT EXISTS idx_army_logs_turn ON army_logs(turn, army_id);

            CREATE TABLE IF NOT EXISTS buildings (
                id TEXT PRIMARY KEY,
                region_id TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                level INTEGER NOT NULL,
                condition INTEGER NOT NULL,
                maintenance INTEGER NOT NULL,
                risk INTEGER NOT NULL,
                output_metric TEXT NOT NULL DEFAULT '',
                output_amount INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                origin TEXT NOT NULL DEFAULT 'preset',
                created_turn INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(region_id) REFERENCES regions(id)
            );

            CREATE TABLE IF NOT EXISTS economy_accounts (
                account TEXT PRIMARY KEY,
                metric_key TEXT NOT NULL UNIQUE,
                balance INTEGER NOT NULL,
                note TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS economy_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn INTEGER NOT NULL, year INTEGER NOT NULL, period INTEGER NOT NULL,
                account TEXT NOT NULL,
                delta INTEGER NOT NULL,
                balance_after INTEGER NOT NULL,
                category TEXT NOT NULL,
                reason TEXT NOT NULL,
                event_id TEXT, edict_id INTEGER, actor TEXT,
                purpose TEXT, target_kind TEXT, target_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(account) REFERENCES economy_accounts(account)
            );
            CREATE INDEX IF NOT EXISTS idx_economy_ledger_turn ON economy_ledger(turn, account);

            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                kind TEXT NOT NULL,
                summary TEXT NOT NULL,
                urgency INTEGER NOT NULL,
                severity INTEGER NOT NULL,
                credibility INTEGER NOT NULL,
                interests TEXT NOT NULL DEFAULT '[]',
                audiences TEXT NOT NULL DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS event_triggers (
                event_id TEXT PRIMARY KEY,
                turn INTEGER NOT NULL, year INTEGER NOT NULL, period INTEGER NOT NULL,
                source TEXT NOT NULL DEFAULT 'simulation',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES events(id)
            );

            CREATE TABLE IF NOT EXISTS turn_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn INTEGER NOT NULL, year INTEGER NOT NULL, period INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS turn_reports (
                turn INTEGER PRIMARY KEY,
                year INTEGER NOT NULL, period INTEGER NOT NULL,
                report TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS turn_extractions (
                turn INTEGER PRIMARY KEY,
                year INTEGER NOT NULL, period INTEGER NOT NULL,
                decree_text TEXT NOT NULL DEFAULT '',
                narrative TEXT NOT NULL DEFAULT '',
                extractor_input TEXT NOT NULL DEFAULT '',
                extractor_output TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                minister_name TEXT NOT NULL,
                turn INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_chat_messages_minister ON chat_messages(minister_name, id);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_turn ON chat_messages(turn);

            CREATE TABLE IF NOT EXISTS secret_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn_issued INTEGER NOT NULL,
                due_turn INTEGER NOT NULL DEFAULT 0,
                year_issued INTEGER NOT NULL,
                period_issued INTEGER NOT NULL,
                minister_name TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '[]',
                importance INTEGER NOT NULL DEFAULT 4,
                status TEXT NOT NULL DEFAULT 'active',
                result TEXT NOT NULL DEFAULT '',
                sim_note TEXT NOT NULL DEFAULT '',
                turn_closed INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_secret_orders_minister ON secret_orders(minister_name, status);
            CREATE INDEX IF NOT EXISTS idx_secret_orders_turn ON secret_orders(turn_issued, status);
            CREATE INDEX IF NOT EXISTS idx_secret_orders_status ON secret_orders(status);

            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                origin_kind TEXT NOT NULL DEFAULT '',
                origin_ref TEXT NOT NULL DEFAULT '',
                origin_turn INTEGER NOT NULL,
                bar_value INTEGER NOT NULL DEFAULT 40,
                bar_good_meaning TEXT NOT NULL DEFAULT '已平',
                bar_bad_meaning TEXT NOT NULL DEFAULT '失控',
                inertia INTEGER NOT NULL DEFAULT 0,
                phase TEXT NOT NULL DEFAULT '起',
                stage_text TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active',
                severity INTEGER NOT NULL DEFAULT 50,
                region_hint TEXT NOT NULL DEFAULT '',
                faction_hint TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '[]',
                ongoing_effects TEXT NOT NULL DEFAULT '{}',
                cancellable TEXT NOT NULL DEFAULT 'never',
                cancel_cost TEXT NOT NULL DEFAULT '{}',
                effect_on_resolve TEXT NOT NULL DEFAULT '{}',
                effect_on_fail TEXT NOT NULL DEFAULT '{}',
                resolve_condition TEXT NOT NULL DEFAULT '',
                fail_condition TEXT NOT NULL DEFAULT '',
                resolution_summary TEXT NOT NULL DEFAULT '',
                last_advance_turn INTEGER NOT NULL DEFAULT 0,
                closed_turn INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_issues_active ON issues(kind, status, severity DESC);

            CREATE TABLE IF NOT EXISTS issue_advances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                turn INTEGER NOT NULL,
                trigger_kind TEXT NOT NULL,
                trigger_ref TEXT NOT NULL DEFAULT '',
                delta_bar INTEGER NOT NULL DEFAULT 0,
                from_value INTEGER NOT NULL DEFAULT 0,
                to_value INTEGER NOT NULL DEFAULT 0,
                from_stage_text TEXT NOT NULL DEFAULT '',
                to_stage_text TEXT NOT NULL DEFAULT '',
                narrative TEXT NOT NULL DEFAULT '',
                metric_delta TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(issue_id) REFERENCES issues(id)
            );
            CREATE INDEX IF NOT EXISTS idx_issue_advances_issue ON issue_advances(issue_id, turn);

            CREATE TABLE IF NOT EXISTS event_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_type TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                turn INTEGER NOT NULL,
                year INTEGER NOT NULL,
                period INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                cause TEXT NOT NULL DEFAULT '',
                process TEXT NOT NULL DEFAULT '',
                outcome TEXT NOT NULL DEFAULT '',
                sentiment TEXT NOT NULL DEFAULT 'neutral',
                importance INTEGER NOT NULL DEFAULT 3,
                tags TEXT NOT NULL DEFAULT '[]',
                source_kind TEXT NOT NULL,
                source_id TEXT NOT NULL,
                expires_turn INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(subject_type, subject_id, event_type, source_kind, source_id)
            );
            CREATE INDEX IF NOT EXISTS idx_event_memories_subject ON event_memories(subject_type, subject_id, turn);
            CREATE INDEX IF NOT EXISTS idx_event_memories_turn ON event_memories(turn, importance);
            CREATE INDEX IF NOT EXISTS idx_event_memories_expiry ON event_memories(expires_turn, turn);

            CREATE TABLE IF NOT EXISTS event_memory_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                source_kind TEXT NOT NULL,
                source_id TEXT NOT NULL,
                excerpt TEXT NOT NULL DEFAULT '',
                locator TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(memory_id) REFERENCES event_memories(id) ON DELETE CASCADE,
                UNIQUE(memory_id, source_kind, source_id, locator)
            );
            CREATE INDEX IF NOT EXISTS idx_event_memory_sources_memory ON event_memory_sources(memory_id);

            CREATE TABLE IF NOT EXISTS fiscal_config (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL,
                kind TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS turn_directives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn INTEGER NOT NULL,
                year INTEGER NOT NULL,
                period INTEGER NOT NULL,
                event_id TEXT,
                actor TEXT,
                skill_id TEXT,
                text TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES events(id),
                FOREIGN KEY(actor) REFERENCES characters(name)
            );
            CREATE INDEX IF NOT EXISTS idx_turn_directives_turn ON turn_directives(turn, status);

            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS emperor_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                emperor_skill_id TEXT NOT NULL,
                acquired_turn INTEGER NOT NULL DEFAULT 0,
                UNIQUE(campaign_id, emperor_skill_id)
            );

            CREATE TABLE IF NOT EXISTS minister_skill_grants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                minister_name TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                granted_turn INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                UNIQUE(campaign_id, minister_name, skill_id)
            );

            CREATE TABLE IF NOT EXISTS directives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'decree',
                kind TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                content TEXT NOT NULL DEFAULT '',
                issued_turn INTEGER NOT NULL DEFAULT 0,
                expires_turn INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_directives_campaign ON directives(campaign_id, status);
            CREATE INDEX IF NOT EXISTS idx_directives_turn ON directives(issued_turn, status);

            CREATE TABLE IF NOT EXISTS consorts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                name TEXT NOT NULL,
                rank TEXT NOT NULL DEFAULT '采女',
                traits TEXT NOT NULL DEFAULT '[]',
                skills TEXT NOT NULL DEFAULT '[]',
                favorability INTEGER NOT NULL DEFAULT 50,
                palace TEXT NOT NULL DEFAULT '永巷',
                status TEXT NOT NULL DEFAULT 'active',
                portrait_id TEXT NOT NULL DEFAULT '',
                entered_turn INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(campaign_id, name)
            );

            CREATE TABLE IF NOT EXISTS consort_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL DEFAULT 18,
                background TEXT NOT NULL DEFAULT '',
                appearance INTEGER NOT NULL DEFAULT 50,
                talent INTEGER NOT NULL DEFAULT 50,
                temperament TEXT NOT NULL DEFAULT '温婉',
                skills TEXT NOT NULL DEFAULT '[]',
                traits TEXT NOT NULL DEFAULT '[]',
                portrait_id TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                selected_turn INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS consort_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                turn INTEGER NOT NULL,
                consort_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                favorability_delta INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS consort_traits (
                name TEXT PRIMARY KEY,
                extra_skills TEXT NOT NULL DEFAULT '[]',
                extra_traits TEXT NOT NULL DEFAULT '[]',
                updated_turn INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS legacies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_issue_id INTEGER,
                modifiers TEXT NOT NULL DEFAULT '{}',
                narrative_hint TEXT NOT NULL DEFAULT '',
                start_turn INTEGER NOT NULL,
                duration_months INTEGER NOT NULL DEFAULT 24,
                status TEXT NOT NULL DEFAULT 'active',
                clear_gate TEXT NOT NULL DEFAULT '{}',
                legacy_key TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_legacies_active ON legacies(status);

            CREATE TABLE IF NOT EXISTS building_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn INTEGER NOT NULL,
                year INTEGER NOT NULL,
                period INTEGER NOT NULL,
                building_id TEXT NOT NULL,
                field TEXT NOT NULL,
                old_value TEXT NOT NULL,
                new_value TEXT NOT NULL,
                delta INTEGER,
                reason TEXT NOT NULL,
                event_id TEXT,
                edict_id INTEGER,
                actor TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_building_logs_turn ON building_logs(turn, building_id);

            CREATE TABLE IF NOT EXISTS power_name_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn INTEGER NOT NULL,
                year INTEGER NOT NULL,
                period INTEGER NOT NULL,
                power_id TEXT NOT NULL,
                old_name TEXT NOT NULL,
                new_name TEXT NOT NULL,
                old_aliases TEXT NOT NULL DEFAULT '',
                new_aliases TEXT NOT NULL DEFAULT '',
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def init_fiscal_config(self) -> None:
        rows = [
            ("辽饷_base",   15,  "base", "辽东加派月额，万两"),
            ("辽饷_rate",   100,  "rate", "辽饷实收率%"),
            ("盐税_base",    10,  "base", "盐引月度定额，万两。查私盐可拉高"),
            ("盐税_rate",   100,  "rate", "盐税实收率%"),
            ("商税_base",     5,  "base", "各地关卡店税月额，万两"),
            ("商税_rate",   100,  "rate", "商税实收率%"),
            ("宗室禄米_base", 40,  "base", "诸藩宗室禄米月度账面额，万两"),
            ("宗室禄米_rate", 55, "rate", "宗室禄米实发率%"),
            ("官俸_base",    15,  "base", "在京百官俸禄月额，万两"),
            ("官俸_rate",   100,  "rate", "官俸发放率%"),
            ("宫廷_base",     7,  "base", "皇室日常用度月额，万两"),
            ("宫廷_rate",   100,  "rate", "宫廷开支率%"),
            ("工程_base",     3,  "base", "工部月度维护支出，万两"),
            ("工程_rate",   100,  "rate", "工程维护率%"),
            ("赈灾_base",     3,  "base", "制度性赈灾备用，万两/月"),
            ("赈灾_rate",   100,  "rate", "赈灾拨付率%"),
            ("皇庄_base",    10,  "base", "皇庄地租月度上缴内库，万两"),
            ("皇庄_rate",   100,  "rate", "皇庄收益率%"),
            ("内库_base",    20,  "base", "皇庄/没收财产月均上缴，万两"),
            ("妃嫔_base",     3,  "base", "后宫妃嫔月度供奉，万两"),
            ("妃嫔_rate",   100,  "rate", "妃嫔供奉率%"),
        ]
        SCHEMA_VERSION = 2
        cur_ver_row = self.conn.execute(
            "SELECT value FROM fiscal_config WHERE key = '__schema_version'"
        ).fetchone()
        cur_ver = int(cur_ver_row["value"]) if cur_ver_row else 0
        if cur_ver < SCHEMA_VERSION:
            self.conn.execute(
                "INSERT INTO fiscal_config (key, value, kind, note) VALUES ('__schema_version', ?, 'meta', '财政默认值版本号') "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (SCHEMA_VERSION,),
            )
            for key, value, kind, note in rows:
                self.conn.execute(
                    "INSERT INTO fiscal_config (key, value, kind, note) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note",
                    (key, value, kind, note),
                )
        else:
            for key, value, kind, note in rows:
                self.conn.execute(
                    "INSERT OR IGNORE INTO fiscal_config (key, value, kind, note) VALUES (?, ?, ?, ?)",
                    (key, value, kind, note),
                )
        self.conn.commit()

    def get_fiscal_config(self) -> Dict[str, int]:
        rows = self.conn.execute(
            "SELECT key, value FROM fiscal_config WHERE key NOT GLOB '__*'"
        ).fetchall()
        return {str(r["key"]): int(r["value"]) for r in rows}

    def set_fiscal_config(self, key: str, value: int) -> None:
        self.conn.execute("UPDATE fiscal_config SET value = ? WHERE key = ?", (value, key))
        self.conn.commit()

    def ensure_column(self, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def table_has_rows(self, table: str) -> bool:
        row = self.conn.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
        return row is not None

    # ── 种子数据 ───────────────────────────────────────────────────

    def seed_static_data(self) -> None:
        pass  # TODO: docstring
        if self.table_has_rows("characters"):
            return  # Already initialized, skip
        characters = self.content.load_characters()
        powers_data = self.content.load_powers()
        regions_data = self.content.load_regions()
        events_data = self.content.load_events()
        seed_events = self.content.load_seed_events()
        armies_data = self.content.load_armies()
        buildings_data = self.content.load_buildings()

        # 人物（转为 id→dict dict 以支持 upsert）
        char_dict = {c["id"]: c for c in characters if "id" in c}
        for char_id, char in char_dict.items():
            self.conn.execute(
                """INSERT OR IGNORE INTO characters
                   (name, office, office_type, faction, aliases, personal_skills,
                    loyalty, ability, integrity, courage, style,
                    birth_year, historical_death_year, historical_death_month,
                    debut_year, debut_month, status, power_id, location, summary)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    char.get("name", char_id),
                    char.get("office", ""),
                    char.get("office_type", ""),
                    char.get("faction", "中立"),
                    json.dumps(char.get("aliases", []), ensure_ascii=False),
                    json.dumps(char.get("personal_skills", []), ensure_ascii=False),
                    char.get("loyalty", 50),
                    char.get("ability", 50),
                    char.get("integrity", 50),
                    char.get("courage", 50),
                    char.get("style", ""),
                    char.get("birth_year", 0),
                    char.get("historical_death_year", 0),
                    char.get("historical_death_month", 0),
                    char.get("debut_year", 0),
                    char.get("debut_month", 0),
                    "active",
                    char.get("power_id", "han"),
                    char.get("location", ""),
                    char.get("summary", ""),
                ),
            )

        # 势力
        power_dict = {p["id"]: p for p in powers_data if "id" in p}
        for power_id, p in power_dict.items():
            self.conn.execute(
                """INSERT OR IGNORE INTO powers
                   (id, name, kind, leader, stance, leverage, satisfaction,
                    military_strength, cohesion, supply, agenda, status, last_action, aliases)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    power_id,
                    p.get("name", power_id),
                    p.get("kind", "势力"),
                    p.get("leader", ""),
                    p.get("stance", "中立"),
                    p.get("leverage", 50),
                    p.get("satisfaction", 50),
                    p.get("military_strength", 50),
                    p.get("cohesion", 50),
                    p.get("supply", 50),
                    p.get("agenda", ""),
                    p.get("status", "active"),
                    p.get("last_action", ""),
                    p.get("aliases", ""),
                ),
            )

        # 地区
        region_dict = {r["id"]: r for r in regions_data if "id" in r}
        for region_id, r in region_dict.items():
            self.conn.execute(
                """INSERT OR IGNORE INTO regions
                   (id, name, kind, population, public_support, unrest,
                    natural_disaster, human_disaster, registered_land, hidden_land,
                    tax_per_turn, grain_security, gentry_resistance, military_pressure,
                    status, controlled_by, fiscal)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    region_id,
                    r.get("name", region_id),
                    r.get("kind", "州"),
                    r.get("population", 0),
                    r.get("public_support", 50),
                    r.get("unrest", 0),
                    r.get("natural_disaster", "无"),
                    r.get("human_disaster", "无"),
                    r.get("registered_land", 0),
                    r.get("hidden_land", 0),
                    r.get("tax_per_turn", 0),
                    r.get("grain_security", 0),
                    r.get("gentry_resistance", 0),
                    r.get("military_pressure", 0),
                    r.get("status", "安稳"),
                    r.get("controlled_by", "han"),
                    json.dumps(r.get("fiscal", {}), ensure_ascii=False),
                ),
            )

        # 军队
        army_dict = {a["id"]: a for a in armies_data if "id" in a}
        for army_id, a in army_dict.items():
            self.conn.execute(
                """INSERT OR IGNORE INTO armies
                   (id, name, station, theater, commander, controller, troop_type,
                    manpower, maintenance_per_turn, supply, morale, training,
                    equipment, arrears, mobility, loyalty, status, owner_power)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    army_id,
                    a.get("name", army_id),
                    a.get("station", ""),
                    a.get("theater", ""),
                    a.get("commander", ""),
                    a.get("controller", ""),
                    a.get("troop_type", "步兵"),
                    a.get("manpower", 0),
                    a.get("maintenance_per_turn", 0),
                    a.get("supply", 50),
                    a.get("morale", 50),
                    a.get("training", 50),
                    a.get("equipment", 50),
                    a.get("arrears", 0),
                    a.get("mobility", 50),
                    a.get("loyalty", 50),
                    a.get("status", "驻守"),
                    a.get("owner_power", "han"),
                ),
            )

        # 建筑
        building_dict = {b["id"]: b for b in buildings_data if "id" in b}
        for bld_id, b in building_dict.items():
            self.conn.execute(
                """INSERT OR IGNORE INTO buildings
                   (id, region_id, name, category, level, condition, maintenance, risk,
                    output_metric, output_amount, status, origin, created_turn)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'preset', 0)""",
                (
                    bld_id,
                    b.get("region_id", ""),
                    b.get("name", bld_id),
                    b.get("category", ""),
                    b.get("level", 1),
                    b.get("condition", 100),
                    b.get("maintenance", 0),
                    b.get("risk", 0),
                    b.get("output_metric", ""),
                    b.get("output_amount", 0),
                    b.get("status", "正常"),
                ),
            )

        # 事件
        for e in events_data + seed_events:
            if not isinstance(e, dict) or "id" not in e:
                continue
            self.conn.execute(
                """INSERT OR IGNORE INTO events
                   (id, title, kind, summary, urgency, severity, credibility, interests, audiences)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    e.get("id", ""),
                    e.get("title", ""),
                    e.get("kind", "事件"),
                    e.get("summary", ""),
                    e.get("urgency", 50),
                    e.get("severity", 50),
                    e.get("credibility", 100),
                    json.dumps(e.get("interests", []), ensure_ascii=False),
                    json.dumps(e.get("audiences", []), ensure_ascii=False),
                ),
            )

        self.conn.commit()

    # ── 状态读写 ───────────────────────────────────────────────────

    def has_state(self) -> bool:
        row = self.conn.execute("SELECT 1 FROM game_state WHERE id = 1").fetchone()
        return row is not None

    def save_state(self, state: "GameState") -> None:
        self.conn.execute(
            """INSERT INTO game_state (id, year, period, turn, turn_phase)
               VALUES (1, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   year=excluded.year, period=excluded.period,
                   turn=excluded.turn, turn_phase=excluded.turn_phase""",
            (state.year, state.period, state.turn, getattr(state, "turn_phase", "summoning")),
        )
        for key, value in state.metrics.items():
            self.conn.execute(
                """INSERT INTO metrics (key, value)
                   VALUES (?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (key, value),
            )
        self.sync_economy_accounts(state)
        self.conn.commit()

    def load_state(self, start_ym: str = "") -> "GameState":
        from han_sim.models import GameState

        row = self.conn.execute(
            "SELECT year, period, turn, turn_phase FROM game_state WHERE id = 1"
        ).fetchone()
        if row is None:
            state = GameState()
            if start_ym:
                try:
                    y_str, m_str = start_ym.split(".")
                    y, m = int(y_str), int(m_str)
                except (ValueError, AttributeError):
                    raise SystemExit(f"--start-ym 格式非法：{start_ym!r}，应为 YYYY.MM（如 189.01）")
                if not (180 <= y <= 230 and 1 <= m <= 12):
                    raise SystemExit(f"--start-ym 超范围：{start_ym!r}，年须 180-230、月 1-12。")
                state.turn = (y - 189) * 12 + m
                state.year, state.period = y, m
            self.save_state(state)
            self.ensure_opening_ledger(state)
            self.seed_opening_gazette(state)
            return state

        metrics = {
            r["key"]: int(r["value"])
            for r in self.conn.execute("SELECT key, value FROM metrics").fetchall()
        }
        state = GameState(
            year=int(row["year"]),
            period=int(row["period"]),
            turn=int(row["turn"]),
            turn_phase=str(row["turn_phase"] or "summoning"),
        )
        valid_keys = set(state.metrics.keys())
        state.metrics.update({k: v for k, v in metrics.items() if k in valid_keys})
        account_rows = self.conn.execute(
            "SELECT account, balance FROM economy_accounts"
        ).fetchall()
        for account in account_rows:
            state.metrics[str(account["account"])] = int(account["balance"])
        self.sync_economy_accounts(state)
        self.conn.commit()
        return state

    def sync_economy_accounts(self, state: "GameState") -> None:
        notes = {
            "汉室库": "朝廷国库，用于军饷、赈济、官俸和工程。",
            "内库": "皇帝可直接调度的钱物，用于救急、密支和政治缓冲。",
        }
        for account in ECONOMY_ACCOUNTS:
            self.conn.execute(
                """INSERT INTO economy_accounts (account, metric_key, balance, note)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(account) DO UPDATE SET
                       balance=excluded.balance, note=excluded.note,
                       updated_at=CURRENT_TIMESTAMP""",
                (account, account, int(state.metrics.get(account, 0)), notes[account]),
            )

    def ensure_opening_ledger(self, state: "GameState") -> None:
        for account in ECONOMY_ACCOUNTS:
            exists = self.conn.execute(
                "SELECT 1 FROM economy_ledger WHERE account=? LIMIT 1", (account,)
            ).fetchone()
            if exists:
                continue
            balance = int(state.metrics.get(account, 0))
            self.conn.execute(
                """INSERT INTO economy_ledger
                   (turn, year, period, account, delta, balance_after, category, reason, actor)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (state.turn, state.year, state.period, account, balance, balance, "期初", "登基初始账册", "朝廷"),
            )
        self.conn.commit()

    def seed_opening_gazette(self, state: "GameState") -> None:
        """新档塞一份「即位前一月」邸报，让大臣首回合可读开局简报。"""
        from pathlib import Path
        prev_turn = state.turn - 1
        prev_year, prev_period = state.year, state.period - 1
        if prev_period < 1:
            prev_period = 12
            prev_year -= 1
        exists = self.conn.execute(
            "SELECT 1 FROM turn_reports WHERE turn=?", (prev_turn,)
        ).fetchone()
        if exists is not None:
            return
        gazette_path = Path(self.path).parent / "content" / "opening_gazette.md"
        if not gazette_path.is_file():
            return
        text = gazette_path.read_text(encoding="utf-8").strip()
        if not text:
            return
        self.conn.execute(
            "INSERT INTO turn_reports (turn, year, period, report) VALUES (?, ?, ?, ?)",
            (prev_turn, prev_year, prev_period, text),
        )
        self.conn.commit()

    # ── 人物状态 ───────────────────────────────────────────────────

    def set_character_status(
        self, state: "GameState", name: str, status: str, reason: str = ""
    ) -> None:
        valid = {"active", "offstage", "dismissed", "imprisoned", "exiled", "retired", "dead"}
        if status not in valid:
            raise ValueError(f"character status 非法：{status}")
        ousted = status in {"dismissed", "imprisoned", "exiled", "retired", "dead"}
        if ousted:
            self.conn.execute(
                "UPDATE characters SET status=?, status_reason=?, status_changed_turn=?, "
                "office='' WHERE name=?",
                (status, reason[:200], state.turn, name),
            )
        else:
            self.conn.execute(
                "UPDATE characters SET status=?, status_reason=?, status_changed_turn=? WHERE name=?",
                (status, reason[:200], state.turn, name),
            )
        self.conn.commit()

    def get_character_status(self, name: str) -> Tuple[str, str]:
        row = self.conn.execute(
            "SELECT status, status_reason FROM characters WHERE name=?", (name,)
        ).fetchone()
        if row is None:
            return ("active", "")
        return (str(row["status"]), str(row["status_reason"] or ""))

    # ── 角色 CRUD ─────────────────────────────────────────────────

    def upsert_character(self, c: dict) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO characters
               (name, office, office_type, faction, aliases, personal_skills,
                loyalty, ability, integrity, courage, style,
                birth_year, historical_death_year, historical_death_month,
                debut_year, debut_month, status, power_id, location, summary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                c.get("name", ""),
                c.get("office", ""),
                c.get("office_type", ""),
                c.get("faction", "中立"),
                json.dumps(c.get("aliases", []), ensure_ascii=False),
                json.dumps(c.get("personal_skills", []), ensure_ascii=False),
                c.get("loyalty", 50),
                c.get("ability", 50),
                c.get("integrity", 50),
                c.get("courage", 50),
                c.get("style", ""),
                c.get("birth_year", 0),
                c.get("historical_death_year", 0),
                c.get("historical_death_month", 0),
                c.get("debut_year", 0),
                c.get("debut_month", 0),
                c.get("status", "active"),
                c.get("power_id", "han"),
                c.get("location", ""),
                c.get("summary", ""),
            ),
        )

    def list_characters(self, status: str = "") -> List[Dict]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM characters WHERE status=?", (status,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM characters").fetchall()
        return self._rows_to_dicts(rows)

    def get_character_by_name(self, name: str) -> Optional[Dict]:
        row = self.conn.execute(
            "SELECT * FROM characters WHERE name=?", (name,)
        ).fetchone()
        return dict(row) if row else None

    # ── 省份 CRUD ────────────────────────────────────────────────

    def upsert_region(self, r: dict) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO regions
               (id, name, kind, population, public_support, unrest,
                natural_disaster, human_disaster, registered_land, hidden_land,
                tax_per_turn, grain_security, gentry_resistance, military_pressure,
                status, controlled_by, fiscal)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                r.get("id", ""),
                r.get("name", ""),
                r.get("kind", "州"),
                r.get("population", 0),
                r.get("public_support", 50),
                r.get("unrest", 0),
                r.get("natural_disaster", "无"),
                r.get("human_disaster", "无"),
                r.get("registered_land", 0),
                r.get("hidden_land", 0),
                r.get("tax_per_turn", 0),
                r.get("grain_security", 0),
                r.get("gentry_resistance", 0),
                r.get("military_pressure", 0),
                r.get("status", "安稳"),
                r.get("controlled_by", "han"),
                json.dumps(r.get("fiscal", {}), ensure_ascii=False),
            ),
        )

    def list_regions(self) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM regions").fetchall()
        return self._rows_to_dicts(rows)

    # ── 建筑 CRUD ─────────────────────────────────────────────────

    def upsert_building(self, b: dict) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO buildings
               (id, region_id, name, category, level, condition, maintenance, risk,
                output_metric, output_amount, status, origin, created_turn)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                b.get("id", ""),
                b.get("region_id", ""),
                b.get("name", b.get("id", "")),
                b.get("category", ""),
                b.get("level", 1),
                b.get("condition", 100),
                b.get("maintenance", 0),
                b.get("risk", 0),
                b.get("output_metric", ""),
                b.get("output_amount", 0),
                b.get("status", "正常"),
                b.get("origin", "preset"),
                b.get("created_turn", 0),
            ),
        )

    def list_buildings(self) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM buildings").fetchall()
        return self._rows_to_dicts(rows)

    def inspect_building(self, building_id: str) -> Optional[Dict]:
        row = self.conn.execute(
            "SELECT * FROM buildings WHERE id=?", (building_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── 军队 CRUD ────────────────────────────────────────────────

    def upsert_army(self, a: dict) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO armies
               (id, name, station, theater, commander, controller, troop_type,
                manpower, maintenance_per_turn, supply, morale, training,
                equipment, arrears, mobility, loyalty, status, owner_power)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                a.get("id", ""),
                a.get("name", ""),
                a.get("station", ""),
                a.get("theater", ""),
                a.get("commander", ""),
                a.get("controller", ""),
                a.get("troop_type", "步兵"),
                a.get("manpower", 0),
                a.get("maintenance_per_turn", 0),
                a.get("supply", 50),
                a.get("morale", 50),
                a.get("training", 50),
                a.get("equipment", 50),
                a.get("arrears", 0),
                a.get("mobility", 50),
                a.get("loyalty", 50),
                a.get("status", "驻守"),
                a.get("owner_power", "han"),
            ),
        )

    def list_armies(self) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM armies").fetchall()
        return self._rows_to_dicts(rows)

    # ── 势力 CRUD ──────────────────────────────────────────────

    def upsert_power(self, p: dict) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO powers
               (id, name, kind, leader, stance, leverage, satisfaction,
                military_strength, cohesion, supply, agenda, status, last_action, aliases)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                p.get("id", ""),
                p.get("name", ""),
                p.get("kind", "势力"),
                p.get("leader", ""),
                p.get("stance", "中立"),
                p.get("leverage", 50),
                p.get("satisfaction", 50),
                p.get("military_strength", 50),
                p.get("cohesion", 50),
                p.get("supply", 50),
                p.get("agenda", ""),
                p.get("status", "active"),
                p.get("last_action", ""),
                p.get("aliases", ""),
            ),
        )

    def upsert_event(self, e: dict) -> None:
        import json
        interests = e.get("interests")
        audiences = e.get("audiences")
        if isinstance(interests, list):
            interests = json.dumps(interests, ensure_ascii=False)
        if isinstance(audiences, list):
            audiences = json.dumps(audiences, ensure_ascii=False)
        self.conn.execute(
            """INSERT OR IGNORE INTO events
               (id, title, kind, summary, urgency, severity, credibility, interests, audiences)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                e.get("id", ""),
                e.get("title", ""),
                e.get("kind", ""),
                e.get("summary", ""),
                e.get("urgency", 0),
                e.get("severity", 0),
                e.get("credibility", 0),
                interests or "",
                audiences or "",
            ),
        )

    def list_powers(self) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM powers").fetchall()
        return self._rows_to_dicts(rows)

    # ── 事件记忆 ───────────────────────────────────────────────

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
            expires_turn = int(state.turn) + _ttl.get(importance, 12)
        clean_tags = [str(t).strip()[:40] for t in (tags or []) if str(t).strip()]
        self.conn.execute(
            """INSERT INTO event_memories
               (subject_type, subject_id, turn, year, period, event_type, title,
                cause, process, outcome, sentiment, importance, tags,
                source_kind, source_id, expires_turn)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(subject_type, subject_id, event_type, source_kind, source_id)
               DO UPDATE SET
                   turn=excluded.turn, year=excluded.year, period=excluded.period,
                   title=excluded.title, cause=excluded.cause, process=excluded.process,
                   outcome=excluded.outcome, sentiment=excluded.sentiment,
                   importance=excluded.importance, tags=excluded.tags,
                   expires_turn=excluded.expires_turn,
                   updated_at=CURRENT_TIMESTAMP""",
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
            "SELECT id FROM event_memories WHERE subject_type=? AND subject_id=? AND event_type=? AND source_kind=? AND source_id=?",
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
        self.conn.execute(
            """INSERT INTO event_memory_sources
               (memory_id, source_kind, source_id, excerpt, locator)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(memory_id, source_kind, source_id, locator)
               DO UPDATE SET excerpt=excluded.excerpt, updated_at=CURRENT_TIMESTAMP""",
            (
                int(memory_id),
                str(source_kind or "system"),
                str(source_id or ""),
                str(excerpt or "")[:200],
                json.dumps(locator or {}, ensure_ascii=False, sort_keys=True),
            ),
        )
        self.conn.commit()

    def prune_event_memories_for_turn(self, turn: int, per_subject: int = 3) -> None:
        rows = self.conn.execute(
            """SELECT id, subject_type, subject_id, importance, updated_at
               FROM event_memories WHERE turn=? ORDER BY subject_type, subject_id, importance DESC, id DESC""",
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
            self.conn.execute(f"DELETE FROM event_memory_sources WHERE memory_id IN ({placeholders})", delete_ids)
            self.conn.execute(f"DELETE FROM event_memories WHERE id IN ({placeholders})", delete_ids)
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
        active_issues = self.get_active_issues()
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
            f"""SELECT * FROM event_memories
                WHERE turn <= ? {expiry_clause}
                  AND (
                    (subject_type='character' AND subject_id=?)
                    OR (subject_type='faction' AND subject_id=?)
                    OR (subject_type='court' AND importance>=4)
                    OR tags LIKE ?
                    OR tags LIKE ?
                    OR tags LIKE ?
                  )""",
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
        result = []
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

    def get_memories_by_keywords(
        self, keywords: List[str], turn: int, limit: int = 8, ignore_expiry: bool = False
    ) -> List[Dict]:
        if not keywords:
            return []
        tag_conditions = " OR ".join([f"tags LIKE :kw{i}" for i in range(len(keywords))])
        named_params = {f"kw{i}": f"%{kw}%" for i, kw in enumerate(keywords)}
        all_params = {"turn": int(turn), "limit": int(limit), **named_params}
        if ignore_expiry:
            sql = (
                "SELECT * FROM event_memories "
                "WHERE turn <= :turn "
                "AND (" + tag_conditions + ") "
                "ORDER BY importance DESC, turn DESC LIMIT :limit"
            )
        else:
            all_params["exp_turn"] = int(turn)
            sql = (
                "SELECT * FROM event_memories "
                "WHERE (expires_turn IS NULL OR expires_turn >= :exp_turn) "
                "AND turn <= :turn "
                "AND (" + tag_conditions + ") "
                "ORDER BY importance DESC, turn DESC LIMIT :limit"
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

    # ── 日志 ───────────────────────────────────────────────────

    def append_log(self, turn: int, phase: str, entry: str) -> None:
        self.conn.execute(
            "INSERT INTO turn_logs (turn, year, period, message) VALUES (?, ?, ?, ?)",
            (turn, (turn - 1) // 12 + 189, ((turn - 1) % 12) + 1, entry),
        )

    def get_recent_log(self, limit: int = 20) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT * FROM turn_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return self._rows_to_dicts(rows)

    # ── 事项追踪（Issues）────────────────────────────

    def insert_issue(
        self,
        state: "GameState",
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
        severity: int = 50,
        kind: str = "situation",
        bar_value: int = 40,
        bar_good_meaning: str = "已平",
        bar_bad_meaning: str = "失控",
        inertia: int = 0,
    ) -> int:
        tags = tags or []
        self.conn.execute(
            """INSERT INTO issues
               (title, kind, origin_kind, origin_ref, origin_turn, bar_value,
                bar_good_meaning, bar_bad_meaning, status, severity,
                tags, ongoing_effects, cancellable, cancel_cost,
                effect_on_resolve, effect_on_fail,
                resolve_condition, fail_condition, last_advance_turn,
                region_hint, faction_hint, resolution_summary)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                title, kind, origin_kind, origin_ref, state.turn, bar_value,
                bar_good_meaning, bar_bad_meaning, "active", severity,
                json.dumps(tags, ensure_ascii=False),
                json.dumps(ongoing_effects or {}, ensure_ascii=False),
                cancellable, "{}",
                json.dumps(effect_on_resolve or {}, ensure_ascii=False),
                json.dumps(effect_on_fail or {}, ensure_ascii=False),
                resolve_condition, fail_condition, state.turn,
                "", "", "",
            ),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT last_insert_rowid()").fetchone()
        return int(row[0]) if row else 0

    def advance_issue(
        self,
        state: "GameState",
        issue_id: int,
        trigger_kind: str = "decree",
        delta_bar: int = 0,
        stage_text: str = "",
        narrative: str = "",
        metric_delta: Optional[Dict[str, int]] = None,
        inertia_delta: int = 0,
    ) -> Optional[Dict]:
        """推进事项，记录 issue_advances 条日志，返回更新后行（含结案状态）。"""
        row = self.conn.execute(
            "SELECT * FROM issues WHERE id=?", (int(issue_id),)
        ).fetchone()
        if row is None:
            return None

        from_val = int(row["bar_value"]) if "bar_value" in row.keys() else int(dict(row).get("progress", 40))
        new_val = max(0, min(100, from_val + delta_bar))
        status = row["status"]

        # 判断结案
        if new_val >= 80 and row["resolve_condition"]:
            status = "resolved"
        elif new_val <= 0 and row["fail_condition"]:
            status = "failed"
        elif new_val >= 80:
            status = "resolved"
        elif new_val <= 0:
            status = "failed"

        # inertia 变化
        cur_inertia = int(dict(row).get("inertia", 0))
        new_inertia = max(-10, min(10, cur_inertia + inertia_delta))

        # 更新 issues 表
        self.conn.execute("UPDATE issues SET bar_value=?, inertia=?, stage_text=?, status=? WHERE id=?",
            (new_val, new_inertia, stage_text[:120], status, int(issue_id)))

        # 记录 issue_advances
        self.conn.execute(
            """INSERT INTO issue_advances
               (issue_id, turn, trigger_kind, delta_bar,
                from_value, to_value, from_stage_text, to_stage_text,
                narrative, metric_delta)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                int(issue_id), state.turn, trigger_kind, delta_bar,
                from_val, new_val,
                dict(row).get("stage_text", "")[:120], stage_text[:120],
                narrative[:400],
                json.dumps(metric_delta or {}, ensure_ascii=False),
            ),
        )
        self.conn.commit()

        return dict(self.conn.execute(
            "SELECT * FROM issues WHERE id=?", (int(issue_id),)
        ).fetchone())

    def _issue_total_steps(self, issue_id: int) -> int:
        row = self.conn.execute("SELECT total_steps FROM issues WHERE id=?", (issue_id,)).fetchone()
        return int(row["total_steps"]) if row else 1

    def close_issue(
        self,
        state: "GameState",
        issue_id: int,
        reason: str = "resolved",
        narrative: str = "",
    ) -> Optional[Dict]:
        """结案事项，返回更新后行。reason='resolved'|'failed'。"""
        success = reason == "resolved"
        self.conn.execute(
            "UPDATE issues SET status='closed', closed_turn=?, "
            "resolution_summary=? WHERE id=?",
            (state.turn, narrative[:400], int(issue_id)),
        )
        self.conn.execute(
            """INSERT INTO issue_advances
               (issue_id, turn, trigger_kind, delta_bar,
                from_value, to_value, narrative, metric_delta)
               VALUES (?, ?, 'close', 0, ?, ?, ?, '{}')""",
            (
                int(issue_id), state.turn,
                int(self.conn.execute(
                    "SELECT bar_value FROM issues WHERE id=?", (int(issue_id),)
                ).fetchone()["bar_value"]),
                0 if success else 100,
                narrative[:400],
            ),
        )
        self.conn.commit()
        return dict(self.conn.execute(
            "SELECT * FROM issues WHERE id=?", (int(issue_id),)
        ).fetchone())

    def cancel_issue(
        self,
        state: "GameState",
        issue_id: int,
        narrative: str = "",
        applied_cost: Optional[Dict] = None,
    ) -> None:
        """撤销事项。"""
        self.conn.execute(
            "UPDATE issues SET status='cancelled', closed_turn=?, "
            "resolution_summary=? WHERE id=?",
            (state.turn, narrative[:400], int(issue_id)),
        )
        self.conn.execute(
            """INSERT INTO issue_advances
               (issue_id, turn, trigger_kind, delta_bar,
                from_value, to_value, narrative, metric_delta)
               VALUES (?, ?, 'cancel', 0, ?, ?, ?, '{}')""",
            (
                int(issue_id), state.turn,
                int(self.conn.execute(
                    "SELECT bar_value FROM issues WHERE id=?", (int(issue_id),)
                ).fetchone()["bar_value"]),
                0, narrative[:400],
            ),
        )
        self.conn.commit()

    def list_active_issues(self, tag: str = "") -> List[Dict]:
        """兼容旧名：查询进行中事项。"""
        return self.get_active_issues(tag)

    def get_active_issues(self, tag: str = "") -> List[Dict]:
        if tag:
            rows = self.conn.execute(
                "SELECT * FROM issues WHERE status='active' AND tags LIKE ? ORDER BY severity DESC, id",
                (f"%{tag}%",),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM issues WHERE status='active' ORDER BY severity DESC, id"
            ).fetchall()
        return self._rows_to_dicts(rows)

    def get_issues_by_tag(self, tag: str) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT * FROM issues WHERE tags LIKE ? ORDER BY id", (f"%{tag}%",)
        ).fetchall()
        return self._rows_to_dicts(rows)

    def get_active_issues_by_kind(self, kind: str) -> List[Dict]:
        """按 kind 筛选进行中的事项。"""
        rows = self.conn.execute(
            "SELECT * FROM issues WHERE status='active' AND kind=? ORDER BY severity DESC, id",
            (kind,),
        ).fetchall()
        return self._rows_to_dicts(rows)

    def get_issue_deadline(self, issue_id: int) -> Optional[int]:
        """返回事项的 deadline_turn，不存在则返回 None。"""
        row = self.conn.execute(
            "SELECT deadline_turn FROM issues WHERE id=?", (int(issue_id),)
        ).fetchone()
        return int(row["deadline_turn"]) if row and row["deadline_turn"] else None

    def advance_issue_with_deadline(self, state: "GameState") -> List[Dict]:
        """检查所有进行中事项的 deadline，超时则应用 fail_effect 并关闭事项。
        返回被超时关闭的事项列表。"""
        expired: List[Dict] = []
        rows = self.conn.execute(
            "SELECT * FROM issues WHERE status='active' AND deadline_turn > 0 AND deadline_turn <= ?",
            (state.turn,),
        ).fetchall()
        for row in rows:
            effect = json.loads(row["effect_on_fail"] or "{}")
            for k, v in (effect.get("metrics") or {}).items():
                if k in state.metrics and isinstance(v, (int, float)):
                    state.metrics[k] = max(0, min(100, state.metrics.get(k, 0) + int(v)))
            new_row = self.close_issue(state, int(row["id"]), reason="failed",
                                      narrative=f"截止月份已过，事项自动失败。")
            if new_row:
                expired.append({"issue_id": int(row["id"]), "title": row["title"],
                                "effect_applied": effect})
        return expired

    def find_any_issue_by_origin(self, origin_kind: str, origin_ref: str) -> Optional[Dict]:
        row = self.conn.execute(
            "SELECT * FROM issues WHERE origin_kind=? AND origin_ref=?",
            (origin_kind, origin_ref),
        ).fetchone()
        return dict(row) if row else None

    def mark_event_triggered(self, state: "GameState", event_id: str) -> None:
        """标记事件已触发（写入 event_triggers 表）。"""
        self.conn.execute(
            """INSERT OR IGNORE INTO event_triggers (event_id, turn, year, period, source)
               VALUES (?, ?, ?, ?, 'issues')""",
            (event_id, state.turn, state.year, state.period),
        )
        self.conn.commit()

    # ── 工具 ───────────────────────────────────────────────────

    def _rows_to_dicts(self, rows) -> List[Dict]:
        result = []
        for row in rows:
            d = dict(row)
            for field in (
                "aliases", "personal_skills", "interests", "audiences",
                "trigger_gate", "trigger_condition", "fiscal", "on_restore",
                "ongoing_effects", "cancel_cost", "effect_on_resolve", "effect_on_fail",
                "tags",
            ):
                if field in d and d[field]:
                    try:
                        d[field] = json.loads(d[field])
                    except Exception:
                        pass
            result.append(d)
        return result

    def load_state_key(self, key: str, default=None):
        row = self.conn.execute(
            "SELECT value FROM metrics WHERE key=?", (key,)
        ).fetchone()
        return int(row["value"]) if row else default

    def commit(self) -> None:
        self.conn.commit()

    # ── 天子技能树 ─────────────────────────────────────────────────

    def activate_skill(self, campaign_id: str, skill_id: str, turn: int) -> bool:
        """激活（学习）一个天子技能。返回是否成功。"""
        self.conn.execute(
            """INSERT OR IGNORE INTO emperor_skills
               (campaign_id, emperor_skill_id, acquired_turn)
               VALUES (?, ?, ?)""",
            (campaign_id, skill_id, turn),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM emperor_skills WHERE campaign_id=? AND emperor_skill_id=?",
            (campaign_id, skill_id),
        ).fetchone()
        return row is not None

    def deactivate_skill(self, campaign_id: str, skill_id: str) -> bool:
        """删除已学的天子技能（遗忘）。返回是否成功。"""
        cur = self.conn.execute(
            "SELECT id FROM emperor_skills WHERE campaign_id=? AND emperor_skill_id=?",
            (campaign_id, skill_id),
        ).fetchone()
        if not cur:
            return False
        self.conn.execute(
            "DELETE FROM emperor_skills WHERE campaign_id=? AND emperor_skill_id=?",
            (campaign_id, skill_id),
        )
        self.conn.commit()
        return True

    def list_acquired_skills(self, campaign_id: str) -> List[Dict]:
        """返回当前已学的所有天子技能。"""
        rows = self.conn.execute(
            "SELECT emperor_skill_id, acquired_turn FROM emperor_skills WHERE campaign_id=?",
            (campaign_id,),
        ).fetchall()
        return [{"skill_id": str(r["emperor_skill_id"]), "acquired_turn": int(r["acquired_turn"])} for r in rows]

    # ── 大臣技能授权 ───────────────────────────────────────────────

    def grant_skill_to_minister(self, campaign_id: str, minister_name: str, skill_id: str, turn: int) -> bool:
        """授权技能给大臣。返回是否成功。"""
        self.conn.execute(
            """INSERT OR IGNORE INTO minister_skill_grants
               (campaign_id, minister_name, skill_id, granted_turn, status)
               VALUES (?, ?, ?, ?, 'active')""",
            (campaign_id, minister_name, skill_id, turn),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM minister_skill_grants WHERE campaign_id=? AND minister_name=? AND skill_id=?",
            (campaign_id, minister_name, skill_id),
        ).fetchone()
        return row is not None

    def revoke_minister_skill(self, campaign_id: str, minister_name: str, skill_id: str) -> bool:
        """撤销大臣的某项技能授权。返回是否成功。"""
        cur = self.conn.execute(
            "SELECT id FROM minister_skill_grants WHERE campaign_id=? AND minister_name=? AND skill_id=? AND status='active'",
            (campaign_id, minister_name, skill_id),
        ).fetchone()
        if not cur:
            return False
        self.conn.execute(
            "UPDATE minister_skill_grants SET status='revoked' WHERE campaign_id=? AND minister_name=? AND skill_id=?",
            (campaign_id, minister_name, skill_id),
        )
        self.conn.commit()
        return True

    def active_skill_grants(self, campaign_id: str, minister_name: str) -> List[str]:
        """返回大臣当前有效的技能授权列表。"""
        rows = self.conn.execute(
            "SELECT skill_id FROM minister_skill_grants WHERE campaign_id=? AND minister_name=? AND status='active'",
            (campaign_id, minister_name),
        ).fetchall()
        return [str(r["skill_id"]) for r in rows]

    # ── 指令状态机（诏书/密令）────────────────────────────────────────────

    def create_directive(
        self,
        campaign_id: str,
        kind: str,
        status: str = "draft",
        content: str = "",
        issued_turn: int = 0,
        expires_turn: int = 0,
    ) -> int:
        """创建一条指令（如诏书），返回新记录 id。"""
        self.conn.execute(
            """INSERT INTO directives
               (campaign_id, type, kind, status, content, issued_turn, expires_turn)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (campaign_id, "decree", kind, status, content, issued_turn, expires_turn),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT last_insert_rowid()").fetchone()
        return int(row[0]) if row else 0

    def update_directive_status(self, directive_id: int, status: str) -> bool:
        """更新指令状态。返回是否成功。"""
        self.conn.execute(
            "UPDATE directives SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, directive_id),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT id FROM directives WHERE id=?", (directive_id,)).fetchone()
        return row is not None

    def list_active_directives(self, campaign_id: str) -> List[Dict]:
        """列出当前有效的指令（draft/issued/approved，不含 expired/rejected）。"""
        rows = self.conn.execute(
            """SELECT * FROM directives
               WHERE campaign_id=? AND status IN ('draft','issued','approved')
               ORDER BY issued_turn DESC, id DESC""",
            (campaign_id,),
        ).fetchall()
        return self._rows_to_dicts(rows)

    def expire_old_directives(self, current_turn: int) -> List[Dict]:
        """将已过期的指令标记为 expired，返回被过期的指令列表。"""
        rows = self.conn.execute(
            """SELECT * FROM directives
               WHERE expires_turn > 0 AND expires_turn < ? AND status NOT IN ('expired','rejected')
               ORDER BY id""",
            (int(current_turn),),
        ).fetchall()
        expired = []
        for row in rows:
            self.conn.execute(
                "UPDATE directives SET status='expired', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (int(row["id"]),),
            )
            expired.append(dict(row))
        if expired:
            self.conn.commit()
        return expired

    def get_directive(self, directive_id: int) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM directives WHERE id=?", (directive_id,)).fetchone()
        return dict(row) if row else None

    # ── 财政账目查询 ───────────────────────────────────────────────────────────

    def inspect_treasury(self, state: "GameState") -> Dict:
        """返回汉室库/内库收支细目。"""
        rows = self.conn.execute(
            """SELECT account, delta, category, reason, turn, year, period
               FROM economy_ledger ORDER BY turn DESC, id DESC LIMIT 30"""
        ).fetchall()
        entries = [dict(r) for r in rows]
        return {
            "汉室库": state.metrics.get("汉室库", 0),
            "内库": state.metrics.get("内库", 0),
            "recent_entries": entries,
        }

    # ── 天子日记 ─────────────────────────────────────────────────────────────

    def init_emperor_diary_schema(self) -> None:
        """创建 emperor_diary 表（如不存在）。"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS emperor_diary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                turn INTEGER NOT NULL,
                year INTEGER NOT NULL,
                period INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_diary_campaign
            ON emperor_diary(campaign_id, turn)""")
        self.conn.commit()

    def write_diary(
        self,
        campaign_id: str,
        turn: int,
        year: int,
        period: int,
        content: str,
    ) -> None:
        """写入一条天子日记。"""
        self.init_emperor_diary_schema()
        self.conn.execute(
            """INSERT INTO emperor_diary
               (campaign_id, turn, year, period, content)
               VALUES (?, ?, ?, ?, ?)""",
            (campaign_id, turn, year, period, str(content)[:200]),
        )
        self.conn.commit()

    def list_diary(self, campaign_id: str, limit: int = 20) -> List[Dict]:
        """返回天子日记列表（最近 limit 条）。"""
        self.init_emperor_diary_schema()
        rows = self.conn.execute(
            """SELECT id, turn, year, period, content
               FROM emperor_diary
               WHERE campaign_id=?
               ORDER BY turn DESC, id DESC
               LIMIT ?""",
            (campaign_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── 遗产/开局修正系统 ───────────────────────────────────────────────

    def insert_legacy(
        self,
        name: str,
        modifiers: Optional[Dict] = None,
        narrative_hint: str = "",
        start_turn: int = 0,
        duration_months: int = 24,
        source_issue_id: Optional[int] = None,
        legacy_key: str = "",
        clear_gate: Optional[Dict] = None,
    ) -> int:
        """插入一条遗产（开局负面修正）。"""
        mid = self.conn.execute("SELECT MAX(turn) FROM game_state").fetchone()
        start = start_turn or (int(mid["MAX(turn)"]) if mid else 0)
        self.conn.execute(
            """INSERT INTO legacies
               (name, modifiers, narrative_hint, start_turn, duration_months,
                source_issue_id, legacy_key, clear_gate, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')""",
            (name, json.dumps(modifiers or {}, ensure_ascii=False), narrative_hint,
             start, duration_months, source_issue_id, legacy_key,
             json.dumps(clear_gate or {}, ensure_ascii=False)),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT last_insert_rowid()").fetchone()
        return int(row[0]) if row else 0

    def list_active_legacies(self, turn: int = 0) -> List[Dict]:
        """返回当前激活的遗产。"""
        rows = self.conn.execute(
            "SELECT * FROM legacies WHERE status='active' ORDER BY id"
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d.get("modifiers"):
                try:
                    d["modifiers"] = json.loads(d["modifiers"])
                except Exception:
                    d["modifiers"] = {}
            if d.get("clear_gate"):
                try:
                    d["clear_gate"] = json.loads(d["clear_gate"])
                except Exception:
                    d["clear_gate"] = {}
            remaining = d.get("duration_months", 24)
            start = d.get("start_turn", 0)
            if turn > 0 and start > 0:
                elapsed = turn - start
                remaining = max(0, remaining - elapsed)
                if remaining <= 0 and d.get("duration_months", 24) != -1:
                    continue
            result.append(d)
        return result

    def expire_legacies(self, current_turn: int) -> List[Dict]:
        """将已到期的遗产标记为过期。"""
        expired = []
        rows = self.conn.execute(
            """SELECT * FROM legacies
               WHERE status='active' AND duration_months > 0
               AND (start_turn + duration_months) <= ?""",
            (current_turn,),
        ).fetchall()
        for row in rows:
            self.conn.execute("UPDATE legacies SET status='expired' WHERE id=?", (row["id"],))
            expired.append(dict(row))
        if expired:
            self.conn.commit()
        return expired

    # ── 建筑日志 ─────────────────────────────────────────────────────────

    def log_building_change(
        self,
        turn: int,
        year: int,
        period: int,
        building_id: str,
        field: str,
        old_value: str,
        new_value: str,
        delta: int = 0,
        reason: str = "",
        event_id: str = "",
        edict_id: int = 0,
        actor: str = "",
    ) -> None:
        """记录建筑变更日志。"""
        self.conn.execute(
            """INSERT INTO building_logs
               (turn, year, period, building_id, field, old_value, new_value,
                delta, reason, event_id, edict_id, actor)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (turn, year, period, building_id, field, old_value, new_value,
             delta, reason, event_id, edict_id, actor),
        )
        self.conn.commit()

    # ── kv_store（键值存储）───────────────────────────────────────────────

    def kv_get(self, key: str) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM kv_store WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def kv_set(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO kv_store (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
            (key, value),
        )
        self.conn.commit()

    def kv_delete(self, key: str) -> None:
        self.conn.execute("DELETE FROM kv_store WHERE key=?", (key,))
        self.conn.commit()

    # ── 存档备份 ──────────────────────────────────────────────────────────

    def backup_to(self, target_path: str) -> None:
        """将当前数据库备份到目标路径。"""
        import shutil
        shutil.copy2(self.path, target_path)

    def restore_from(self, source_path: str) -> None:
        """从源路径恢复数据库。"""
        import shutil
        shutil.copy2(source_path, self.path)

    # ── 预算明细（参考明末系统）──────────────────────────────────────────

    def compute_budget_lines(self, state: "GameState") -> Dict[str, Any]:
        """计算月度预算明细：收入/支出/流动。"""
        fiscal = self.get_fiscal_config()
        authority = state.metrics.get("威权", 0)

        regions = self.list_regions()
        total_tax = 0
        for reg in regions:
            base = reg.get("tax_per_turn", 0)
            eff = max(0.05, 1.0 - reg.get("gentry_resistance", 0) / 100 * 0.55
                      - max(0, reg.get("unrest", 0) - 20) / 100 * 0.30)
            total_tax += int(base * eff)

        army_expense = 0
        for army in self.list_armies():
            if army.get("status") == "active":
                army_expense += army.get("maintenance_per_turn", 0)

        rent = int(fiscal.get("皇庄_base", 10) * fiscal.get("皇庄_rate", 100) / 100)
        tribute = int(fiscal.get("内库_base", 20) * fiscal.get("皇庄_rate", 100) / 100)
        palace_exp = int(fiscal.get("宫廷_base", 7) * fiscal.get("宫廷_rate", 100) / 100)
        consort_exp = int(fiscal.get("妃嫔_base", 3) * fiscal.get("妃嫔_rate", 100) / 100)

        han_income = total_tax
        han_expense = army_expense + palace_exp
        han_net = han_income - han_expense

        nei_income = rent + tribute
        nei_expense = consort_exp
        nei_net = nei_income - nei_expense

        return {
            "国库": {
                "balance": state.metrics.get("汉室库", 0),
                "income": [
                    {"item": "田赋盐铁商税", "amount": han_income, "category": "田赋盐铁"},
                ],
                "expense": [
                    {"item": "军费", "amount": army_expense, "category": "各军军饷"},
                    {"item": "宫廷开支", "amount": palace_exp, "category": "宫廷开支"},
                ],
                "net": han_net,
            },
            "内库": {
                "balance": state.metrics.get("内库", 0),
                "income": [
                    {"item": "皇庄", "amount": rent, "category": "皇庄"},
                    {"item": "税入", "amount": tribute, "category": "内廷俸禄"},
                ],
                "expense": [
                    {"item": "妃嫔供奉", "amount": consort_exp, "category": "妃嫔供奉"},
                ],
                "net": nei_net,
            },
            "authority": authority,
        }

    # ── 地区/军队/势力预警 ────────────────────────────────────────────────

    def region_report(self, limit: int = 5) -> List[Dict]:
        """返回不安定的地区列表。"""
        rows = self.conn.execute(
            "SELECT * FROM regions ORDER BY (unrest + gentry_resistance + military_pressure) DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return self._rows_to_dicts(rows)

    def army_report(self, limit: int = 5) -> List[Dict]:
        """返回需要关注的军队列表（欠饷/低士气）。"""
        rows = self.conn.execute(
            """SELECT * FROM armies
               WHERE status='active' AND (arrears > 0 OR morale < 50)
               ORDER BY (arrears + (100 - morale)) DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return self._rows_to_dicts(rows)

    def power_report(self, exclude_self: bool = True) -> List[Dict]:
        """返回外部势力概况。"""
        if exclude_self:
            rows = self.conn.execute(
                "SELECT * FROM powers WHERE id != 'han' ORDER BY military_strength DESC LIMIT 10"
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM powers ORDER BY military_strength DESC LIMIT 10"
            ).fetchall()
        return self._rows_to_dicts(rows)

    def treasury_report(self, state: "GameState") -> Dict[str, Any]:
        """返回国库/内库概况。"""
        return {
            "汉室库": state.metrics.get("汉室库", 0),
            "内库": state.metrics.get("内库", 0),
        }

    # ── 派系影响力更新 ───────────────────────────────────────────────────

    def update_faction_influence(self, state: "GameState") -> None:
        """根据当前大臣派系和指标，计算并写入 factions 表的影响力量。"""
        from han_sim.flows import calc_faction_influence
        influences = calc_faction_influence(state, self)
        for fname, influence in influences.items():
            self.conn.execute(
                """INSERT INTO factions (name, satisfaction, leverage, agenda)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET
                       leverage=excluded.leverage,
                       updated_at=CURRENT_TIMESTAMP""",
                (fname, 50, int(influence), f"{fname}影响力{influence}"),
            )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ── 后宫系统 ─────────────────────────────────────────────────────────────

    def list_consorts(self, campaign_id: str) -> List[Dict]:
        """返回所有在册妃嫔。"""
        rows = self.conn.execute(
            "SELECT * FROM consorts WHERE campaign_id=? AND status='active' ORDER BY entered_turn DESC",
            (campaign_id,),
        ).fetchall()
        return self._rows_to_dicts(rows)

    def get_consort(self, campaign_id: str, name: str) -> Optional[Dict]:
        """获取指定妃嫔。"""
        row = self.conn.execute(
            "SELECT * FROM consorts WHERE campaign_id=? AND name=?",
            (campaign_id, name),
        ).fetchone()
        return dict(row) if row else None

    def add_consort(
        self,
        campaign_id: str,
        name: str,
        rank: str = "采女",
        traits: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        favorability: int = 50,
        palace: str = "永巷",
        portrait_id: str = "",
        turn: int = 0,
    ) -> Dict:
        """新增妃嫔入宫。"""
        traits = traits or []
        skills = skills or []
        self.conn.execute(
            """INSERT OR REPLACE INTO consorts
               (campaign_id, name, rank, traits, skills, favorability, palace, portrait_id, entered_turn)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (campaign_id, name, rank, json.dumps(traits, ensure_ascii=False),
             json.dumps(skills, ensure_ascii=False), favorability, palace, portrait_id, turn),
        )
        self.conn.commit()
        return self.get_consort(campaign_id, name)

    def update_consort(self, campaign_id: str, name: str, **fields) -> Optional[Dict]:
        """更新妃嫔属性。"""
        if not fields:
            return self.get_consort(campaign_id, name)
        allowed = {"rank", "traits", "skills", "favorability", "palace", "status", "portrait_id"}
        sets = []
        vals = []
        for k, v in fields.items():
            if k in allowed:
                if k in ("traits", "skills") and isinstance(v, list):
                    v = json.dumps(v, ensure_ascii=False)
                sets.append(f"{k}=?")
                vals.append(v)
        if not sets:
            return self.get_consort(campaign_id, name)
        vals.extend([campaign_id, name])
        self.conn.execute(
            f"UPDATE consorts SET {','.join(sets)}, updated_at=CURRENT_TIMESTAMP WHERE campaign_id=? AND name=?",
            vals,
        )
        self.conn.commit()
        return self.get_consort(campaign_id, name)

    def cultivate_consort(self, campaign_id: str, name: str, skill: str = "", trait: str = "") -> Dict:
        """调教妃嫔：添加技能或性情，同时写入consort_traits永久记录。返回更新后的妃嫔。"""
        consort = self.get_consort(campaign_id, name)
        if not consort:
            return {}
        traits = consort.get("traits", [])
        skills = consort.get("skills", [])
        if skill and skill not in skills:
            skills.append(skill)
        if trait and trait not in traits:
            traits.append(trait)
        self.update_consort(campaign_id, name, traits=traits, skills=skills)

        turn_row = self.conn.execute("SELECT MAX(turn) as t FROM game_state").fetchone()
        turn = int(turn_row["t"]) if turn_row else 0

        self.conn.execute(
            """INSERT INTO consort_events
               (campaign_id, turn, consort_name, event_type, description, favorability_delta)
               VALUES (?, ?, ?, 'cultivate', ?, 0)""",
            (campaign_id, turn, name, f"调教：习得{skill}" if skill else f"调教：性情变化{trait}"),
        )

        existing = self.conn.execute("SELECT name FROM consort_traits WHERE name=?", (name,)).fetchone()
        extra_skills = json.dumps(skills, ensure_ascii=False)
        extra_traits = json.dumps(traits, ensure_ascii=False)
        if existing:
            self.conn.execute(
                "UPDATE consort_traits SET extra_skills=?, extra_traits=?, updated_turn=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
                (extra_skills, extra_traits, turn, name),
            )
        else:
            self.conn.execute(
                "INSERT INTO consort_traits (name, extra_skills, extra_traits, updated_turn) VALUES (?, ?, ?, ?)",
                (name, extra_skills, extra_traits, turn),
            )
        self.conn.commit()
        return self.get_consort(campaign_id, name)

    def get_consort_traits(self, name: str) -> Dict:
        """返回 {extra_skills: [...], extra_traits: [...]}"""
        row = self.conn.execute("SELECT extra_skills, extra_traits FROM consort_traits WHERE name=?", (name,)).fetchone()
        if not row:
            return {"extra_skills": [], "extra_traits": []}
        return {
            "extra_skills": json.loads(row["extra_skills"] or "[]"),
            "extra_traits": json.loads(row["extra_traits"] or "[]"),
        }

    def change_consort_favorability(self, campaign_id: str, name: str, delta: int, reason: str = "") -> Optional[Dict]:
        """增减妃嫔好感度。"""
        consort = self.get_consort(campaign_id, name)
        if not consort:
            return None
        new_fav = max(0, min(100, consort["favorability"] + delta))
        self.update_consort(campaign_id, name, favorability=new_fav)
        turn_row = self.conn.execute("SELECT turn, year, period FROM game_state ORDER BY turn DESC LIMIT 1").fetchone()
        turn = turn_row["turn"] if turn_row else 0
        self.conn.execute(
            """INSERT INTO consort_events
               (campaign_id, turn, consort_name, event_type, description, favorability_delta)
               VALUES (?, ?, ?, 'favor', ?, ?)""",
            (campaign_id, turn, name, reason, delta),
        )
        self.conn.commit()
        return self.get_consort(campaign_id, name)

    def list_consort_candidates(self, status: str = "pending") -> List[Dict]:
        """返回待选秀女。"""
        rows = self.conn.execute(
            "SELECT * FROM consort_candidates WHERE status=? ORDER BY id",
            (status,),
        ).fetchall()
        return self._rows_to_dicts(rows)

    def add_consort_candidate(
        self,
        name: str,
        age: int = 18,
        background: str = "",
        appearance: int = 50,
        talent: int = 50,
        temperament: str = "温婉",
        skills: Optional[List[str]] = None,
        traits: Optional[List[str]] = None,
        portrait_id: str = "",
    ) -> Dict:
        """添加候选秀女。"""
        skills = skills or []
        traits = traits or []
        self.conn.execute(
            """INSERT INTO consort_candidates
               (name, age, background, appearance, talent, temperament, skills, traits, portrait_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, age, background, appearance, talent, temperament,
             json.dumps(skills, ensure_ascii=False), json.dumps(traits, ensure_ascii=False), portrait_id),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM consort_candidates WHERE name=?", (name,)).fetchone()
        return dict(row)

    def select_consort(self, campaign_id: str, candidate_name: str, turn: int = 0) -> Optional[Dict]:
        """皇帝选妃：秀女入宫。"""
        row = self.conn.execute("SELECT * FROM consort_candidates WHERE name=?", (candidate_name,)).fetchone()
        if not row:
            return None
        self.conn.execute(
            "UPDATE consort_candidates SET status='selected', selected_turn=? WHERE name=?",
            (turn, candidate_name),
        )
        self.add_consort(
            campaign_id=campaign_id,
            name=candidate_name,
            rank="采女",
            traits=json.loads(row["traits"] or "[]"),
            skills=json.loads(row["skills"] or "[]"),
            favorability=50,
            portrait_id=row["portrait_id"] or "",
            turn=turn,
        )
        self.conn.commit()
        return self.get_consort(campaign_id, candidate_name)

    def set_consort_portrait(self, campaign_id: str, name: str, portrait_id: str) -> Optional[Dict]:
        """设置妃嫔头像。"""
        return self.update_consort(campaign_id, name, portrait_id=portrait_id)

    def consort_event_record(
        self, campaign_id: str, turn: int, consort_name: str, event_type: str,
        description: str, favorability_delta: int = 0,
    ) -> None:
        """记录妃嫔事件。"""
        self.conn.execute(
            """INSERT INTO consort_events
               (campaign_id, turn, consort_name, event_type, description, favorability_delta)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (campaign_id, turn, consort_name, event_type, description, favorability_delta),
        )
        self.conn.commit()

    def list_consort_events(self, campaign_id: str, consort_name: str = "") -> List[Dict]:
        """返回妃嫔事件记录。"""
        if consort_name:
            rows = self.conn.execute(
                "SELECT * FROM consort_events WHERE campaign_id=? AND consort_name=? ORDER BY turn DESC",
                (campaign_id, consort_name),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM consort_events WHERE campaign_id=? ORDER BY turn DESC LIMIT 50",
                (campaign_id,),
            ).fetchall()
        return [dict(r) for r in rows]