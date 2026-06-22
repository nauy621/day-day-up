import datetime
import json
import os
import sys
from pathlib import Path

import requests


SHANGHAI_TZ = datetime.timezone(datetime.timedelta(hours=8), "Asia/Shanghai")
STATE_FILE = Path("state.json")
WINDOW_MINUTES = 15
PUSHPLUS_TITLE = "每日健身提醒"

REMINDERS = [
    {
        "key": "breakfast",
        "time": "08:30",
        "name": "早餐提醒",
        "content": """🍳 早餐提醒

- 热干面 / 蒸饺
- 鸡蛋
- 黑咖啡

⚠️ 不要空腹咖啡
""",
    },
    {
        "key": "lunch",
        "time": "12:00",
        "name": "午餐提醒",
        "content": """🍽 午餐提醒

- 金枪鱼谷物碗 / 轻食

⚠️ 保持蛋白摄入
""",
    },
    {
        "key": "snack",
        "time": "15:30",
        "name": "加餐提醒",
        "content": """⚡ 加餐提醒

- 鸡蛋 / 面包 / 香蕉
""",
    },
    {
        "key": "workout",
        "time": "18:00",
        "name": "训练提醒",
        "content": """🏋️ 训练提醒

- 背 / 腿 / 核心
- 最后一组力竭
""",
    },
    {
        "key": "recovery",
        "time": "21:00",
        "name": "恢复提醒",
        "content": """💪 恢复提醒

- 肠粉
- 蛋白粉
- 肌酸
""",
    },
]

MANUAL_TEST_REMINDER = {
    "key": "manual-test",
    "time": "manual",
    "name": "手动测试推送",
    "content": """🧪 手动测试推送

GitHub Actions 已成功运行，PushPlus 通知链路正常。
""",
    "manual": True,
}


def parse_shanghai_time(value):
    value = value.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(value, fmt).replace(tzinfo=SHANGHAI_TZ)
        except ValueError:
            pass

    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=SHANGHAI_TZ)
    return parsed.astimezone(SHANGHAI_TZ)


def get_now():
    override = os.getenv("NOW_SHANGHAI")
    if override:
        return parse_shanghai_time(override)
    return datetime.datetime.now(datetime.timezone.utc).astimezone(SHANGHAI_TZ)


def minutes_since_midnight(value):
    return value.hour * 60 + value.minute


def target_minutes(reminder):
    hour, minute = reminder["time"].split(":")
    return int(hour) * 60 + int(minute)


def find_due_reminder(now):
    current = minutes_since_midnight(now)
    for reminder in REMINDERS:
        if abs(current - target_minutes(reminder)) <= WINDOW_MINUTES:
            return reminder
    return None


def get_manual_reminder(choice):
    choice = (choice or "test").strip()
    if choice in ("", "test", "manual-test"):
        return MANUAL_TEST_REMINDER

    for reminder in REMINDERS:
        if reminder["key"] == choice:
            manual_reminder = dict(reminder)
            manual_reminder["manual"] = True
            manual_reminder["key"] = f"manual-{reminder['key']}"
            return manual_reminder

    valid = ", ".join(["test"] + [reminder["key"] for reminder in REMINDERS])
    raise ValueError(f"Unknown manual reminder '{choice}'. Valid choices: {valid}")


def should_persist_state(reminder):
    return not reminder.get("manual", False)


def load_state(path=STATE_FILE):
    if not path.exists():
        return {"sent": {}}

    try:
        with path.open("r", encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"⚠️ Failed to read {path}: {exc}; starting with empty state")
        return {"sent": {}}

    if not isinstance(state, dict):
        return {"sent": {}}
    if not isinstance(state.get("sent"), dict):
        state["sent"] = {}
    return state


def save_state(state, path=STATE_FILE):
    with path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


def state_day(now):
    return now.strftime("%Y-%m-%d")


def was_sent_today(state, reminder, now):
    if not should_persist_state(reminder):
        return False
    return reminder["key"] in state.get("sent", {}).get(state_day(now), {})


def mark_sent(state, reminder, now):
    day = state_day(now)
    state.setdefault("sent", {}).setdefault(day, {})[reminder["key"]] = {
        "name": reminder["name"],
        "scheduled_time": reminder["time"],
        "sent_at": now.isoformat(timespec="seconds"),
    }


def get_token():
    token = os.getenv("PUSHPLUS_TOKEN")
    if token:
        return token

    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f).get("pushplus_token")
    except FileNotFoundError:
        return None


def select_reminder(now):
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    manual_choice = os.getenv("MANUAL_REMINDER", "")

    if event_name == "workflow_dispatch" or manual_choice:
        return get_manual_reminder(manual_choice)
    return find_due_reminder(now)


def send_pushplus(token, reminder):
    return requests.get(
        "https://www.pushplus.plus/send",
        params={
            "token": token,
            "title": PUSHPLUS_TITLE,
            "content": reminder["content"],
        },
        timeout=15,
    )


def main():
    now = get_now()
    state = load_state()
    reminder = select_reminder(now)

    print("Shanghai time:", now.strftime("%Y-%m-%d %H:%M:%S"))
    print("Event:", os.getenv("GITHUB_EVENT_NAME", "<local>"))
    print("Manual reminder:", os.getenv("MANUAL_REMINDER", "<none>") or "<none>")

    if not reminder:
        print(f"⏭️ No reminder due within ±{WINDOW_MINUTES} minutes; skipping.")
        return

    print(f"Reminder: {reminder['name']} ({reminder['time']})")

    if was_sent_today(state, reminder, now):
        print(f"⏭️ {reminder['name']} already sent today; skipping duplicate.")
        return

    token = get_token()
    if not token:
        print("❌ Missing PUSHPLUS_TOKEN")
        sys.exit(1)

    response = send_pushplus(token, reminder)
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

    if should_persist_state(reminder):
        mark_sent(state, reminder, now)
        save_state(state)
        print("State updated:", STATE_FILE)
    else:
        print("Manual reminder sent; state not updated.")


if __name__ == "__main__":
    main()
