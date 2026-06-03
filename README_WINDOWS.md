# 汉献帝之末路 - Windows 用户说明

> LLM 驱动的回合制古风帝王策略游戏。三国历史迷 + 喜欢大模型 AI 对话 + 玩 Windows 游戏 → 选这个。

## 一、玩家直接玩（不需要懂 Python）

### 1.1 下载
从 [Releases 页面](https://github.com/lz2026km/han-empire/releases) 下载最新 `汉献帝之末路-Windows.zip`。

### 1.2 解压
解压到任意位置（推荐 `D:\Games\汉献帝之末路\`）。

### 1.3 配置 API Key（必须）
首次启动会弹出配置窗：
1. 选 "MiniMax" provider
2. 填入 API Key（[REDACTED]）
3. 点保存

API Key 仅写入同目录 `runtime_llm.json`，不会上传。

### 1.4 双击 EXE
- `汉献帝之末路.exe` ← 双击这个
- 首次启动会创建窗口并打开游戏

> 注：Windows SmartScreen 可能提示"未知发布者"，点"仍要运行"。

## 二、开发者打包（从源码）

### 2.1 准备
- Windows 10 / 11
- Python 3.11+ （[下载](https://www.python.org/downloads/)，**安装时勾选 Add to PATH**）
- Git（[下载](https://git-scm.com/download/win)）

### 2.2 拉源码
```cmd
git clone https://github.com/lz2026km/han-empire.git
cd han-empire
```

### 2.3 一键打包
双击 `build_windows.bat`，等待 3-5 分钟。

打包完成后：
```
dist\
  └ 汉献帝之末路.exe   ← 这个就是游戏
```

### 2.4 分发
- 整个 `dist/` 文件夹 = 可分发的游戏
- 用户解压后双击 `汉献帝之末路.exe` 即可
- 用户存档保存在 EXE 同目录的 `data/` 文件夹

## 三、常见问题

### Q1: 双击 EXE 闪退
**A:** 看 `han_empire_error.log`（EXE 同目录），找错误原因。
最常见：API Key 未配置 / 网络不通 / 端口被占。

### Q2: 弹窗说"已在运行"
**A:** 检查任务栏，已开一个窗口。
或 `Ctrl+Shift+Esc` 任务管理器 → 结束 `汉献帝之末路.exe`。

### Q3: 端口 7860 被占
**A:** 启动器会自动选 7860-7999 空闲端口，无须手动管。

### Q4: 防火墙询问
**A:** 选"允许"——游戏只在 127.0.0.1 起服务，不对外暴露。

### Q5: 游戏卡 / 慢
**A:** LLM 调用需 2-10 秒，属正常。
可关闭其他占显存/内存的程序。

## 四、架构说明（给好奇玩家）

游戏 = 三个组件，**全部在用户机器上跑**：

1. **后端 (Flask)** —— 游戏逻辑、数据库、LLM 调用
2. **前端 (React + Vite)** —— 1920×1080 原生窗口（pywebview 包装）
3. **大模型 (LLM)** —— 通过 API Key 调云端 LLM (OpenAI 兼容协议)

**LLM 驱动核心**：
- 18 个 `.agno_skills/` 描述 LLM 何时调什么工具
- 5 个 agent: 大臣对话 / 诏书拟定 / 廷议裁判 / 推演官 / 记忆抽取
- 多轮对话: agno session 持久化
- tool_call: 4 个内置 tool (query_state / propose_decree / estimate_resistance / suggest_audience)

## 五、反馈

遇到问题或建议：
- GitHub Issues: https://github.com/lz2026km/han-empire/issues
- 附 `han_empire_error.log` 帮排查

—— 享三国，品汉风。
