"""汉献帝之末路 - 入口文件。"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    """支持 CLI 和桌面两种启动方式。"""
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        print("正在启动 CLI 模式...")
        try:
            from han_sim.cli.terminal import run_cli
            run_cli()
        except ImportError as e:
            print(f"CLI 模式不可用：{e}")
            print("请使用 python launcher.py 启动桌面版")
            sys.exit(1)
    else:
        print("正在启动桌面版...")
        from launcher import main as launcher_main
        launcher_main()


if __name__ == "__main__":
    main()
