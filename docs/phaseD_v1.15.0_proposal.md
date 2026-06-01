# v1.15.0 (乾坤大挪移·Phase D) 实施方案

> 乾坤大挪移一号方案 · Phase D · 汉献帝后宫系统完整化
> 弟子拟定，待主公审批
>
> **核心目标**：把明末 consort_agent.md 移植汉献帝 + 补齐 6 位汉献帝专属后宫人物
> + 后宫 Tab + 调教工具 + 数据库表
>
> **底册依据**：docs/game-bible-localization-plan.md §3（267-374 行）
>
> **绝不**改任何朝政/大臣/事件/记忆/推演逻辑，**纯新增**后宫模块
> 0 业务影响，旧 server 进程 (pid 4116087) 不重启

---

## 0. 修复目标

新增汉献帝专属后宫系统，含 7 个子任务：

| 编号 | 子任务 | 工期 | 文件 |
|------|--------|------|------|
| D1 | consort_agent.md prompt | 0.5d | content/prompts/consort_agent.md |
| D2 | 6 后宫人物 characters.json | 0.5d | content/characters.json |
| D3 | consort_records 表 | 0.5d | han_sim/db.py |
| D4 | ConsortAgent 类 | 1d | han_sim/agents.py |
| D5 | cultivate_consort 工具 | 0.5d | han_sim/tools.py |
| D6 | 7 后宫 API | 1d | server.py |
| D7 | 后宫 13 号 Tab + 验收 | 1d | web/ + tests/ |

**总计 5 天**（与底册原计划一致）

---

## 1. D1 prompt 设计

文件：content/prompts/consort_agent.md（80-100 行，4 章节）

底册 §3.3.2 已有完整 markdown 内容，直接落地 + 汉化校对：

- §0 身份（汉末深宫）
- §1 调教记录工具（最高优先级）
- §2 语气以位份定调（皇后/贵妃/嫔/贵人/常在/答应）
- §3 枕边密谋尺度（衣带诏特色）
- §4 绝不出戏
- §5 无 propose_directive
- §6 委屈与宠爱

**关键修正**：
- 明末"严旨/切责" → 汉末"切责/申斥"
- 明末"奏章/奏议" → 汉末"奏议/表章"
- 衣带诏 / 伏寿 / 董贵 等汉末专属条目保留

---

## 2. D2 6 后宫人物

| 姓名 | 位份 | 派系 | 性格 | 技能 | 历史角色 |
|------|------|------|------|------|---------|
| 伏寿 | 皇后 | 忠汉派 | 端庄隐忍外柔内刚 | 诗书礼仪书法 | 衣带诏主谋 |
| 董贵 | 贵人 | 忠汉派 | 温顺坚贞 | 刺绣女红 | 衣带诏事件 |
| 曹贵人 | 贵人 | 务实派 | 谨言慎行 | 琴艺书画 | 曹操之女政治婚 |
| 李婉 | 嫔 | 忠汉派 | 聪慧敏锐 | 棋艺医理 | 伏寿集团 |
| 何莹 | 贵人 | 离心派 | 怯懦怀旧 | 歌舞声律 | 何进侄女 |
| 王美人 | 美人 | 忠汉派 | 温柔机敏 | 刺绣琴艺 | 王允族女 |

字段对齐底册 §3.3.1 schema（id/canonical_name/title/rank/personality/loyalty/boldness/skills/traits/faction/family/is_actively_in_palace/historical_role/debut_year）

---

## 3. D3 db 表

新增 consort_records 表（与 v1.9.0 db 风格一致）：

