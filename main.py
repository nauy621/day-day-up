import requests
import datetime
import json

# ======================
# 🧪 测试模式（关键）
# True = 强制跑12:00内容
# False = 正常运行
# ======================
TEST_MODE = True

# ======================
# 上海时间
# ======================
now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)

hour = now.hour
weekday = now.weekday()

# ======================
# 🧠 强制测试逻辑
# ======================
if TEST_MODE:
    print("🧪 TEST MODE ON → 强制模拟12:00")
    hour = 12

# ======================
# PushPlus配置
# ======================
with open("config.json","r") as f:
    config = json.load(f)

TOKEN = config["pushplus_token"]

# ======================
# 内容系统
# ======================
def get_content(hour, weekday):

    # 🍳 早餐
    if 7 <= hour < 10:
        return """
🍳 早餐提醒

- 热干面 / 蒸饺
- 鸡蛋
- 黑咖啡

⚠️ 不要空腹咖啡
"""

    # 🍽 午餐
    if 11 <= hour < 13:
        return """
🍽 午餐时间（TEST触发）

- 金枪鱼谷物碗 / 轻食

⚠️ 保持蛋白摄入
"""

    # ⚡ 加餐
    if 15 <= hour < 16:
        return """
⚠️ 防发飘加餐

- 鸡蛋 / 面包 / 香蕉
"""

    # 🏋️ 训练
    if 17 <= hour < 20:
        return f"""
🏋️ 今日训练（周{weekday}）

- 背 / 腿 / 核心
- 最后一组力竭
"""

    # 🌙 恢复
    if 20 <= hour < 23:
        return """
💪 训练后恢复

- 肠粉
- 蛋白粉
- 肌酸
"""

    return None


content = get_content(hour, weekday)

if not content:
    print("❌ NO CONTENT")
    exit()

# ======================
# 🚀 推送
# ======================
url = "https://www.pushplus.plus/send"

r = requests.get(url, params={
    "token": TOKEN,
    "title": "🔥 V10 测试推送",
    "content": content
})

print("STATUS:", r.status_code)
print("RESPONSE:", r.text)
