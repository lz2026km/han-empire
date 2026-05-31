"""人物头像服务。L6。

三国志7/8风格头像映射。
优先使用网络头像，失败时使用Emoji占位。

头像来源策略：
1. 优先：从网络素材站直接拼URL
2. 兜底：Emoji头像 + 首字标注

Version: 0.2.0
"""

from typing import Dict, List, Optional
import os

from han_sim.paths import user_data_path

# ── 头像URL映射表（按portrait_id）────────────────────────────────────────────
# 格式：portrait_id -> 图片URL或空（走emoji兜底）
PORTRAIT_URLS: Dict[str, Optional[str]] = {
    # ── 君主/诸侯 ─────────────────────────────────
    "warlord_pool_1":   "https://img.3keengames.net/avatar/rothsaga/cao_cao.png",     # 曹操
    "warlord_pool_2":   "https://img.3keengames.net/avatar/rothsaga/liu_bei.png",      # 刘备
    "warlord_pool_3":   "https://img.3keengames.net/avatar/rothsaga/sun_quan.png",     # 孙权
    "warlord_pool_4":   "https://img.3keengames.net/avatar/rothsaga/sun_ce.png",        # 孙策
    "warlord_pool_5":   "https://img.3keengames.net/avatar/rothsaga/yuan_shao.png",     # 袁绍
    "warlord_pool_6":   "https://img.3keengames.net/avatar/rothsaga/dong_zhuo.png",     # 董卓
    "warlord_pool_7":   "https://img.3keengames.net/avatar/rothsaga/lu_bu.png",         # 吕布
    "warlord_pool_8":   "https://img.3keengames.net/avatar/rothsaga/zhang_jiao.png",    # 张角
    "warlord_pool_9":   "https://img.3keengames.net/avatar/rothsaga/yuan_shu.png",      # 袁术
    "warlord_pool_10":  "https://img.3keengames.net/avatar/rothsaga/zhang_xiu.png",      # 张绣
    # ── 魏国文臣 ─────────────────────────────────
    "minister_pool_1":   "https://img.3keengames.net/avatar/rothsaga/xun_yu.png",       # 荀彧
    "minister_pool_2":   "https://img.3keengames.net/avatar/rothsaga/guo_jia.png",      # 郭嘉
    "minister_pool_3":   "https://img.3keengames.net/avatar/rothsaga/wei_yan.png",       # 魏延
    "minister_pool_4":   "https://img.3keengames.net/avatar/rothsaga/zhu_ge.png",       # 诸葛亮
    "minister_pool_5":   "https://img.3keengames.net/avatar/rothsaga/zhong_hui.png",    # 钟会
    "minister_pool_6":   "https://img.3keengames.net/avatar/rothsaga/zhou_yu.png",      # 周瑜
    "minister_pool_7":   "https://img.3keengames.net/avatar/rothsaga/lu_xun.png",       # 陆逊
    "minister_pool_8":   "https://img.3keengames.net/avatar/rothsaga/sima_yi.png",      # 司马懿
    # ── 蜀国文臣 ─────────────────────────────────
    "minister_pool_9":   "https://img.3keengames.net/avatar/rothsaga/fa_zheng.png",      # 法正
    "minister_pool_10":  "https://img.3keengames.net/avatar/rothsaga/wei_yan.png",       # 魏延
    # ── 吴国文臣 ─────────────────────────────────
    "minister_pool_11":  "https://img.3keengames.net/avatar/rothsaga/lu_xun.png",        # 陆逊
    "minister_pool_12":  "https://img.3keengames.net/avatar/rothsaga/zhang_zhao.png",    # 张昭
    # ── 皇帝/汉室 ────────────────────────────────
    "emperor_pool_1":    "https://img.3keengames.net/avatar/rothsaga/huang_emperor.png",  # 献帝
    "emperor_pool_2":    "https://img.3keengames.net/avatar/rothsaga/huang_emperor.png",  # 献帝
    "han_pool_1":        "https://img.3keengames.net/avatar/rothsaga/huang_emperor.png",  # 献帝
    # ── 后宫妃嫔 ─────────────────────────────────────────
    "consort_pool_1":   "https://img.3keengames.net/avatar/rothsaga/zhenji.png",      # 甄宓
    "consort_pool_2":   "https://img.3keengames.net/avatar/rothsaga/huizhen.png",     # 慧珍
    "consort_pool_3":   "https://img.3keengames.net/avatar/rothsaga/daqiao.png",      # 大乔
    "consort_pool_4":   "https://img.3keengames.net/avatar/rothsaga/xiaoqiao.png",    # 小乔
    "consort_pool_5":   "https://img.3keengames.net/avatar/rothsaga/ganji.png",       # 甘夫人
    "consort_pool_6":   "https://img.3keengames.net/avatar/rothsaga/sunshangxiang.png", # 孙尚香
    "consort_pool_7":   "https://img.3keengames.net/avatar/rothsaga/mishi.png",      # 糜夫人
    "consort_pool_8":   "https://img.3keengames.net/avatar/rothsaga/bu.png",         # 步氏
    "consort_pool_9":   "https://img.3keengames.net/avatar/rothsaga/zhang.png",      # 张氏
    "consort_pool_10":  "https://img.3keengames.net/avatar/rothsaga/dui.png",        # 堕姬
    "consort_pool_11":  "https://img.3keengames.net/avatar/rothsaga/other.png",      # 其他妃嫔
    "consort_pool_12":  "https://img.3keengames.net/avatar/rothsaga/other.png",
    "consort_pool_13":  "https://img.3keengames.net/avatar/rothsaga/other.png",
    "consort_pool_14":  "https://img.3keengames.net/avatar/rothsaga/other.png",
    "consort_pool_15":  "https://img.3keengames.net/avatar/rothsaga/other.png",
}

