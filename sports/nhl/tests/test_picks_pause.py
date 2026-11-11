"""Matt's dated picks pause (ops.picks_pause, 2026-11-09): no NEW picks from `from` until `until`; grading and the rest keep running."""
import json
import os
import unittest

import helpers
import engine


def cfg_with(start, until):
    c = helpers.cfg()
    c.setdefault("ops", {})["picks_pause"] = {"from": start, "until": until, "text": "Paused.", "sub": "Back Monday."}
    return c


class PicksPause(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("PC_NOW")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("PC_NOW", None)
        else:
            os.environ["PC_NOW"] = self._old

    def at(self, iso):
        os.environ["PC_NOW"] = iso

    def test_paused_inside_the_window(self):
        self.at("2026-11-10T10:00:00-05:00")
        self.assertEqual(engine.picks_pause(cfg_with("2026-11-09", "2026-11-16")),
                         {"text": "Paused.", "sub": "Back Monday."})

    def test_first_and_last_paused_day(self):
        cfg = cfg_with("2026-11-09", "2026-11-16")
        self.at("2026-11-09T08:00:00-05:00")
        self.assertIsNotNone(engine.picks_pause(cfg))
        self.at("2026-11-15T23:59:00-05:00")
        self.assertIsNotNone(engine.picks_pause(cfg))

    def test_resumes_on_until_date(self):
        self.at("2026-11-16T08:00:00-05:00")
        self.assertIsNone(engine.picks_pause(cfg_with("2026-11-09", "2026-11-16")))

    def test_historical_slates_are_not_paused(self):
        self.at("2026-10-20T10:00:00-05:00")
        self.assertIsNone(engine.picks_pause(cfg_with("2026-11-09", "2026-11-16")))

    def test_no_block_without_config(self):
        self.at("2026-11-10T10:00:00-05:00")
        cfg = helpers.cfg()
        cfg["ops"].pop("picks_pause", None)
        self.assertIsNone(engine.picks_pause(cfg))

    def test_safety_pause_reports_the_pause_first(self):
        self.at("2026-11-10T10:00:00-05:00")
        self.assertEqual(engine.safety_pause([], cfg_with("2026-11-09", "2026-11-16"))["text"], "Paused.")



if __name__ == "__main__":
    unittest.main()
