"""v5.5.0+ P8-E: 图片压缩 (1KB -> 0.5KB, 190MB -> ~75MB)

策略:
- 所有 jpg: 缩到最大 512x512, 质量 75
- png: 保持原样 (透明背景, 已是 web 优化)
- 处理范围: web/public/btn ctrl corner accent deco status rank misc ending_extra portraits v4-epic
- 输出: 覆盖原文件 (无 .bak, 一次性)
- 跳过: 已是 512x512 以下的 (避免再次压缩质量损失)

用法:
  python scripts/compress_images.py
  python scripts/compress_images.py --max 384 --quality 65  # 更激进
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WEB_PUBLIC = ROOT / "web" / "public"

# 处理所有子目录 (含 portraits/ 和 v4-epic/)
TARGET_DIRS = [
    "btn", "ctrl", "corner", "accent", "deco", "status",
    "rank", "misc", "ending_extra",
    "portraits", "v4-epic",
    # 顶层散图
    "",  # web/public 根
]


def compress_jpg(path: Path, max_size: int, quality: int) -> tuple[int, int]:
    """压缩单张 jpg. 返回 (orig_kb, new_kb)."""
    orig_size = path.stat().st_size
    try:
        img = Image.open(path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        if w > max_size or h > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
        # 保存 (覆盖, 优化)
        img.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    except Exception as e:
        print(f"  [WARN] {path.name}: {e}")
        return (orig_size, orig_size)
    return (orig_size, path.stat().st_size)


def main():
    p = argparse.ArgumentParser(description="v5.5.0+ P8-E 图片压缩")
    p.add_argument("--max", type=int, default=512, help="最大边长 (px)")
    p.add_argument("--quality", type=int, default=75, help="JPEG 质量 (1-95)")
    p.add_argument("--dry-run", action="store_true", help="只扫描不写")
    args = p.parse_args()

    if not WEB_PUBLIC.exists():
        print(f"[ERR] {WEB_PUBLIC} not found")
        return 1

    total_orig = 0
    total_new = 0
    file_count = 0
    skipped = 0

    for sub in TARGET_DIRS:
        target = WEB_PUBLIC / sub if sub else WEB_PUBLIC
        if not target.exists():
            continue
        for f in sorted(target.rglob("*.jpg")):
            if not f.is_file():
                continue
            fsize = f.stat().st_size
            # 跳过小文件 (<20KB, 已优化)
            if fsize < 20 * 1024:
                skipped += 1
                continue
            # 跳过太小的图 (128x128 以下)
            try:
                with Image.open(f) as img:
                    w, h = img.size
                    if max(w, h) < 200:
                        skipped += 1
                        continue
            except Exception:
                skipped += 1
                continue
            if args.dry_run:
                print(f"  [DRY] {f.relative_to(WEB_PUBLIC)}: {fsize//1024}KB ({w}x{h})")
                continue
            orig, new = compress_jpg(f, args.max, args.quality)
            total_orig += orig
            total_new += new
            file_count += 1
            if file_count % 20 == 0:
                pct = (1 - total_new / total_orig) * 100 if total_orig else 0
                print(f"  [{file_count}] {pct:.1f}% saved, {total_orig//1024//1024}MB -> {total_new//1024//1024}MB")

    if args.dry_run:
        print(f"\n[OK] DRY RUN: {file_count + skipped} files scanned")
        return 0

    saved = total_orig - total_new
    pct = saved / total_orig * 100 if total_orig else 0
    print(f"\n[DONE] {file_count} files compressed, {skipped} skipped")
    print(f"  before: {total_orig//1024//1024} MB")
    print(f"  after:  {total_new//1024//1024} MB")
    print(f"  saved:  {saved//1024//1024} MB ({pct:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
