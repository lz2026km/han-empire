"""路径工具。"""

import os

# 项目根目录（web_app.py / launcher.py 所在目录的父目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(PROJECT_ROOT, "content")


def user_data_path(filename: str) -> str:
    """返回 ~/.hermes/han-empire/filename。"""
    base = os.path.expanduser("~/.hermes/han-empire")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, filename)


def content_path(filename: str) -> str:
    return os.path.join(CONTENT_DIR, filename)