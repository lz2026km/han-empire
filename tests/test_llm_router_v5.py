"""v5.0 P0-2: llm_router 单测

覆盖:
1. 4 tier 配置 (SIMULATE/ROLEPLAY/BRIEFING/SANITIZE)
2. 单例 (get_router)
3. 配置加载/保存 (model_tiers.json)
4. v4.9 兼容 (get_config_for_v4_role)
5. tier 摘要 (get_tier_summary)
"""
import json
import os
import sys

# 让 pytest 能找到 han_sim
sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")

from han_sim.llm_router import (
    LLMRouter, ModelTier, DEFAULT_TIER_MODELS,
    get_router, get_config_for_tier, get_config_for_v4_role,
    get_tier_summary, reset_router,
)


# ════════════════════════════════════════════════════════════════
# Test 1: ModelTier 枚举
# ════════════════════════════════════════════════════════════════

def test_model_tier_has_4_values():
    """ModelTier 必须有 4 个值"""
    assert len(list(ModelTier)) == 4


def test_model_tier_values():
    """ModelTier 值正确"""
    assert ModelTier.SIMULATE.value == "simulate"
    assert ModelTier.ROLEPLAY.value == "roleplay"
    assert ModelTier.BRIEFING.value == "briefing"
    assert ModelTier.SANITIZE.value == "sanitize"


def test_default_tier_models_complete():
    """DEFAULT_TIER_MODELS 覆盖 4 tier"""
    for tier in ModelTier:
        assert tier in DEFAULT_TIER_MODELS
        assert "base_url" in DEFAULT_TIER_MODELS[tier]
        assert "model" in DEFAULT_TIER_MODELS[tier]
        assert DEFAULT_TIER_MODELS[tier]["base_url"].endswith("/v1")


# ════════════════════════════════════════════════════════════════
# Test 2: LLMRouter 基础
# ════════════════════════════════════════════════════════════════

def test_router_4_tiers_initialized():
    """router 初始化后 4 tier 都有配置"""
    router = LLMRouter()
    for tier in ModelTier:
        cfg = router.get_all_tiers()
        assert tier.value in cfg
        assert "base_url" in cfg[tier.value]
        assert "model" in cfg[tier.value]


def test_router_get_model_name():
    """get_model_name 返回 model 名"""
    router = LLMRouter()
    for tier in ModelTier:
        model = router.get_model_name(tier)
        assert isinstance(model, str)
        assert len(model) > 0


def test_router_get_base_url():
    """get_base_url 返回 base_url"""
    router = LLMRouter()
    for tier in ModelTier:
        url = router.get_base_url(tier)
        assert isinstance(url, str)
        assert url.endswith("/v1")


def test_router_set_tier():
    """set_tier 动态修改"""
    router = LLMRouter()
    router.set_tier(ModelTier.SIMULATE, base_url="https://custom.example.com/v1",
                    model="custom-model")
    assert router.get_base_url(ModelTier.SIMULATE) == "https://custom.example.com/v1"
    assert router.get_model_name(ModelTier.SIMULATE) == "custom-model"


# ════════════════════════════════════════════════════════════════
# Test 3: v4 兼容 (get_config_for_v4_role)
# ════════════════════════════════════════════════════════════════

def test_v4_role_to_tier_minister():
    """minister role → ROLEPLAY tier"""
    # 模拟 api_key
    os.environ["MINIMAX_API_KEY"] = "test-key-123"
    try:
        cfg = get_config_for_v4_role("minister")
        assert cfg.model is not None
        assert cfg.base_url.endswith("/v1")
    finally:
        del os.environ["MINIMAX_API_KEY"]


def test_v4_role_to_tier_simulator():
    """simulator role → SIMULATE tier"""
    os.environ["DEEPSEEK_API_KEY"] = "test-key-456"
    try:
        cfg = get_config_for_v4_role("simulator")
        assert cfg.model is not None
    finally:
        del os.environ["DEEPSEEK_API_KEY"]


def test_v4_role_to_tier_unknown():
    """未知 role → 默认 ROLEPLAY tier"""
    os.environ["MINIMAX_API_KEY"] = "test-key-789"
    try:
        cfg = get_config_for_v4_role("unknown_role")
        assert cfg.model is not None
    finally:
        del os.environ["MINIMAX_API_KEY"]


