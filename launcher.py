"""汉献帝之末路 pywebview 桌面启动器。"""

import json
import os
import random
import shutil
import socket
import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import webview
except ImportError:
    webview = None

from han_sim.llm_config import load_runtime_llm, RUNTIME_LLM_PATH


def _find_free_port(start: int = 7860, end: int = 7999) -> int:
    for _ in range(end - start):
        port = random.randint(start, end)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("无法找到可用端口")


def _check_api_key() -> bool:
    runtime = load_runtime_llm()
    api_key = (runtime.get("api_key", "") or os.environ.get("OPENAI_API_KEY", "")).strip()
    return bool(api_key)


def _prompt_api_key(gui_root: str) -> bool:
    """显示 GUI 对话框让用户配置 API key。返回是否配置成功。"""
    if gui_root is None:
        return False

    import tkinter as tk
    from tkinter import ttk, messagebox

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.title("汉献帝之末路 - 配置")

    win = tk.Toplevel(root)
    win.title("配置 API Key")
    win.resizable(False, False)
    win.update_idletasks()
    w, h = 480, 320
    x = (win.winfo_screenwidth() // 2) - (w // 2)
    y = (win.winfo_screenheight() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(win, text="请配置 LLM API Key", font=("Microsoft YaHei", 14, "bold")).pack(pady=(20, 10))
    tk.Label(win, text="Base URL：", font=("Microsoft YaHei", 10)).place(x=40, y=60)
    base_url_var = tk.StringVar(value="https://api.deepseek.com/v1")
    tk.Entry(win, textvariable=base_url_var, width=45).place(x=40, y=85)

    tk.Label(win, text="Model：", font=("Microsoft YaHei", 10)).place(x=40, y=115)
    model_var = tk.StringVar(value="deepseek-v4-flash")
    tk.Entry(win, textvariable=model_var, width=45).place(x=40, y=140)

    tk.Label(win, text="API Key：", font=("Microsoft YaHei", 10)).place(x=40, y=170)
    api_key_var = tk.StringVar()
    api_key_entry = tk.Entry(win, textvariable=api_key_var, width=45, show="*")
    api_key_entry.place(x=40, y=195)

    result = {"ok": False}

    def save():
        os.makedirs(os.path.dirname(RUNTIME_LLM_PATH), exist_ok=True)
        payload = {
            "base_url": base_url_var.get().strip(),
            "model": model_var.get().strip(),
            "api_key": api_key_var.get().strip(),
        }
        with open(RUNTIME_LLM_PATH, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        result["ok"] = True
        win.destroy()
        root.destroy()

    def cancel():
        win.destroy()
        root.destroy()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=20)
    ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.LEFT, padx=10)
    ttk.Button(btn_frame, text="取消", command=cancel).pack(side=tk.LEFT, padx=10)

    win.protocol("WM_DELETE_WINDOW", cancel)
    win.transient(root)
    win.grab_set()
    root.mainloop()
    return result["ok"]


def _start_flask_server(port: int) -> threading.Thread:
    from server import app
    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, debug=False, threaded=True),
        daemon=True,
    )
    thread.start()
    return thread


def _resolve_url(path: str) -> str:
    if os.path.isdir(path):
        return path
    return path


class WindowController:
    def __init__(self):
        self.window = None
        self.server_thread = None

    def start(self):
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        if not _check_api_key():
            if not _prompt_api_key("tk"):
                print("[启动器] 未配置 API key，退出。")
                sys.exit(0)

        port = _find_free_port()
        self.server_thread = _start_flask_server(port)
        print(f"[启动器] Flask 服务已启动：http://127.0.0.1:{port}")

        web_dir = os.path.join(os.path.dirname(__file__), "web", "dist")
        if os.path.isdir(web_dir):
            url = f"http://127.0.0.1:{port}"
        else:
            url = f"http://127.0.0.1:{port}"

        if webview is None:
            print("[启动器] pywebview 未安装，正在打开浏览器...")
            webbrowser.open(url)
            print("[启动器] 浏览器已打开。关闭此窗口退出。")
            input()
            return

        self.window = webview.create_window(
            "汉献帝之末路",
            url,
            width=1280,
            height=800,
            min_size=(960, 600),
            resizable=True,
            js_api=None,
        )

        webview.start(debug=False)

    def stop(self):
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                pass
        print("[启动器] 已关闭。")


def main():
    print("=" * 50)
    print("  汉献帝之末路 - 桌面版")
    print("=" * 50)
    print()

    try:
        controller = WindowController()
        controller.start()
    except KeyboardInterrupt:
        print("\n[启动器] 收到中断信号，正在退出...")
    except Exception as e:
        print(f"[启动器] 错误：{e}")
        sys.exit(1)
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()