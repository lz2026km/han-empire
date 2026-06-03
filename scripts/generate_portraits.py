#!/usr/bin/env python3
"""
生成无版权争议的大臣头像占位符 SVG
这些SVG使用纯色背景和书法字体，可自由使用
"""
import os

PORTRAITS_DIR = "web/public/portraits"
PLACEHOLDER_DIR = os.path.join(PORTRAITS_DIR, "placeholder")

MINISTERS = [
    "黄道周", "黄立极", "魏忠贤", "韩爌", "阿敏", "阎鸣泰", "钱龙锡", "钱谦益",
    "赵率教", "许显纯", "袁崇焕", "袁可立", "莽古尔泰", "范文程", "祖大寿", "皇太极",
    "田尔耕", "王绍徽", "王承恩", "王在晋", "王嘉胤", "王体乾", "王之臣", "满桂",
    "温体仁", "洪承畴", "毛文龙", "毕自严", "林丹汗", "杨嗣昌", "来宗道", "李若琏",
    "李自成", "李标", "曹文诏", "曹化淳", "施凤来", "徐光启", "张维", "张瑞图",
    "张献忠", "崔呈秀", "客氏", "孙承宗", "孙传庭", "周延儒", "史可法", "卢象升",
    "刘鸿训", "倪元璐", "佟养性", "代善", "仁祖"
]

def generate_portrait_svg(name: str, color: str = "#2a1f12") -> str:
    """生成单个大臣头像SVG"""
    first_char = name[0] if name else "?"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="240" viewBox="0 0 200 240">
  <defs>
    <linearGradient id="bg_{name}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2a1f12"/>
      <stop offset="100%" style="stop-color:#1a1208"/>
    </linearGradient>
    <linearGradient id="border_{name}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#c9a84c"/>
      <stop offset="50%" style="stop-color:#e8c86d"/>
      <stop offset="100%" style="stop-color:#8a7034"/>
    </linearGradient>
  </defs>
  <rect width="200" height="240" fill="url(#bg_{name})" rx="0"/>
  <rect x="4" y="4" width="192" height="232" fill="none" stroke="url(#border_{name})" stroke-width="2" rx="4"/>
  <text x="100" y="130" font-family="serif" font-size="96" fill="#c9a84c" text-anchor="middle">{first_char}</text>
  <text x="100" y="180" font-family="serif" font-size="20" fill="#8a7034" text-anchor="middle">{name}</text>
</svg>'''

def main():
    os.makedirs(PLACEHOLDER_DIR, exist_ok=True)
    
    for name in MINISTERS:
        svg_content = generate_portrait_svg(name)
        filename = f"minister_{name}.svg"
        filepath = os.path.join(PLACEHOLDER_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f"Generated: {filename}")
    
    # 生成consort占位符
    consorts = ["袁贵妃", "田贵妃", "慧妃", "周贵人", "周皇后"]
    for name in consorts:
        svg_content = generate_portrait_svg(name)
        filename = f"consort_{name}.svg"
        filepath = os.path.join(PLACEHOLDER_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f"Generated: {filename}")
    
    print(f"\n生成完成! 共 {len(MINISTERS) + len(consorts)} 个占位符头像")
    print(f"保存在: {PLACEHOLDER_DIR}")

if __name__ == "__main__":
    main()