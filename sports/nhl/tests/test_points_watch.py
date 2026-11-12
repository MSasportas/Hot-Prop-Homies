"""2026-10-28 (Matt): player points "behind the scenes", replacing the goalie saves track. The points watch track runs the exact
Gap + Guard maths of shots on Hard Rock's points lines into data/paper_watch/points/ (page: Behind the scenes tab). It is never
a pick, never in the Record, never in Discord, and the live shots research log never sees it. Offline: the made-up league (Sim)."""
import json
import os
import unittest

import helpers  # noqa: F401  (puts scripts/ on sys.path)
import common
import odds
import world
from helpers import Sim, BOOKS

POINTS = {"id": "points", "market": "points", "label": "Points", "from_slate": "2026-10-01", "lines": "any",
          "offsets": {"*": 0.0}}


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.s = Sim(pool=400)
        c = json.load(open(os.environ["PC_CONFIG"]))
        c["ops"]["gap_guard"]["watch"] = [dict(POINTS)]
        json.dump(c, open(os.environ["PC_CONFIG"], "w"))
        self.s.at("09:00")
        self.s.read("13:02")
        self.s.clock("17:00")
        self.wdir = os.path.join(os.environ["PC_DATA_DIR"], "paper_watch", "points")

    def tearDown(self):
        self.s.close()

    def points_lines(self, i=1, line=0.5, ev=0.06):
        """(Hard Rock points line, {book: line}): the books agree on a fair chance F near the model's; Hard Rock pays +ev on the
        UNDER (a made-up skater's 0.5-point over would price near +145, outside the -200..+120 window, as real ones often do)."""
        raw = self.s.model_over("CAR", i, "points", line)
        F = min(0.6, max(0.4, raw))
        b_under = (1.0 - F) / (1.0 + ev)
        name = world.name_of("CAR", i)
        hr = ("player_points", name, line, world.american_from_prob(1.05 - b_under), world.american_from_prob(b_under))
        oth = {}
        for bk in BOOKS:
            o, u = world.two_sided(F, 0.05)
            oth[bk] = ("player_points", name, line, o, u)
        return hr, oth

    def wevents(self):
        p = os.path.join(self.wdir, "events.jsonl")
        if not os.path.exists(p):
            return []
        with open(p) as fh:
            return [json.loads(x) for x in fh.read().split("\n") if x]

    def test_the_points_track_is_asked_for_and_logged_never_a_pick(self):
        cfg = common.load_config()
        self.assertEqual(odds.paper_markets(cfg, world.SLATE), ["shots", "points"])
        sl = self.s.read("17:31", cp=[self.points_lines()])
        self.assertEqual(sl["picks"], [])                          # not on the page as a pick
        self.assertEqual(self.s.events(), [])                      # nothing in the Record
        ev = [e for e in self.wevents() if e["t"] in ("flag", "veto")]
        self.assertTrue(ev, "the points line with a +6% gap on the under should be logged as a flag or a veto")
        self.assertEqual({e["market"] for e in ev}, {"points"})
        self.assertEqual({(e["line"], e["side"]) for e in ev}, {(0.5, "under")})
        summ = common.read_json(os.path.join(self.wdir, "summary.json"))
        self.assertEqual(summ["market"], "points")
        self.assertIn("research only", summ["note"])
        live = os.path.join(os.environ["PC_DATA_DIR"], "paper", "events.jsonl")
        if os.path.exists(live):
            with open(live) as fh:
                self.assertNotIn('"points"', fh.read())            # the live research log never sees points

    def go_live(self, at):
        c = json.load(open(os.environ["PC_CONFIG"]))
        c["ops"]["gap_guard"]["watch"][0]["live_from_at"] = at
        json.dump(c, open(os.environ["PC_CONFIG"], "w"))

    def test_live_points_flags_become_picks_in_the_record(self):
        # Matt 2026-11-12: points go live. A flag read after live_from_at is a pick on the page and in the Record.
        self.go_live("%sT00:00:00-05:00" % world.SLATE)
        sl = self.s.read("17:31", cp=[self.points_lines()])
        flags = [e for e in self.wevents() if e["t"] == "flag"]
        self.assertTrue(flags, "the +6% points under should flag in the made-up league")
        self.assertEqual([(p["market"], p["line"], p["side"]) for p in sl["picks"]], [("points", 0.5, "under")])
        self.assertEqual(sl["picks"][0]["price"], flags[0]["price"])               # frozen at the flag's price
        shown = [e for e in self.s.events() if e["t"] == "shown"]
        self.assertEqual(len(shown), 1)
        self.assertEqual(shown[0]["pick"]["market"], "points")
        self.assertEqual(shown[0]["pick"]["gg_id"], "points|" + flags[0]["id"])    # can never collide with a shots flag
        self.assertIn(":points:", shown[0]["id"])
        self.s.read("17:41", cp=[self.points_lines()])                             # the next run adds nothing twice
        self.assertEqual(len([e for e in self.s.events() if e["t"] == "shown"]), 1)

    def test_points_flags_from_before_the_go_live_moment_stay_research(self):
        self.go_live("2099-01-01T00:00:00-05:00")
        sl = self.s.read("17:31", cp=[self.points_lines()])
        self.assertTrue([e for e in self.wevents() if e["t"] == "flag"])
        self.assertEqual(sl["picks"], [])
        self.assertEqual(self.s.events(), [])

    def test_saves_is_not_asked_when_only_the_points_track_runs(self):
        self.assertNotIn("saves", odds.paper_markets(common.load_config(), world.SLATE))


class LiveConfig(unittest.TestCase):
    def test_the_live_config_has_the_points_track_and_no_saves(self):
        # 2026-10-28 (Matt): saves removed everywhere, points is the research market.
        cfg = common.load_config()
        watch = common.gap_guard(cfg)["watch"]
        tr = [t for t in watch if t.get("id") == "points"]
        self.assertEqual(len(tr), 1)
        self.assertEqual((tr[0]["market"], tr[0]["lines"]), ("points", "any"))
        self.assertEqual([t.get("market") for t in watch], ["points"])
        self.assertNotIn("saves", cfg["ops"]["markets"])
        self.assertEqual(odds.paper_markets(cfg, "2026-10-28"), ["shots", "points"])
        self.assertEqual(odds.paper_markets(cfg, "2026-10-27"), ["shots"])           # before from_slate
        self.assertEqual(tr[0]["live_from_at"], "2026-11-12T16:15:00-05:00")       # Matt 2026-11-12: points are live picks

    def test_points_any_line_and_the_star_offset(self):
        import paper
        T = {"lines": "any", "offsets": {"*": 0.0}}
        self.assertTrue(paper.line_ok(0.5, T))
        self.assertEqual(paper.calibrated_over(0.5, 0.5, T), 0.5)
        self.assertFalse(paper.line_ok(0.5, {"lines": [1.5, 2.5]}))


if __name__ == "__main__":
    unittest.main()
