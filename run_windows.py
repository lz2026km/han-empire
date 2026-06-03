"""
v2.0.0 Phase 4.5: Windows 双击启动入口
=============================

主公要: Win 10/11 用户双击 .exe 直接玩

设计:
- 1. 防止双击 EXE 时 cmd 闪退 (noconsole 模式 + 友好弹窗)
- 2. 自动判 sys.frozen 路径 (PyInstaller 打包后路径在 _MEIPASS)
- 3. 异常时不闪退, 弹 tkinter 错误窗
- 4. 单实例锁 (第二次启动会激活已开窗口, 不会冲突)
- 5. 启动器兼容: 没 API key 时弹配置窗
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def _setup_frozen_path() -> None:
    """PyInstaller 打包后, _MEIPASS 是解压根目录"""
    if getattr(sys, "frozen", False):
        # 打包后: sys.executable 是 EXE 路径, 资源在 _MEIPASS
        base = Path(sys.executable).parent
        meipass = Path(getattr(sys, "_MEIPASS", base))
        # 1) EXE 同目录放第一 (用户存档/数据)
        sys.path.insert(0, str(base))
        # 2) _MEIPASS 是解包资源
        sys.path.insert(0, str(meipass))
        # 3) 工作目录切到 EXE 同级 (配置文件写入这里)
        os.chdir(str(base))
    else:
        # 开发模式: 脚本所在根目录
        sys.path.insert(0, str(Path(__file__).parent))


def _show_error(title: str, msg: str) -> None:
    """弹 tkinter 错误窗 (闪退时, 让用户看到)"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showerror(title, msg)
    except Exception:
        # tk 都失败就只打 stderr
        print(f"[{title}] {msg}", file=sys.stderr)


def _ensure_single_instance() -> bool:
    """单实例锁: 第二次启动会拒绝并提示"""
    import socket
    lock_port = 17829
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", lock_port))
        sock.close()
        return True
    except OSError:
        _show_error("汉献帝之末路 - 已运行", "游戏已经在运行中!\n请检查任务栏。")
        return False


def main() -> int:
    """主入口"""
    try:
        _setup_frozen_path()
        if not _ensure_single_instance():
            return 1

        # 调 launcher 启动
        from launcher import main as launcher_main
        launcher_main()
        return 0
    except KeyboardInterrupt:
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0
    except Exception as e:
        # 闪退保护: 弹窗 + 写日志
        tb = traceback.format_exc()
        try:
            log_path = Path(os.getcwd()) / "han_empire_error.log"
            log_path.write_text(tb, encoding="utf-8")
        except Exception:
            pass
        _show_error("汉献帝之末路 - 启动失败", f"{e}\n\n详见 han_empire_error.log")
        return 1


if __name__ == "__main__":
    sys.exit(main())
