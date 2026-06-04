#!/usr/bin/env python3
"""v5.2.0 P6-19: 一键打包 EXE (Windows / macOS / Linux)

前置:
  1. pip install pyinstaller
  2. cd web && npm install && npm run build   # 产出 web/dist/
  3. cd .. && python scripts/build_exe.py     # 跑本脚本

产物:
  - dist/HanEmpireSim/HanEmpireSim.exe (Windows)
  - dist/HanEmpireSim.app (macOS)
  - dist/HanEmpireSim/ (Linux)

调试: 改 console=True 重新打, 双击 EXE 看 Flask 启动日志
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _check_dependencies() -> bool:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[ERR] PyInstaller 未安装. 跑: pip install pyinstaller")
        return False
    web_dist = ROOT / "web" / "dist"
    if not web_dist.exists():
        print(f"[ERR] web/dist 不存在. 跑: cd web && npm install && npm run build")
        return False
    return True


def _build() -> int:
    print("=" * 60)
    print("汉献帝之末路 v5.2.0 EXE 打包")
    print("=" * 60)
    if not _check_dependencies():
        return 1
    spec = ROOT / "HanEmpireSim.spec"
    if not spec.exists():
        print(f"[ERR] spec 不存在: {spec}")
        return 1
    print(f"[1/3] 检查依赖 ... OK")
    print(f"[2/3] 调 pyinstaller {spec.name} ...")
    rc = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec), "--noconfirm"],
        cwd=str(ROOT),
    ).returncode
    if rc != 0:
        print(f"[FAIL] pyinstaller rc={rc}")
        return rc
    print(f"[3/3] 清理 pycache ...")
    for d in [ROOT / "build", ROOT / "__pycache__"]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    dist = ROOT / "dist" / "HanEmpireSim"
    if dist.exists():
        size_mb = sum(p.stat().st_size for p in dist.rglob("*") if p.is_file()) / 1024 / 1024
        print(f"\n[DONE] 产物: {dist} (~{size_mb:.0f} MB)")
        if sys.platform == "win32":
            print(f"  双击: {dist / 'HanEmpireSim.exe'}")
        elif sys.platform == "darwin":
            print(f"  双击: {ROOT / 'dist' / 'HanEmpireSim.app'}")
        else:
            print(f"  跑: {dist / 'HanEmpireSim'}")
    else:
        print("[WARN] dist/HanEmpireSim 未找到, 查 pyinstaller 日志")
    return 0


if __name__ == "__main__":
    sys.exit(_build())
