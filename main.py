import datetime
import json
import os
import sys

import requests

# GitHub Actions cron uses UTC. Map each scheduled trigger to the intended
# reminder so delayed runs do not fall through to NO CONTENT.
SCHEDULE_CONTENT = {
    "30 0 * * *": """
🍳 早餐提醒

- 热干面 / 蒸饺
- 鸡蛋
- 黑咖啡

⚠️ 不要空腹咖啡
""",
    "0 4 * * *": """
🍽 午餐时间

- 金枪鱼谷物碗 / 轻食

⚠️ 保持蛋白摄入
""",
    "30 7 * * *": """
⚠️ 防发飘加餐

- 鸡蛋 / 面包 / 香蕉
""",
    "0 10 * * *": """
🏋️ 今日训练

- 背 / 腿 / 核心
- 最后一组力竭
""",
    "0 13 * * *": """
💪 训练后恢复

- 肠粉
- 蛋白粉
- 肌酸
""",
}


def get_token():
    token = os.getenv("PUSHPLUS_TOKEN")
    if token:
        return token

    # Local fallback only. In GitHub Actions, use repository Secrets instead of
    # committing config.json with a real token.
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f).get("pushplus_token")
    except FileNotFoundError:
        return None


def get_content(schedule, hour):
    if schedule in SCHEDULE_CONTENT:
        print(f"✅ Matched schedule: {schedule}")
        return SCHEDULE_CONTENT[schedule]

    # Manual workflow_dispatch test: choose content by current Shanghai hour.
    if 7 <= hour < 10:
        return SCHEDULE_CONTENT["30 0 * * *"]
    if 11 <= hour < 13:
        return SCHEDULE_CONTENT["0 4 * * *"]
    if 15 <= hour < 16:
        return SCHEDULE_CONTENT["30 7 * * *"]
    if 17 <= hour < 20:
        return SCHEDULE_CONTENT["0 10 * * *"]
    if 20 <= hour < 23:
        return SCHEDULE_CONTENT["0 13 * * *"]
    return """
🧪 手动测试推送

GitHub Actions 已成功运行，PushPlus 通知链路正常。
"""


def main():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    schedule = os.getenv("GITHUB_EVENT_SCHEDULE", "")
    token = get_token()

    print("Shanghai time:", now.strftime("%Y-%m-%d %H:%M:%S"))
    print("GITHUB_EVENT_SCHEDULE:", schedule or "<manual>")

    if not token:
        print("❌ Missing PUSHPLUS_TOKEN")
        sys.exit(1)

    content = get_content(schedule, now.hour)
    if not content:
        print("❌ NO CONTENT")
        sys.exit(1)

    response = requests.get(
        "https://www.pushplus.plus/send",
        params={
            "token": token,
            "title": "🔥 V10 健身提醒",
            "content": content,
        },
        timeout=15,
    )

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)
    response.raise_for_status()

    try:
        data = response.json()
    except ValueError:
        data = {}

    if data.get("code") not in (200, "200", None):
        print("❌ PushPlus returned an error")
        sys.exit(1)


if __name__ == "__main__":
    main()
