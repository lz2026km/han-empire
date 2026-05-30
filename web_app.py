"""汉献帝之末路 Gradio Web 交互界面。L8。"""

import uuid
import sys
from pathlib import Path

import gradio as gr

sys.path.insert(0, str(Path(__file__).parent))
from han_sim.content import load_game_content
from han_sim.db import GameDB
from han_sim.decree import issue_decree
from han_sim.llm_config import load_llm_config
from han_sim.models import GameState
from han_sim.paths import user_data_path
from han_sim.session import GameSession
from han_sim.simulation import run_monthly_simulation

# ── API Key ─────────────────────────────────────────────────────────────
def _get_api_key() -> str:
    key_path = Path.home() / ".hermes-agent" / ".minimax-key.json"
    if key_path.exists():
        import json
        with open(key_path) as f:
            d = json.load(f)
            return d.get("apiKey", "")
    return ""


# ── 帮助文本 ────────────────────────────────────────────────────────────
HELP = """
**游戏目标**：在东汉末年的乱局中复兴汉室。

**游戏机制**：
- 每月有两个阶段：**召见大臣** 和 **月末推演**
- **召见大臣**：向大臣询问局势、寻求建议
- **拟旨**：针对某种意图（如"赈济灾民"）生成诏书并下达
- **月末推演**：推进时间，结算财政和事件，触发历史事件

**指标说明**：
- 汉室库：财政收入（万两/月）
- 声望：汉室民心（0-100）
- 威权：天子威权（0-100）
- 藩镇：藩镇割据程度（越低越好，0=完全统一）
"""

DECREE_TYPES = [
    "赈济灾民", "减免赋税", "颁布罪己诏", "提拔贤才", "整饬吏治",
    "军事调度", "外交安抚", "流通铜钱", "改革税制", "召集兵马",
]


# ── 会话状态管理 ────────────────────────────────────────────────────────
class GameUI:
    def __init__(self):
        self.session: GameSession = None
        self.decree_log: list = []

    def new_game(self, campaign_id: str = ""):
        cid = campaign_id.strip() or str(uuid.uuid4())[:8]
        content = load_game_content()
        self.session = GameSession.new(cid, content)
        self.decree_log = []
        return self._render_state()

    def _render_state(self):
        s = self.session.state
        lines = [
            f"**【{s.year}年{s.period}月 · 第{s.turn}回合】**",
            f"",
            f"📦 汉室库：{s.metrics.get('汉室库', 0)}万两",
            f"📦 内库：{s.metrics.get('内库', 0)}万两",
            f"⭐ 声望：{s.metrics.get('声望', 0)}/100",
            f"👑 威权：{s.metrics.get('威权', 0)}/100",
            f"⚔️  藩镇：{s.metrics.get('藩镇', 0)}/100",
            f"",
        ]
        return "\n".join(lines)

    def _render_ministers(self):
        ministers = self.session.get_active_ministers()
        if not ministers:
            return "_（无可用大臣）_"
        lines = ["| 姓名 | 官职 | 忠诚 | 能力 |", "|------|------|------|------|"]
        for m in ministers:
            lines.append(
                f"| {m['name']} | {m.get('office','无')} | {m.get('loyalty',0)} | {m.get('ability',0)} |"
            )
        return "\n".join(lines)

    def cmd_summon(self, minister_name: str, question: str):
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not minister_name:
            return "❗ 请选择或输入大臣姓名。"
        q = question.strip() or "本月局势如何？"
        try:
            result = self.session.summon_minister(minister_name, q)
            lines = [f"**【{minister_name}】**", "", result.chat_text]
            if result.refresh_ministers:
                lines.append("")
                lines.append(f"_（{minister_name} 离开，改日再召。）_")
            return "\n".join(lines)
        except Exception as e:
            return f"❗ 召见失败：{str(e)}"

    def cmd_decree(self, intent: str):
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not intent:
            return "❗ 请输入拟旨意图。"
        try:
            result = issue_decree(intent, self.session.state, self.session.db)
            d = result.decree
            entry = f"《{d.decree_type}》：{d.full_text[:50]}…"
            self.decree_log.append(entry)
            lines = [
                f"**【诏书已下】《{d.decree_type}》**",
                "",
                d.full_text,
                "",
                f"_下达原因：{intent}_",
            ]
            if result.log_entries:
                lines.append("")
                lines.append("**效果**：" + "；".join(result.log_entries))
            return "\n".join(lines)
        except Exception as e:
            return f"❗ 拟旨失败：{str(e)}"

    def cmd_review(self):
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        try:
            triggered = self.session.db.load_state("triggered_events") or []
            sim = run_monthly_simulation(self.session.state, self.session.db, triggered)
            lines = [
                f"**【{self.session.state.year - 1}年{self.session.state.period}月 · 月末推演】**",
                "",
                sim.narrative[:500] if len(sim.narrative) > 500 else sim.narrative,
                "",
            ]
            if sim.historical:
                lines.append("**📜 历史事件**")
                for e in sim.historical:
                    lines.append(f"- **{e['title']}**：{e['summary']}")
                lines.append("")
            if sim.threshold_crisis:
                lines.append("**🚨 危机事件**")
                for e in sim.threshold_crisis:
                    lines.append(f"- **{e['title']}**：{e['summary']}")
                lines.append("")
            if sim.random_events:
                lines.append("**⚡ 突发**")
                for e in sim.random_events:
                    lines.append(f"- **{e['title']}**：{e['summary']}")
                lines.append("")
            net = sim.fiscal.get("net", 0)
            lines.extend([
                "**📊 本月结算**",
                f"- 财政：{'盈余' if net >= 0 else '亏损'}{abs(net)}万两",
                f"- 声望 {sim.metrics_delta.get('声望', 0):+d}",
                f"- 威权 {sim.metrics_delta.get('威权', 0):+d}",
                f"- 藩镇 {sim.metrics_delta.get('藩镇', 0):+d}",
                "",
            ])
            if self.decree_log:
                lines.append("**📋 本月诏书**")
                for d in self.decree_log:
                    lines.append(f"- {d}")
                lines.append("")
            lines.append("─" * 40)
            lines.append("")
            lines.append(self._render_state())
            self.decree_log = []
            return "\n".join(lines)
        except Exception as e:
            return f"❗ 月末推演失败：{str(e)}"


