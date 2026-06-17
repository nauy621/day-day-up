import datetime
import requests
import json
from logic import *

# ======================
# 读取配置
# ======================
with open("config.json","r") as f:
    config = json.load(f)

TOKEN = config["pushplus_token"]

# ======================
# 读取状态
# ======================
state = load_state()

last = state["last_intensity"]

# 🧠 AI决策
today_intensity = get_today_intensity(last)
training = get_training(today_intensity)
diet = get_diet(today_intensity)

# ======================
# 📲 时间系统
# ======================
hour = datetime.datetime.now().hour

def build_msg():

    if 7 <= hour < 10:
        return f"""
🍳 早餐提醒

{diet}

⚠️ 不要空腹咖啡
"""

    if 11 <= hour < 13:
        return """
🍽 午餐

轻食 / 便当 / 金枪鱼谷物碗
"""

    if 15 <= hour < 16:
        return """
⚠️ 防发飘加餐

鸡蛋 / 面包 / 香蕉
"""

    if 17 <= hour < 20:
        return f"""
🏋️ 今日训练（{today_intensity}强度）

{training}

执行原则：
- 接近力竭
- 不要每组爆
"""

    if 20 <= hour < 23:
        return """
💪 训练后恢复

肠粉 / 蛋白粉 / 肌酸
"""

    return None

msg = build_msg()

if not msg:
    exit()

# ======================
# 🚀 推送
# ======================
def push(content):

    url = "https://www.pushplus.plus/send"

    r = requests.get(url, params={
    "token": TOKEN,
    "title": "🔥 V10.1 AI健身系统",
    "content": content
})

    print("STATUS:", r.status_code)
    print("RESPONSE:", r.text)

    print(r.text)

push(msg)

# ======================
# 🧠 更新状态（关键🔥）
# ======================
state["last_intensity"] = today_intensity
save_state(state)
