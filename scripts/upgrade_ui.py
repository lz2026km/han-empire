with open('web_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

search = '        return f"""<div style="font-family:system-ui,sans-serif">\n        <!-- 威权状态卡 -->'
idx = content.find(search)
if idx == -1:
    print("❌ Not found")
    exit(1)

# Build the replacement - inject enhanced dashboard before the existing card
# Then keep the rest of the original return block

# We need to inject after the first line of return but before <!-- 威权状态卡 -->
# The enhanced dashboard will go BEFORE <!-- 威权状态卡 -->

authority_color = '"{authority_color}"'  # placeholder
fanzhen_color = '"{fanzhen_color}"'
popularity_color = '"{popularity_color}"'
auth_bar_color = '"{auth_bar_color}"'
fanz_bar_color = '"{fanz_bar_color}"'

replacement = '''        # UI升级大明风仪表盘前缀
        faction_data = s.metrics.get('faction_influence', {})
        faction_colors = {"忠汉派": "#22c55e", "务实派": "#3b82f6", "离心派": "#f59e0b", "叛逆派": "#ef4444"}
        faction_bar = "".join([
            f"<span style=\\'background:{faction_colors.get(k,\'#9ca3af\')};color:white;padding:2px 6px;border-radius:4px;margin-right:4px;font-size:10px\\'>{k}:{v}</span>"
            for k, v in faction_data.items()
        ]) if faction_data else "<span style=\\'color:#9ca3af;font-size:11px\\'>尚未分化</span>"
        triggered = s.metrics.get('triggered_events', [])
        event_badge = f"<span style=\\'background:#ef4444;color:white;padding:2px 6px;border-radius:10px;font-size:10px\\'>{len(triggered)}事件</span>" if triggered else "<span style=\\'color:#9ca3af;font-size:11px\\'>暂无</span>"
        activated = s.metrics.get('activated_skills', [])
        skill_badge = f"<span style=\\'background:#c9a96e;color:#1a1a2e;padding:2px 6px;border-radius:10px;font-size:10px\\'>{len(activated)}技</span>" if activated else "<span style=\\'color:#9ca3af;font-size:11px\\'>暂无</span>"
        built = s.metrics.get('buildings', {})
        built_count = len(built)
        building_badge = f"<span style=\\'background:#22c55e;color:#1a1a2e;padding:2px 6px;border-radius:10px;font-size:10px\\'>{built_count}建筑</span>" if built_count else "<span style=\\'color:#9ca3af;font-size:11px\\'>暂无</span>"

        authority_color = "#22c55e" if authority >= 60 else "#f59e0b" if authority >= 30 else "#ef4444"
        popularity_color = "#22c55e" if popularity >= 60 else "#f59e0b" if popularity >= 30 else "#ef4444"
        fanzhen_color = "#22c55e" if fanzhen <= 30 else "#f59e0b" if fanzhen <= 60 else "#ef4444"
        auth_bar_color = "#22c55e" if authority >= 60 else "#f59e0b" if authority >= 30 else "#ef4444"
        fanz_bar_color = "#22c55e" if fanzhen <= 30 else "#f59e0b" if fanzhen <= 60 else "#ef4444"

        enhanced_dashboard = f"""<div style="font-family:system-ui,sans-serif">
        <!-- 大明风仪表盘 -->
        <div style="background:linear-gradient(135deg,#1a2d1a 0%,#1a1a2e 100%);border:1px solid #c9a96e;border-radius:12px;padding:14px;margin-bottom:12px;box-shadow:0 4px 16px rgba(201,169,110,0.1)">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                <div>
                    <span style="font-size:16px;font-weight:bold;color:#c9a96e">📊 总览仪表盘</span>
                    <span style="font-size:12px;color:#9ca3af;margin-left:12px">第 {year} 年 · {month}月</span>
                </div>
                <div style="text-align:right">
                    <span style="font-size:20px;font-weight:bold;color:#f59e0b">{era_name}</span>
                    <div style="font-size:11px;color:#9ca3af">{era_year}</div>
                </div>
            </div>
            <div style="background:#0d1f0d;border-radius:8px;padding:10px;margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                    <span style="color:#9ca3af;font-size:11px">威权 <span style="color:{authority_color};font-weight:bold">{authority}</span></span>
                    <span style="color:#9ca3af;font-size:11px">藩镇 <span style="color:{fanzhen_color};font-weight:bold">{fanzhen}</span></span>
                    <span style="color:#9ca3af;font-size:11px">民心 <span style="color:{popularity_color};font-weight:bold">{popularity}</span></span>
                </div>
                <div style="background:#2d2d44;border-radius:4px;height:8px;margin-bottom:4px">
                    <div style="background:{auth_bar_color};border-radius:4px;height:8px;width:{authority}%;transition:width 0.5s"></div>
                </div>
                <div style="background:#2d2d44;border-radius:4px;height:8px">
                    <div style="background:{fanz_bar_color};border-radius:4px;height:8px;width:{fanzhen}%;transition:width 0.5s"></div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:10px">
                <div style="background:#1a3d1a;border-radius:6px;padding:8px 4px;text-align:center;border:1px solid #2d4a2d">
                    <div style="font-size:18px;font-weight:bold;color:#22c55e">{authority}</div>
                    <div style="font-size:10px;color:#9ca3af">威权</div>
                </div>
                <div style="background:#1a3d1a;border-radius:6px;padding:8px 4px;text-align:center;border:1px solid #2d4a2d">
                    <div style="font-size:18px;font-weight:bold;color:#ef4444">{fanzhen}</div>
                    <div style="font-size:10px;color:#9ca3af">藩镇</div>
                </div>
                <div style="background:#1a3d1a;border-radius:6px;padding:8px 4px;text-align:center;border:1px solid #2d4a2d">
                    <div style="font-size:18px;font-weight:bold;color:#3b82f6">{popularity}</div>
                    <div style="font-size:10px;color:#9ca3af">民心</div>
                </div>
                <div style="background:#1a3d1a;border-radius:6px;padding:8px 4px;text-align:center;border:1px solid #2d4a2d">
                    <div style="font-size:18px;font-weight:bold;color:#f59e0b">{treasury}</div>
                    <div style="font-size:10px;color:#9ca3af">汉室库</div>
                </div>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
                <span style="color:#9ca3af;font-size:11px">系统：</span>
                {faction_bar}
                {event_badge}
                {skill_badge}
                {building_badge}
                <span style="margin-left:4px;color:#9ca3af;font-size:11px">军力:<span style="color:#ef4444;font-weight:bold">{military}</span></span>
            </div>
        </div>
        <!-- 威权状态卡 -->
        <div style="background:{auth_bg};border:1px solid {auth_color};border-radius:8px;padding:10px;margin-bottom:10px;text-align:center">
            <div style="font-size:11px;color:#9ca3af">当前威权</div>
            <div style="font-size:28px;font-weight:bold;color:{auth_color}">{authority}</div>
            <div style="font-size:12px;color:{auth_color};font-weight:bold">{auth_level.label}</div>
            <div style="font-size:11px;color:#9ca3af;margin-top:4px">诏书效果：{auth_level.decree_mult:.0%} · 召对效果：{auth_level.summon_mult:.0%}</div>
        </div>'''

        return enhanced_dashboard
'''

# Replace the return block
content = content[:idx] + replacement + content[idx + len(search):]

with open('web_app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Replaced return block")