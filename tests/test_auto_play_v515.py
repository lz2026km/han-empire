"""v5.1.5 P5-3: auto_play 平衡性测试 (无 LLM 跑 N 局, 验证脚本 + run_history)"""
import os
import subprocess
import sys
import tempfile

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


def _run_script(db_path: str, runs: int = 5) -> str:
    """调 scripts/auto_play_v51.py 子进程."""
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "auto_play_v51.py"),
         "--runs", str(runs), "--db", db_path, "--max-turn", "50"],
        capture_output=True, text=True, timeout=60,
        cwd=ROOT,
    )
    if r.returncode != 0:
        raise RuntimeError(f"auto_play_v51 failed: {r.stderr}")
    return r.stdout


def test_auto_play_runs_and_records(tmp_path):
    """v5.1.5 P5-3: auto_play 跑 N 局后 run_history 表有 N 行."""
    db = str(tmp_path / "balance.db")
    out = _run_script(db, runs=5)
    assert "崩盘率" in out
    assert "ending 分布" in out
    from han_sim.db import GameDB
    g = GameDB(db)
    rows = g.conn.execute("SELECT COUNT(*) AS c FROM run_history").fetchone()["c"]
    assert rows == 5
    g.close()


def test_auto_play_endings_varied(tmp_path):
    """v5.1.5 P5-3: 30 局 (seed 范围 2026..2055) 至少应触发 1 种非崩盘结局
    (证明 detect_ending 路径可被命中, 平衡性通过)."""
    db = str(tmp_path / "balance2.db")
    _run_script(db, runs=30)
    from han_sim.db import GameDB
    g = GameDB(db)
    rows = g.conn.execute(
        "SELECT DISTINCT ending FROM run_history"
    ).fetchall()
    g.close()
    endings = {r["ending"] for r in rows}
    # 至少 1 种 (崩盘 之外) — 30 局纯随机应至少 1 局非崩盘
    # 若只崩盘也接受, 但不通过
    non_bengkui = endings - {"崩盘"}
    # 至少要触发 1 次崩盘 (代码路径覆盖)
    assert "崩盘" in endings, "no 崩盘 triggered, detect_ending path not covered"
    # 30 局应至少 1 局非崩盘
    assert len(non_bengkui) >= 1, (
        f"all 30 runs collapsed to 崩盘, no variety. endings={endings}"
    )


def test_auto_play_report_shape(tmp_path):
    """v5.1.5 P5-3: 报告含 局数/耗时/平均回合/崩盘率/ending 分布 5 段."""
    db = str(tmp_path / "balance3.db")
    out = _run_script(db, runs=3)
    for k in ("局数", "耗时", "平均回合", "崩盘率", "ending 分布"):
        assert k in out, f"report missing {k}\n{out}"


def test_auto_play_quick(tmp_path):
    """v5.1.5 P5-3: 10 局 < 5s (无 LLM 性能断言)."""
    import time
    db = str(tmp_path / "balance4.db")
    t0 = time.time()
    _run_script(db, runs=10)
    elapsed = time.time() - t0
    assert elapsed < 5.0, f"auto_play took {elapsed:.1f}s, expected < 5s"
