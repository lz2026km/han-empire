# v1.17.0 (乾坤大挪移·Phase F) 实施方案

> 乾坤大挪移一号方案 · Phase F · 后宫系统 Web 化
> 弟子拟定，待主公审批

## 1. 设计核心

**底册依据**：docs/game-bible-localization-plan.md
- §3.3.3 "web_app.py 新增后宫 Tab（13 号 Tab）：妃嫔名册 / 召幸对话 / 调教记录 / 衣带诏线索"
- §6 文件清单 web_app.py
- §8 "把 game_world.md 渲染到 Web 的游戏说明 Tab"
- §8 "README 核心玩法加后宫一项"

**核心目标**：把 v1.15.0 后端后宫（6 人物 / 7 API / 1 agent）暴露给 Web 前端，让玩家能在浏览器里：
- 阅 6 后宫人物名册
- 召幸妃嫔对话
- 阅调教记录
- 阅衣带诏线索

## 2. 现状速览（已实测 2026-06-01）

| 项目 | 实测 | 目标 |
|------|------|------|
| `web/src/tabs/ConsortTab.tsx` | **缺失** | 新建 |
| `web_app.py` 后宫 API | 7 个（v1.15.0） | 加固（错误处理 / 返回 schema） |
| `web/src/App.tsx` Tab 注册 | **缺 ConsortTab** | 加 13 号 Tab |
| `README.md` 核心玩法 | 6 系统无后宫 | 加 1 行后宫 |
| `docs/product-plan.md` | 1969 字节 | 加后宫玩法 |
| game_world.md 渲染 | 缺 | 抽 game_world API → 前端游戏说明 Tab |
| web 端口 | 5555 | 不改 |
| 单元测试 | 83 | +10 |

## 3. 6 个子任务 / 3 天

| 编号 | 子任务 | 工期 |
|------|--------|------|
| F1 | 后端加固：web_app.py 7 后宫 API 返回 schema 统一 + 错误处理 | 0.5d |
| F2 | 后端加固：/api/game_world API（返回 game_world.md 全文） | 0.3d |
| F3 | 前端：ConsortTab.tsx 新建（3 子组件：名册 / 召幸 / 调教） | 1.0d |
| F4 | 前端：App.tsx 加 13 号 Tab 注册 + 路由 | 0.3d |
| F5 | 文档：README.md 核心玩法 + product-plan.md | 0.2d |
| F6 | 测试 + 验收 + commit + push | 0.7d |

## 4. 关键设计

### F1: API 加固
- 7 后宫 API 统一返 `{ok, code, message, data}` 格式
- 错误处理：consort_id 不存在 / 调教参数缺失 / 派系不存在 → 返 400/404
- 0 业务影响（v1.15.0 既有 API 仅加 wrapper，不改核心逻辑）

### F2: game_world API
- 返 `content/prompts/game_world.md` 全文（按段落切分）
- 让 Web 游戏说明 Tab 渲染
- 缓存 1 小时（避免每分钟读盘）

### F3: ConsortTab.tsx（核心）
3 子组件：
1. **名册 (ConsortRoster)**：6 人物卡片（头像/位份/性格/家族/技能）
2. **召幸 (ConsortAudience)**：下拉选妃嫔 + 输入框 + 调教按钮（"学某技能" / "改某性格"）
3. **调教记录 (ConsortRecords)**：列表展示调教历史
4. **衣带诏线索 (SecretEdictHint)**：根据 game_state 显示相关线索

**布局**：用 v1.15.0 CSS 风格（避免侧栏撑开）。**注意**：v1.15.0 theme.py 主公明确**侧栏 width=260 不要 min_width**。

### F4: Tab 注册
- App.tsx 顶部加 import ConsortTab
- tabs 数组加 `{key: 'consort', label: '🏯 后宫', component: ConsortTab}`
- 不改既有 12 个 Tab

### F5: 文档
- README.md "核心玩法" 加 1 行：`- 🏯 后宫系统（v1.17.0+）：召幸妃嫔 / 调教技能 / 衣带诏密谋`
- docs/product-plan.md 加 §3 后宫玩法循环

## 5. 验收 10 条

- ✅ ConsortTab.tsx 4 子组件可渲染
- ✅ App.tsx 13 个 Tab 注册
- ✅ 后宫 API 返统一 schema
- ✅ game_world API 返 markdown 切分
- ✅ README 核心玩法有后宫
- ✅ product-plan.md 有后宫循环
- ✅ 明朝漏网词 0
- ✅ 旧 12 Tab 不破坏
- ✅ server pid 4116087 不杀不重启
- ✅ 单元测试 ≥ 10 个

## 6. 风险

| 风险 | 缓解 |
|------|------|
| 前端 1920×1080 布局撑开 | 严格 width=260（不用 min_width） |
| Agno agent 慢 | 召幸按钮用 loading state |
| 调教 prompt 错 | v1.15.0 已验证 cultivate_consort |
| web 依赖缺 | 用既有 react-flowbite 组件 |
| 主公偏好"零移动端" | 不加任何 @media query |

## 7. 工期估算

**底册原计划**：3 天
**v1.12.0-v1.16.0 实测节省率 80%**
**v1.17.0 估算**：**0.5-1 天**（前端为主，API 简单）
