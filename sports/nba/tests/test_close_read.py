"""Closing read (Matt 2026-11-12): one late read for games holding a Record pick, kept apart from data/odds."""
import json
import os
import sys
import tempfile
import unittest
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import common  # noqa: E402
import odds  # noqa: E402


class Pool:
    fixture = False

    def __init__(self, left):
        self.left, self.saved = left, 0

    def total_left(self):
        return self.left

    def save(self):
        self.saved += 1


class Client:
    def __init__(self):
        self.calls = []

    def event_odds(self, ev, away, home, slate, read, gid, links=True):
        self.calls.append((ev, read, links))
        return {"bookmakers": []}, 4


class CloseRead(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = {k: os.environ.get(k) for k in ("PC_DATA_DIR", "PC_NOW")}
        os.environ["PC_DATA_DIR"] = self.tmp.name
        os.makedirs(os.path.join(self.tmp.name, "record"))
        self.cfg = json.load(open(os.path.join(ROOT, "config", "rules.json"), encoding="utf-8"))
        self.now = common.parse_iso("2026-11-12T18:50:00-05:00")
        self.slate = "2026-11-12"
        self.games = [{"id": "1", "away": "AAA", "home": "BBB", "start": common.iso(self.now + timedelta(minutes=10))},
                      {"id": "2", "away": "CCC", "home": "DDD", "start": common.iso(self.now + timedelta(minutes=10))},
                      {"id": "3", "away": "EEE", "home": "FFF", "start": common.iso(self.now + timedelta(minutes=40))}]
        self.day = {"events": {"1": "ev1", "2": "ev2", "3": "ev3"}}
        self.plan = {"reads": ["A", "B", "C", "D"], "spare": ["A"]}
        with open(os.path.join(self.tmp.name, "record", "events.jsonl"), "w", encoding="utf-8") as f:
            for gid in ("1", "3"):
                f.write('{"at":"x","id":"%s:%s:99:points:10.5:under","price":-110,"t":"shown"}\n' % (self.slate, gid))
            f.write('{"at":"x","id":"2026-11-11:2:99:points:10.5:under","price":-110,"t":"shown"}\n')

    def tearDown(self):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def run_it(self, pool, client, started=None, now=None):
        return odds.close_reads(now or self.now, self.slate, self.games, 100, self.cfg, lambda g: None, started or {},
                                self.day, self.plan, pool, client)

    def test_config_is_on_and_late(self):
        c = self.cfg["reads"]["close"]
        self.assertTrue(c["active"])
        self.assertLess(c["min"], self.cfg["reads"]["d_min"])

    def test_only_pick_games_inside_the_window_and_only_once(self):
        pool, client = Pool(5000), Client()
        self.assertEqual(self.run_it(pool, client), 1)                 # game 1: pick + 10 min. 2: no pick. 3: too early
        self.assertEqual(client.calls, [("ev1", "E", False)])
        doc = json.load(open(odds.close_path(self.slate)))
        self.assertEqual([(f["game_id"], f["read"]) for f in doc["fetches"]], [("1", "E")])
        self.assertFalse(os.path.exists(odds.odds_path(self.slate)))   # the engine's file is untouched
        self.assertEqual(self.run_it(pool, client), 0)                 # never twice
        self.assertEqual(len(client.calls), 1)

    def test_not_after_tip_or_too_late(self):
        client = Client()
        self.assertEqual(self.run_it(Pool(5000), client, started={"1": True}), 0)
        self.assertEqual(self.run_it(Pool(5000), client, now=self.now + timedelta(minutes=9)), 0)
        self.assertEqual(client.calls, [])

    def test_never_spends_what_planned_reads_need(self):
        client = Client()
        self.assertEqual(self.run_it(Pool(1000), client), 0)           # 3 planned reads x 4 credits x 100 games = 1200
        self.assertEqual(client.calls, [])

    def test_off_switch_and_fixture_runs(self):
        self.cfg["reads"]["close"]["active"] = False
        self.assertEqual(self.run_it(Pool(5000), Client()), 0)
        self.cfg["reads"]["close"]["active"] = True
        p = Pool(5000)
        p.fixture = True
        os.environ.pop("PC_CLOSE_TEST", None)
        self.assertEqual(self.run_it(p, Client()), 0)


class FasterChecks(unittest.TestCase):
    """reads.extra (Matt 2026-11-12): checks at 75, 60 and 30 minutes too, so the last 90 minutes are checked every 15."""

    def setUp(self):
        self.cfg = json.load(open(os.path.join(ROOT, "config", "rules.json"), encoding="utf-8"))
        self.tip = common.parse_iso("2026-11-12T19:00:00-05:00")
        self.g = {"id": "1", "away": "AAA", "home": "BBB", "start": common.iso(self.tip)}

    def test_config(self):
        self.assertEqual(odds.extra_reads(self.cfg), {"X75": 75, "X60": 60, "X30": 30})
        self.assertEqual(odds.all_reads(self.cfg), ("A", "B", "C", "D", "X75", "X60", "X30"))
        self.assertEqual(self.cfg["pin_solo"]["flag_reads"], ["B", "X75", "X60", "C", "X30", "D"])

    def test_due_times_and_order(self):
        dt = odds.due_times(self.g, [self.g], self.cfg)
        mins = {k: int((self.tip - v).total_seconds() / 60) for k, v in dt.items() if k != "A"}
        self.assertEqual(mins, {"B": 90, "X75": 75, "X60": 60, "C": 45, "X30": 30, "D": 20})

    def test_each_check_is_due_in_turn(self):
        reads = set(odds.all_reads(self.cfg))
        done = {"1": []}
        seen = []
        for m in (90, 75, 60, 45, 30, 20):
            now = self.tip - timedelta(minutes=m)
            due = odds.due_reads(now, [self.g], reads, done, {}, self.cfg)
            self.assertEqual(len(due), 1, m)
            seen.append(due[0]["read"])
            done["1"].append({"read": due[0]["read"], "at": now, "returned": True})
            self.assertEqual(odds.due_reads(now + timedelta(minutes=5), [self.g], reads, done, {}, self.cfg), [])
        self.assertEqual(seen, ["B", "X75", "X60", "C", "X30", "D"])

    def test_plan_lists_them_and_they_never_count_as_planned(self):
        plan = odds.make_plan(5000, 100, 8, self.cfg)
        self.assertEqual(plan["extra"], ["X30", "X60", "X75"])
        for k in plan["extra"]:
            self.assertNotIn(k, plan["reads"])               # beside the plan, never inside it
        base = len([r for r in plan["reads"] if r not in plan["spare"]])
        self.assertIn(base, (3, 4))                          # the fixed reads only, never the extra ones
        need = base * 4 * 100                                # what the planned reads of 100 games cost
        self.assertTrue(odds.spare_ok(need + 4, 100, plan, 4))
        self.assertFalse(odds.spare_ok(need + 3, 100, plan, 4))

    def test_off_switch(self):
        self.cfg["reads"]["extra"]["active"] = False
        self.assertEqual(odds.extra_reads(self.cfg), {})
        self.assertEqual(odds.all_reads(self.cfg), ("A", "B", "C", "D"))

    def test_window_labels(self):
        import engine
        self.assertEqual(engine.window_label("B", "X75"), "90 → 75 min")
        self.assertEqual(engine.window_label("X30", "D"), "30 → 20 min")
        self.assertEqual(engine.window_label("A", "B"), "11 AM → 90 min")
        self.assertEqual(engine.window_label("B", "C"), "90 → 45 min")


if __name__ == "__main__":
    unittest.main()
