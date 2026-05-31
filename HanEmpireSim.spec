# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for 汉献帝之末路 桌面包。

打 onedir（首选）：
    pyinstaller HanEmpireSim.spec

打 onefile（单文件，启动慢）：
    pyinstaller --onefile HanEmpireSim.spec

产物：dist/HanEmpireSim/
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules
from pathlib import Path

# agno / openai / tiktoken
_agno_data, _agno_bin, _agno_hidden = collect_all("agno")
_openai_data, _openai_bin, _openai_hidden = collect_all("openai")
_tiktoken_data, _tiktoken_bin, _tiktoken_hidden = collect_all("tiktoken")
# pywebview
_webview_data, _webview_bin, _webview_hidden = collect_all("webview")


def tree_datas(root: str, dest: str, exclude_parts=()):
    """Collect files under root while excluding dev-only backup/cache folders."""
    root_path = Path(root)
    rows = []
    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root_path)
        parts = set(rel.parts)
        if path.name == ".DS_Store" or any(part in parts for part in exclude_parts):
            continue
        rows.append((str(path), str(Path(dest) / rel.parent)))
    return rows


hiddenimports = (
    _agno_hidden
    + _openai_hidden
    + _tiktoken_hidden
    + _webview_hidden
    + collect_submodules("uvicorn")
    + collect_submodules("fastapi")
    + collect_submodules("anyio")
    + collect_submodules("starlette")
    + [
        "han_sim",
        "han_sim.cli.terminal",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
    ]
)

datas = (
    _agno_data
    + _openai_data
    + _tiktoken_data
    + _webview_data
    + tree_datas("web/dist", "web/dist", exclude_parts={"_backup_rgb", "_original_before_cutout"})
    + tree_datas("web/public", "web/public", exclude_parts={"_backup_rgb", "_original_before_cutout"})
    + [
        ("content", "content"),
    ]
)

binaries = _agno_bin + _openai_bin + _tiktoken_bin + _webview_bin

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "matplotlib",
        "pandas",
        "numpy.tests",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="HanEmpireSim",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="HanEmpireSim",
)