# -*- mode: python ; coding: utf-8 -*-
"""汉献帝之末路 PyInstaller 构建脚本 (build.spec)。"""

import os
import sys
from pathlib import Path

block_cipher = None

project_root = Path(SPECFILE).parent if 'SPECFILE' in dir() else Path(__file__).parent
assets_path = project_root / 'web' / 'public'
han_sim_path = project_root / 'han_sim'
content_path = project_root / 'content'

a = Analysis(
    ['launcher.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(assets_path / 'images'), 'web/public/images'),
        (str(assets_path / 'animations'), 'web/public/animations'),
        (str(assets_path / 'icons.svg'), 'web/public/icons.svg'),
        (str(assets_path / 'favicon.svg'), 'web/public/favicon.svg'),
        (str(content_path), 'content'),
    ],
    hiddenimports=[
        'webview', 'flask', 'jinja2', 'werkzeug', 'markupsafe', 'click',
        'itsdangerous', 'colorama', 'PIL', 'PIL._imaging', 'ctypes', 'socket',
        'threading', 'json', 'random', 'shutil', 're', 'sqlite3', 'uuid',
        'unicodedata', 'struct', 'subprocess', 'inspect', 'traceback',
        'functools', 'collections', 'itertools', 'operator', 'builtins',
        'typing', 'dataclasses', 'types', 'pathlib', 'configparser', 'getpass',
        'platform', 'errno', 'signal', 'fcntl', 'select', 'selectors', 'heapq',
        'bisect', 'weakref', 'copy', 'ast', 'io', 'os.path', 'time', 'locale',
        'calendar', 'html', 'html.parser', 'html.entities',
        'xml.etree.ElementTree', 'xml.parsers.expat', 'gzip', 'zipfile',
        'tarfile', 'fileinput', 'linecache', 'tokenize', 'keyword', 'token',
        'dis', 'code', 'codeop', 'pty', 'tty', 'termios', 'sysconfig', 'abc',
        'fractions', 'decimal', 'numbers', 'cmath', 'math', '_thread',
        '_weakrefset', '_bootlocale', '_compat_pickle', '_compression',
        '_markupbase', '_opcode_metadata', '_pydecimal', '_strptime',
        '_symtable', '_threading_local', 'mimetypes', 'contextlib', 'copyreg',
        'genericpath', 'ntpath', 'posixpath', 'warnings', 'encodings',
        'encodings.utf_8', 'encodings.ascii', 'encodings.latin_1',
        'encodings.gbk', 'encodings.gb2312', 'encodings.cp1252', 'base64',
        'quopri', 'uu', 'binhex', 'bz2', 'lzma', 'zlib',
        'flask_cors',
    ],
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
    version='version_info.txt',
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

single_exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='HanEmpireSim_Single',
    debug=False,
    console=False,
    icon=str(assets_path / 'favicon.svg') if (assets_path / 'favicon.svg').exists() else None,
    version='version_info.txt',
)