"""地区/军队/人物名称模糊匹配。L1（仅依赖 models + re）。

接受 regions/armies/characters 字典作参数——不持全局态，db 与 context 都可调用。
"""


import re
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING




def compact_name(value: str) -> str:
    """去除所有标点/空格，生成规范化的比对键。"""
    return re.sub(r"[\s/／、，。,.：:；;（）()《》<>-]+", "", value)


def region_aliases(region: Dict) -> List[str]:
    """生成地区的所有别名（id / 全称 / 简称 / 历史别名）。"""
    aliases = [region.get("id", ""), region.get("name", ""), compact_name(region.get("name", ""))]
    name = region.get("name", "")
    for part in re.split(r"\s*/\s*|\s*／\s*", name):
        if part.strip():
            aliases.append(part.strip())
    # 历史别名（汉末特色）
    special = {
        "河南尹": ["洛阳", "河南", "洛", "雒阳"],
        "颍川郡": ["许县", "许昌", "颍川", "颍"],
        "南阳郡": ["宛城", "南阳", "宛"],
        "涿郡": ["幽州", "涿", "范阳"],
        "太原郡": ["晋阳", "太原", "并州"],
        "北平郡": ["蓟县", "蓟城", "燕京", "幽州"],
        "辽东郡": ["襄平", "辽东", "平州"],
        "辽西郡": ["辽西", "柳城"],
        "乐浪郡": ["朝鲜", "乐浪", "平壤"],
        "安定郡": ["安定", "陇东"],
        "北地郡": ["北地", "冯翊"],
        "武都郡": ["武都", "陇南"],
        "天水郡": ["上邽", "天水", "秦州"],
        "金城郡": ["金城", "兰州"],
        "武威郡": ["姑臧", "武威", "凉州"],
        "张掖郡": ["张掖", "甘州"],
        "酒泉郡": ["酒泉", "肃州"],
        "敦煌郡": ["敦煌", "沙州"],
        "西平郡": ["西平", "鄯州"],
        "代郡": ["代县", "代郡", "雁门"],
        "上党郡": ["长子", "上党", "潞州"],
        "河内郡": ["怀县", "河内", "怀庆"],
        "东郡": ["濮阳", "东郡", "濮州"],
        "陈留郡": ["陈留", "汴梁", "开封"],
        "济阴郡": ["定陶", "济阴", "曹州"],
        "泰山郡": ["奉高", "泰山", "泰安"],
        "琅琊国": ["开阳", "琅琊", "临沂"],
        "北海国": ["剧县", "北海", "潍州"],
        "东莱郡": ["黄县", "东莱", "登州"],
        "太原郡": ["晋阳", "太原", "并州"],
        "上党郡": ["长子", "上党", "潞州"],
        "西河郡": ["离石", "西河", "汾州"],
        "五原郡": ["九原", "五原", "包头"],
        "朔方郡": ["临戎", "朔方", "鄂尔多斯"],
        "云中郡": ["云中", "托克托"],
        "定襄郡": ["善无", "定襄", "和林格尔"],
        "雁门郡": ["阴馆", "雁门", "代县"],
        "广陵郡": ["广陵", "扬州", "邢江"],
        "丹阳郡": ["建业", "丹阳", "江宁"],
        "吴郡": ["吴县", "吴郡", "苏州"],
        "会稽郡": ["山阴", "会稽", "绍兴"],
        "豫章郡": ["南昌", "豫章", "洪州"],
        "庐陵郡": ["高昌", "庐陵", "吉州"],
        "南海郡": ["番禹", "南海", "广州"],
        "苍梧郡": ["广信", "苍梧", "梧州"],
        "郁林郡": ["布山", "郁林", "贵港"],
        "合浦郡": ["合浦", "廉州"],
        "交趾郡": ["龙编", "交趾", "河内"],
        "九真郡": ["胥浦", "九真", "清化"],
        "日南郡": ["西卷", "日南", "顺化"],
        "零陵郡": ["泉陵", "零陵", "永州"],
        "桂阳郡": ["郴县", "桂阳", "郴州"],
        "武陵郡": ["临沅", "武陵", "常德"],
        "长沙郡": ["临湘", "长沙", "湘州"],
        "江夏郡": ["西陵", "江夏", "武昌"],
        "南郡": ["江陵", "南郡", "荆州"],
        "南阳郡": ["宛城", "南阳", "宛"],
    }
    region_id = region.get("id", "")
    aliases.extend(special.get(region_id, []))
    unique: List[str] = []
    seen: set = set()
    for alias in aliases:
        key = compact_name(alias)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(alias)
    return unique


