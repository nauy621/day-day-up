import requests
import datetime
import json

# ======================
# 🔧 读取配置
# ======================
with open("config.json","r") as f:
    config = json.load(f)

TOKEN = config["pushplus_token"]

now = datetime.datetime.now()
hour = now.hour
weekday = now.weekday()

# ======================
# 🧠 内容生成系统
# ======================
def get_content(hour, weekday):

    # 🍳 早餐
    if 7 <= hour < 10:
        return """
🍳 早餐提醒

- 热干面 / 蒸饺
- 鸡蛋 1-2个
- 黑咖啡（饭后）
- 维生素

⚠️ 不要空腹咖啡（防发飘）
"""

    # 🍽 午餐
    if 11 <= hour < 13:
        return """
🍽 午餐

- 轻食 / 金枪鱼谷物碗 / 便当

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

- 背 / 腿 / 核心（周期训练）
- 最后一组力竭
- 不要每组爆

🔥 状态：执行中
"""

    # 🌙 恢复
    if 20 <= hour < 23:
        return """
💪 训练后恢复

- 肠粉
- 蛋白粉
- 肌酸

⚠️ 恢复 + 防掉肌肉
"""

    return None


content = get_content(hour, weekday)

# ======================
# 🚨 防空内容
# ======================
if not content:
    print("❌ NO CONTENT - NO PUSH")
    exit()

# ======================
# 🚀 PushPlus 推送
# ======================
url = "https://www.pushplus.plus/send"

print("🔥 START PUSH")
print("TOKEN:", TOKEN)
print("HOUR:", hour)

try:
    r = requests.get(url, params={
        "token": TOKEN,
        "title": "🔥 V10.2 健身提醒系统",
        "content": content
    })

    print("STATUS:", r.status_code)
    print("RESPONSE:", r.text)

except Exception as e:
    print("❌ ERROR:", str(e))
