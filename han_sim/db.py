"""SQLite 游戏数据库。L3。

完整 schema + 种子数据初始化 + 状态持久化。启动时由 GameSession 注入 content。
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

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
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_schema()
        self.init_fiscal_config()
        if self.content is None:
            from han_sim.content import load_game_content
            self.content = load_game_content()

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
        """)
        self.conn.commit()

    def init_fiscal_config(self) -> None:
        """汉末财政配置：田赋/盐铁/商税/兵饷/官俸/宫廷等。"""
        rows = [
            ("田赋_rate", 60, "rate", "诸州田赋实收率%，60%为汉末默认"),
            ("口赋_rate", 100, "rate", "人口钱实收率%"),
            ("盐铁_rate", 70, "rate", "盐铁专营实收率%，可升至90"),
            ("商税_rate", 40, "rate", "关卡商税实收率%，40%为汉末默认"),
            ("兵饷_base", 80, "base", "常备军兵饷季度额，万钱"),
            ("官俸_base", 50, "base", "在京百官俸禄季额，万钱"),
            ("宫廷_base", 30, "base", "皇室日常用度季额，万钱"),
            ("工程_base", 10, "base", "工部季度维护支出，万钱"),
            ("赈济_base", 10, "base", "制度性赈灾备用，万钱"),
            ("内库_base", 20, "base", "皇庄/没收财产季均上缴，万钱"),
            ("皇威_rate", 50, "rate", "皇威影响诏令成功率%"),
        ]
        for key, value, kind, note in rows:
            self.conn.execute(
                """INSERT INTO fiscal_config (key, value, kind, note)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
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
        """首次启动时将 content/*.json 全部写入 DB。已有数据不覆盖。"""
        if self.table_has_rows("characters"):
            return  # 已初始化则跳过

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

    def get_character_status(self, name: str) -> tuple[str, str]:
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

    # ── 事项追踪（Issues）──────────────────────────────

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

    def advance_issue(self, issue_id: int, steps: int = 1, state: Optional["GameState"] = None) -> None:
        turn = state.turn if state else self.load_state_key("turn", 1)
        total = self._issue_total_steps(issue_id)
        pct = (100 // max(1, total)) * steps
        self.conn.execute(
            "UPDATE issues SET current_step=current_step+?, progress=progress+?, "
            "last_advance_turn=? WHERE id=?",
            (steps, pct, turn, issue_id),
        )
        self.conn.commit()

    def _issue_total_steps(self, issue_id: int) -> int:
        row = self.conn.execute("SELECT total_steps FROM issues WHERE id=?", (issue_id,)).fetchone()
        return int(row["total_steps"]) if row else 1

    def close_issue(self, issue_id: int, success: bool, state: Optional["GameState"] = None) -> None:
        turn = state.turn if state else self.load_state_key("turn", 1)
        self.conn.execute(
            "UPDATE issues SET status='closed', closed_turn=?, success=? WHERE id=?",
            (turn, 1 if success else 0, issue_id),
        )
        self.conn.commit()

    def get_active_issues(self, tag: str = "") -> List[Dict]:
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
        row = self.conn.execute(
            "SELECT * FROM issues WHERE origin_kind=? AND origin_ref=?",
            (origin_kind, origin_ref),
        ).fetchone()
        return dict(row) if row else None

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

    def close(self) -> None:
        self.conn.close()