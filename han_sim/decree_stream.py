"""v2.2.0 Phase 1-5: SSE 流式推演

5 大功能:
P0-1 SSE 流式颁诏
P0-2 3 态显示
P0-3 全屏锁
P0-4 退朝不下旨
P0-5 密令实证注入

被 server.py /api/decree/issue/stream 调用
"""
import random
import json
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass, asdict

from .models import GameState
from .db import GameDB
from .decree import issue_decree, _build_decree_text_from_template


def _state_dict(s) -> Dict:
    """GameState 序列化为 dict (兼容非 dataclass 字段)"""
    try:
        return asdict(s)
    except Exception:
        return s.__dict__ if hasattr(s, '__dict__') else {}


# ════════════════════════════════════════════════════════════════
# v2.2.0 P0-5: 密令实证注入 (closed_evidence)
# ════════════════════════════════════════════════════════════════
def collect_closed_evidence(db: GameDB, campaign_id: str) -> List[Dict]:
    """从 secret_orders 表收集已办结密令的 result 作为诏书实证

    主公下旨拿人/定罪时可在诏书中引用: 「据密令X所查实...」
    """
    evidence = []
    try:
        rows = db.conn.execute(
            "SELECT id, title, minister_name, result, status FROM secret_orders "
            "WHERE campaign_id = ? AND status = 'done' ORDER BY id DESC LIMIT 5",
            (campaign_id,)
        ).fetchall()
        for r in rows:
            if r[3]:  # result 非空
                evidence.append({
                    "id": int(r[0]),
                    "title": r[1],
                    "minister": r[2],
                    "evidence": r[3][:200] if r[3] else "",  # 截 200 字
                })
    except Exception:
        pass
    return evidence


# ════════════════════════════════════════════════════════════════
# v2.2.0 P0-1+P0-2: SSE 流式推演引擎
# ════════════════════════════════════════════════════════════════
@dataclass
class StreamEvent:
    """SSE 事件 - 3 种类型"""
    kind: str  # stage / thinking / text / done / error
    content: str = ""
    data: Optional[Dict] = None

    def to_sse(self) -> str:
        if self.kind == 'done':
            return f"event: done\ndata: {json.dumps(self.data or {}, ensure_ascii=False)}\n\n"
        if self.kind == 'error':
            return f"event: error\ndata: {json.dumps({'message': self.content}, ensure_ascii=False)}\n\n"
        return f"event: {self.kind}\ndata: {json.dumps({'content': self.content}, ensure_ascii=False)}\n\n"


# 推演阶段文案 (5 阶段: 拟诏/研判/推演/月结/完成)
STAGES = [
    ("📜 拟诏", "汇总本月指令, 起草诏书正文"),
    ("🔍 研判", "研判诏书对各派系/阶级的影响"),
    ("⚙️ 推演", "推演诏令执行效果与连锁反应"),
    ("📊 月结", "月度结算: 税收/支出/库银"),
    ("✅ 完成", "诏书已颁布, 天下闻风"),
]


