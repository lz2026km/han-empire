"""
v2.5.0 UI/UX 旗舰版 — 2 项 e2e 测试 (静态校验)
- UI-1: Intro 启动动画三幕过场验证
- UI-3: HexagonDashboard 6 维雷达数值验证
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
WEB_SRC = ROOT / "web" / "src"


def test_intro_three_phases():
    """UI-1: Intro 启动动画 (3 幕 + 跳过) 验证"""
    intro_path = WEB_SRC / "components" / "intro" / "Intro.tsx"
    assert intro_path.exists(), f"Intro.tsx 不存在: {intro_path}"
    content = intro_path.read_text(encoding="utf-8")

    # 3 幕过场
    for phase in ["taiji", "ascension", "chamber"]:
        assert f"phase === '{phase}'" in content or f"phase == '{phase}'" in content, \
            f"Intro 缺幕: {phase}"

    # 跳过支持
    assert "onComplete" in content and "Escape" in content, "Intro 缺跳过分支"

    # 默认时长 30s
    m = re.search(r"duration\s*=\s*(\d+)", content)
    if m:
        assert int(m.group(1)) >= 20000, f"启动动画太短: {m.group(1)}ms"

    # 进度条
    assert "intro-progress" in content, "Intro 缺进度条"
    print("✅ UI-1 Intro: 3 幕 + 跳过 (Esc) + 进度条")
    return True


def test_hexagon_six_dims():
    """UI-3: 6 维雷达 (民/军/库/族/阉/戚) 验证"""
    hex_path = WEB_SRC / "components" / "dashboard" / "HexagonDashboard.tsx"
    assert hex_path.exists(), f"HexagonDashboard.tsx 不存在: {hex_path}"
    content = hex_path.read_text(encoding="utf-8")

    # 6 维
    for dim in ["民忠", "军心", "国库", "士族", "阉党", "外戚"]:
        assert f"label: '{dim}'" in content, f"雷达缺维度: {dim}"

    # 6 个极角
    assert "(i * 2 * Math.PI / 6)" in content, "雷达未用 6 等分极角"

    # 数字滚动
    assert "useAnimatedNumber" in content or "requestAnimationFrame" in content, \
        "雷达缺数字滚动"

    # 网格层
    assert "gridLevels" in content, "雷达缺网格层"
    print("✅ UI-3 Hexagon: 6 维 (民/军/库/族/阉/戚) + 极角 + 数字滚动 + 网格")
    return True


if __name__ == "__main__":
    print("🧪 v2.5.0 UI/UX 旗舰版 e2e")
    print("=" * 50)
    results = []
    try:
        results.append(("UI-1 Intro", test_intro_three_phases()))
    except Exception as e:
        print(f"❌ UI-1 Intro: {e}")
        results.append(("UI-1 Intro", False))
    try:
        results.append(("UI-3 Hexagon", test_hexagon_six_dims()))
    except Exception as e:
        print(f"❌ UI-3 Hexagon: {e}")
        results.append(("UI-3 Hexagon", False))

    print("=" * 50)
    passed = sum(1 for _, ok in results if ok)
    print(f"🎉 通过 {passed}/{len(results)} 项 UI e2e")
    sys.exit(0 if passed == len(results) else 1)
