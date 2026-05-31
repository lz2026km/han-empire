# -*- mode: python ; coding: utf-8 -*-
"""汉献帝之末路 PyInstaller 打包配置。
   目标: Windows exe桌面程序
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

project_root = Path(__file__).parent
assets_path = project_root / 'web' / 'public'
han_sim_path = project_root / 'han_sim'
content_path = project_root / 'content'

# 收集所有动态导入的模块
_agno_data, _agno_bin, _agno_hidden = collect_all("agno")
_openai_data, _openai_bin, _openai_hidden = collect_all("openai")
_tiktoken_data, _tiktoken_bin, _tiktoken_hidden = collect_all("tiktoken")
_webview_data, _webview_bin, _webview_hidden = collect_all("webview")


def tree_datas(root: str, dest: str, exclude_parts=()):
    """收集目录下的文件，排除指定部分"""
    root_path = Path(root)
    rows = []
    if not root_path.exists():
        return rows
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
        "flask",
        "jinja2",
        "werkzeug",
        "markupsafe",
        "click",
        "itsdangerous",
        "colorama",
        "PIL",
        "PIL._imaging",
        "ctypes",
        "socket",
        "threading",
        "json",
        "random",
        "shutil",
        "re",
        "sqlite3",
        "uuid",
        "unicodedata",
        "struct",
        "subprocess",
        "inspect",
        "traceback",
        "functools",
        "collections",
        "itertools",
        "operator",
        "builtins",
        "typing",
        "dataclasses",
        "types",
        "pathlib",
    ]
)

datas = (
    _agno_data
    + _openai_data
    + _tiktoken_data
    + _webview_data
    + tree_datas(str(assets_path / 'portraits'), 'web/public/portraits')
    + tree_datas(str(assets_path / 'images'), 'web/public/images')
    + tree_datas(str(assets_path / 'animations'), 'web/public/animations')
    + [
        (str(assets_path / 'icons.svg'), 'web/public'),
        (str(assets_path / 'favicon.svg'), 'web/public'),
    ]
    + tree_datas(str(content_path), 'content')
)

binaries = _agno_bin + _openai_bin + _tiktoken_bin + _webview_bin

a = Analysis(
    ['launcher.py'],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    keys=[],
    exclusionplugins=[],
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
    name='HanEmpireSim',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets_path / 'favicon.svg') if (assets_path / 'favicon.svg').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='HanEmpireSim',
)