#!/usr/bin/env python3
"""v5.2.0 P6-19: 桌面包启动器 (汉献帝之末路 EXE)

启动 Flask server + 自动开浏览器, console=False 时无终端窗口.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser


def _find_free_port(preferred: int = 5555) -> int:
    for port in (preferred, 5556, 5557, 5558, 0):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                if port != 0:
                    return port
                return s.getsockname()[1]
        except OSError:
            continue
    return 5555


def _open_browser(url: str, delay: float = 2.0) -> None:
    """v5.2.0 P6-19: 2s 后开浏览器 (给 Flask 启动时间)."""
    def _run():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()


def main() -> int:
    # 改 workdir 到 EXE 所在目录 (PyInstaller _MEIPASS 之外)
    if getattr(sys, "frozen", False):
        bundle_dir = os.path.dirname(sys.executable)
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(bundle_dir)

    # 端口
    port = int(os.environ.get("PORT", "5555"))
    port = _find_free_port(port)
    os.environ["PORT"] = str(port)

    # 启动 Flask (在子线程)
    print(f"汉献帝之末路 v5.2.0 启动中...")
    print(f"  端口: {port}")
    print(f"  浏览器: http://127.0.0.1:{port}")

    from server import app  # noqa: E402
    _open_browser(f"http://127.0.0.1:{port}", delay=1.5)

    try:
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n再见, 主公。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
