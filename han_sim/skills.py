"""天子技能体系查询：技能来源、可用技能、技能卡渲染、skill_tool 模板。L4。

通过 bind_content() 注入 GameContent；汉末特色：技能树分为经略/权谋/武功/文治四系。
"""


from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from han_sim.content import GameContent
    from han_sim.models import Character

_content: Optional["GameContent"] = None


def bind_content(content: "GameContent") -> None:
    """注入静态设定。GameSession 启动时调用一次。"""
    global _content
    _content = content


def _ctx() -> "GameContent":
    if _content is None:
        raise RuntimeError("skills.bind_content() 未调用：GameContent 未注入。")
    return _content


# ── 技能树信息 ──────────────────────────────────────────────────────────────

def get_skill_trees() -> List[str]:
    """返回所有技能树名称。"""
    return ["经略", "权谋", "武功", "文治"]


def get_skills_by_tree(tree: str) -> List[Dict]:
    """返回指定技能树的所有技能。"""
    return [s for s in _ctx().emperor_skills if s.get("tree") == tree]


def skill_unlock_met(skill: Dict, authority: int, acquired_ids: List[str]) -> bool:
    """检查技能是否已解锁（威权条件 + 前置技能）。"""
    unlock_cond = skill.get("unlock", "")
    # 解析威权条件（如"威权>=30"）
    if "威权>=" in unlock_cond:
        try:
            required = int(unlock_cond.split("威权>=")[1])
            if authority < required:
                return False
        except (ValueError, IndexError):
            pass
    elif "威权>" in unlock_cond:
        try:
            required = int(unlock_cond.split("威权>")[1])
            if authority <= required:
                return False
        except (ValueError, IndexError):
            pass
    # 检查前置技能
    prereq = skill.get("req", "")
    if prereq and prereq not in acquired_ids:
        return False
    return True


def available_emperor_skills(authority: int, acquired_ids: List[str]) -> List[Dict]:
    """返回当前可学习的全部技能（含已解锁和未解锁但可预览）。

    返回结构化技能状态列表，每项含：
      - id/name/tree/cost/unlock/req 等原始字段
      - status: "acquired" | "available" | "locked"
      - tree_label: 如"经略系"
    """
    all_skills = _ctx().emperor_skills
    result = []
    for skill in all_skills:
        skill_id = skill.get("id", "")
        unlocked = skill_unlock_met(skill, authority, acquired_ids)
        if skill_id in acquired_ids:
            status = "acquired"
        elif unlocked:
            status = "available"
        else:
            status = "locked"
        result.append({
            **skill,
            "status": status,
            "tree_label": f"{skill['tree']}系",
        })
    return result


def get_skill_cost(skill_id: str) -> int:
    """获取技能学习花费。"""
    for skill in _ctx().emperor_skills:
        if skill.get("id") == skill_id:
            return skill.get("cost", 1)
    return 1


# ── 大臣技能（通用/官职/个人）─────────────────────────────────────────────

def office_skills(office_type: str) -> List[str]:
    """返回某官职类型对应的默认技能列表。"""
    office_skill_map = {
        "chancellor": ["经邦论道", "拟办", "谏诤"],
        "general": ["军事奏对", "练兵", "犒军", "拟办"],
        "minister": ["奏对", "拟办", "谏诤", "查办"],
        "warlord": ["军事奏对", "自保", "扩军", "征粮"],
        "emperor": ["拟旨", "召见", "祭天", "决策"],
    }
    return office_skill_map.get(office_type, ["奏对", "拟办"])


def available_skill_ids(character: Dict, db=None) -> List[str]:
    """返回人物当前可用的技能 ID 列表。"""
    c = _ctx()
    skill_ids = list(c.common_skills)
    skill_ids.extend(c.office_default_skills.get(character.get("office_type", ""), []))
    skill_ids.extend(c.personal_skill_ids.get(character.get("name", ""), []))
    if db is not None:
        skill_ids.extend(getattr(db, "active_skill_grants", lambda n: [])(character.get("name", "")))
    seen: set = set()
    unique = []
    for skill_id in skill_ids:
        if skill_id in seen:
            continue
        seen.add(skill_id)
        unique.append(skill_id)
    return unique


def available_skill_names(character: Dict, db=None) -> str:
    """返回人物当前可用技能名称（字符串，供上下文使用）。"""
    names = []
    for skill_id in available_skill_ids(character, db):
        definition = _ctx().skill_catalog.get(skill_id, {"name": skill_id, "kind": "未知"})
        names.append(f"{definition['name']}[{definition['kind']}]")
    return "，".join(names) if names else "无"


def skill_display_name(skill_id: str) -> str:
    """获取技能显示名。"""
    return str(_ctx().skill_catalog.get(skill_id, {}).get("name", skill_id))


# ── 技能来源标签 ──────────────────────────────────────────────────────────────

