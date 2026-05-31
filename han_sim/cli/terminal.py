"""汉家天子终端界面。L5。"""

import sys
import textwrap
from typing import Optional, List, Dict

from han_sim.session import GameSession
from han_sim.models import get_authority_level


BANNER = r"""
═══════════════════════════════════════════════════════
     奉 天 承运  皇 帝 诏曰
═══════════════════════════════════════════════════════
""".strip()

MENU_OPTIONS = [
    ("1", "召见大臣", "宣大臣入宫问对"),
    ("2", "下月", "推进日程，处理朝政"),
    ("3", "查看状态", "审阅天下大势"),
    ("4", "保存", "存档以备后用"),
    ("5", "加载", "读取先前存档"),
    ("6", "列存档", "查阅所有存档记录"),
]

RESIDENCE_TITLES = [
    "未央宫", "长乐宫", "太极殿", "北海苑", "含元殿",
]


def wrap(text: str, width: int = 60) -> str:
    """简单缩进包裹。"""
    wrapped: List[str] = []
    for line in text.splitlines():
        if line.strip():
            wrapped.extend(textwrap.wrap(line, width=width))
        else:
            wrapped.append("")
    return "\n".join(wrapped)


def print_banner():
    for line in BANNER.splitlines():
        print(f"  {line}")


def print_divider(char: str = "─", width: int = 62):
    print(f"  {char * width}")


def render_box(lines: List[str], width: int = 62) -> str:
    """渲染一个居中ASCII盒子。"""
    out_lines: List[str] = []
    out_lines.append(f"  ┌{'─' * width}┐")
    for ln in lines:
        padded = ln + " " * max(0, width - len(ln))
        out_lines.append(f"  │{padded}│")
    out_lines.append(f"  └{'─' * width}┘")
    return "\n".join(out_lines)


def format_loyalty_color(loyalty: int) -> str:
    """忠诚度着色（返回描述）。"""
    if loyalty >= 80:
        return f"忠耿{loyalty}"
    elif loyalty >= 60:
        return f"勤勉{loyalty}"
    elif loyalty >= 40:
        return f"观望{loyalty}"
    elif loyalty >= 20:
        return f"首鼠{loyalty}"
    else:
        return f"叛逆{loyalty}"


def format_authority_bar(authority: int, width: int = 20) -> str:
    """威权进度条。"""
    filled = authority * width // 100
    return "█" * filled + "░" * (width - filled)


def format_metric(metrics: Dict[str, int], key: str) -> str:
    val = metrics.get(key, 0)
    return f"{val}"