def stream_issue_decree(
    state: GameState,
    db: GameDB,
    campaign_id: str,
    on_event: Callable[[str, str], None],
    cheat_directive: str = "",
) -> Dict:
    """SSE 流式推演: 拟诏 → 研判 → 推演 → 月结 → 完成

    on_event(kind, content):
        kind: 'stage' | 'thinking' | 'text' | 'done' | 'error'
        content: 该类型内容

    cheat_directive: v5.1.1 P1-1 天命控制台强制结算项 (M# 仿点)
        非空时拼到本期 narrative 前, 标 CHEAT_NARRATIVE_PREFIX, 强制
        LLM/规则把它当既成事实. 一次性, 不持久化.

    返回: {'decree': ..., 'report': ..., 'state': ...}
    """
    # ---- 阶段 1: 拟诏 ----
    on_event('stage', STAGES[0][0])
    on_event('thinking', f'📋 准备: 草拟本月诏书 (公元{state.year}年{state.period}月)\n')

    # v5.1.1 P1-1: 注入 cheat_directive 到 narrative (若非空)
    if cheat_directive and cheat_directive.strip():
        from han_sim.decree import CHEAT_NARRATIVE_PREFIX
        cheat_block = CHEAT_NARRATIVE_PREFIX + cheat_directive.strip() + "\n\n"
        on_event('thinking', f'⚡ 天命控制台: 强制结算项已挂载 ({len(cheat_directive)} 字)\n')
        # cheat_directive 通过 tlog 记入状态, 一次性
        try:
            from han_sim.token_stats import tlog
            tlog(f"[CHEAT] 强制结算项注入 ({len(cheat_directive)}字): {cheat_directive[:200]}")
        except Exception:
            pass
    else:
        cheat_block = ""

    # 收集 confirmed 草案
    directives = []
    try:
        rows = db.conn.execute(
            "SELECT id, kind, content FROM directives "
            "WHERE campaign_id = ? AND status = 'confirmed' ORDER BY id",
            (campaign_id,)
        ).fetchall()
        directives = [dict(r) for r in rows]
    except Exception:
        pass

    if not directives:
        on_event('stage', STAGES[4][0])
        on_event('thinking', '⚠️ 本月无待颁草案\n')
        on_event('text', cheat_block + '本月无待颁诏书, 天下静默。')

    on_event('thinking', f'   ✓ 找到 {len(directives)} 道待颁指令\n')

    # P0-5: 收集密令实证
    closed_evidence = collect_closed_evidence(db, campaign_id)
    if closed_evidence:
        on_event('thinking', f'   ✓ 找到 {len(closed_evidence)} 件已办结密令作为实证\n')
        for ev in closed_evidence:
            on_event('thinking', f'     · [{ev["id"]}] {ev["title"]} ({ev["minister"]}): {ev["evidence"][:50]}...\n')
    else:
        on_event('thinking', '   · 无已办结密令作为实证\n')

    # 取第一个 confirmed 草案作为本次诏书主题
    main = directives[0]
    intent = main.get('content', '颁布新政')
    on_event('thinking', f'   ✓ 诏书主题: 《{main.get("kind", "新政")}》\n')

    # LLM/模板生成诏书
    try:
        # 优先模板生成 (速度快, 不依赖 LLM)
        full_text = _build_decree_text_from_template(
            main.get('kind', '颁布新政'),
            {'type': main.get('kind', '颁布新政'), 'style': '庄重', 'historical_refs': []},
            state
        )
        # P0-5: 在诏书前注入密令实证
        if closed_evidence:
            evidence_intro = '【援引已办密令】\n'
            for ev in closed_evidence[:2]:
                evidence_intro += f'  · 据密令「{ev["title"]}」所查: {ev["evidence"]}。\n'
            evidence_intro += '\n'
            full_text = evidence_intro + full_text
    except Exception as e:
        full_text = f'奉天承运, 皇帝诏曰: {intent}。布告天下, 咸使闻知。'

    # v5.1.1 P1-1: cheat_directive 拼在最前 (最高优先级)
    full_text = cheat_block + full_text

    on_event('text', full_text)

    # ---- 阶段 2: 研判 (派系影响) ----
    on_event('stage', STAGES[1][0])
    on_event('thinking', '🔍 分析诏书对 4 派系/5 阶级的影响:\n')
    on_event('thinking', '   · 忠汉派: 好感 +5\n')
    on_event('thinking', '   · 务实派: 好感 +2\n')
    on_event('thinking', '   · 离心派: 好感 -3\n')
    on_event('thinking', '   · 叛逆派: 好感 -8\n')

    # ---- 阶段 3: 推演 (执行诏书) ----
    on_event('stage', STAGES[2][0])
    on_event('thinking', '⚙️ 执行诏书效果:\n')
    try:
        result = issue_decree(intent, state, db, campaign_id=campaign_id)
        on_event('thinking', f'   ✓ 诏书已颁布, 类型: {result.decree.decree_type}\n')
        on_event('thinking', f'   ✓ 效果: {len(result.decree.effects)} 项指标变化\n')
        for e in result.decree.effects[:3]:
            on_event('thinking', f'     · {e["metric"]}: {e["delta"]:+d} ({e["description"]})\n')
    except Exception as e:
        on_event('thinking', f'   ⚠️ 推演出错: {e}\n')
        result = None

    # ---- 阶段 4: 月结 (apply_monthly_flow) ----
    on_event('stage', STAGES[3][0])
    on_event('thinking', '📊 月度结算:\n')
    try:
        from .flows import apply_monthly_flow
        flow = apply_monthly_flow(state, db)
        on_event('thinking', f'   · 税收: {flow["tax"]} 万两\n')
        on_event('thinking', f'   · 支出: {flow["expense"]} 万两\n')
        on_event('thinking', f'   · 净流入: {flow["net"]:+d} 万两\n')
        on_event('thinking', f'   · 库银: {flow["treasury"]} 万两\n')
    except Exception as e:
        on_event('thinking', f'   ⚠️ 月结失败: {e}\n')

    # ---- 阶段 5: 完成 ----
    on_event('stage', STAGES[4][0])
    on_event('thinking', '✅ 诏书已颁布, 天下闻风而动\n')

    # 更新 directives 状态为 issued
    try:
        db.conn.execute(
            "UPDATE directives SET status = 'issued' WHERE campaign_id = ? AND status = 'confirmed'",
            (campaign_id,)
        )
        db.commit()
    except Exception:
        pass

    return {
        'decree': full_text,
        'report': {
            'decree_type': main.get('kind', '新政'),
            'closed_evidence_count': len(closed_evidence),
            'directives_count': len(directives),
        },
        'state': _state_dict(state),
    }


# ════════════════════════════════════════════════════════════════
# v2.2.0 P0-4: 退朝不下旨 (advance_without_edict)
# ════════════════════════════════════════════════════════════════
def advance_without_edict(
    state: GameState,
    db: GameDB,
    on_event: Callable[[str, str], None],
) -> Dict:
    """退朝不下旨: 跳过诏书, 只跑月度推演

    主公「本月无大事, 退朝」按钮触发
    """
    on_event('stage', STAGES[3][0])
    on_event('thinking', '📊 本月退朝, 未下正式圣旨, 诸事仍待来月处置\n')
    on_event('thinking', '⚙️ 仅执行月度结算:\n')
    try:
        from .flows import apply_monthly_flow
        flow = apply_monthly_flow(state, db)
        on_event('thinking', f'   · 税收: {flow["tax"]} 万两\n')
        on_event('thinking', f'   · 支出: {flow["expense"]} 万两\n')
        on_event('thinking', f'   · 净流入: {flow["net"]:+d} 万两\n')
        on_event('thinking', f'   · 库银: {flow["treasury"]} 万两\n')
    except Exception as e:
        on_event('thinking', f'   ⚠️ 推演失败: {e}\n')
    on_event('stage', STAGES[4][0])
    on_event('text', f'{state.year}年{state.period}月, 天子退朝未下旨, 仅行月结。')

    return {
        'decree': '',
        'report': {'advanced_only': True, 'no_decree': True},
        'state': _state_dict(state),
    }
