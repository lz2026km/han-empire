# -*- mode: python ; coding: utf-8 -*-
# v2.0.0 Phase 4.5: PyInstaller 打包配置
# 主公: Win 10/11 点 EXE 即可
# 用法: pyinstaller han_empire.spec
#
# 输出: dist/汉献帝之末路.exe (单文件, 含 Python 解释器+所有依赖)
# 大小: ~80-120 MB (含 agno + flask + openai + pymupdf)
#
# 注意: 重新打包前先删 build/ dist/ 两个目录

import sys
from pathlib import Path

block_cipher = None

# 项目根
PROJECT_ROOT = Path(SPECPATH).resolve()

# ── 数据文件 (含 .agno_skills/ 18 个 SKILL.md + static/ + templates/) ──
datas = [
    # 技能库 (LLM 驱动核心 - 18 个 SKILL.md)
    (str(PROJECT_ROOT / '.agno_skills'), '.agno_skills'),
    # 静态资源
    (str(PROJECT_ROOT / 'web' / 'dist'), 'web/dist'),
    (str(PROJECT_ROOT / 'han_sim' / 'static'), 'han_sim/static'),
    (str(PROJECT_ROOT / 'han_sim' / 'templates'), 'han_sim/templates'),
    (str(PROJECT_ROOT / 'han_sim' / 'data'), 'han_sim/data'),
    # 角色/事件 JSON
    (str(PROJECT_ROOT / 'data'), 'data'),
]

# ── 隐藏导入 (PyInstaller 自动分析不到的) ──
hiddenimports = [
    # agno (LLM 框架)
    'agno',
    'agno.agent',
    'agno.models',
    'agno.models.openai',
    'agno.memory',
    # flask
    'flask',
    'flask_cors',
    'werkzeug',
    # pywebview 桌面
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    # tkinter (API key 配置窗)
    'tkinter',
    # agno 工具
    'pydantic',
    'requests',
    'httpx',
]

# ── 排除 (大依赖, 不打包) ──
excludes = [
    'matplotlib',
    'numpy.tests',
    'pandas.tests',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'notebook',
    'IPython',
    'jupyter',
    'pytest',
    'sphinx',
    'pytest_asyncio',
]

a = Analysis(
    ['run_windows.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='汉献帝之末路',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # UPX 压缩, 减小体积
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不开 cmd 窗口 (主公要 GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 图标: 用 web/favicon.ico
    icon=str(PROJECT_ROOT / 'web' / 'favicon.ico') if (PROJECT_ROOT / 'web' / 'favicon.ico').exists() else None,
)
