"""游戏常量。L0。"""

TURN_UNIT = "月"
TURN_LABEL = TURN_UNIT

# 游戏结局
VICTORY_TOTAL_RESTORATION = "total_restoration"   # 兴复汉室，还于旧都
VICTORY_PARTITION = "partition"                     # 三分天下
VICTORY_ABDICATION = "abdication"                  # 禅让
VICTORY_DOWNFALL = "downfall"                      # 汉室覆灭

# 事件类型
EVENT_SITUATION = "situation"   # 转 issue
EVENT_NODE = "node"             # 只播报
EVENT_ENDING = "ending"         # 结局判定

# 回合阶段
PHASE_SUMMONING = "summoning"   # 召见
PHASE_REVIEWING = "reviewing"    # 推演
PHASE_ISSUED = "issued"          # 已拟旨

# 藩镇威胁等级
WARLORD_THREAT_LOW = 30
WARLORD_THREAT_MED = 60
WARLORD_THREAT_HIGH = 80