"""汉献帝之末路 启动器 + 回合交互 REPL。"""



import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from han_sim.content import load_game_content
from han_sim.decree import issue_decree
from han_sim.session import GameSession, SummonResult
from han_sim.simulation import run_monthly_simulation


def _print_metrics(state):
    print(f"  汉室库：{state.metrics.get('汉室库', 0)}万两")
    print(f"  声望：{state.metrics.get('声望', 0)}/100")
    print(f"  威权：{state.metrics.get('威权', 0)}/100")
    print(f"  藩镇：{state.metrics.get('藩镇', 0)}/100")


def _cmd_summon(session: GameSession, args: str) -> None:
    """召见大臣：summon 张昭"""
    parts = args.split(maxsplit=1)
    if not parts:
        print("用法：summon <大臣姓名> [问题]")
        return
    name = parts[0]
    instruction = parts[1] if len(parts) > 1 else "本月局势如何？"
    result = session.summon_minister(name, instruction)
    print()
    print(f"【{name}】")
    print(result.chat_text)
    print()


def _cmd_decree(session: GameSession, args: str) -> None:
    """拟旨：decree 赈济灾民"""
    if not args:
        print("用法：decree <意图>  （如：decree 赈济灾民）")
        return
    result = issue_decree(args, session.state, session.db)
    print()
    print(f"【诏书已下】《{result.decree.decree_type}》")
    print("─" * 40)
    print(result.decree.full_text)
    print("─" * 40)
    if result.log_entries:
        print("效果：" + "；".join(result.log_entries))
    print()


def _cmd_review(session: GameSession) -> None:
    """月末推演：review"""
    triggered = session.db.load_state("triggered_events") or []
    sim = run_monthly_simulation(session.state, session.db, triggered)
    print()
    print(f"【{sim.narrative[:60]}...】" if len(sim.narrative) > 60 else f"【{sim.narrative}】")
    print()
    if sim.historical:
        for e in sim.historical:
            print(f"  ▶ 历史事件：{e['title']}")
    if sim.threshold_crisis:
        for e in sim.threshold_crisis:
            print(f"  ▶ 危机事件：{e['title']}")
    if sim.random_events:
        for e in sim.random_events:
            print(f"  ▶ 突发：{e['title']}")
    print()
    print("【本月结算】")
    print(f"  财政：{'盈余' if sim.fiscal.get('net',0) >= 0 else '亏损'}{abs(sim.fiscal.get('net',0))}万两")
    for k, v in sim.metrics_delta.items():
        print(f"  {k} {v:+d}")
    print()
    _print_metrics(session.state)
    print()


def _cmd_ministers(session: GameSession) -> None:
    """列出大臣列表"""
    ministers = session.get_active_ministers()
    print("【可用大臣】")
    for m in ministers:
        print(f"  {m['name']}（{m['office']}）忠诚{m.get('loyalty',0)} 能力{m.get('ability',0)}")
    print()


def _cmd_status(session: GameSession) -> None:
    """查看当前状态"""
    print(f"【{session.state.year}年{session.state.period}月】回合{session.state.turn}  [{session.turn_phase}]")
    _print_metrics(session.state)
    print()


def _cmd_log(session: GameSession, args: str) -> None:
    """查看游戏日志"""
    limit = 20
    if args.isdigit():
        limit = int(args)
    rows = session.db.get_recent_log(limit)
    print(f"【最近日志】（共{len(rows)}条）")
    for r in rows:
        print(f"  [{r['turn']}月/{r['phase']}] {r['entry']}")
    print()


def _cmd_help() -> None:
    print("【可用命令】")
    print("  status           查看当前状态")
    print("  ministers        列出可用大臣")
    print("  summon <名> [问] 召见大臣（可指定问题）")
    print("  decree <意图>     拟旨（例：decree 赈济灾民）")
    print("  review           月末推演（推进到下月）")
    print("  log [N]          查看最近日志（默认20条）")
    print("  help             显示本帮助")
    print("  exit             退出游戏")
    print()


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
    _print_metrics(session.state)
    print()

    ministers = session.get_active_ministers()
    print("【可用大臣】")
    for m in ministers:
        print(f"  - {m['name']}（{m['office']}）")
    print()
    print("输入 help 查看可用命令，或直接输入指令。")
    print()

    while True:
        try:
            line = input("天子 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n游戏结束。")
            break

        if not line:
            continue
        if line in ("exit", "quit", "q"):
            print("游戏结束。")
            break

        # 解析命令
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in ("help", "h", "?"):
            _cmd_help()
        elif cmd in ("status", "s"):
            _cmd_status(session)
        elif cmd in ("ministers", "m"):
            _cmd_ministers(session)
        elif cmd == "summon":
            _cmd_summon(session, args)
        elif cmd == "decree":
            _cmd_decree(session, args)
        elif cmd == "review":
            _cmd_review(session)
        elif cmd == "log":
            _cmd_log(session, args)
        else:
            print(f"未知命令：{cmd}，输入 help 查看可用命令。")


if __name__ == "__main__":
    main()