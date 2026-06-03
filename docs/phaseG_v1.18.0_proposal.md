# v1.18.0 实施方案（乾坤大挪移一号方案 · Phase G · 合并施工）

> 弟子拟定，**待主公审批**
> **特别说明**：v1.18.0 由主公确认 = 5 score_extractor 变种 + 古风背景图（合并双任务）

## 0. 历史与修正

底册原 Phase G = 古风背景图（2d）；v1.15.0 实际是后宫**不是**底册写的 score_extractor 5 变种。
→ v1.18.0 **合并施工**：补做底册 Phase D（5 变种）+ 底册 Phase G（古风背景图），工期 4d（原 2+2d）。

## 1. 5 个 score_extractor 变种拆分（底册 Phase D 补做）

### 设计

**当前**：1 个 `score_extractor.md` (43K 明朝版没汉化)
**目标**：拆 5 个变种，按调用上下文分流
- `score_extractor_1_authority.md`（威权/汉室库/内库/民心 4 量表）
- `score_extractor_2_faction.md`（5 朝廷派系 sat+lev）
- `score_extractor_3_region.md`（51 州郡 unrest/corruption/economy）
- `score_extractor_4_class.md`（8 阶级 sat+lev）
- `score_extractor_5_misc.md`（office_changes / character_status / decrees）

### 路由
- `agents.py` `create_score_extractor_*_agent()` 5 个工厂
- `content.py` 5 个 `*_prompt` 字段
- `simulation.py` 按调用上下文分流（authorize/faction/region/class/misc）

## 2. 明朝词汉化（顺手）

**实测明朝词 7 个 26 次**：
- 崇祯(1) / 魏忠贤(1) / 辽东(1) / 锦衣卫(4) / 阉党(10) / 东林(9) / 湖广(1)
- 替换为：献帝/曹操/校事/.../忠汉/务实/.../颍川等
- 1 个 score_extractor.md 全文件汉化

## 3. 古风背景图 + 视觉系统（底册 Phase G）

### 设计

**当前**：v0.9.4 theme.py 17 色，但 web 端无 `assets/`
**目标**：4 套古风背景图 + 主题切换

| Tab | 背景主题 | 用意 |
|-----|---------|------|
| 🏠 总览 | 紫禁城朝会大殿 | 庄重 |
| 📜 诏书 | 圣旨黄绢+龙纹边框 | 诏令权威 |
| 💬 召对 | 御书房明黄 | 内廷对话 |
| 👥 大臣 | 汉宫殿柱 | 群臣 |
| ⚔️ 战役 | 沙场山水 | 战争 |
| 🏯 后宫 | 朱红纱幔+珠帘 | 后宫闺阁 |

### 技术
- `web/src/assets/bg/` 4 SVG/CSS 渐变（无版权争议）
- `web/src/styles/themes.css` 主题切换 class
- 复 v0.9.4 17 色 + 加 CSS 变量

## 4. 6 子任务 / 4 天工期

| 子 | 内容 | 工时 |
|---|------|------|
| G1 | 5 score_extractor 变种 prompt | 1.5d |
| G2 | 5 factory + content.py 字段 + simulation 路由 | 1d |
| G3 | 明朝词 26 处汉化（顺手） | 0.3d |
| G4 | 6 套古风背景 CSS | 0.7d |
| G5 | 测试 + CHANGELOG + 法正 + commit + push | 0.5d |
| **合计** | | **4d** |

## 5. 验收 12 条

- [ ] 5 score_extractor_*_agent 工厂可调
- [ ] simulation.py 按 5 上下文路由
- [ ] 明朝词 0（regex 验证）
- [ ] 6 套古风背景 CSS 加载
- [ ] 主题切换工作（不变 tab 编号）
- [ ] 11 tab 不破坏
- [ ] v1.15.0 后宫 v1.17.0 Web 化 v1.16.0 event_selector 不动
- [ ] 单元测试 ≥100（83 + 17 变种）
- [ ] server pid 4116087 不杀不重启
- [ ] 工期 4d 估算
- [ ] CHANGELOG.md v1.18.0 章节
- [ ] 法正同步 work_logs