```sql
CREATE TABLE IF NOT EXISTS consort_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT NOT NULL,
    consort_id TEXT NOT NULL,
    turn INTEGER NOT NULL,
    skill TEXT,
    trait TEXT,
    emperor_words TEXT,
    sentiment TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

含 3 方法：add_consort_record / list_consort_records / get_consort_traits

---

## 4. D4 ConsortAgent 类

在 han_sim/agents.py 末尾追加：

```python
class ConsortAgent:
    """后宫妃嫔 agent（汉献帝版）。"""
    def __init__(self, consort_id: str, content: GameContent):
        self.consort_id = consort_id
        self.content = content
        self.prompt = content.load_prompt("consort_agent.md")
    
    def system_message(self) -> str:
        return f"{self.prompt}\n\n---\n## 7. 当前被召妃嫔\n{json.dumps(self._load_consort(), ensure_ascii=False, indent=2)}"
    
    def _load_consort(self) -> Dict:
        return self.content.characters.get(self.consort_id, {})
    
    async def run(self, user_message: str, db, state, chat_history: List) -> str:
        """献帝对当前妃嫔说话，返她以角色口吻回应。
        若献帝明确"学某技能/改某性格"，先调 cultivate_consort 工具。
        """
        # 1. 判定是否要调 cultivate_consort（关键词匹配）
        # 2. 调 LLM 拿回应
        # 3. 返回应
```

---

## 5. D5 工具

在 han_sim/tools.py 末尾追加：

```python
def build_consort_tools(consort_id: str, db, state):
    """汉献帝后宫 1 工具：cultivate_consort(skill, trait)。"""
    def cultivate_consort(skill: str = "", trait: str = "") -> str:
        """皇帝要妃嫔学技能/改性格时调。skill 新技能；trait 新性格。
        调用后不出戏——继续用角色语气回话。
        """
        sk = (skill or "").strip()
        tr = (trait or "").strip()
        if not sk and not tr:
            return "调教失败：至少要填一个新技能或新性格。"
        # 写入 db
        db.add_consort_record(
            campaign_id=state.campaign_id,
            consort_id=consort_id,
            turn=state.turn,
            skill=sk,
            trait=tr,
            emperor_words="",
            sentiment="positive",
        )
        return f"__cultivated__{consort_id}__已调教。"
    
    return [cultivate_consort]
```

---

## 6. D6 7 API

server.py 末尾追加：

| API | 方法 | 功能 |
|-----|------|------|
| /api/consort/list | GET | 后宫名册 |
| /api/consort/<id> | GET | 单妃嫔详情 |
| /api/consort/<id>/audience | POST | 召幸对话（LLM） |
| /api/consort/<id>/records | GET | 调教记录 |
| /api/consort/<id>/cultivate | POST | 调教（学技能/改性格） |
| /api/consort/<id>/traits | GET | 当前性格 |
| /api/consort/tab | GET | 后宫 Tab 整体数据 |

---

## 7. D7 Tab + 验收

- web/src/components/ConsortTab.tsx（不动手，仅记入方案；web 项目单独维护）
- 验收 30 单元测试（test_han_consort_v1150.py）：
  - 6 人物加载 OK
  - cultivate_consort 工具 3 场景
  - ConsortAgent 系统消息含身份/性格/技能
  - 明朝漏网词 0
  - LLM 失败 graceful

---

## 8. 验收 15 条（关键 5 条）

- ✅ consort_agent.md ≥ 80 行 + 4 章节全
- ✅ 6 后宫人物 schema 全字段
- ✅ consort_records 表可增查
- ✅ cultivate_consort 工具 3 场景（学技能/改性格/两者都填）
- ✅ 明朝漏网词 = 0

---

## 9. 不动的范围

- ❌ 不动 agents.py 已有 5 个 Agent 类
- ❌ 不动 tools.py 已有 4+3 build 函数
- ❌ 不动 server.py 已有 12 Tab API
- ❌ 不动 db.py 已有 41 表
- ❌ 不动 session.py / simulation.py / extract 流程

---

## 10. 风险 + 回退

- 风险：6 人物写入破坏 characters.json 整体结构 → 改用 v1.14.0 同款 append 而非 overwrite
- 风险：新表 init 失败 → 用 IF NOT EXISTS 兜底
- 风险：cultivate_consort LLM 失败 → try/except + 返"已记录"伪码
- 回退：单 commit + git revert HEAD + 旧 server 进程 (pid 4116087) 不杀

---

**详细方案**已写入 docs/phaseD_v1.15.0_proposal.md

**主公，方案是否同意？** 同意则弟子立即开工 D1（prompt 0.5 天）。