# ── Emoji 兜底配置 ───────────────────────────────────────────────────────────
OFFICE_EMOJI: Dict[str, str] = {
    "emperor":    "👑",   # 皇帝
    "chancellor": "🎓",   # 丞相
    "general":    "⚔️",   # 将军
    "minister":  "📜",   # 文臣
    "warlord":    "🐉",   # 诸侯
    "default":    "🎭",
}


def get_portrait_url(portrait_id: str) -> Optional[str]:
    """返回头像URL，无则返回None走兜底。"""
    return PORTRAIT_URLS.get(portrait_id)


def get_office_emoji(office_type: str) -> str:
    """根据官职类型返回emoji。"""
    return OFFICE_EMOJI.get(office_type, OFFICE_EMOJI["default"])


def get_affection_border_color(affection: int) -> str:
    """根据好感度返回边框颜色。
    
    Args:
        affection: 好感度值 (0-100)
        
    Returns:
        颜色hex字符串：≥70金色#c9a96e，40-69银色#8b9eb3，<40灰色#9ca3af
    """
    if affection >= 70:
        return "#c9a96e"  # 金色
    elif affection >= 40:
        return "#8b9eb3"  # 银色
    else:
        return "#9ca3af"  # 灰色


def render_character_portrait_html(
    name: str,
    office_type: str = "default",
    portrait_id: str = "",
    size: int = 64,
    extra_style: str = "",
) -> str:
    """生成单个角色头像HTML。

    Args:
        name: 角色名
        office_type: 官职类型（emperor/chancellor/general/minister/warlord/default）
        portrait_id: 头像ID，用于从PORTRAIT_URLS查找网络头像
        size: 头像尺寸（px）
        extra_style: 额外CSS样式

    Returns:
        HTML字符串，可直接塞进Gradio HTML组件
    """
    emoji = get_office_emoji(office_type)
    url = get_portrait_url(portrait_id)

    base_style = f"border-radius:8px;border:2px solid #c9a96e;{extra_style}"

    if url:
        # 网络头像（带加载失败兜底）
        img_html = (
            f'<img src="{url}" alt="{name}" width="{size}" height="{size}" '
            f'style="{base_style}object-fit:cover;" '
            f'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';">'
            f'<div style="display:none;width:{size}px;height:{size}px;{base_style}'
            f'align-items:center;justify-content:center;font-size:{size//2}px;'
            f'background:linear-gradient(135deg,#1a1a2e,#2d2d44);color:#c9a96e;">'
            f'{emoji}</div>'
        )
    else:
        # Emoji兜底（古风渐变背景）
        img_html = (
            f'<div style="width:{size}px;height:{size}px;{base_style}'
            f'display:flex;align-items:center;justify-content:center;font-size:{size//2}px;'
            f'background:linear-gradient(135deg,#1a1a2e,#2d2d44);color:#c9a96e;">'
            f'{emoji}</div>'
        )

    return img_html