# ── Gradio UI ──────────────────────────────────────────────────────────
def build_ui():
    ui = GameUI()

    with gr.Blocks(title="汉献帝之末路", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 👑 汉献帝之末路")
        gr.Markdown("_189年，董卓进京，废少帝立献帝。名为天子，实为阶下囚。_")
        gr.Markdown(HELP)

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 📊 当前状态")
                state_display = gr.Markdown("*点击「新游戏」查看初始状态*")

            with gr.Column(scale=1):
                gr.Markdown("### 👥 大臣列表")
                ministers_display = gr.Markdown("*点击「新游戏」查看*")

        gr.Markdown("---")

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 🎙️ 召见大臣")
                with gr.Row():
                    minister_input = gr.Textbox(
                        label="大臣姓名", placeholder="如：张昭", scale=1
                    )
                    summon_btn = gr.Button("召见", variant="primary", scale=0)
                question_input = gr.Textbox(
                    label="询问内容（选填）",
                    placeholder="本月局势如何？",
                    lines=2,
                )
                summon_output = gr.Markdown()

            with gr.Column(scale=1):
                gr.Markdown("### 📜 拟旨")
                intent_input = gr.Dropdown(
                    label="选择或输入拟旨意图",
                    choices=DECREE_TYPES,
                    value="",
                    allow_custom_value=True,
                )
                decree_btn = gr.Button("拟旨", variant="primary")
                decree_output = gr.Markdown()

        gr.Markdown("---")

        with gr.Row():
            review_btn = gr.Button("⏭️ 月末推演（推进到下月）", variant="stop", size="lg")
        review_output = gr.Markdown()

        gr.Markdown("---")

        with gr.Row():
            new_game_btn = gr.Button("🆕 新游戏", variant="secondary")

        # ── 事件绑定 ──────────────────────────────────────────────
        def do_new_game():
            out = ui.new_game()
            ministers = ui._render_ministers()
            return out, ministers

        summon_btn.click(
            fn=ui.cmd_summon,
            inputs=[minister_input, question_input],
            outputs=summon_output,
        )
        decree_btn.click(
            fn=ui.cmd_decree,
            inputs=[intent_input],
            outputs=decree_output,
        )
        review_btn.click(
            fn=ui.cmd_review,
            inputs=[],
            outputs=review_output,
        )
        new_game_btn.click(
            fn=do_new_game,
            inputs=[],
            outputs=[state_display, ministers_display],
        )

        # 初始化
        demo.load(
            fn=do_new_game,
            inputs=[],
            outputs=[state_display, ministers_display],
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=5199,
        share=False,
    )