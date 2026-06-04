"""v5.3.0 P7-5: 视觉回归 (AI 生成 25 张图的完整性 + 尺寸校验, 无 Pillow 依赖)"""
import os
import sys
import struct

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

WEB_PUBLIC = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "web", "public",
)

# v5.3.0 P7-5: 25 张 AI 图清单 (含尺寸, 主公可调)
# v5.5.0+ P8-E: 压缩后最大 512, 所以 min 调到 256 (16:9) / 256 (1:1)
EXPECTED_FILES = [
    ("portraits/main/liuxie_emperor.jpg", (256, 256), 10),
    ("banner_empire.jpg", (256, 144), 10),
    ("bg_season_spring.jpg", (256, 144), 10),
    ("bg_season_summer.jpg", (256, 144), 10),
    ("bg_season_autumn.jpg", (256, 144), 10),
    ("bg_season_winter.jpg", (256, 144), 10),
    ("v4-epic/tab_hero_overview.jpg", (256, 144), 10),
    ("v4-epic/tab_hero_decree.jpg", (256, 144), 10),
    ("v4-epic/tab_hero_chat.jpg", (256, 144), 10),
    ("v4-epic/tab_hero_ministers.jpg", (256, 144), 10),
    ("v4-epic/tab_hero_factions.jpg", (256, 144), 10),
    ("v4-epic/tab_hero_skills.jpg", (256, 144), 10),
    ("v4-epic/tab_hero_buildings.jpg", (256, 144), 10),
    ("v4-epic/tab_hero_map.jpg", (256, 144), 10),
    ("v4-epic/tab_hero_orders.jpg", (256, 144), 10),
    ("v4-epic/modal_report.jpg", (256, 144), 10),
    ("v4-epic/modal_closed.jpg", (256, 144), 10),
    ("v4-epic/modal_history.jpg", (256, 144), 10),
    ("v4-epic/modal_extraction.jpg", (256, 144), 10),
    ("v4-epic/modal_state.jpg", (256, 144), 10),
    ("v4-epic/ending_zhongxing.jpg", (256, 256), 10),
    ("v4-epic/ending_nanqian.jpg", (256, 256), 10),
    ("v4-epic/ending_yihe.jpg", (256, 256), 10),
    ("v4-epic/ending_chanrang.jpg", (256, 256), 10),
    ("v4-epic/ending_yidaizhao.jpg", (256, 256), 10),
    ("v4-epic/ending_liuwang.jpg", (256, 256), 10),
    ("v4-epic/ending_bengpan.jpg", (256, 256), 10),
]


def parse_jpeg_size(path: str):
    """v5.3.0 P7-5: 解析 JPEG 尺寸 (无 Pillow 依赖, SOF marker)."""
    try:
        with open(path, "rb") as f:
            data = f.read(65536)
    except Exception:
        return None
    if data[:2] != b"\xff\xd8":
        return None  # 不是 JPEG
    i = 2
    while i < len(data) - 1:
        if data[i] == 0xff and 0xc0 <= data[i+1] <= 0xcf \
                and data[i+1] not in (0xc4, 0xc8, 0xcc):
            try:
                h = struct.unpack(">H", data[i+5:i+7])[0]
                w = struct.unpack(">H", data[i+7:i+9])[0]
                return (w, h)
            except Exception:
                return None
        i += 1
    return None


@pytest.mark.parametrize("filename,expected_min_size,min_kb", EXPECTED_FILES)
def test_ai_image_integrity(filename, expected_min_size, min_kb):
    """v5.3.0 P7-5: 25 张 AI 图存在 + 有效 JPEG + 尺寸 >= 最小 + 大小 >= min_kb KB."""
    path = os.path.join(WEB_PUBLIC, filename)
    if not os.path.exists(path):
        pytest.skip(f"{filename} not yet generated (主公跑 gen_images_v52.py)")
    size = parse_jpeg_size(path)
    assert size is not None, f"{filename} 不是有效 JPEG"
    assert size[0] >= expected_min_size[0], \
        f"{filename} 宽 {size[0]} < {expected_min_size[0]}"
    assert size[1] >= expected_min_size[1], \
        f"{filename} 高 {size[1]} < {expected_min_size[1]}"
    file_kb = os.path.getsize(path) // 1024
    assert file_kb >= min_kb, \
        f"{filename} 仅 {file_kb}KB < 最小 {min_kb}KB (可能下载不完整)"


def test_ai_image_count():
    """v5.3.0 P7-5: 至少 19 张 (已有 6 ending 可能未覆盖)."""
    n = 0
    for filename, _, _ in EXPECTED_FILES:
        if os.path.exists(os.path.join(WEB_PUBLIC, filename)):
            n += 1
    # 至少主公头像 + banner + 4 季节 + 9 tab hero + 5 modal = 20
    assert n >= 20, f"AI 图只找到 {n}/27 张 (含已有 ending)"


def test_ai_image_aspect_ratio():
    """v5.3.0 P7-5: aspect_ratio 验证 (16:9 = 1.78, 1:1 = 1.0).

    允许 ±20% 误差 (AI 图偶尔会偏).
    """
    files_16_9 = [f for f, _, _ in EXPECTED_FILES
                  if f.startswith("bg_") or "tab_hero" in f or "modal_" in f]
    files_1_1 = [f for f, _, _ in EXPECTED_FILES
                 if f.startswith("portraits/") or "ending_" in f]
    for fn in files_16_9:
        path = os.path.join(WEB_PUBLIC, fn)
        if not os.path.exists(path):
            continue
        size = parse_jpeg_size(path)
        if size is None:
            continue
        w, h = size
        ratio = w / h
        # 16:9 = 1.78, 允许 1.4-2.1
        assert 1.4 <= ratio <= 2.1, f"{fn} aspect {ratio:.2f} 偏离 16:9"
    for fn in files_1_1:
        path = os.path.join(WEB_PUBLIC, fn)
        if not os.path.exists(path):
            continue
        size = parse_jpeg_size(path)
        if size is None:
            continue
        w, h = size
        ratio = w / h
        # 1:1 = 1.0, 允许 0.85-1.18
        assert 0.85 <= ratio <= 1.18, f"{fn} aspect {ratio:.2f} 偏离 1:1"
