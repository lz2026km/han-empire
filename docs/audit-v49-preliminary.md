# v4.9 全面审查 - 初步发现 (2026-06-03)

## 一、版本基线
- 本地 master HEAD: `0ebc643` (v4.5 ci 修 release 配置)
- 远端 master HEAD: `ff3749a` (v4.6 工程师控制台, 已拉)
- v4.5.0 tag 存在: `431351b` ✅
- v4.6 实际有 commit 但**没 tag 也没 release** ⚠️

## 二、项目体量
- 总文件: 1862
- Python LOC: 335,166 (33.5万行)
- TS/TSX LOC: 9,897
- CSS LOC: 9,165
- 图片资源: 237 PNG + 12 SVG = 249

## 三、贴图缺口清单 (铁证)
### 已有 (119 张)
- portraits/main/: 76 张 jpg (caocao.jpg / guanyu.jpg / zhugeliang.jpg 等)
- portraits/consort_pool_*.png: 15 张 (1-13, 15, 16) — 缺 14
- portraits/emperor_pool_*.png: 15 张 (1-13, 15, 16) — 缺 14
- portraits/minister_pool_*.png: 15 张 (1-13, 15, 16) — 缺 14
- placeholder.svg: 1

### 缺失 (按 characters.json 引用)
- **warlord_pool_*.png 全部缺失** (characters 引用 30+ 次)
- **general_pool_*.png 全部缺失** (characters 引用 20+ 次)
- **pool 14 全部缺失** (consort/emperor/minister 都缺 _14)

## 四、其他发现
- 项目文档 (docs/) 有 50+ 份产品/技术/历史文档
- content/ 包含 19 个 json 数据 + 11 个 prompt 模板
- .agno_skills/ 包含 19 个 agent skill 模板
- han_sim/ 包含 ~50 个 Python 模块
- v4.6 工程师控制台已实现 19 调试命令 + 5 场景预设

## 五、待主公决策
1. 是否需要我继续深入审查 33.5 万行 Python 代码? (耗时, 但有 bug 早发现)
2. 是否先批量补全 pool 缺失图? (general/warlord 池)
3. 是否先跑通 v4.5/v4.6 现有功能验证?
