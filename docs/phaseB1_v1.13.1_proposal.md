# v1.13.1 (乾坤大挪移·修小版本) 实施方案

> 乾坤大挪移一号方案 · v1.13.1 插队小版本 · 2026-06-01 弟子拟定，待主公审批
> **核心目标**：修 v1.13.0 Phase B 实测发现的 3 个现有 BUG，**0.5 天**完工
>
> **绝不**改任何业务逻辑，**纯修复** — 0 业务影响

---

## 0. 修复目标

| 编号 | BUG | 触发场景 | 修复方式 |
|------|-----|---------|---------|
| 🐛 #1 | `parse_agent_json_full` 不支持 ```json``` 代码块包裹 | LLM 99% 会用代码块 | 加策略 0：先剥 ``` ... ``` |
| 🐛 #2 | `constants.py` 缺 `PHASE_ISSUED/REVIEWING/SUMMONING` | `session.py` import 必失败 | 在 constants.py 补 3 个字符串常量 |
| 🐛 #3 | `runtime_llm.json` 路径硬编码 + api_key 为空 | `load_llm_config` 走 getpass 提示 | 路径搜 2 处 + 从 `auth-profiles.json` 读 minimax key |

---

## 1. 修复方案详述

### 🐛 #1 修复：`agents.py` parse_agent_json_full 加代码块剥离

**位置**：`han_sim/agents.py:parse_agent_json_full()` 函数头
**改动**：在策略 1（原文直解）**之前**加策略 0：

```python
# 策略 0：剥离 ```json ... ``` 或 ``` ... ``` 代码块包裹
m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
if m:
    candidate = m.group(1).strip()
    try:
        return _json.loads(candidate)
    except Exception:
        pass  # 落入原文直解
```

**行数**：+8 行
**风险**：0 — 失败时落入策略 1，行为不变
**测试**：用 v1.13.0 phaseB-4 端到端 2-3 测试用例验证

### 🐛 #2 修复：`constants.py` 补 3 个 PHASE_* 常量

**位置**：`han_sim/constants.py` 末尾新增块
**改动**：加 3 个字符串常量（不是 Enum，session.py 期望字符串字面量）

```python
# ── 回合阶段（v1.13.1 乾坤大挪移修小版本补：session.py 引用但常量缺失）──
# 历史上 TurnPhase Enum 的字符串值，session.py 直接 import 用作默认值
PHASE_SUMMONING = "SUMMONING"   # 召对中
PHASE_REVIEWING = "REVIEWING"   # 御览中
PHASE_ISSUED    = "ISSUED"      # 诏书已下
```

**行数**：+6 行
**风险**：0 — 纯常量补充，不动任何逻辑
**测试**：实跑 `from han_sim.session import GameSession` 应该成功

### 🐛 #3 修复：`llm_config.py` 多路径读 + 兜底 auth-profiles

**位置**：`han_sim/llm_config.py:load_runtime_llm()` 函数体
**改动**：路径回退 + 读 auth-profiles.json

```python
def load_runtime_llm() -> Dict[str, str]:
    """优先级：
    1. RUNTIME_LLM_PATH（~/.hermes/han-empire/runtime_llm.json）
    2. <工作目录>/runtime_llm.json
    3. ~/.openclaw/agents/main/agent/auth-profiles.json (minimax:cn profile)
    """
    candidates = [RUNTIME_LLM_PATH]
    # 加工作目录 runtime_llm.json
    cwd_rt = os.path.join(os.getcwd(), "runtime_llm.json")
    if cwd_rt not in candidates:
        candidates.append(cwd_rt)
    # auth-profiles.json 兜底
    auth = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")

    data: Dict = {}
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    break
            except (OSError, json.JSONDecodeError):
                pass
    # auth-profiles 兜底
    if not data.get("api_key") and os.path.isfile(auth):
        try:
            with open(auth, "r", encoding="utf-8") as fh:
                auth_data = json.load(fh)
            profile = auth_data.get("profiles", {}).get("minimax:cn", {})
            if profile.get("key"):
                data["api_key"] = profile["key"]
                if not data.get("base_url"):
                    data["base_url"] = "https://api.minimaxi.com/v1"
                if not data.get("model"):
                    data["model"] = "MiniMax-Text-01"
        except (OSError, json.JSONDecodeError):
            pass
    if not isinstance(data, dict):
        return {}
    out = {k: str(data.get(k, "") or "") for k in (...)}
    ...
    return out
```

**行数**：+30 行（用新增 2 个辅助函数可能更简洁）
**风险**：0 — 不破坏现有读单路径行为，仅增加回退
**测试**：实跑 `load_runtime_llm()` 返非空字典且 api_key > 0

---

## 2. 验收 8 条

| # | 验收 | 期望 |
|---|------|------|
| 1 | BUG #1 修：纯 JSON 仍能解析 | 返 dict |
| 2 | BUG #1 修：```json\n{...}\n``` 包裹 | 返 dict |
| 3 | BUG #1 修：LLM 垃圾前缀+代码块 | 返 dict |
| 4 | BUG #1 修：破损 JSON | 仍返 None（graceful） |
| 5 | BUG #2 修：session.py 完整 import | 成功 |
| 6 | BUG #2 修：TurnPhase 三个值等于常量 | SUMMONING/REVIEWING/ISSUED 字符串 |
| 7 | BUG #3 修：load_runtime_llm 返非空 + api_key > 0 | 实测 >= 100 字符 |
| 8 | BUG #3 修：原路径仍生效 | RUNTIME_LLM_PATH 文件优先 |

---

## 3. 不动的范围

- ❌ 不动 `chat_memory_extractor.md` 任何字符
- ❌ 不动 `content.py` 字段注册
- ❌ 不动 `server.py` hook
- ❌ 不动其他业务模块

---

## 4. 风险

- BUG #3 修可能**暴露隐藏 LLM 调用链**（之前因 api_key 为空从来未真正调通过）— 修好后若 LLM 仍有问题会暴露
- BUG #2 修好后**重启 server 必加载新代码**（不像之前因 import 失败实际跑老进程）— 任何新的 session.py bug 会暴露

---

## 5. 工时

**预计 0.5 天**（4 小时）：
- BUG #1: 0.5 小时
- BUG #2: 0.5 小时
- BUG #3: 1.5 小时
- 测试 + commit + push: 1.5 小时

---

## 6. 回退方案

- 单 commit，git revert HEAD 即回退所有 3 个修复
- 旧 server 进程仍跑着（pid 4116087）— 紧急回退时**保留旧进程不杀**

---

**详细方案**：`/home/admin/.openclaw/workspace/han-empire/docs/phaseB1_v1.13.1_proposal.md`（即本文件）

**主公，方案是否同意？** 同意则弟子立即开工。修改意见请直接指出。
