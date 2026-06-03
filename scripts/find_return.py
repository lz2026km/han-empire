with open('/home/admin/.openclaw/workspace/han-empire/web_app.py', 'rb') as f:
    content = f.read()

lines = content.split(b'\n')
start = sum(len(lines[i]) + 1 for i in range(242))
end = sum(len(lines[i]) + 1 for i in range(311))

old_block = content[start:end]
print("Old block length:", len(old_block))
print("First 80 chars:", old_block[:80])
print("Last 80 chars:", old_block[-80:])
stripped = old_block.strip()
ends_check = stripped.endswith(b'"""')
print("Ends with closing triple quote:", ends_check)

marker1 = 'return f"""<div style="font-family:system-ui,sans-serif">'.encode('utf-8')
marker2 = '<!-- 威权状态卡 -->'.encode('utf-8')
if marker1 in old_block and marker2 in old_block:
    print("CONFIRMED: this is the dashboard return block")
else:
    print("NOT the expected block")
    print("Has marker1:", marker1 in old_block)
    print("Has marker2:", marker2 in old_block)