def render_portrait_with_name_html(
    name: str,
    office: str = "",
    office_type: str = "default",
    portrait_id: str = "",
    show_name: bool = True,
    size: int = 64,
) -> str:
    """生成带名字的角色头像HTML（用于召对/大臣列表）。

    Args:
        name: 角色名
        office: 官职名称
        office_type: 官职类型
        portrait_id: 头像ID
        show_name: 是否显示名字
        size: 头像尺寸

    Returns:
        HTML字符串，头像+名字+官职垂直排列
    """
    portrait = render_character_portrait_html(name, office_type, portrait_id, size=size)
    name_html = (
        f"<div style='text-align:center;margin-top:4px;font-size:12px;font-weight:bold;"
        f"color:#c9a96e;font-family:system-ui;'>{name}</div>"
    )
    office_html = (
        f"<div style='text-align:center;font-size:10px;color:#9ca3af;"
        f"font-family:system-ui;'>{office}</div>"
    ) if office else ""
    return (
        f"<div style='display:inline-block;text-align:center;margin:6px;"
        f"padding:8px;border-radius:8px;background:#f9fafb;"
        f"border:1px solid #e5e7eb;'>"
        f"{portrait}{name_html}{office_html}</div>"
    )


def render_avatar_grid_html(
    characters: List[Dict],
    cols: int = 4,
    size: int = 64,
) -> str:
    """渲染多角色网格（用于在朝大臣Tab）。

    Args:
        characters: 角色列表，每项含 name/office/office_type/portrait_id
        cols: 每行几列
        size: 头像尺寸

    Returns:
        HTML字符串，网格排列的头像+名字+官职
    """
    cells = []
    for ch in characters:
        cell = render_portrait_with_name_html(
            name=ch.get("name", ""),
            office=ch.get("office", ""),
            office_type=ch.get("office_type", "default"),
            portrait_id=ch.get("portrait_id", ""),
            show_name=True,
            size=size,
        )
        cells.append(cell)

    rows = []
    for i in range(0, len(cells), cols):
        row_cells = cells[i:i + cols]
        rows.append(
            "<div style='display:flex;gap:12px;justify-content:flex-start;flex-wrap:wrap;margin-bottom:12px'>"
            + "".join(row_cells)
            + "</div>"
        )

    return (
        f"<div style='font-family:system-ui,sans-serif;padding:8px'>"
        f"{''.join(rows)}</div>"
    )


if __name__ == "__main__":
    # 测试
    chars = [
        {"name": "曹操", "office": "丞相", "office_type": "warlord", "portrait_id": "warlord_pool_1"},
        {"name": "刘备", "office": "汉室宗亲", "office_type": "warlord", "portrait_id": "warlord_pool_2"},
        {"name": "孙权", "office": "吴侯", "office_type": "warlord", "portrait_id": "warlord_pool_3"},
        {"name": "董卓", "office": "太师", "office_type": "warlord", "portrait_id": "warlord_pool_6"},
        {"name": "诸葛亮", "office": "蜀汉丞相", "office_type": "minister", "portrait_id": "minister_pool_4"},
        {"name": "荀彧", "office": "尚书令", "office_type": "minister", "portrait_id": "minister_pool_1"},
        {"name": "周瑜", "office": "吴将", "office_type": "minister", "portrait_id": "minister_pool_6"},
        {"name": "司马懿", "office": "魏都督", "office_type": "minister", "portrait_id": "minister_pool_8"},
    ]
    html = render_avatar_grid_html(chars, cols=4)
    with open("/tmp/portrait_test.html", "w", encoding="utf-8") as f:
        f.write(f"<div style='padding:20px;background:#f0ece0'>{html}</div>")
    print("Portrait test written to /tmp/portrait_test.html")


# ── Custom Portraits ───────────────────────────────────────────────────────────

def _custom_portrait_dir() -> str:
    path = user_data_path("portraits/custom")
    os.makedirs(path, exist_ok=True)
    return path


def save_custom_portrait(character_name: str, image_data: bytes, filename: str) -> str:
    safe_name = "".join(c if c.isalnum() or c in ("_", "-", " ") else "_" for c in character_name)
    dir_path = _custom_portrait_dir()
    ext = os.path.splitext(filename)[1] if filename else ".png"
    file_path = os.path.join(dir_path, f"{safe_name}{ext}")
    with open(file_path, "wb") as f:
        f.write(image_data)
    return file_path


def delete_custom_portrait(character_name: str) -> bool:
    dir_path = _custom_portrait_dir()
    for fname in os.listdir(dir_path):
        base = os.path.splitext(fname)[0]
        if base == character_name or base == "".join(c if c.isalnum() or c in ("_", "-", " ") else "_" for c in character_name):
            os.remove(os.path.join(dir_path, fname))
            return True
    return False


def list_custom_portraits() -> List[str]:
    dir_path = _custom_portrait_dir()
    if not os.path.exists(dir_path):
        return []
    return sorted(os.listdir(dir_path))