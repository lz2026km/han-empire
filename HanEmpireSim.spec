# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for 汉献帝之末路 v5.2.0 桌面包。

打 onedir（推荐，首启快）：
    pyinstaller HanEmpireSim.spec

打 onefile（单文件，启动慢 ~3-5s）：
    pyinstaller --onefile HanEmpireSim.spec

前置：先 `npm run build` 生成 web/dist/

产物：
- Windows: dist/HanEmpireSim/HanEmpireSim.exe + 资源
- macOS: dist/HanEmpireSim.app (自动 BUNDLE)
- Linux: dist/HanEmpireSim/

双击 EXE 后：自动开浏览器到 http://127.0.0.1:5555
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules
from pathlib import Path

# 收集 flask + openai SDK 的隐藏 import
_flask_data, _flask_bin, _flask_hidden = collect_all("flask")
_flask_cors_data, _, _flask_cors_hidden = collect_all("flask_cors")
_openai_data, _openai_bin, _openai_hidden = collect_all("openai")
_urllib_data, _urllib_bin, _urllib_hidden = collect_all("urllib3")


def tree_datas(root: str, dest: str, exclude_parts=()):
    """v5.2.0 P6-19: 递归收集文件, 排除 dev 缓存."""
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


# han_sim + flask + 第三方 hidden imports
hiddenimports = (
    _flask_hidden
    + _flask_cors_hidden
    + _openai_hidden
    + _urllib_hidden
    + collect_submodules("han_sim")
    + collect_submodules("werkzeug")
    + [
        "han_sim.image_gen",
        "han_sim.legacy_stats",
        "han_sim.llm_config",
        "han_sim.llm_router",
        "server",
        "launcher",
        "sqlite3",
    ]
)

# 资源: web/dist (Vite build) + web/public (静态资源) + data
datas = (
    _flask_data + _flask_cors_data + _openai_data + _urllib_data
    + tree_datas("web/dist", "web/dist", exclude_parts={"_backup", "_v4"})
    + tree_datas("web/public", "web/public", exclude_parts={"_backup", "v4-epic"})
    + [
        ("data", "data"),
        (".env.example", "."),
    ]
)

binaries = _flask_bin + _openai_bin + _urllib_bin

block_cipher = None

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "PyQt5", "PyQt6", "PySide2", "PySide6",
        "matplotlib", "pandas",
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
    console=False,  # 双击无终端窗口, debug 改 True
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

# macOS .app bundle
import sys
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="HanEmpireSim.app",
        icon=None,
        bundle_identifier="com.local.hanempire",
        info_plist={
            "NSHighResolutionCapable": True,
            "LSBackgroundOnly": False,
            "CFBundleShortVersionString": "5.2.0",
            "CFBundleVersion": "5.2.0",
        },
    )
