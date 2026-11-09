"""Matt 2026-11-09: a paused day makes no odds-feed call at all. Run: python -m unittest discover -s tests"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, HERE)

import common  # noqa: E402
import odds  # noqa: E402
from world import World  # noqa: E402


class TestOddsPause(unittest.TestCase):
    def setUp(self):
        self.old = common.http_get
        self.old_keys = os.environ.get("ODDS_API_KEYS")
        os.environ.pop("PC_ODDS_FIXTURE_DIR", None)
        os.environ["ODDS_API_KEYS"] = "key-aaaaaa1,key-bbbbbb2"
        self.tmp = World()
        os.environ["PC_DATA_DIR"] = self.tmp.data
        self.cfg = json.load(open(os.path.join(ROOT, "config", "rules.json")))
        self.calls = []

        def fake(url, **kw):
            self.calls.append(url)
            raise AssertionError("odds feed called on a paused day")
        common.http_get = fake

    def tearDown(self):
        common.http_get = self.old
        if self.old_keys is None:
            os.environ.pop("ODDS_API_KEYS", None)
        else:
            os.environ["ODDS_API_KEYS"] = self.old_keys
        os.environ.pop("PC_DATA_DIR", None)
        self.tmp.close()

    def test_paused_day_makes_no_call(self):
        self.cfg["ops"]["paused"] = {"from": "2026-10-24", "until": "2026-10-26", "back": "Tue Oct 27"}
        now = common.parse_iso("2026-10-25T11:00:00-04:00")
        games = [{"id": "1", "away": "LAL", "home": "UTAH", "start": "2026-10-25T19:30:00-04:00"}]
        res = odds.run_reads(now, "2026-10-25", games, 100, self.cfg, lambda g: (lambda n: None), {"1": False},
                             lambda n: None)
        self.assertEqual(self.calls, [])
        self.assertTrue(res["paused"])
        self.assertEqual(res["status"], "skipped")
        self.assertIsNone(res["next_read_at"])

    def test_window_edges(self):
        self.cfg["ops"]["paused"] = {"from": "2026-11-09", "until": "2026-11-15", "back": "Mon Nov 16"}
        self.assertIsNone(odds.paused(self.cfg, "2026-11-08"))
        self.assertTrue(odds.paused(self.cfg, "2026-11-09"))
        self.assertTrue(odds.paused(self.cfg, "2026-11-15"))
        self.assertIsNone(odds.paused(self.cfg, "2026-11-16"))
        self.cfg["ops"]["paused"] = None
        self.assertIsNone(odds.paused(self.cfg, "2026-11-10"))


if __name__ == "__main__":
    unittest.main()