class EmperorTerminal:
    """汉室天子终端会话控制器。"""

    def __init__(self, session: GameSession):
        self.session: GameSession = session
        self._running: bool = False
        self.turn_count: int = 0

    # ── 渲染 ──────────────────────────────────────────────────────────

    def _header(self, title: str) -> str:
        lines = [
            "",
            f"  ╔{'═' * 60}╗",
            f"  ║{title:^60}║",
            f"  ╚{'═' * 60}╝",
            "",
        ]
        return "\n".join(lines)

    def _footer(self) -> str:
        state = self.session.state
        authority = state.metrics.get("威权", 0)
        auth_label = get_authority_level(authority).label
        return (
            f"  ┌{'─' * 60}┐\n"
            f"  │  [{state.year}年{state.period}月  第{state.turn}回合]"
            f"  威权: {authority}（{auth_label}）"
            f"  {'─' * max(0, 26 - len(str(authority)) - len(auth_label))}│\n"
            f"  └{'─' * 60}┘"
        )

    def _render_state_overview(self) -> str:
        """渲染天下大势概览。"""
        state = self.session.state
        metrics = state.metrics
        authority = metrics.get("威权", 0)
        auth_level = get_authority_level(authority)
        parts: List[str] = []

        parts.append(self._header(" 天 下 大 势 "))
        parts.append(f"  年号：{state.year}年  {state.period}月")
        parts.append(f"  回合：第{state.turn}回合")
        parts.append("")
        parts.append(f"  ┌{'─' * 58}┐")
        parts.append(f"  │  威权：{format_authority_bar(authority)}  {authority}/100  {auth_level.label}  │")
        parts.append(f"  └{'─' * 58}┘")
        parts.append("")

        # 核心指标
        key_metrics = [
            ("汉室库", "国库", "万两"),
            ("内库", "内库", "万两"),
            ("军备", "军备", "点"),
            ("民心", "民心", ""),
            ("藩镇", "藩镇", "点"),
        ]
        parts.append(f"  {'指标':<10} {'数值':>8}  {'说明'}")
        parts.append(f"  {'─' * 40}")
        for key, label, unit in key_metrics:
            val = metrics.get(key, 0)
            parts.append(f"  {label:<10} {val:>8}{unit}  {key}")
        parts.append("")

        # 在朝大臣列表
        ministers = self.session.get_active_ministers()
        parts.append(f"  在朝大臣（{len(ministers)}人）：")
        if ministers:
            for m in ministers[:8]:
                loyalty_str = format_loyalty_color(m.get("loyalty", 50))
                office = m.get("office", "无职")
                parts.append(
                    f"    【{m['name']}】{office}  忠诚:{loyalty_str}  能力:{m.get('ability', 50)}"
                )
            if len(ministers) > 8:
                parts.append(f"    ...另有{len(ministers) - 8}人")
        else:
            parts.append("    暂无在朝大臣")

        parts.append("")
        parts.append(self._footer())
        return "\n".join(parts)

    def _render_ministers_list(self) -> str:
        """渲染大臣列表。"""
        ministers = self.session.get_active_ministers()
        parts: List[str] = []
        parts.append(self._header(" 在 朝 大 臣 "))
        if not ministers:
            parts.append("  暂无在朝大臣")
            return "\n".join(parts)

        for idx, m in enumerate(ministers, 1):
            loyalty_str = format_loyalty_color(m.get("loyalty", 50))
            office = m.get("office", "无职")
            office_type = m.get("office_type", "")
            faction = m.get("faction", "中立")
            parts.append(
                f"  {idx}. {m['name']}  [{office}]  派系:{faction}\n"
                f"     忠诚:{loyalty_str}  能力:{m.get('ability', 50)}  "
                f"正直:{m.get('integrity', 50)}  胆识:{m.get('courage', 50)}"
            )
            parts.append("")
        return "\n".join(parts)

    def _render_save_success(self, path: str) -> str:
        parts = [""]
        parts.append(r"  ╔════════════════════════════════════════════╗")
        parts.append(r"  ║          朕 已 存 档  █                    ║")
        parts.append(r"  ╚════════════════════════════════════════════╝")
        parts.append(f"  存档路径：{path}")
        return "\n".join(parts)

    def _render_load_menu(self, saves: List[Dict]) -> str:
        parts: List[str] = []
        parts.append(self._header(" 读 取 存 档 "))
        if not saves:
            parts.append("  暂无可用存档")
            return "\n".join(parts)
        for idx, s in enumerate(saves, 1):
            parts.append(
                f"  {idx}. 战役: {s['campaign_id']}  "
                f"修改: {s['modified']}"
            )
        parts.append("")
        parts.append("  请输入存档编号加载，或按 Enter 返回：")
        return "\n".join(parts)

    def _render_save_list(self, saves: List[Dict]) -> str:
        parts: List[str] = []
        parts.append(self._header(" 存 档 列 表 "))
        if not saves:
            parts.append("  暂无可用存档")
            return "\n".join(parts)
        for idx, s in enumerate(saves, 1):
            parts.append(
                f"  {idx}. 战役: {s['campaign_id']}  "
                f"修改: {s['modified']}  路径: {s['path']}"
            )
        return "\n".join(parts)

    def _render_monthly_report(self, result) -> str:
        parts: List[str] = []
        parts.append(self._header(" 月 末 結 算 "))
        for entry in result.log_entries:
            parts.append(f"  {entry}")
        parts.append("")
        parts.append(f"  → {result.summary}")
        return "\n".join(parts)

    # ── 菜单操作 ─────────────────────────────────────────────────────

    def do_summon(self) -> Optional[str]:
        """召见大臣。"""
        ministers = self.session.get_active_ministers()
        if not ministers:
            return "  暂无在朝大臣可召对。"

        # 列出大臣
        lines: List[str] = [self._header(" 召 见 大 臣 ")]
        lines.append("  请选择召见的大臣：\n")
        for idx, m in enumerate(ministers, 1):
            lines.append(f"  {idx}. {m['name']}  [{m.get('office', '无职')}]")
        lines.append("")
        lines.append("  请输入编号（Enter返回）：")

        print("\n".join(lines))

        try:
            choice = input("  > ").strip()
            if not choice:
                return None
            idx = int(choice) - 1
            if idx < 0 or idx >= len(ministers):
                return "  无效选择。"
        except (ValueError, EOFError):
            return "  取消召见。"

        selected = ministers[idx]
        print(f"\n  【朕】宣 {selected['name']} 入宫问对……\n")
        print(f"  ┌{'─' * 58}┐")
        print(f"  │  卿有何事禀报？                                    │")
        print(f"  └{'─' * 58}┘")

        instruction = input("  > ").strip()
        if not instruction:
            return "  问对取消。"

        result = self.session.summon_minister(selected["name"], instruction)

        # 显示大臣回复
        reply_lines = wrap(result.chat_text, 56)
        parts = [
            "",
            f"  ┌{'─' * 58}┐",
            f"  │  【{selected['name']}】奏曰：                              │",
        ]
        for ln in reply_lines.splitlines():
            parts.append(f"  │  {ln:<56} │")
        parts.append(f"  └{'─' * 58}┘")
        return "\n".join(parts)

    def do_next_month(self) -> str:
        """推进到下月。"""
        self.turn_count += 1
        result = self.session.run_review()
        return self._render_monthly_report(result)

    def do_view_status(self) -> str:
        """查看状态。"""
        return self._render_state_overview()

    def do_save(self) -> str:
        """保存游戏。"""
        try:
            path = self.session.save()
            return self._render_save_success(path)
        except Exception as e:
            return f"  存档失败：{e}"

    def do_load(self) -> str:
        """加载存档。"""
        saves = GameSession.list_saves()
        if not saves:
            return "  暂无可用存档。"
        print(self._render_load_menu(saves))
        try:
            choice = input("  > ").strip()
            if not choice:
                return "  取消加载。"
            idx = int(choice) - 1
            if idx < 0 or idx >= len(saves):
                return "  无效选择。"
        except (ValueError, EOFError):
            return "  取消加载。"

        try:
            cid = saves[idx]["campaign_id"]
            self.session = GameSession.load(cid)
            return (
                f"  存档 [{cid}] 已加载。\n"
                f"  {self.session.state.year}年{self.session.state.period}月  "
                f"第{self.session.state.turn}回合"
            )
        except Exception as e:
            return f"  加载失败：{e}"

    def do_list_saves(self) -> str:
        """列出存档。"""
        saves = GameSession.list_saves()
        return self._render_save_list(saves)

    # ── 主循环 ────────────────────────────────────────────────────────

    def main_loop(self):
        """天子主循环。"""
        self._running = True
        print_banner()
        print(f"\n  欢迎，朕。\n")
        print(self._render_state_overview())

        while self._running:
            print("")
            print("  ┌──────────────────────────────────────────────────────┐")
            print("  │  主  菜  单                                          │")
            print("  ├──────────────────────────────────────────────────────┤")
            for key, label, desc in MENU_OPTIONS:
                print(f"  │  {key}. {label:<12}  {desc:<32} │")
            print("  │  0. 退出                                             │")
            print("  └──────────────────────────────────────────────────────┘")

            try:
                raw = input("\n  朕的选择（0-6）：").strip()
                if not raw:
                    continue
                choice = raw.lower()
            except (EOFError, KeyboardInterrupt):
                choice = "0"

            print("")
            if choice == "0":
                print("  朕去也。")
                self._running = False
                break
            elif choice == "1":
                output = self.do_summon()
            elif choice == "2":
                output = self.do_next_month()
            elif choice == "3":
                output = self.do_view_status()
            elif choice == "4":
                output = self.do_save()
            elif choice == "5":
                output = self.do_load()
            elif choice == "6":
                output = self.do_list_saves()
            else:
                output = "  无此选项，请重新输入。"

            if output:
                print(output)

    def run(self):
        """对外入口。"""
        try:
            self.main_loop()
        except KeyboardInterrupt:
            print("\n  朕去也。")


def launch_terminal(session: GameSession):
    """启动终端。"""
    terminal = EmperorTerminal(session)
    terminal.run()
