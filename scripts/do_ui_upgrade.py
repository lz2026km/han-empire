#!/usr/bin/env python3
# -*- coding: utf-8 -*-
with open('web_app.py', 'rb') as f:
    content = f.read()

lines = content.split(b'\n')

# Find auth_bg line
auth_bg_line_idx = None
for i, line in enumerate(lines):
    if b'auth_bg = ' in line and b'#2d1f1f' in line:
        auth_bg_line_idx = i
        break

print(f"auth_bg at line {auth_bg_line_idx + 1}")

# Check if variables already injected
if b'# UI升级颜色变量' in lines[auth_bg_line_idx]:
    print("Variables already injected, skipping")
else:
    # Check which vars exist
    has_popularity = any(b"popularity = s.metrics.get" in lines[j] for j in range(len(lines)))
    inject_after = auth_bg_line_idx
    new_lines = [b'']
    if not has_popularity:
        new_lines.append(b'        popularity = s.metrics.get(\'民心\', 60)')
        new_lines.append(b'        treasury = s.metrics.get(\'treasury\', 1000)')
        new_lines.append(b'        military = s.metrics.get(\'military\', 50)')
        new_lines.append(b'        year = s.metrics.get(\'year\', 189)')
        new_lines.append(b'        month = s.metrics.get(\'month\', 1)')
        era_map_str = "        era_map = {184: (\"黄巾之乱前夜\", \"中平元年\"), 189: (\"董卓之乱\", \"初平元年\"), 190: (\"诸侯割据\", \"初平二年\"), 191: (\"群雄逐鹿\", \"初平三年\"), 192: (\"军阀混战\", \"初平四年\"), 193: (\"曹操崛起\", \"兴平元年\"), 194: (\"孙权守江东\", \"兴平二年\"), 195: (\"刘备入蜀\", \"建安元年\")}"
        new_lines.append(era_map_str.encode('utf-8'))
        new_lines.append(b'        era_name, era_year = era_map.get(year, ("乱世", f"第{year-184}年"))')
    new_lines.extend([
        b'        # UI升级颜色变量',
        b'        authority_color = "#22c55e" if authority >= 60 else "#f59e0b" if authority >= 30 else "#ef4444"',
        b'        popularity_color = "#22c55e" if popularity >= 60 else "#f59e0b" if popularity >= 30 else "#ef4444"',
        b'        fanzhen_color = "#22c55e" if fanzhen <= 30 else "#f59e0b" if fanzhen <= 60 else "#ef4444"',
        b'        auth_bar_color = "#22c55e" if authority >= 60 else "#f59e0b" if authority >= 30 else "#ef4444"',
        b'        fanz_bar_color = "#22c55e" if fanzhen <= 30 else "#f59e0b" if fanzhen <= 60 else "#ef4444"',
    ])
    lines = lines[:inject_after+1] + new_lines + lines[inject_after+1:]
    print("Injected", len(new_lines), "lines")

# Rebuild and find return block
content = b'\n'.join(lines)
start = sum(len(lines[i]) + 1 for i in range(242))
end = sum(len(lines[i]) + 1 for i in range(311))
old_return = content[start:end]

marker_pos = old_return.find('        <!-- 威权状态卡 -->'.encode('utf-8'))
if marker_pos == -1:
    print("ERROR: marker not found")
    exit(1)

