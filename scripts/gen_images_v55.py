#!/usr/bin/env python3
"""v5.5.0+ P8-A: 批量 AI 生图 (200+ 小图: button/控件/弹窗角饰/状态/装饰)

200+ 张图分类 (总耗时 ~ 40-80 分钟 @ 5 RPM):
  - 16 button 按钮 (主导航 4 + 辅助 3 + modal 9)
  - 24 control 控件 (slider/tab/progress/checkbox/dropdown/toggle/...)
  - 44 modal_corner 弹窗角饰 (11 modal x 4 季节)
  - 30 modal_accent 弹窗装饰 (各 modal 3-4 个状态/分隔)
  - 25 small_deco 小装饰 (卷轴端/分隔条/花纹/...)
  - 20 status 状态指示 (loading/success/error/warning/info 4 季节)
  - 15 ranking 品阶 (5 阶 x 3 风格)
  - 22 misc 杂项 (trophy/coin/jade/scroll/...) 
  - 12 扩展 ending 备用 (1:1)

合计 208 张

风格: 与 v5.2.0/v5.4.0 保持一致 (水墨 + 赭金 + 朱砂 + 翡翠 + 灰蓝)

用法:
  export MINIMAX_API_KEY=sk-xxx
  python scripts/gen_images_v55.py            # 跑全部缺失
  python scripts/gen_images_v55.py --only button  # 只跑含此串的文件名
  python scripts/gen_images_v55.py --limit 50   # 只跑前 50 张
  python scripts/gen_images_v55.py --force     # 覆盖已有
  python scripts/gen_images_v55.py --dry-run   # 只打印计划
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB_PUBLIC = ROOT / "web" / "public"

STYLE_SUFFIX = (
    "Chinese ink wash painting shuimo style, Han dynasty, "
    "rice paper background texture, fine line work, gold and red seal accents, "
    "master brushwork, no text overlay, no watermark, masterpiece"
)

# 200+ 张小图 (按类别分块, 方便 --only 过滤)
IMAGES: list[tuple[str, str, str]] = []


def add(filename: str, prompt: str, aspect: str = "1:1") -> None:
    IMAGES.append((filename, prompt, aspect))


# ════════════════════════════════════════════════════════════════
# 1. 16 button 按钮 (主导航 4 + 辅助 3 + modal 9)
# ════════════════════════════════════════════════════════════════
add(
    "btn/btn_play_swords.jpg",
    "Ancient Chinese bronze sword icon, Han dynasty warring states style, "
    "jade hilt, gold inlay, ink wash painting, square button shape, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_report_scroll.jpg",
    "Imperial gazette bamboo scroll icon, Han dynasty, "
    "red seal stamp, tied with golden cord, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_decree_brush.jpg",
    "Imperial writing brush on golden scroll, "
    "Han dynasty calligraphy, jade brush holder, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_history_book.jpg",
    "Ancient Chinese history book, bamboo slips bound with leather, "
    "Han dynasty archive, ink wash, square button, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_menu_grid.jpg",
    "Imperial menu grid, Han dynasty nine-rank system, "
    "jade tiles, ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_settings_gear.jpg",
    "Ancient Chinese mechanical gear, Han dynasty water clock, "
    "bronze and jade, ink wash, square button, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_help_lamp.jpg",
    "Ancient Chinese palace lamp, bronze and silk shade, "
    "Han dynasty, warm light, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_confirm.jpg",
    "Imperial jade seal of approval, vermillion paste, "
    "Han dynasty emperor's chop, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_cancel.jpg",
    "Broken imperial seal, void stamp mark, "
    "Han dynasty rejected edict, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_danger.jpg",
    "Ancient Chinese red flag of warning, "
    "vermillion warning banner, Han dynasty military alert, ink wash, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_close_x.jpg",
    "Ancient Chinese crossing swords, dual blades forming X, "
    "Han dynasty dismiss gesture, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_save.jpg",
    "Imperial bamboo slip storage chest, locked and sealed, "
    "Han dynasty archive box, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_load.jpg",
    "Han dynasty bamboo slip unrolling, opening ancient archive, "
    "ink wash painting, square button, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_quick_play.jpg",
    "Imperial fast march banner, Han dynasty military speed order, "
    "vermillion flag with horses, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_cheat.jpg",
    "Mysterious ancient Chinese talisman, hidden imperial cheat code, "
    "vermillion paper with gold seal, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "btn/btn_tts.jpg",
    "Ancient Chinese bronze bell, ringing court announcement, "
    "Han dynasty, ink wash, square button, " + STYLE_SUFFIX,
    "1:1",
)

# ════════════════════════════════════════════════════════════════
# 2. 24 control 控件 (slider/tab/progress/checkbox/...)
# ════════════════════════════════════════════════════════════════
add(
    "ctrl/ctrl_slider_track.jpg",
    "Ancient Chinese scroll unfurling track, "
    "bamboo rail with gold markers, ink wash, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "ctrl/ctrl_slider_thumb.jpg",
    "Imperial jade slider thumb, polished jade sphere, "
    "Han dynasty, gold filigree, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_tab_active.jpg",
    "Active imperial edict scroll, opened and lit, "
    "Han dynasty decree, vermillion ribbon, ink wash, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "ctrl/ctrl_tab_inactive.jpg",
    "Closed imperial scroll, tied with red cord, "
    "Han dynasty waiting edict, ink wash, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "ctrl/ctrl_progress_bar.jpg",
    "Ancient Chinese progress beam, bronze ruler with marks, "
    "Han dynasty measurement, ink wash, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "ctrl/ctrl_checkbox_checked.jpg",
    "Imperial check mark seal, vermillion approval stamp, "
    "Han dynasty pass mark, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_checkbox_unchecked.jpg",
    "Empty imperial verdict box, blank jade tablet, "
    "Han dynasty awaiting judgment, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_dropdown_arrow.jpg",
    "Han dynasty downward imperial banner, vermillion arrow, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_toggle_on.jpg",
    "Imperial switch in ON position, jade lever, "
    "Han dynasty mechanism, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_toggle_off.jpg",
    "Imperial switch in OFF position, jade lever, "
    "Han dynasty mechanism at rest, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_radio_selected.jpg",
    "Selected imperial seal, vermillion impression, "
    "Han dynasty chosen option, ink wash, circular, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_radio_unselected.jpg",
    "Empty jade circle, Han dynasty unchosen option, "
    "ink wash painting, circular, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_input_field.jpg",
    "Ancient Chinese writing box, empty bamboo slip awaiting inscription, "
    "Han dynasty input field, ink wash, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "ctrl/ctrl_input_focused.jpg",
    "Imperial writing box with focused cursor, golden brush, "
    "Han dynasty active input, ink wash, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "ctrl/ctrl_search_icon.jpg",
    "Han dynasty imperial search, bronze magnifier lens, "
    "scholar searching archives, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_filter_icon.jpg",
    "Ancient Chinese water filter, bronze filtration vessel, "
    "Han dynasty refinement, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_sort_icon.jpg",
    "Han dynasty bamboo slip sorting, ordered ranks, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_expand_icon.jpg",
    "Imperial expanding fan, unfurling court decree, "
    "Han dynasty, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_collapse_icon.jpg",
    "Imperial folded fan, collapsed court decree, "
    "Han dynasty, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_refresh_icon.jpg",
    "Ancient Chinese waterwheel, cyclic flow, "
    "Han dynasty refresh mechanism, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_pagination_prev.jpg",
    "Han dynasty leftward scroll movement, returning to previous page, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_pagination_next.jpg",
    "Han dynasty rightward scroll movement, advancing to next page, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_volume_icon.jpg",
    "Ancient Chinese bronze bell, volume indicator, "
    "Han dynasty court sound level, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ctrl/ctrl_theme_icon.jpg",
    "Han dynasty seasonal color wheel, four seasons on jade disc, "
    "ink wash painting, circular, " + STYLE_SUFFIX,
    "1:1",
)

# ════════════════════════════════════════════════════════════════
# 3. 44 modal_corner 弹窗角饰 (11 modal x 4 季节)
# ════════════════════════════════════════════════════════════════
MODALS = [
    "state", "history", "extraction", "closed_issues", "report",
    "decree", "settlement", "cheat", "settings", "help", "confirm",
]
SEASONS = ["spring", "summer", "autumn", "winter"]
for modal in MODALS:
    for season in SEASONS:
        if season == "spring":
            desc = "jade green tendrils, fresh buds, gold filigree"
        elif season == "summer":
            desc = "vermillion lotus, red fire, gold tassel"
        elif season == "autumn":
            desc = "gold maple leaves, brown bark, jade accent"
        else:
            desc = "jade white plum blossoms, ice crystal, gold dust"
        add(
            f"corner/modal_{modal}_{season}_tl.jpg",
            f"Top-left Chinese cloud corner ornament, {desc}, "
            f"Han dynasty, fine line work, no text, " + STYLE_SUFFIX,
            "1:1",
        )

# ════════════════════════════════════════════════════════════════
# 4. 30 modal_accent 弹窗装饰 (分隔条/状态徽章/收尾)
# ════════════════════════════════════════════════════════════════
add(
    "accent/divider_horizontal.jpg",
    "Ancient Chinese horizontal divider, gold filigree, "
    "Han dynasty scroll separator, ink wash, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "accent/divider_vertical.jpg",
    "Ancient Chinese vertical divider, jade inlay, "
    "Han dynasty scroll separator, ink wash, " + STYLE_SUFFIX,
    "9:16",
)
add(
    "accent/divider_double.jpg",
    "Double horizontal divider, twin gold lines, "
    "Han dynasty formal section break, ink wash, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "accent/scroll_end_top.jpg",
    "Han dynasty bamboo scroll top end, golden cap, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "accent/scroll_end_bottom.jpg",
    "Han dynasty bamboo scroll bottom end, jade weight, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "accent/badge_authority.jpg",
    "Imperial authority badge, jade and gold nine-rank seal, "
    "Han dynasty official rank, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/badge_trust.jpg",
    "Imperial trust badge, double vermillion heart seal, "
    "Han dynasty popular support, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/badge_faction.jpg",
    "Imperial faction badge, five colored faction flags, "
    "Han dynasty political group, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/badge_military.jpg",
    "Imperial military badge, bronze tiger talisman, "
    "Han dynasty army command, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/badge_treasury.jpg",
    "Imperial treasury badge, gold and jade coin stack, "
    "Han dynasty national wealth, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/badge_population.jpg",
    "Imperial population badge, multiple figures on silk, "
    "Han dynasty census record, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/badge_crisis.jpg",
    "Imperial crisis badge, vermillion warning lantern, "
    "Han dynasty emergency signal, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/badge_alliance.jpg",
    "Imperial alliance badge, twin jade discs linked, "
    "Han dynasty diplomatic pact, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/badge_war.jpg",
    "Imperial war badge, red banner with crossed swords, "
    "Han dynasty conflict, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/badge_peace.jpg",
    "Imperial peace badge, dove and olive branch Han style, "
    "Han dynasty tranquility, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/section_header_l.jpg",
    "Han dynasty section header left, gold seal mark, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "accent/section_header_r.jpg",
    "Han dynasty section header right, jade ornament, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "accent/section_header_lr.jpg",
    "Han dynasty section header full, twin gold seals, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "accent/quill_pen.jpg",
    "Han dynasty writing brush quill, with ink drop, "
    "ink wash painting, vertical, " + STYLE_SUFFIX,
    "9:16",
)
add(
    "accent/ink_stone.jpg",
    "Han dynasty ink stone, black ink well, "
    "scholar's writing tool, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/paper_blank.jpg",
    "Han dynasty rice paper, blank scroll, "
    "ink wash painting texture, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/ribbon_red.jpg",
    "Vermillion silk ribbon, Han dynasty tie, "
    "flowing red fabric, ink wash, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "accent/ribbon_gold.jpg",
    "Golden silk ribbon, Han dynasty imperial tie, "
    "flowing gold fabric, ink wash, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "accent/stamp_round.jpg",
    "Round vermillion imperial stamp, Han dynasty chop, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/stamp_square.jpg",
    "Square vermillion imperial stamp, Han dynasty chop, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/loading_dots.jpg",
    "Han dynasty rotating dots, three bronze weights, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "accent/loading_spinner.jpg",
    "Han dynasty spinning wheel, bronze rotating disc, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/empty_state.jpg",
    "Han dynasty empty archive, blank bamboo slips, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/error_state.jpg",
    "Han dynasty error broken seal, cracked jade, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "accent/success_state.jpg",
    "Han dynasty success golden seal, vermillion approval, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)

# ════════════════════════════════════════════════════════════════
# 5. 25 small_deco 小装饰 (花纹/卷轴端/纹样)
# ════════════════════════════════════════════════════════════════
add(
    "deco/cloud_pattern_1.jpg",
    "Chinese auspicious cloud pattern 1, Han dynasty, "
    "jade green and gold, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/cloud_pattern_2.jpg",
    "Chinese auspicious cloud pattern 2, Han dynasty, "
    "vermillion and gold, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/cloud_pattern_3.jpg",
    "Chinese auspicious cloud pattern 3, Han dynasty, "
    "jade white and gold, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/cloud_pattern_4.jpg",
    "Chinese auspicious cloud pattern 4, Han dynasty, "
    "gold and brown, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/dragon_motif.jpg",
    "Han dynasty imperial dragon motif, gold and jade, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/phoenix_motif.jpg",
    "Han dynasty imperial phoenix motif, vermillion and gold, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/tiger_motif.jpg",
    "Han dynasty white tiger motif, bronze and jade, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/snake_motif.jpg",
    "Han dynasty imperial snake motif, jade green and gold, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/tortoise_motif.jpg",
    "Han dynasty black tortoise motif, bronze and jade, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/bamboo_motif.jpg",
    "Han dynasty bamboo motif, jade green leaves, "
    "ink wash painting, vertical, " + STYLE_SUFFIX,
    "9:16",
)
add(
    "deco/plum_motif.jpg",
    "Han dynasty plum blossom motif, jade white petals, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/orchid_motif.jpg",
    "Han dynasty orchid motif, jade green leaves, "
    "ink wash painting, vertical, " + STYLE_SUFFIX,
    "9:16",
)
add(
    "deco/chrysanthemum_motif.jpg",
    "Han dynasty chrysanthemum motif, gold and white petals, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/lotus_motif.jpg",
    "Han dynasty lotus motif, vermillion and gold, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/wave_pattern.jpg",
    "Chinese wave pattern, Han dynasty, jade green and gold, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "deco/mountain_pattern.jpg",
    "Chinese mountain pattern, Han dynasty landscape, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "deco/border_frame_thin.jpg",
    "Han dynasty thin border frame, gold filigree, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "deco/border_frame_thick.jpg",
    "Han dynasty thick border frame, jade inlay, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "deco/border_double_line.jpg",
    "Han dynasty double-line border, twin gold lines, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "deco/endcap_left.jpg",
    "Han dynasty scroll endcap left, jade carving, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/endcap_right.jpg",
    "Han dynasty scroll endcap right, gold carving, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/centerpiece_a.jpg",
    "Han dynasty centerpiece alpha, twin dragons, "
    "gold and jade, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/centerpiece_b.jpg",
    "Han dynasty centerpiece beta, phoenix and dragon, "
    "vermillion and gold, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/centerpiece_c.jpg",
    "Han dynasty centerpiece gamma, jade seal, "
    "imperial chop, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "deco/centerpiece_d.jpg",
    "Han dynasty centerpiece delta, four treasures of study, "
    "brush ink paper stone, ink wash, square, " + STYLE_SUFFIX,
    "1:1",
)

# ════════════════════════════════════════════════════════════════
# 6. 20 status 状态指示 (loading/success/error/warning/info 4 季节)
# ════════════════════════════════════════════════════════════════
STATUS_TYPES = ["loading", "success", "error", "warning", "info"]
for st in STATUS_TYPES:
    for season in SEASONS:
        if season == "spring":
            desc = "jade green"
        elif season == "summer":
            desc = "vermillion"
        elif season == "autumn":
            desc = "gold"
        else:
            desc = "jade white"
        add(
            f"status/{st}_{season}.jpg",
            f"Han dynasty {st} status indicator, {desc} palette, "
            f"ink wash painting, square, " + STYLE_SUFFIX,
            "1:1",
        )

# ════════════════════════════════════════════════════════════════
# 7. 15 ranking 品阶 (5 阶 x 3 风格)
# ════════════════════════════════════════════════════════════════
RANKS = ["gong", "hou", "bo", "zi", "nan"]
RANK_STYLES = ["formal", "battle", "scholar"]
for rank in RANKS:
    for style in RANK_STYLES:
        add(
            f"rank/rank_{rank}_{style}.jpg",
            f"Han dynasty {rank} rank insignia, {style} style, "
            f"gold and jade, ink wash, square, " + STYLE_SUFFIX,
            "1:1",
        )

# ════════════════════════════════════════════════════════════════
# 8. 22 misc 杂项 (奖杯/钱币/玉石/卷轴/...)
# ════════════════════════════════════════════════════════════════
add(
    "misc/item_jade.jpg",
    "Imperial jade bi disc, Han dynasty treasure, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_gold_coin.jpg",
    "Han dynasty gold coin, round with square hole, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_silver_coin.jpg",
    "Han dynasty silver coin, round with square hole, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_bronze_coin.jpg",
    "Han dynasty bronze coin, round with square hole, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_pearl.jpg",
    "Han dynasty luminous pearl, white jade orb, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_gemstone.jpg",
    "Han dynasty imperial gemstone, multi-faceted jade, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_silk.jpg",
    "Han dynasty silk bolt, flowing red and gold, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "misc/item_tea.jpg",
    "Han dynasty tea set, bronze teapot and cups, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_wine.jpg",
    "Han dynasty bronze wine vessel, ceremonial jar, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_book.jpg",
    "Han dynasty ancient book, bamboo slips, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_painting.jpg",
    "Han dynasty scroll painting, landscape on silk, "
    "ink wash painting, vertical, " + STYLE_SUFFIX,
    "9:16",
)
add(
    "misc/item_calligraphy.jpg",
    "Han dynasty calligraphy work, brush and ink masterpiece, "
    "ink wash painting, vertical, " + STYLE_SUFFIX,
    "9:16",
)
add(
    "misc/item_chariot.jpg",
    "Han dynasty bronze chariot model, war vehicle, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_horse.jpg",
    "Han dynasty imperial horse, red war horse, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_armor.jpg",
    "Han dynasty general armor, lamellar plates, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_helmet.jpg",
    "Han dynasty general helmet, bronze and red plume, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_sword.jpg",
    "Han dynasty ceremonial sword, jade hilt, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_bow.jpg",
    "Han dynasty recurve bow, bamboo and sinew, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_arrow.jpg",
    "Han dynasty bronze arrowhead, three fletched, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_shield.jpg",
    "Han dynasty bronze shield, round with central boss, "
    "ink wash painting, square, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "misc/item_flag_red.jpg",
    "Han dynasty vermillion command flag, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)
add(
    "misc/item_flag_gold.jpg",
    "Han dynasty golden imperial flag, "
    "ink wash painting, horizontal, " + STYLE_SUFFIX,
    "16:9",
)

# ════════════════════════════════════════════════════════════════
# 9. 12 扩展 ending 备用 (1:1)
# ════════════════════════════════════════════════════════════════
add(
    "ending_extra/ending_heqin.jpg",
    "Han dynasty peace through marriage, heqin princess, "
    "two courts united, ink wash, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_tuishi.jpg",
    "Han dynasty emperor abdicating in tuishi, formal regency, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_zhenzhu.jpg",
    "Han dynasty hidden pearl, secret heir, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_wujing.jpg",
    "Han dynasty wujing uprising, peasant revolt, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_guanjun.jpg",
    "Han dynasty crown prince enthroned, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_beiping.jpg",
    "Han dynasty northern pacification, frontier general triumph, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_nanzheng.jpg",
    "Han dynasty southern campaign, river battle, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_xixing.jpg",
    "Han dynasty western expedition, silk road, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_xiandi.jpg",
    "Han dynasty xiandi retired, hermit life, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_zaoxiang.jpg",
    "Han dynasty premature death, sudden passing, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_beibu.jpg",
    "Han dynasty northern barbarian invasion, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)
add(
    "ending_extra/ending_chongguang.jpg",
    "Han dynasty restoration of light, second bloom, "
    "ink wash painting, " + STYLE_SUFFIX,
    "1:1",
)


def main():
    p = argparse.ArgumentParser(description="v5.5.0+ P8-A 批量 AI 生图 (200+ 小图)")
    p.add_argument("--only", type=str, help="只跑文件名含此串")
    p.add_argument("--limit", type=int, default=0, help="最多跑 N 张 (0=全部)")
    p.add_argument("--force", action="store_true", help="覆盖已有")
    p.add_argument("--dry-run", action="store_true", help="只打印计划不生图")
    args = p.parse_args()

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

    pending = []
    for filename, prompt, aspect in IMAGES:
        if args.only and args.only not in filename:
            continue
        target = WEB_PUBLIC / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not args.force:
            continue
        pending.append((filename, prompt, aspect))
    if args.limit > 0:
        pending = pending[:args.limit]
    if not pending:
        print(f"[OK] 全部已存在, 无需生图 (总 {len(IMAGES)} 张, --force 覆盖)")
        return 0

    print(f"[PLAN] 准备生 {len(pending)} 张图 (总 {len(IMAGES)} 张)")
    print(f"       估算耗时 {len(pending)*12/60:.1f} 分钟 (5 RPM 限流, 含 60s retry)")
    if args.dry_run:
        for fn, p, a in pending:
            print(f"  - {fn} ({a}): {p[:60]}...")
        return 0

    ok_count = 0
    fail_count = 0
    t0 = time.time()
    for i, (filename, prompt, aspect) in enumerate(pending, 1):
        target = WEB_PUBLIC / filename
        elapsed = time.time() - t0
        avg = elapsed / i if i > 1 else 12
        eta = avg * (len(pending) - i)
        print(f"[{i}/{len(pending)}] {filename} ({aspect}) ETA {eta/60:.1f}min")
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
    print(f"\n[DONE] {ok_count} 成功 / {fail_count} 失败, 耗时 {elapsed/60:.1f}min")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
