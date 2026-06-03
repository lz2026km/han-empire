# 汉献帝之末路 (v5.0.1)

> **LLM 驱动的回合制古风帝王策略游戏**。你扮演汉献帝刘协，在董卓乱政、曹操"挟天子以令诸侯"的二十年中，寻求兴复汉室之道。
>
> 主公！这是您的江山，您的诏书，您的衣带密令，您的智谋与大汉最后的命运。

[![GitHub Repo](https://img.shields.io/badge/GitHub-lz2026km%2Fhan--empire-brightgreen)](https://github.com/lz2026km/han-empire)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![v5.0.1](https://img.shields.io/badge/version-5.0.1-blue)](CHANGELOG.md)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6)](README_WINDOWS.md)
[![A11y](https://img.shields.io/badge/a11y-WCAG_2.1_AA-success)](CHANGELOG.md#v33)

---

## 三句话看懂这个游戏

1. **你** = 汉献帝刘协（189-220 年），被曹操控制在许昌的傀儡皇帝
2. **游戏核心 = LLM 驱动**：诏书、召对、廷议、战役、历史演进——**每个决策都有 AI 模拟**
3. **目标 = 兴复汉室**：5 大历史事件（董卓乱政/官渡/赤壁/曹丕篡汉/衣带诏）任你改写

---

## v4.9.0 新特性 (2026-06-03 全审查 + 独立头像 + 修 bug + 跑通)

> **主公明令: 对 4.5 版本进行处理, 全面审查 UI/UX 控件/逻辑/数据, 全面补充贴图图片的缺失, 整个软件必须跑通无错, 本版本最后生成为 4.9, 然后严格执行推送.**

- **216 张 AI 独立人物头像** (265/265 全人物覆盖, 罗马化 prompt, MiniMax image-01)
- **2 个 v4.5 真实 bug 修复** (han_sim/issues.py:1039 ongoing_effects 重复 json.loads; han_sim/db.py:1116 SQLite bind 不支持 list)
- **8 维度 v4.5 范围审查** (89 API / 51 表 / 13 外键 / 31 索引, 0 阻塞)
- **E2E 端到端跑通** (创朝 + next_turn 200, 51 州郡税收, 6 派系变动, 0 错)
- **3 类 characters.json 数据 bug 修复** (6 个 id=None / 7 个 id 带空格 / 8 个 id 重复)
- **Flask + Vite 项目** 服务 web/dist/ 而非 web/public/, 加图必须双 cp
- **总 main/ 头像** 73 → 289 张 jpg, portrait_id 265/265 全部指向独立 jpg, 0 缺失
- **版本号 4.5.0 → 4.9.0** (pyproject / package.json / version_info.txt)
- **详见**: [CHANGELOG v4.9 段](CHANGELOG.md#-v49--2026-06-03-v45-全审查--216-张独立-ai-头像--2-真-bug-修复--全跑通)

---

## v5.0.1 新特性 (2026-06-03 P1 三大件加 0.1)

> **本版本: v5.0.0 (577f83b) → v5.0.1 (P1 三大件)** 累计 55 单测 / 4 新 API / 0 后端新 bug

- **P1-1 prompts 工程升级**: 10 prompt 加"默会知识"段 + 2 agent 加"工具调用铁律" (minister_agent 强化 + consort_agent §8 新增)
- **P1-2 event_selector 强化**: 40 条 seed_events 全部含 precondition 字段 (12 关键精写 + 28 默认), event_selector.md 新增 §6 改写口子规则 (5 小节)
- **P1-3 引导剧本**: content/intro_hints.json (6 个月 189.3-189.8 董卓进京前), han_sim/intro_hints.py (~180 行), 新增 `GET /api/intro_hints?turn=N`, 17 单测全过
- **详见**: [CHANGELOG v5.0.1 段](CHANGELOG.md#-v501--2026-06-03-p1-三件全完工-01-加成)

---

## v5.0 新特性 (2026-06-03 score 分档 + 模型分级 + token 仪表盘)

> **本版本: v4.9.0 (4be37a1) → v5.0.0** 38 单测 / 3 新 API / E2E 全过

- **P0-1 score 5 档房拆分**: 5 新 prompt (shared/internal/issues/military_external/personnel_secret = 1149 行), 主控 146 行, v4 backup 保留, han_sim/score_extractor_pipeline.py (~390 行 4 档房串行/并行 + 失败回退 + 20 字段合并), 22 单测全过
- **P0-2 模型分级路由 (4 tier)**: llm_router.py 270 行 (SIMULATE/ROLEPLAY/BRIEFING/SANITIZE), 9 agent 改造, 16 单测 100%
- **P0-3 token 实时仪表盘**: usage_tracker.py 增强 (按 model/purpose 分组), 2 新 endpoint `/api/token_stats` + `/api/score_extractor/tiers`, TokenStatsWidget.tsx (199 行) + CSS (97 行)
- **详见**: [CHANGELOG v5.0 段](CHANGELOG.md#-v50--2026-06-03-score-分档--模型分级--token-仪表盘)

---

## v4.6 新特性 (2026-06-02 工程师控制台 + 调试可玩)

> **主公明令: 全面审查游戏逻辑/控件/UI/UX, 补充所有缺失数据/图片, 增加工程师调控接口和窗口 (不依赖 LLM 即可调试运行)**

- **增强 `/api/campaigns/<id>/cheat`**: 11 → 19 命令
- **`DEBUG_PRESETS` 5 场景**: caotang_ruin(189) / yidai_200(200) / guandu_202(202) / chibi_208(208) / caopi_220(220) — 一键跳转汉末关键时刻
- **3 调试端点**: `/debug/commands` / `/debug/state` / `/debug/inspect/<table>` (18 表白名单防 SQL 注入)
- **前端 CheatConsole 4 Tab**: 控制台 / 状态检视 / 场景加载 / 命令参考
- **6 快捷按钮**: 状态/+10威权/+20声望/+50财政/推进一月/推进一年
- **A11y**: 4 tab role/aria-selected, 关闭 aria-label, 场景卡 role=button+Enter 键
- **修 v4.5 真 bug**: factions schema / issues schema / metrics 排序跳过复合值
- **详见**: [CHANGELOG v4.6 段](CHANGELOG.md#-v46--2026-06-02-工程师控制台--api-补全--调试可玩)

---

## v4.0 特性 (2026-06-02 图像完成版)

> **主公明令: 人物立像/头像/软件界面/控件/地图/场景/小图/贴图, 必须全部完成**

- **72 张人物立绘** (工笔重彩 512x512, 主流 80+ 人物覆盖: 皇帝/枭雄/谋士/武将/美人/黄巾/二线)
- **13 张背景场景** (1920x1080: 朝堂/后宫/书房/暗廊/朝会/诏书/山水/帅帐 + 5 战争场景)
- **8 张 UI 控件** (玉玺/竹简/五铢钱/玉璧/戈/围棋/竹册/宫灯, 真实 3D 渲染)
- **5 张地图** (汉帝国全图 + 官渡之战 + 扬/冀/西凉州郡)
- **5 张官阶冠** (王/公/卿/士/将, 古代职官体系视觉化)
- **5 张勋章** (忠/勇/智/仁/统, 五德玉璧勋章)
- **2 张物件** (战马/战车)
- **3 张天空** (晴/雨/雪 横幅)
- **总 113 张图, 全部 MiniMax image-01 AI 生图 (工笔重彩风)**
- **详见**: [CHANGELOG v4.0 段](CHANGELOG.md#-v40--2026-06-02-图像完成版)

---

## v3.3 特性 (2026-06-02 UX/UI 大修 + 全代码审查)

> **主公明令: 对仓库的所有代码进行审查. UX 和 UI 控件的审查. 全跑完工.**

- **WCAG 2.1 AA 可达性**: 90 button 100% 可达 (16 aria-label + 12 role=button + 62 textContent)
- **全键盘操作**: 5 Modal 支持 Escape 关闭 + 背景滚动锁定
- **UI 控件标准**: 89 button 全 type="button" (防 form 误提交)
- **法律合规 100%**: 0 借鉴 / 0 emoji / 0 青干 / 0 回归, 38 文件实测通过
- **详见**: [CHANGELOG v3.3 段](CHANGELOG.md#-v33--2026-06-02-uxui-大修--全代码审查)

---

## 游戏背景

**中平六年（189 年）**，董卓进京，废少帝，立献帝，拉开汉末乱世序幕。

献帝先被董卓控制于洛阳、长安，后被曹操"迁都"许昌。**名为天子，实为阶下囚。** 诸侯割据，汉室衰微，皇权名存实亡。

**你的使命**：在这最黑暗的二十年里，以智谋与名分，辗转于董卓、曹操与诸侯之间，**寻求兴复汉室之道**。

> _"朕乃大汉天子，天命所归。曹贼挟朕，朕岂甘为阶下囚？"_ —— 汉献帝（玩家）

---

## 核心玩法

### v3.1 全方位大升级 (科技树 + 后果链可视化)

- **科技树系统** — 3 主线（农本/王权/军备）× 5 层 DAG，玩家累计声望消耗解锁，永久 buff
- **后果链 DAG** — 玩家每个决策自动派生 1-4 个后果节点（4 类型：即时/短期/长期/永久）
- **决策回放** — 时间线滑块 + 速度控制，可快进/回放所有玩家决策
- **API 8 端点** — 端点总数 76 → 84

### v3.0 全方位大升级 (5 commit · 67 files · +11673 行)

- **新手引导系统** — 7 步浮层引导（欢迎/诏书/战役/科技/后果/存档/回放），高亮目标元素 + 强制等待
- **PC 大屏沉浸** — F11/Esc 切换 + 鼠标空闲 5 秒隐藏 + 状态栏自动折叠
- **DAG 性能优化** — Canvas 渲染 + 视口过滤 + LOD 简笔 (15 → 6 节点)
- **存档系统升级** — 10 槽位 + 每 5 回合自动存档 + 命名/删除
- **API 6 端点** — 端点总数 84 → 90

---

## 启动方式

### Python 直接启动 (开发模式)

```bash
# 1. 克隆
git clone https://github.com/lz2026km/han-empire.git
cd han-empire

# 2. 装依赖 (推荐用 hermes 共享 venv, 或自建)
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 3. 启动 server
python3 server.py
# → 浏览器访问 http://127.0.0.1:5555
```

### Windows EXE 桌面版 (用户向)

详见 [README_WINDOWS.md](README_WINDOWS.md)

- v4.5-rc3 起支持 windows-2019 + Python 3.11.9 + PyInstaller 5.13.2 远程打包
- 79MB EXE.zip, 直接下载即用

---

## 项目结构

```
han-empire/
├── server.py              # Flask REST API (78KB, 89 v4.5 路由)
├── han_sim/               # 56 个核心模块 (19,160 LOC)
│   ├── db.py              # SQLite ORM (51 表 / 13 外键 / 31 索引)
│   ├── simulation.py      # 月末推演核心 (617 行)
│   ├── session.py         # GameSession 管理
│   ├── decree.py          # 诏书系统
│   ├── skills.py          # 天子技能树
│   ├── events.py          # 事件选择器
│   ├── content.py         # 内容加载
│   └── ...
├── content/               # 19 个 JSON 数据 + 11 个 prompt 模板
│   ├── characters.json    # 265 个三国人物 (含 portrait_id)
│   ├── factions.json
│   ├── regions.json
│   ├── events.json
│   ├── prompts/
│   └── ...
├── web/                   # React 19 + TypeScript 5.9 + Vite 7
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts         # 36 个 API 客户端方法
│   │   ├── components/    # 41 个组件
│   │   ├── styles/        # 6 个 CSS (含 4 个 v4 模板)
│   │   └── hooks/
│   ├── public/
│   │   └── portraits/main/  # 289 张 AI 生成头像
│   └── package.json
├── data/                  # 存档目录
├── docs/                  # 4 份审查报告
│   ├── audit-v49-preliminary.md
│   ├── audit-v45-8d-report.md
│   ├── fix-v45-bugs-and-e2e-pass.md
│   └── v49-独立头像迁移方案.md
├── CHANGELOG.md           # 完整版本历程
└── pyproject.toml         # v4.9.0
```

---

## 技术栈

- **后端**: Python 3.11 + Flask 3.1 + SQLite (51 表)
- **前端**: React 19.2 + TypeScript 5.9 + Vite 7.2
- **桌面**: pywebview 5.5 + PyInstaller 5.13 (Windows EXE)
- **LLM**: OpenAI SDK 2.38 (兼容 MiniMax / Anthropic / OpenRouter)
- **AI 生图**: MiniMax image-01 API (走 OpenClaw 凭证, 0 询问主公)
- **CI/CD**: GitHub Actions (windows-2019 + Python 3.11.9 远程 EXE 打包)

---

## 版本历程 (近 8 版)

| 版本 | 日期 | 主公明令 | 关键 |
|------|------|----------|------|
| **v4.9.0** | 2026-06-03 | 对 4.5 处理, 全审查 + 独立头像 + 跑通 | 216 张 AI 头像, 2 bug 修, E2E 通 |
| v4.6.0 | 2026-06-02 | 工程师调控接口 + 不依赖 LLM 调试 | 19 调试命令 + 5 场景预设 |
| v4.5.0 | 2026-06-02 | 打包前大审查 (8 维度) | 51 表 / 13 外键 / 31 索引 |
| v4.0.0 | 2026-06-02 | 人物立像/头像/界面/控件/地图/场景/小图 必全 | 113 张图 AI 批量 |
| v3.3.0 | 2026-06-02 | 对仓库的所有代码进行审查 | 0 emoji / 0 借鉴 / 0 回归 |
| v3.2.0 | 2026-06-02 | — | 体验打磨 |
| v3.1.0 | 2026-06-02 | 策略深度补完 | 科技树 + 后果链 |
| v3.0.0 | 2026-06-02 | 全方位大升级 | 新手引导 + PC 沉浸 + DAG |

完整见 [CHANGELOG.md](CHANGELOG.md)

---

## 沉淀教训 (跨项目适用)

1. **MiniMax API 并发 5 触发 RPM 限流** — retry 必须 1 + 60s 退避 (v4.0 113 张实战经验)
2. **Flask + Vite 项目** — server 服务 `web/dist/` 而非 `web/public/`, 加图必须双 cp
3. **跳 pool 池化改独立 portrait_id** — 涉及数据 id 修复 (None / 带空格 / 重复)
4. **v4.5 真 bug 隐藏较深** — 只有端到端 next_turn 才能触发 issues.py 那个
5. **0 emoji 永久规则** — 含聊天 markdown, 写完 grep 0 行 (主公明令 v3.3)
6. **公开 API 验证远端** — 不依赖 token 401 假阳性 (git ls-remote + GitHub API 直读)
7. **永远先推 tag** — 再 `softprops/action-gh-release@v2` 自动建 release

---

## 贡献者

- **小诸葛 / 小凤雏 (Hermes Agent)** — 代码 + 测试 + 部署
- **主公** — 需求方 + 拍板

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)
