"""v3.0 W1: 4 个新模块集成测试 (不调 LLM)"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace/han-empire')

def test_3_0_be_1_api_key_router():
    from han_sim.api_key_router import (
        KeyMode, KeyRoute, decide_route,
        get_server_routes_summary, get_supported_modes,
    )
    # mock _load_server_fallback_key
    import han_sim.api_key_router as r
    r._load_server_fallback_key = lambda: {
        "base_url": "https://api.minimax.chat/v1",
        "api_key": "mock-key-for-test",
        "model": "MiniMax-Text-01",
    }
    # 1) 默认回退到服务端
    route = decide_route("server")
    assert route.mode == KeyMode.SERVER_PROXY
    print(f"  ✓ server 模式: provider={route.mode.value}")

    # 2) local 模式 + 有 client key
    client_keys = {"api_key": "sk-test-123", "base_url": "https://api.deepseek.com", "model": "deepseek-chat"}
    route2 = decide_route("local", client_keys)
    assert route2.mode == KeyMode.LOCAL
    assert route2.from_local is True
    print(f"  ✓ local 模式: from_local=True")

    # 3) hybrid 模式 + 关键用途走 local
    route3 = decide_route("hybrid", client_keys, purpose="decree")
    assert route3.mode == KeyMode.HYBRID
    assert route3.from_local is True
    print(f"  ✓ hybrid 关键用途: mode=hybrid")

    # 4) hybrid + 普通用途走 server
    route4 = decide_route("hybrid", client_keys, purpose="general")
    assert route4.mode == KeyMode.SERVER_PROXY
    print(f"  ✓ hybrid 普通用途: mode=server_proxy")

    # 5) 摘要 (不暴露 Key)
    summary = get_server_routes_summary()
    print(f"  ✓ 服务端摘要: {summary}")

    # 6) 模式列表
    modes = get_supported_modes()
    assert "local" in modes
    print(f"  ✓ 支持模式: {modes}")


def test_3_0_be_2_kv_cache():
    from han_sim.llm_cache import (
        split_prompt_for_cache, get_cache_stats, reset_cache_stats,
        static_hash, estimate_cache_savings,
    )
    reset_cache_stats()
    static = "你是汉献帝刘协的尚书令, 负责拟旨. 格式: 奉天承运皇帝诏曰..."
    dyn1 = "陛下要在 3 月内讨羌"
    dyn2 = "陛下要在 4 月内赈灾"

    # 1) 第一次 = miss
    s1, u1 = split_prompt_for_cache("decree", "minimax", static, dyn1)
    assert "[STATIC-CACHE" in s1
    assert u1 == dyn1

    # 2) 同样 static 第二次 = hit
    s2, u2 = split_prompt_for_cache("decree", "minimax", static, dyn2)
    assert "[STATIC-CACHE" in s2

    stats = get_cache_stats()
    assert stats["total_calls"] == 2
    assert stats["cache_hits"] == 1
    assert stats["cache_misses"] == 1
    print(f"  ✓ KV cache: {stats['hit_rate']} 命中率")

    # 3) hash 一致性
    h1 = static_hash(static)
    h2 = static_hash(static)
    assert h1 == h2
    print(f"  ✓ 静态 hash 一致: {h1}")

    # 4) 节省估算
    saved = estimate_cache_savings()
    print(f"  ✓ 节省估算: {saved}")


def test_3_0_be_3_model_adapter():
    from han_sim.model_adapter import (
        Provider, detect_provider, list_supported_providers, PROVIDER_DEFAULT_MODELS,
    )
    # 1) provider 检测
    assert detect_provider("https://api.deepseek.com/v1") == Provider.DEEPSEEK
    assert detect_provider("https://dashscope.aliyuncs.com/v1") == Provider.QWEN
    assert detect_provider("https://api.minimax.chat/v1") == Provider.MINIMAX
    assert detect_provider("https://open.bigmodel.cn/api/paas/v4") == Provider.GLM
    print(f"  ✓ Provider 检测 4 家全过")

    # 2) 默认模型
    assert PROVIDER_DEFAULT_MODELS[Provider.DEEPSEEK] == "deepseek-chat"
    assert PROVIDER_DEFAULT_MODELS[Provider.QWEN] == "qwen-plus"
    print(f"  ✓ 默认模型映射")

    # 3) 列表
    providers = list_supported_providers()
    assert len(providers) >= 4
    print(f"  ✓ 支持 {len(providers)} 家: {[p['name'] for p in providers]}")


def test_3_0_be_4_context_injector():
    from han_sim.context_injector import (
        inject_current_issue, build_npc_hint_block, extract_mentioned_npcs,
        push_history_turn, build_history_compression, reset_history,
        validate_npc_consistency, ContextBudget,
    )
    reset_history()
    # 1) 议题注入
    sys_p = "你是尚书令"
    injected = inject_current_issue(sys_p, "讨羌皇甫嵩", "建安3年3月")
    assert "[CURRENT-ISSUE-LOCK]" in injected
    assert "讨羌皇甫嵩" in injected
    print(f"  ✓ 议题硬约束注入 ({len(injected)-len(sys_p)} 字)")

    # 2) NPC 提示块
    npc_db = {
        "曹操": {"faction": "外戚", "office": "丞相", "stance": "挟天子"},
        "刘备": {"faction": "皇叔", "office": "豫州牧", "stance": "兴复汉室"},
    }
    block = build_npc_hint_block(["曹操", "刘备", "虚构人物"], npc_db)
    assert "曹操" in block
    assert "虚构人物" in block  # 应警告
    print(f"  ✓ NPC 现实提示 + 幻觉警告")

    # 3) 提及提取
    text = "曹操与刘备会于许昌"
    known = {"曹操", "刘备", "孙权"}
    mentioned = extract_mentioned_npcs(text, known)
    assert "曹操" in mentioned
    assert "刘备" in mentioned
    print(f"  ✓ NPC 提取: {mentioned}")

    # 4) 历史压缩
    push_history_turn("建安元年 迁都许昌, 曹操迎奉献帝")
    push_history_turn("建安二年 颁布屯田令")
    comp = build_history_compression()
    assert "[HISTORY-COMPRESS]" in comp
    assert "迁都许昌" in comp
    print(f"  ✓ 历史压缩: {len(comp)} 字")

    # 5) 一致性校验
    fake = "董卓与张角在许昌会面"  # 张角已死
    issues = validate_npc_consistency(fake, {"董卓", "曹操", "刘备"})
    assert len(issues) >= 1
    print(f"  ✓ 一致性校验: {issues}")

    # 6) 预算
    budget = ContextBudget()
    assert budget.total_budget == 76_000
    print(f"  ✓ 上下文预算: {budget.total_budget} tokens")


# === 跑全部 ===
print("=" * 60)
print("W1 阶段一: 后端 P0 4 项集成测试")
print("=" * 60)
tests = [
    ("3.0-BE-1 本地 API Key 路由", test_3_0_be_1_api_key_router),
    ("3.0-BE-2 KV cache 优化", test_3_0_be_2_kv_cache),
    ("3.0-BE-3 多模型适配器", test_3_0_be_3_model_adapter),
    ("3.0-BE-4 长上下文防幻觉", test_3_0_be_4_context_injector),
]
passed = 0
for name, fn in tests:
    print(f"\n[{name}]")
    try:
        fn()
        passed += 1
        print(f"  ✅ {name} PASSED")
    except Exception as e:
        print(f"  ❌ {name} FAILED: {e}")
        import traceback; traceback.print_exc()

print(f"\n{'='*60}\n结果: {passed}/{len(tests)} passed\n{'='*60}")
sys.exit(0 if passed == len(tests) else 1)