def match_region_id_from_text(text: str, regions: Dict[str, Dict]) -> Optional[str]:
    """从任意文本模糊匹配地区 ID。返回匹配的 region id 或 None。"""
    cleaned = compact_name(text)
    if not cleaned:
        return None
    matches: List[Tuple[int, str]] = []
    for region in regions.values():
        score = 0
        for alias in region_aliases(region):
            alias_key = compact_name(alias)
            if cleaned == alias_key:
                score = max(score, 120)
            elif alias_key and alias_key in cleaned:
                score = max(score, 80 + len(alias_key))
            elif cleaned in alias_key:
                score = max(score, 45 + len(cleaned))
        if score:
            matches.append((score, region.get("id", "")))
    if not matches:
        return None
    matches.sort(reverse=True, key=lambda item: item[0])
    if len(matches) == 1 or matches[0][0] >= matches[1][0] + 8:
        return matches[0][1]
    return None


def army_aliases(army: Dict) -> List[str]:
    """生成军队的所有别名。"""
    aliases = [
        army.get("id", ""),
        army.get("name", ""),
        compact_name(army.get("name", "")),
        army.get("station", ""),
        army.get("theater", ""),
        army.get("commander", ""),
        army.get("controller", ""),
    ]
    name = army.get("name", "")
    for part in re.split(r"\s*/\s*|\s*／\s*", name):
        if part.strip():
            aliases.append(part.strip())
    # 汉末军队别名
    special = {
        "丁奉骑兵": ["丁奉", "徐寿骑兵", "建业兵"],
        "张辽并州兵": ["张辽", "并州兵", "并州铁骑", "辽兵"],
        "甘宁锦帆营": ["甘宁", "锦帆营", "水师", "锦帆"],
        "周瑜水军": ["周瑜", "东吴水军", "柴桑水军", "吴水军"],
        "公孙瓒白马义从": ["公孙瓒", "白马义从", "幽州骑", "白马"],
        "袁绍先登营": ["袁绍", "先登营", "先登", "大戟士"],
        "曹操虎豹骑": ["曹操", "虎豹骑", "虎骑", "豹骑", "曹骑"],
        "刘备白毦兵": ["刘备", "白毦兵", "白耳兵", "白毦"],
        "吕布并州铁骑": ["吕布", "并州铁骑", "并州骑", "骁骑"],
        "董卓西凉兵": ["董卓", "西凉兵", "凉州兵", "董卓兵"],
    }
    army_id = army.get("id", "")
    aliases.extend(special.get(army_id, []))
    unique: List[str] = []
    seen: set = set()
    for alias in aliases:
        key = compact_name(alias)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(alias)
    return unique


def match_army_id_from_text(text: str, armies: Dict[str, Dict]) -> Optional[str]:
    """从任意文本模糊匹配军队 ID。"""
    cleaned = compact_name(text)
    if not cleaned:
        return None
    matches: List[Tuple[int, str]] = []
    for army in armies.values():
        score = 0
        for alias in army_aliases(army):
            alias_key = compact_name(alias)
            if cleaned == alias_key:
                score = max(score, 125)
            elif alias_key and alias_key in cleaned:
                score = max(score, 80 + len(alias_key))
            elif cleaned in alias_key:
                score = max(score, 45 + len(cleaned))
        if score:
            matches.append((score, army.get("id", "")))
    if not matches:
        return None
    matches.sort(reverse=True, key=lambda item: item[0])
    if len(matches) == 1 or matches[0][0] >= matches[1][0] + 8:
        return matches[0][1]
    return None


def match_character_from_text(text: str, characters: Dict[str, Dict], current: Optional[Dict] = None) -> Optional[Dict]:
    """从文本模糊匹配人物（支持姓名/职位/别名）。"""
    cleaned = text.strip()
    if not cleaned:
        return None
    matches: List[Tuple[int, "Character"]] = []
    for character in characters.values():
        if current is not None and character.get("name") == current.get("name"):
            continue
        score = 0
        name = character.get("name", "")
        office = character.get("office", "")
        office_type = character.get("office_type", "")
        faction = character.get("faction", "")
        aliases = character.get("aliases", [])
        if name in cleaned:
            score += 100
        if office in cleaned or office_type in cleaned or faction in cleaned:
            score += 40
        if any(alias in cleaned for alias in aliases):
            score += 60
        if compact_name(name) == compact_name(cleaned):
            score += 120
        if score > 0:
            matches.append((score, character))
    if not matches:
        return None
    matches.sort(reverse=True, key=lambda item: item[0])
    if len(matches) == 1 or matches[0][0] >= matches[1][0] + 8:
        return matches[0][1]
    return None