def skill_source_labels(character: Dict, skill_id: str, db=None) -> List[str]:
    """返回技能来源标签列表。"""
    c = _ctx()
    labels: List[str] = []
    if skill_id in c.common_skills:
        labels.append("通用")
    if skill_id in c.office_default_skills.get(character.get("office_type", ""), []):
        labels.append(f"{character.get('office_type', '')}官职")
    if skill_id in c.personal_skill_ids.get(character.get("name", ""), []):
        labels.append("个人")
    if db is not None and skill_id in getattr(db, "active_skill_grants", lambda n: [])(character.get("name", "")):
        labels.append("皇帝授权")
    if not labels:
        labels.append(str(c.skill_catalog.get(skill_id, {}).get("kind", "未知")))
    return labels


# ── 技能卡渲染 ──────────────────────────────────────────────────────────────

def skill_summary_line(character: Dict, skill_id: str, db=None) -> str:
    """生成单行技能说明。"""
    c = _ctx()
    labels = "/".join(skill_source_labels(character, skill_id, db))
    description = c.skill_descriptions.get(skill_id, "暂无说明。")
    tool_flag = "可生成指令" if skill_id in c.directive_skill_ids else "可奏对查询"
    return f"- {skill_display_name(skill_id)}（{labels}，{tool_flag}）：{description}"


def print_skill_card(character: Dict, db=None) -> None:
    """打印人物技能卡（控制台用）。"""
    print(f"\n技能卡：{character.get('name', '未知')}（{character.get('office', '无官')}，{character.get('faction', '无派系')}）")
    print(f"属性：忠诚{character.get('loyalty', 0)} | 能力{character.get('ability', 0)} | 清廉{character.get('integrity', 0)} | 胆略{character.get('courage', 0)} | 风格：{character.get('style', '未知')}")
    for skill_id in available_skill_ids(character, db):
        print(skill_summary_line(character, skill_id, db))
    granted = getattr(db, "active_skill_grants", lambda n: [])(character.get("name", "")) if db is not None else []
    if granted:
        print("当前额外授权：" + "、".join(skill_display_name(s) for s in granted))
    else:
        print("当前额外授权：无")


def build_skill_card_text(character: Dict, db=None) -> str:
    """构建人物技能卡文本（用于界面展示）。"""
    lines = [
        f"【{character.get('name', '未知')}】{character.get('office', '无官')}（{character.get('faction', '无派系')}）",
        f"忠诚{character.get('loyalty', 0)} | 能力{character.get('ability', 0)} | 清廉{character.get('integrity', 0)} | 胆略{character.get('courage', 0)} | {character.get('style', '未知')}风格",
    ]
    for skill_id in available_skill_ids(character, db):
        lines.append(skill_summary_line(character, skill_id, db))
    granted = getattr(db, "active_skill_grants", lambda n: [])(character.get("name", "")) if db is not None else []
    if granted:
        lines.append("皇帝额外授权：" + "、".join(skill_display_name(s) for s in granted))
    return "\n".join(lines)


# ── 天子技能树展示 ──────────────────────────────────────────────────────────

def print_emperor_skill_tree(authority: int, acquired_ids: List[str]) -> Dict[str, object]:
    """构建天子技能树结构化数据。

    返回 dict，含：
      - trees: 按技能树分组的结构化技能列表
      - total_points: 当前可用技能点
      - authority: 当前威权
    每项技能含：id/name/cost/desc/status/unlock/req/tree_label
    """
    c = _ctx()
    total_points = c.skill_points if hasattr(c, "skill_points") else 0

    trees_data: Dict[str, List[Dict]] = {tree: [] for tree in get_skill_trees()}

    for skill in c.emperor_skills:
        skill_id = skill.get("id", "")
        unlocked = skill_unlock_met(skill, authority, acquired_ids)
        if skill_id in acquired_ids:
            status = "acquired"
        elif unlocked:
            status = "available"
        else:
            status = "locked"
        req = skill.get("req", "")
        prereq_name = skill_display_name(req) if req else ""
        trees_data[skill.get("tree", "")].append({
            "id": skill_id,
            "name": skill.get("name", ""),
            "tree": skill.get("tree", ""),
            "tree_label": f"{skill['tree']}系",
            "cost": skill.get("cost", 1),
            "desc": skill.get("desc", ""),
            "unlock": skill.get("unlock", ""),
            "req": req,
            "prereq_name": prereq_name,
            "status": status,
        })

    return {
        "authority": authority,
        "acquired_ids": list(acquired_ids),
        "trees": trees_data,
        "total_points": total_points,
    }


# ── 诏令工具模板 ──────────────────────────────────────────────────────────────

def skill_template(template_key: str, **values: object) -> str:
    """根据模板 ID 渲染诏令工具模板。"""
    template = _ctx().skill_tool_templates.get(template_key)
    if template is None:
        return f"[模板缺失：{template_key}]"
    try:
        return template.format(**values)
    except (KeyError, ValueError):
        return template


def list_available_templates() -> List[str]:
    """返回所有可用的诏令模板 ID。"""
    return list(_ctx().skill_tool_templates.keys())