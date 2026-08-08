import importlib.util
import pathlib
import sys
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "main.py"


def load_module():
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace(
            get=lambda *args, **kwargs: None
        )

    spec = importlib.util.spec_from_file_location(
        "reminder_main",
        MAIN_PATH
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


class ReminderTimingTests(unittest.TestCase):

    def setUp(self):
        self.module = load_module()

    def test_early_schedule_window_waits_until_target_time(self):
        now = self.module.parse_shanghai_time(
            "2026-06-22 20:24:00"
        )

        reminder = self.module.select_scheduled_reminder(now)

        self.assertEqual(
            reminder["key"],
            "recovery"
        )

        self.assertFalse(
            self.module.is_send_time(
                reminder,
                now
            )
        )

        self.assertEqual(
            self.module.seconds_until_target(
                reminder,
                now
            ),
            36 * 60
        )

    def test_late_schedule_window_sends_immediately(self):
        now = self.module.parse_shanghai_time(
            "2026-06-22 12:19:30"
        )

        reminder = self.module.select_scheduled_reminder(now)

        self.assertEqual(
            reminder["key"],
            "lunch"
        )

        self.assertTrue(
            self.module.is_send_time(
                reminder,
                now
            )
        )

        self.assertEqual(
            self.module.seconds_until_target(
                reminder,
                now
            ),
            0
        )

    def test_after_late_window_is_skipped(self):
        now = self.module.parse_shanghai_time(
            "2026-06-22 22:00:00"
        )

        self.assertEqual(
            self.module.select_scheduled_reminder(now)["key"],
            "recovery"
        )

        too_late = self.module.parse_shanghai_time(
            "2026-06-22 22:00:01"
        )

        self.assertIsNone(
            self.module.select_scheduled_reminder(
                too_late
            )
        )

    def test_due_reminder_only_matches_at_or_after_target(self):
        cases = [
            ("2026-06-22 08:30", "breakfast"),
            ("2026-06-22 09:30", "breakfast"),

            ("2026-06-22 12:00", "lunch"),
            ("2026-06-22 12:59", "lunch"),

            ("2026-06-22 18:00", "workout"),
            ("2026-06-22 19:00", "workout"),

            ("2026-06-22 21:00", "recovery"),
            ("2026-06-22 22:00", "recovery"),
        ]

        for timestamp, expected_key in cases:

            with self.subTest(
                timestamp=timestamp
            ):
                now = self.module.parse_shanghai_time(
                    timestamp
                )

                reminder = self.module.find_due_reminder(
                    now
                )

                self.assertIsNotNone(reminder)

                self.assertEqual(
                    reminder["key"],
                    expected_key
                )

    def test_removed_snack_times_have_no_due_reminder(self):
        cases = [
            "2026-06-22 15:30",
            "2026-06-22 16:30",
        ]

        for timestamp in cases:

            with self.subTest(
                timestamp=timestamp
            ):
                now = self.module.parse_shanghai_time(
                    timestamp
                )

                self.assertIsNone(
                    self.module.find_due_reminder(
                        now
                    )
                )

    def test_early_times_are_not_due_immediately(self):
        cases = [
            "2026-06-22 08:15",
            "2026-06-22 08:29",

            "2026-06-22 11:45",
            "2026-06-22 11:59",

            "2026-06-22 15:15",
            "2026-06-22 15:29",

            "2026-06-22 17:45",
            "2026-06-22 17:59",

            "2026-06-22 20:45",
            "2026-06-22 20:59",
        ]

        for timestamp in cases:

            with self.subTest(
                timestamp=timestamp
            ):
                now = self.module.parse_shanghai_time(
                    timestamp
                )

                self.assertIsNone(
                    self.module.find_due_reminder(
                        now
                    )
                )


if __name__ == "__main__":
    unittest.main()
