"""v5.1.3 P3-2: 嫔妃立绘池 + 自定义上传 (portraits.py + save/list/delete)"""
import os
import sys
import tempfile
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from han_sim.portraits import (
    save_custom_portrait, delete_custom_portrait, list_custom_portraits,
    _custom_portrait_dir,
)


# 1x1 透明 PNG (合法最小 PNG)
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfc\xff"
    b"\xff?\x00\x05\xfe\x02\xfe\xa6Z\x97\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _cleanup_portrait(name: str):
    """清理测试上传的立绘"""
    try:
        delete_custom_portrait(name)
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════
# Test 1: save + list + delete 立绘全周期
# ════════════════════════════════════════════════════════════════

def test_save_list_delete_cycle():
    """save_custom_portrait 落盘 → list_custom_portraits 含 → delete_custom_portrait 删除"""
    name = "test_consort_01"
    try:
        # 1) 落盘
        path = save_custom_portrait(name, TINY_PNG, "test.png")
        assert os.path.isfile(path), f"立绘未落盘: {path}"
        assert path.endswith(".png")
        # 2) 列出应含 (返完整文件名, 所以检查 startswith)
        portraits = list_custom_portraits()
        assert any(p.startswith(name + ".") for p in portraits), \
            f"立绘 {name} 不在列表中 ({portraits})"
        # 3) 再次 save 应覆盖, 不增
        path2 = save_custom_portrait(name, TINY_PNG, "test2.png")
        assert path2 == path, "save 第二次应覆盖而非新增"
        portraits2 = list_custom_portraits()
        # 覆盖后应只 1 条含此 name
        matches = [p for p in portraits2 if p.startswith(name + ".")]
        assert len(matches) == 1, f"覆盖后应只 1 条, 实际 {len(matches)}"
    finally:
        _cleanup_portrait(name)


# ════════════════════════════════════════════════════════════════
# Test 2: delete 不存在的立绘返 False (无副作用)
# ════════════════════════════════════════════════════════════════

def test_delete_nonexistent_returns_false():
    """delete_custom_portrait 对不存在的 name 返 False, 不崩"""
    try:
        result = delete_custom_portrait("nonexistent_consort_xyz")
        assert result is False
    finally:
        pass


# ════════════════════════════════════════════════════════════════
# Test 3: 文件名清洗 (特殊字符 → _)
# ════════════════════════════════════════════════════════════════

def test_filename_sanitization():
    """save_custom_portrait 清洗特殊字符, 文件名仅含 [alnum, _, -, ' ']"""
    raw_name = "曹操/../../etc/passwd"  # 路径穿越尝试
    try:
        path = save_custom_portrait(raw_name, TINY_PNG, "malicious.png")
        # 路径穿越被清洗, 文件仍在 custom 目录下
        assert "etc" not in path or "passwd" in path and "_" in path
        # 清洗后应只剩合法字符
        base = os.path.basename(path).split(".")[0]
        for c in base:
            assert c.isalnum() or c in ("_", "-", " "), f"非法字符: {c}"
    finally:
        # 清理: 实际文件名可能已被清洗
        _cleanup_portrait(raw_name)
        # 也尝试按可能的清洗名清理
        for safe in ("______etc_passwd", "_._._etc_passwd"):
            try:
                os.remove(os.path.join(_custom_portrait_dir(), safe + ".png"))
            except OSError:
                pass
