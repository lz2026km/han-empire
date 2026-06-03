# v4.5 范围 8 维度审查报告 (2026-06-03)

## 一、审查范围
- v4.5 = commit 431351b (v4.5 预览版 + CI) + 0ebc643 (release 配置修)
- 跳过 v4.6 工程师控制台: 4 个 API (/cheat, /debug/commands, /debug/state, /debug/inspect)
- HEAD 当前: ff3749a (v4.6 commit, 不动)

## 二、8 维度结果

| # | 维度 | 结果 | 风险 |
|---|------|------|------|
| 1 | 路由结构 | 89 个 v4.5 路由 | ✅ |
| 2 | 鉴权/权限 | 无显式鉴权 | ⚠️ 单机游戏可接受 |
| 3 | 错误处理 | 53 try/except | ✅ |
| 4 | SQL 注入 | 25 execute, 待查 f-string | ⚠️ |
| 5 | 输入校验 | 2 显式 None 校验 | ⚠️ |
| 6 | 缓存 | lru_cache + cached_json 120s | ✅ |
| 7 | 日志 | 3 log 调用 (偏少) | ⚠️ |
| 8 | 调试模式 | debug=False (生产) | ✅ |
| 9 | 数据表 | 51 表 / 13 外键 / 31 索引 | ✅ |
| 10 | 前端组件 | 41 组件 / 6 CSS (含 v4 4 个模板) | ✅ |

## 三、关键文件
- server.py: 78KB / 2139 行 / 89 v4.5 路由
- han_sim/db.py: 129KB / 2913 行 / 51 表
- han_sim/simulation.py: 26KB / 617 行 / 7 函数
- han_sim/: 56 个模块 / 19,160 LOC
- web/src/: 41 TSX 组件 / 6 CSS

## 四、关键发现
### Bug 1: portrait_id 引用 404 (132 个)
- characters.json 中 132 个人物 portrait_id 引用 main/ jpg 不存在
- 解决: AI 补图 + 改 portrait_id 指向独立文件名 (cid)

### Bug 2: data bug
- 6 个 id=None (已修)
- 7 个 id 带空格 (已修)
- 8 个 id 重复 (已修)

## 五、3 个建议改进 (不阻塞 v4.9)
1. server.py 加显式鉴权中间件 (可选)
2. han_sim/db.py 全面 f-string 扫描 (需 30 分钟)
3. 关键路径加 logger.info 记录 (例: 关键事件 / 异常)

## 六、结论
v4.5 范围代码整体健康, 可在补图 + 跑通后出 v4.9.