# Build enhanced prefix
enhanced_prefix = '''        # UI升级大明风仪表盘
        faction_data = s.metrics.get('faction_influence', {})
        faction_colors = {"忠汉派": "#22c55e", "务实派": "#3b82f6", "离心派": "#f59e0b", "叛逆派": "#ef4444"}
        faction_bar = "".join([
            f"<span style=\\'background:{faction_colors.get(k,\\'#9ca3af\\')};color:white;padding:2px 6px;border-radius:4px;margin-right:4px;font-size:10px\\'>{k}:{v}</span>"
            for k, v in faction_data.items()
        ]) if faction_data else "<span style=\\'color:#9ca3af;font-size:11px\\'>尚未分化</span>"
        triggered = s.metrics.get('triggered_events', [])
        event_badge = f"<span style=\\'background:#ef4444;color:white;padding:2px 6px;border-radius:10px;font-size:10px\\'>{len(triggered)}事件</span>" if triggered else "<span style=\\'color:#9ca3af;font-size:11px\\'>暂无</span>"
        activated = s.metrics.get('activated_skills', [])
        skill_badge = f"<span style=\\'background:#c9a96e;color:#1a1a2e;padding:2px 6px;border-radius:10px;font-size:10px\\'>{len(activated)}技</span>" if activated else "<span style=\\'color:#9ca3af;font-size:11px\\'>暂无</span>"
        built = s.metrics.get('buildings', {})
        built_count = len(built)
        building_badge = f"<span style=\\'background:#22c55e;color:#1a1a2e;padding:2px 6px;border-radius:10px;font-size:10px\\'>{built_count}建筑</span>" if built_count else "<span style=\\'color:#9ca3af;font-size:11px\\'>暂无</span>"

        enhanced_dashboard = f"""<div style="font-family:system-ui,sans-serif">
        <!-- 大明风仪表盘 -->
        <div style="background:linear-gradient(135deg,#1a2d1a 0%,#1a1a2e 100%);border:1px solid #c9a96e;border-radius:12px;padding:14px;margin-bottom:12px;box-shadow:0 4px 16px rgba(201,169,110,0.1)">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                <div>
                    <span style="font-size:16px;font-weight:bold;color:#c9a96e">📊 总览仪表盘</span>
                    <span style="font-size:12px;color:#9ca3af;margin-left:12px">第 """ + str(year) + """ 年 \xb7 """ + str(month) + """月</span>
                </div>
                <div style="text-align:right">
                    <span style="font-size:20px;font-weight:bold;color:#f59e0b">""" + era_name + """</span>
                    <div style="font-size:11px;color:#9ca3af">""" + era_year + """</div>
                </div>
            </div>
            <div style="background:#0d1f0d;border-radius:8px;padding:10px;margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                    <span style="color:#9ca3af;font-size:11px">威权 <span style="color:""" + authority_color + """;font-weight:bold">""" + str(authority) + """</span></span>
                    <span style="color:#9ca3af;font-size:11px">藩镇 <span style="color:""" + fanzhen_color + """;font-weight:bold">""" + str(fanzhen) + """</span></span>
                    <span style="color:#9ca3af;font-size:11px">民心 <span style="color:""" + popularity_color + """;font-weight:bold">""" + str(popularity) + """</span></span>
                </div>
                <div style="background:#2d2d44;border-radius:4px;height:8px;margin-bottom:4px">
                    <div style="background:""" + auth_bar_color + """;border-radius:4px;height:8px;width:""" + str(authority) + """%;transition:width 0.5s"></div>
                </div>
                <div style="background:#2d2d44;border-radius:4px;height:8px">
                    <div style="background:""" + fanz_bar_color + """;border-radius:4px;height:8px;width:""" + str(fanzhen) + """%;transition:width 0.5s"></div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:10px">
                <div style="background:#1a3d1a;border-radius:6px;padding:8px 4px;text-align:center;border:1px solid #2d4a2d">
                    <div style="font-size:18px;font-weight:bold;color:#22c55e">""" + str(authority) + """</div>
                    <div style="font-size:10px;color:#9ca3af">威权</div>
                </div>
                <div style="background:#1a3d1a;border-radius:6px;padding:8px 4px;text-align:center;border:1px solid #2d4a2d">
                    <div style="font-size:18px;font-weight:bold;color:#ef4444">""" + str(fanzhen) + """</div>
                    <div style="font-size:10px;color:#9ca3af">藩镇</div>
                </div>
                <div style="background:#1a3d1a;border-radius:6px;padding:8px 4px;text-align:center;border:1px solid #2d4a2d">
                    <div style="font-size:18px;font-weight:bold;color:#3b82f6">""" + str(popularity) + """</div>
                    <div style="font-size:10px;color:#9ca3af">民心</div>
                </div>
                <div style="background:#1a3d1a;border-radius:6px;padding:8px 4px;text-align:center;border:1px solid #2d4a2d">
                    <div style="font-size:18px;font-weight:bold;color:#f59e0b">""" + str(treasury) + """</div>
                    <div style="font-size:10px;color:#9ca3af">汉室库</div>
                </div>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
                <span style="color:#9ca3af;font-size:11px">系统：</span>
                """ + faction_bar + """
                """ + event_badge + """
                """ + skill_badge + """
                """ + building_badge + """
                <span style="margin-left:4px;color:#9ca3af;font-size:11px">军力:<span style="color:#ef4444;font-weight:bold">""" + str(military) + """</span></span>
            </div>
        </div>
'''

enhanced_prefix_bytes = enhanced_prefix.encode('utf-8')
enhanced_return_start = enhanced_prefix_bytes + b'        <!-- 威权状态卡 -->' + old_return[marker_pos + len('        <!-- 威权状态卡 -->'.encode('utf-8')):]

content = content[:start] + enhanced_return_start + content[end:]

with open('web_app.py', 'wb') as f:
    f.write(content)
print("DONE")