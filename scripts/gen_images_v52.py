#!/usr/bin/env python3
"""v5.2.0 P6-11: 批量 AI 生图 (25 张关键图)

关键图清单 (25 张, 总耗时 ~ 5-15 分钟):
  1. portraits/main/liuxie_emperor.jpg     (主公头像 1:1)
  2. banner_empire.jpg                     (朝代 banner 16:9)
  3-6. bg_season_{spring,summer,autumn,winter}.jpg (4 季节 16:9)
  7-15. v4-epic/tab_hero_{overview,decree,chat,ministers,factions,skills,buildings,map,orders}.jpg (9 Tab 16:9)
  16-20. v4-epic/modal_{report,closed,history,extraction,state}.jpg (5 modal 16:9)
  21-27. v4-epic/ending_{zhongxing,nanqian,yihe,chanrang,yidaizhao,liuwang,bengpan}.jpg (7 ending 1:1)

风格统一 prompt 后缀: 'Chinese ink painting, Han dynasty, gold-red-black palette,
cinematic lighting, no text, no watermark, ultra-detailed'

用法:
  export MINIMAX_API_KEY=sk-xxx
  python scripts/gen_images_v52.py            # 跑全部缺失
  python scripts/gen_images_v52.py --only liuxie_emperor  # 只跑含此串的文件名
  python scripts/gen_images_v52.py --limit 3   # 只跑前 3 张
  python scripts/gen_images_v52.py --force     # 覆盖已有
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB_PUBLIC = ROOT / "web" / "public"
V4_EPIC = WEB_PUBLIC / "v4-epic"

# 统一风格后缀
STYLE_SUFFIX = (
    "Chinese ink painting, Han dynasty aesthetic, gold-red-black palette, "
    "cinematic lighting, no text, no watermark, no logos, ultra-detailed, "
    "masterpiece, 8k"
)

# 25 张图: (filename, prompt, aspect_ratio)
IMAGES = [
    # 1. 主公头像
    (
        "portraits/main/liuxie_emperor.jpg",
        "Portrait of Emperor Xian of Han (Liu Xie), young Chinese emperor in his 20s, "
        "wearing traditional Han dynasty imperial dragon robe, gold crown with jade beads, "
        "dignified yet melancholic expression, ink painting style, " + STYLE_SUFFIX,
        "1:1",
    ),
    # 2. 朝代 banner
    (
        "banner_empire.jpg",
        "Panoramic view of Han dynasty imperial palace, golden rooftops, ancient Chinese "
        "architecture, mountains in mist, cherry blossoms, ink wash painting style, "
        "epic scale, " + STYLE_SUFFIX,
        "16:9",
    ),
    # 3-6. 4 季节
    (
        "bg_season_spring.jpg",
        "Han dynasty garden in spring, cherry blossoms falling, willows, ancient pavilion, "
        "soft pink and green palette, ink painting, peaceful, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "bg_season_summer.jpg",
        "Han dynasty palace courtyard in summer, lotus pond, hot sun, deep green foliage, "
        "scholar with fan, ink painting, warm, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "bg_season_autumn.jpg",
        "Han dynasty mountain path in autumn, red and gold maple leaves, "
        "travelling scholar, mist, ink painting, melancholic, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "bg_season_winter.jpg",
        "Han dynasty palace in winter, snow-covered rooftops, plum blossoms, "
        "cold mist, lone figure in red, ink painting, stark, " + STYLE_SUFFIX,
        "16:9",
    ),
    # 7-15. 9 Tab hero
    (
        "v4-epic/tab_hero_overview.jpg",
        "Imperial court audience hall, Han emperor on throne, ministers bowing, "
        "scroll of governance, ink painting, formal, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/tab_hero_decree.jpg",
        "Emperor writing imperial edict on golden scroll, brush and ink, "
        "imperial seal, ink painting, focused, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/tab_hero_chat.jpg",
        "Emperor in private audience with single minister, intimate chamber, "
        "tea set, curtains, ink painting, conversational, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/tab_hero_ministers.jpg",
        "Roll call of 200+ Han dynasty officials, ancient Chinese portraits grid, "
        "diverse costumes by rank, ink painting, comprehensive, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/tab_hero_factions.jpg",
        "Five faction banners: foreign relatives, eunuchs, aristocracy, scholars, "
        "border generals, Han dynasty, ink painting, political, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/tab_hero_skills.jpg",
        "Imperial study with skill tree, four branches (ruling/personnel/military/livelihood), "
        "scrolls, jade pieces, ink painting, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/tab_hero_buildings.jpg",
        "Han dynasty city with multiple building types: palace, granary, irrigation, "
        "barracks, ink painting, urban planning, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/tab_hero_map.jpg",
        "Ancient Chinese map of Han dynasty provinces, rivers, mountains, "
        "13 administrative regions, ink painting on silk, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/tab_hero_orders.jpg",
        "Secret imperial order hidden in silk scroll, conspiracy, shadows, "
        "ink painting, suspenseful, " + STYLE_SUFFIX,
        "16:9",
    ),
    # 16-20. 5 modal 装饰
    (
        "v4-epic/modal_report.jpg",
        "Imperial monthly gazette on bamboo slip, ancient newspaper, "
        "multiple reports, ink painting, formal, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/modal_closed.jpg",
        "Scrolls of resolved political issues, tied with red cord, "
        "completion, ink painting, settled, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/modal_history.jpg",
        "Historical archive room, scrolls stacked, ancient Chinese history, "
        "time and memory, ink painting, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/modal_extraction.jpg",
        "Transparent overlay of LLM data extraction, Han dynasty, "
        "structured information from narrative, ink painting + data, " + STYLE_SUFFIX,
        "16:9",
    ),
    (
        "v4-epic/modal_state.jpg",
        "Imperial state of the realm overview, comprehensive dashboard, "
        "Han dynasty metrics visualization, ink painting, grand, " + STYLE_SUFFIX,
        "16:9",
    ),
    # 21-27. 7 结局 (覆盖现有 6 + 加 liuwang)
    (
        "v4-epic/ending_zhongxing.jpg",
        "Triumphant Han dynasty revival, golden age, emperor on throne, "
        "prosperous empire, ink painting, hopeful, " + STYLE_SUFFIX,
        "1:1",
    ),
    (
        "v4-epic/ending_nanqian.jpg",
        "Imperial court relocating south, court on boats, escape, "
        "river journey, ink painting, bittersweet, " + STYLE_SUFFIX,
        "1:1",
    ),
    (
        "v4-epic/ending_yihe.jpg",
        "Peace treaty signing, two sides meeting, compromise, "
        "mutual respect, ink painting, balanced, " + STYLE_SUFFIX,
        "1:1",
    ),
    (
        "v4-epic/ending_chanrang.jpg",
        "Emperor abdicating, handing throne to Cao Wei, formal ceremony, "
        "succession, ink painting, solemn, " + STYLE_SUFFIX,
        "1:1",
    ),
    (
        "v4-epic/ending_yidaizhao.jpg",
        "Secret blood-written edict, hidden plot, conspirators in shadows, "
        "ink painting, dramatic, " + STYLE_SUFFIX,
        "1:1",
    ),
    (
        "v4-epic/ending_liuwang.jpg",
        "Emperor in exile, wandering mountains, hermit life, "
        "freedom lost, ink painting, melancholic, " + STYLE_SUFFIX,
        "1:1",
    ),
    (
        "v4-epic/ending_bengpan.jpg",
        "Collapse of Han dynasty, burning palaces, war everywhere, "
        "people fleeing, ink painting, tragic, " + STYLE_SUFFIX,
        "1:1",
    ),
]


def main():
    p = argparse.ArgumentParser(description="v5.2.0 P6-11 批量 AI 生图 (MiniMax image-01)")
    p.add_argument("--only", type=str, help="只跑文件名含此串")
    p.add_argument("--limit", type=int, default=0, help="最多跑 N 张 (0=全部)")
    p.add_argument("--force", action="store_true", help="覆盖已有")
    p.add_argument("--dry-run", action="store_true", help="只打印计划不生图")
    args = p.parse_args()

    # v5.2.0+ 增量: 启动时加载项目根 .env (让 MINIMAX_API_KEY 自动化)
    env_path = ROOT / ".env"
    if env_path.exists():
        try:
            for line in open(env_path, encoding="utf-8"):
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ and v and v != "your_minimax_key_here":
                    os.environ[k] = v
        except Exception:
            pass

    sys.path.insert(0, str(ROOT))
    try:
        from han_sim.image_gen import generate_image, download_image
    except ImportError as e:
        print(f"[ERR] 无法 import han_sim.image_gen: {e}")
        return 1

    # 过滤
    pending = []
    for filename, prompt, aspect in IMAGES:
        if args.only and args.only not in filename:
            continue
        target = WEB_PUBLIC / filename
        if target.exists() and not args.force:
            print(f"[SKIP] {filename} (已存在, --force 覆盖)")
            continue
        pending.append((filename, prompt, aspect))
    if args.limit > 0:
        pending = pending[:args.limit]
    if not pending:
        print("[OK] 全部已存在, 无需生图")
        return 0

    print(f"[PLAN] 准备生 {len(pending)} 张图 (总耗时估算 {len(pending)*2}-{len(pending)*5}s)")
    if args.dry_run:
        for fn, p, a in pending:
            print(f"  - {fn} ({a}): {p[:60]}...")
        return 0

    # 串行执行 (避免 5 RPM 限流)
    ok_count = 0
    fail_count = 0
    t0 = time.time()
    for i, (filename, prompt, aspect) in enumerate(pending, 1):
        target = WEB_PUBLIC / filename
        print(f"[{i}/{len(pending)}] {filename} ({aspect})")
        try:
            urls = generate_image(prompt, aspect_ratio=aspect, n=1)
            if not urls:
                print(f"  [WARN] 返空 url 列表")
                fail_count += 1
                continue
            download_image(urls[0], str(target))
            ok_count += 1
            size_kb = target.stat().st_size // 1024 if target.exists() else 0
            print(f"  [OK] {size_kb}KB")
        except Exception as e:
            print(f"  [FAIL] {e}")
            fail_count += 1
            continue
    elapsed = time.time() - t0
    print(f"\n[DONE] {ok_count} 成功 / {fail_count} 失败, 耗时 {elapsed:.1f}s")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
