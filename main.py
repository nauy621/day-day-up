import datetime
import json
import os
import sys
import time
from pathlib import Path

import requests


SHANGHAI_TZ = datetime.timezone(
    datetime.timedelta(hours=8),
    "Asia/Shanghai"
)

STATE_FILE = Path("state.json")

EARLY_WINDOW_MINUTES = 60
LATE_WINDOW_MINUTES = 60

PUSHPLUS_TITLE = "每日健身提醒"


REMINDERS = [
    {
        "key": "breakfast",
        "time": "08:30",
        "name": "早餐提醒",
        "content": """🌅 早餐

🥟 巴比菜包 2个

搭配二选一：
🥚 鸡蛋 2个
或
🥛 无糖豆浆 1杯（约300～400ml）

如果比较饿：
🥟 巴比菜包可以吃3个
""",
    },

    {
        "key": "lunch",
        "time": "12:00",
        "name": "午餐提醒",
        "content": """🍽 午餐

🥗 超级碗瓦坎达轻食
""",
    },

    {
        "key": "workout",
        "time": "18:00",
        "name": "训练提醒",
        "content": "",
    },

    {
        "key": "recovery",
        "time": "21:00",
        "name": "晚餐 / 恢复提醒",
        "content": """🌙 晚餐 / 恢复

🍚 米饭 1碗左右
🥩 鸡肉 / 牛肉 / 鱼 / 瘦肉
🥬 蔬菜一份

🥤 BD酵母蛋白粉 30g
💪 肌酸 1勺

💊 京东京造2倍鱼油 1粒
💊 综合维生素 1片
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


def get_workout_content(weekday):
    plans = {
        0: """🏋️ 周一｜胸 + 三头

1. 卧推 4组 × 6～10次
2. 夹胸器械 3组 × 10～15次
3. 哑铃飞鸟 3组 × 10～15次
4. 三头下压 3组 × 10～15次
""",

        1: """🏋️ 周二｜背 + 二头

1. 高位下拉 4组 × 8～12次
2. 坐姿划船 4组 × 8～12次
3. 单臂哑铃划船 3组 × 10～12次
4. 二头弯举 3组 × 10～15次
""",

        2: """🏋️ 周三｜肩 + 腹

1. 哑铃 / 器械肩推 4组 × 8～12次
2. 侧平举 4组 × 12～20次
3. 反向飞鸟 3组 × 12～15次
4. 卷腹 4组
""",

        3: """🏋️ 周四｜胸 + 背

1. 卧推 / 器械推胸 3组 × 8～12次
2. 高位下拉 3组 × 8～12次
3. 夹胸器械 3组 × 10～15次
4. 坐姿划船 3组 × 8～12次
""",

        4: """💪 周五｜肩 + 手臂 + 腹

1. 侧平举 4组 × 12～20次
2. 二头弯举 3组 × 10～15次
3. 三头下压 3组 × 10～15次
4. 锤式弯举 3组 × 10～15次
5. 卷腹 3～4组
""",

        5: """🚲 周六｜自由活动

想去东湖：
🚲 自行车轻松骑约1小时

不去就正常休息
""",

        6: """😴 周日｜休息

💪 肌酸照常
""",
    }

    return plans[weekday]


def parse_shanghai_time(value):
    value = value.strip()

    for fmt in (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.datetime.strptime(
                value,
                fmt
            ).replace(tzinfo=SHANGHAI_TZ)

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

    return datetime.datetime.now(
        datetime.timezone.utc
    ).astimezone(SHANGHAI_TZ)


def minutes_since_midnight(value):
    return value.hour * 60 + value.minute


def target_minutes(reminder):
    hour, minute = reminder["time"].split(":")
    return int(hour) * 60 + int(minute)


def target_datetime(reminder, now):
    hour, minute = reminder["time"].split(":")

    return now.replace(
        hour=int(hour),
        minute=int(minute),
        second=0,
        microsecond=0,
    )


def seconds_from_target(reminder, now):
    return int(
        (
            now - target_datetime(reminder, now)
        ).total_seconds()
    )


def is_in_schedule_window(reminder, now):
    delta = seconds_from_target(reminder, now)

    return (
        -EARLY_WINDOW_MINUTES * 60
        <= delta
        <= LATE_WINDOW_MINUTES * 60
    )


def is_send_time(reminder, now):
    return (
        is_in_schedule_window(reminder, now)
        and seconds_from_target(reminder, now) >= 0
    )


def seconds_until_target(reminder, now):
    return max(
        0,
        int(
            (
                target_datetime(reminder, now) - now
            ).total_seconds()
        ),
    )


def select_scheduled_reminder(now):
    for reminder in REMINDERS:
        if is_in_schedule_window(reminder, now):
            return reminder

    return None


def find_due_reminder(now):
    for reminder in REMINDERS:
        if is_send_time(reminder, now):
            return reminder

    return None


def get_manual_reminder(choice):
    choice = (choice or "test").strip()

    if choice in (
        "",
        "test",
        "manual-test",
    ):
        return MANUAL_TEST_REMINDER

    for reminder in REMINDERS:
        if reminder["key"] == choice:

            manual_reminder = dict(reminder)

            manual_reminder["manual"] = True

            manual_reminder["key"] = (
                f"manual-{reminder['key']}"
            )

            return manual_reminder

    valid = ", ".join(
        ["test"]
        + [
            reminder["key"]
            for reminder in REMINDERS
        ]
    )

    raise ValueError(
        f"Unknown manual reminder '{choice}'. "
        f"Valid choices: {valid}"
    )


def should_persist_state(reminder):
    return not reminder.get("manual", False)


def load_state(path=STATE_FILE):
    if not path.exists():
        return {"sent": {}}

    try:
        with path.open(
            "r",
            encoding="utf-8"
        ) as f:
            state = json.load(f)

    except (
        json.JSONDecodeError,
        OSError,
    ) as exc:

        print(
            f"⚠️ Failed to read {path}: "
            f"{exc}; starting with empty state"
        )

        return {"sent": {}}

    if not isinstance(state, dict):
        return {"sent": {}}

    if not isinstance(
        state.get("sent"),
        dict
    ):
        state["sent"] = {}

    return state


def save_state(
    state,
    path=STATE_FILE
):
    with path.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2,
        )

        f.write("\n")


def state_day(now):
    return now.strftime("%Y-%m-%d")


def was_sent_today(
    state,
    reminder,
    now
):
    if not should_persist_state(reminder):
        return False

    return (
        reminder["key"]
        in state.get(
            "sent",
            {}
        ).get(
            state_day(now),
            {}
        )
    )


def mark_sent(
    state,
    reminder,
    now
):
    day = state_day(now)

    state.setdefault(
        "sent",
        {}
    ).setdefault(
        day,
        {}
    )[reminder["key"]] = {
        "name": reminder["name"],
        "scheduled_time": reminder["time"],
        "sent_at": now.isoformat(
            timespec="seconds"
        ),
    }


def get_token():
    token = os.getenv(
        "PUSHPLUS_TOKEN"
    )

    if token:
        return token

    try:
        with open(
            "config.json",
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f).get(
                "pushplus_token"
            )

    except FileNotFoundError:
        return None


def select_reminder(now):
    event_name = os.getenv(
        "GITHUB_EVENT_NAME",
        "",
    )

    manual_choice = os.getenv(
        "MANUAL_REMINDER",
        "",
    )

    if (
        event_name == "workflow_dispatch"
        or manual_choice
    ):
        return get_manual_reminder(
            manual_choice
        )

    return select_scheduled_reminder(now)


def send_pushplus(
    token,
    reminder
):
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

    reminder = select_reminder(now)

    # 18:00训练提醒：
    # 根据当天星期自动选择训练内容
    if (
        reminder
        and reminder["key"]
        in (
            "workout",
            "manual-workout",
        )
    ):
        reminder = dict(reminder)

        reminder["content"] = (
            get_workout_content(
                now.weekday()
            )
        )

    print(
        "Shanghai time:",
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )

    print(
        "Event:",
        os.getenv(
            "GITHUB_EVENT_NAME",
            "<local>"
        ),
    )

    print(
        "Manual reminder:",
        os.getenv(
            "MANUAL_REMINDER",
            "<none>"
        ) or "<none>",
    )

    if not reminder:

        print(
            "⏭️ No reminder due within "
            f"-{EARLY_WINDOW_MINUTES}/"
            f"+{LATE_WINDOW_MINUTES} "
            "minutes; skipping."
        )

        return

    print(
        f"Reminder: "
        f"{reminder['name']} "
        f"({reminder['time']})"
    )

    if should_persist_state(reminder):

        wait_seconds = (
            seconds_until_target(
                reminder,
                now
            )
        )

        if wait_seconds > 0:

            target = target_datetime(
                reminder,
                now
            )

            print(
                "Waiting until target time:",
                target.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                f"({wait_seconds}s)",
            )

            time.sleep(wait_seconds)

            now = get_now()

            print(
                "Shanghai time after wait:",
                now.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )

    state = load_state()

    if was_sent_today(
        state,
        reminder,
        now
    ):
        print(
            f"⏭️ {reminder['name']} "
            "already sent today; "
            "skipping duplicate."
        )

        return

    token = get_token()

    if not token:
        print(
            "❌ Missing PUSHPLUS_TOKEN"
        )

        sys.exit(1)

    response = send_pushplus(
        token,
        reminder
    )

    print(
        "STATUS:",
        response.status_code
    )

    print(
        "RESPONSE:",
        response.text
    )

    response.raise_for_status()

    try:
        data = response.json()

    except ValueError:
        data = {}

    if data.get("code") not in (
        200,
        "200",
        None,
    ):
        print(
            "❌ PushPlus returned an error"
        )

        sys.exit(1)

    if should_persist_state(reminder):

        mark_sent(
            state,
            reminder,
            now
        )

        save_state(state)

        print(
            "State updated:",
            STATE_FILE
        )

    else:
        print(
            "Manual reminder sent; "
            "state not updated."
        )


if __name__ == "__main__":
    main()
