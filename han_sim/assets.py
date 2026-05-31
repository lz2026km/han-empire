"""资源加载与 JSON 校验辅助。L0 叶子模块。

只读 content/ 下设定文件；不持有任何全局态。
"""


import json
import os
import re
import textwrap
from typing import Dict, List

from han_sim.paths import content_path


# 格式化配置（与 constants.py 保持一致）
WRAP_WIDTH = 80
MONEY_UNIT = "万两"


def wrap(text: str) -> str:
    """按宽度换行，保持语义完整。"""
    return "\n".join(textwrap.wrap(text, width=WRAP_WIDTH, replace_whitespace=False))


def load_text_asset(relative_path: str) -> str:
    """读取纯文本资源，替换占位符。"""
    path = content_path(relative_path)
    try:
        with open(path, "r", encoding="utf-8") as file:
            text = file.read().strip()
    except OSError as error:
        raise SystemExit(f"设定文件缺失或不可读：{path} ({error})") from error
    # 运行时占位符替换（如有）
    return text


def load_json_asset(relative_path: str) -> object:
    """读取 JSON 资源，带解析错误提示。"""
    path = content_path(relative_path)
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except OSError as error:
        raise SystemExit(f"设定文件缺失或不可读：{path} ({error})") from error
    except json.JSONDecodeError as error:
        raise SystemExit(f"设定文件 JSON 格式错误：{path} ({error})") from error


def strip_json_fence(text: str) -> str:
    """去掉 LLM 返回的 ```json ... ``` 外壳。"""
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if match:
        return match.group(1).strip()
    return text.strip()


def format_money(value: int) -> str:
    """格式化银两数值。"""
    return f"{value}{MONEY_UNIT}"


def format_money_delta(value: int) -> str:
    """格式化银两变化量（带正负符号）。"""
    sign = "+" if value > 0 else ""
    return f"{sign}{format_money(value)}"


def format_authority(value: int) -> str:
    """格式化威权数值。"""
    return f"{value}"


def format_authority_delta(value: int) -> str:
    """格式化威权变化量。"""
    sign = "+" if value > 0 else ""
    return f"{sign}{value}"


def format_loyalty(value: int) -> str:
    """格式化忠诚度（百分比形式）。"""
    return f"{value}%"


def format_population(value: int) -> str:
    """格式化人口（万）。"""
    if value >= 10000:
        return f"{value // 10000}亿"
    if value >= 100:
        return f"{value / 100:.0f}百万"
    return f"{value}万"


def require_dict(data: object, path: str) -> Dict[str, object]:
    """要求数据是 dict，否则退出。"""
    if not isinstance(data, dict):
        raise SystemExit(f"设定文件应为 JSON object：content/{path}")
    return data


def require_list(data: object, path: str) -> List[object]:
    """要求数据是 list，否则退出。"""
    if not isinstance(data, list):
        raise SystemExit(f"设定文件应为 JSON array：content/{path}")
    return data


def string_list(value: object, path: str) -> List[str]:
    """要求字段是字符串数组。"""
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SystemExit(f"设定字段应为字符串数组：{path}")
    return [str(item) for item in value]


def int_field(data: Dict[str, object], key: str, path: str) -> int:
    """读取整数字段。"""
    try:
        return int(data[key])
    except (KeyError, TypeError, ValueError) as error:
        raise SystemExit(f"设定字段应为整数：{path}.{key}") from error


def str_field(data: Dict[str, object], key: str, path: str) -> str:
    """读取非空字符串字段。"""
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"设定字段应为非空字符串：{path}.{key}")
    return value.strip()


def optional_str_field(data: Dict[str, object], key: str) -> str:
    """读取可选字符串字段，缺省返回空字符串。"""
    value = data.get(key)
    if isinstance(value, str):
        return value.strip()
    return ""


def optional_int_field(data: Dict[str, object], key: str, default: int = 0) -> int:
    """读取可选整数字段，缺省返回默认值。"""
    value = data.get(key)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default