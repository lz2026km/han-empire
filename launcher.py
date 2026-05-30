"""Han Empire — 汉献帝之末路 启动器。"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

# 确保 han_sim 在路径中
sys.path.insert(0, str(Path(__file__).parent))

from han_sim.content import load_game_content
from han_sim.session import GameSession


def main():
    print("=" * 50)
    print("  汉献帝之末路")
    print("  Han Empire — A Historical LLM Game")
    print("=" * 50)
    print()
    print("【背景】189年，董卓进京，废少帝立献帝。")
    print("         天子先被董卓控制，后被曹操迁都许昌。")
    print("         名为天子，实为阶下囚。")
    print("         汉室能否复兴，取决于你的抉择。")
    print()

    campaign_id = str(uuid.uuid4())[:8]
    content = load_game_content()
    session = GameSession.new(campaign_id, content)

    print(f"【开局】{session.state.year}年{session.state.period}月")
    print(f"        汉室库：{session.state.metrics.get('汉室库', 0)}万两")
    print(f"        声望：{session.state.metrics.get('声望', 0)}")
    print(f"        威权：{session.state.metrics.get('威权', 0)}")
    print(f"        藩镇：{session.state.metrics.get('藩镇', 0)}")
    print()

    ministers = session.get_active_ministers()
    print("【可用大臣】")
    for m in ministers:
        print(f"  - {m['name']}（{m['office']}）")
    print()

    print("输入 exit 退出游戏")
    print()
    while True:
        try:
            cmd = input("天子 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n游戏结束。")
            break

        if not cmd:
            continue
        if cmd in ("exit", "quit", "q"):
            print("游戏结束。")
            break

        print("【系统】功能开发中，请稍候...")
        print()


if __name__ == "__main__":
    main()