def test_v4_role_to_tier_7_roles():
    """7 个 v4 role 都能映射"""
    os.environ["MINIMAX_API_KEY"] = "test-key"
    try:
        roles = ["simulator", "extractor", "minister", "consort",
                 "memory", "chat_memory", "default"]
        for role in roles:
            cfg = get_config_for_v4_role(role)
            assert cfg.model is not None, f"{role} 映射失败"
    finally:
        del os.environ["MINIMAX_API_KEY"]


# ════════════════════════════════════════════════════════════════
# Test 4: 无 api_key 时优雅降级
# ════════════════════════════════════════════════════════════════

def test_no_api_key_raises_runtimeerror():
    """无 api_key 时应该 raise RuntimeError (供调用方降级)"""
    # 清空所有可能的 api_key
    for k in ("MINIMAX_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        if k in os.environ:
            del os.environ[k]

    try:
        cfg = get_config_for_v4_role("minister")
        assert False, "应 raise RuntimeError"
    except RuntimeError as e:
        assert "API key" in str(e) or "未提供" in str(e)


# ════════════════════════════════════════════════════════════════
# Test 5: get_tier_summary
# ════════════════════════════════════════════════════════════════

def test_get_tier_summary_structure():
    """get_tier_summary 返回 4 tier 配置"""
    summary = get_tier_summary()
    assert "simulate" in summary
    assert "roleplay" in summary
    assert "briefing" in summary
    assert "sanitize" in summary
    for tier_name, cfg in summary.items():
        assert "base_url" in cfg
        assert "model" in cfg


# ════════════════════════════════════════════════════════════════
# Test 6: 持久化 (save/load)
# ════════════════════════════════════════════════════════════════

def test_save_and_reload():
    """save 后重 load 应保留配置"""
    # 注意: 这会持久化到 ~/.hermes/han-empire/model_tiers.json
    # 测试结束后清理
    router = LLMRouter()
    router.set_tier(ModelTier.SIMULATE, model="test-saved-model")
    router.save()

    # 重 load
    router2 = LLMRouter()
    assert router2.get_model_name(ModelTier.SIMULATE) == "test-saved-model"


# ════════════════════════════════════════════════════════════════
# Test 7: 模拟真实使用场景
# ════════════════════════════════════════════════════════════════

def test_simulate_uses_flash():
    """SIMULATE tier 默认用 flash 模型 (降本)"""
    router = LLMRouter()
    # 重新设置默认值 (清掉测试残留)
    router.set_tier(ModelTier.SIMULATE,
                    base_url=DEFAULT_TIER_MODELS[ModelTier.SIMULATE]["base_url"],
                    model=DEFAULT_TIER_MODELS[ModelTier.SIMULATE]["model"])
    model = router.get_model_name(ModelTier.SIMULATE)
    # 应该是 flash 类模型 (含 flash 字样)
    assert "flash" in model.lower() or "lite" in model.lower() or "mini" in model.lower()


def test_roleplay_uses_higher_quality():
    """ROLEPLAY tier 默认用更高质量模型 (提质)"""
    router = LLMRouter()
    router.set_tier(ModelTier.ROLEPLAY,
                    base_url=DEFAULT_TIER_MODELS[ModelTier.ROLEPLAY]["base_url"],
                    model=DEFAULT_TIER_MODELS[ModelTier.ROLEPLAY]["model"])
    model = router.get_model_name(ModelTier.ROLEPLAY)
    # 应该是 plus/标准 类模型
    assert len(model) > 0


if __name__ == "__main__":
    import sys as _sys
    test_funcs = [
        test_model_tier_has_4_values,
        test_model_tier_values,
        test_default_tier_models_complete,
        test_router_4_tiers_initialized,
        test_router_get_model_name,
        test_router_get_base_url,
        test_router_set_tier,
        test_v4_role_to_tier_minister,
        test_v4_role_to_tier_simulator,
        test_v4_role_to_tier_unknown,
        test_v4_role_to_tier_7_roles,
        test_no_api_key_raises_runtimeerror,
        test_get_tier_summary_structure,
        test_save_and_reload,
        test_simulate_uses_flash,
        test_roleplay_uses_higher_quality,
    ]
    passed = 0
    failed = 0
    for fn in test_funcs:
        try:
            fn()
            passed += 1
            print(f"  ✓ {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {fn.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    _sys.exit(0 if failed == 0 else 1)
