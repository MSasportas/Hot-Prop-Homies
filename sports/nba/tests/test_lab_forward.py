"""Lab forward tallies for NP1-NP4 and LVA1-LVA2 (research/code/lab_forward.py): the writers that had been missing."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
NBA = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(NBA, "research", "code"))
sys.path.insert(0, os.path.join(NBA, "scripts"))
import lab_forward as lf  # noqa: E402

PID, GID, DAY = "1", "g1", "2026-11-18"


def book_quote(over, under, last_update="2026-11-18T15:00:00Z"):
    return {"last_update": last_update, "outcomes": [
        {"pid": PID, "name": "A Player", "team": "AAA", "side": "over", "line": 5.5, "price": over},
        {"pid": PID, "name": "A Player", "team": "AAA", "side": "under", "line": 5.5, "price": under}]}


def fetch(at, read, hr, exchanges):
    """hr: (over, under) at Hard Rock; exchanges: {book: (over, under)}."""
    return {"game_id": GID, "at": at, "read": read, "markets": {"rebounds": book_quote(*hr)},
            "others": {bk: {"rebounds": book_quote(*q)} for bk, q in exchanges.items()}}


def box(pts_reb):
    return {(GID, PID): {"pid": PID, "dnp": False, "min": 30.0, "reb": pts_reb, "date": DAY, "game": GID}}


class TestNp4(unittest.TestCase):
    def days(self, novig_b, prophetx_b):
        a = fetch("2026-11-18T11:00:00-05:00", "A", (-110, -110), {"novig": (-110, -110), "prophetx": (-110, -110)})
        b = fetch("2026-11-18T12:30:00-05:00", "B", (-110, -110), {"novig": novig_b, "prophetx": prophetx_b})
        return {DAY: {GID: [a, b]}}

    def test_both_exchanges_move_the_same_way_bets_that_side(self):
        bets = lf.np_disc.run_np4(self.days((-130, 110), (-125, 105)), box(7.0))
        self.assertEqual([(b["side"], b["price"], b["res"]) for b in bets], [("over", -110, "W")])

    def test_exchanges_moving_apart_or_one_still_is_no_event(self):
        self.assertEqual(lf.np_disc.run_np4(self.days((-130, 110), (-110, -110)), box(7.0)), [])
        self.assertEqual(lf.np_disc.run_np4(self.days((-130, 110), (110, -130)), box(7.0)), [])

    def test_hard_rock_price_change_is_no_event(self):
        days = self.days((-130, 110), (-125, 105))
        days[DAY][GID][1]["markets"] = {"rebounds": book_quote(-115, -105)}
        self.assertEqual(lf.np_disc.run_np4(days, box(7.0)), [])

    def test_np_bets_keep_only_forward_nights(self):
        old = self.days((-130, 110), (-125, 105))
        out = lf.np_bets({"2026-11-10": old[DAY], DAY: old[DAY]}, box(7.0))
        self.assertEqual({tid: len(b) for tid, b in out.items()}["NP4"], 1)


class TestTally(unittest.TestCase):
    def test_counts_units_and_pending(self):
        t = lf.tally([{"res": "W", "price": 100}, {"res": "L", "price": -110}, {"res": "?", "price": -110},
                      {"res": "P", "price": -110}, {"res": "V", "price": -110}])
        self.assertEqual(t, {"w": 1, "l": 1, "units": 0.0, "pending": 1, "push": 1, "void": 1})


class TestLva(unittest.TestCase):
    CFG = {"threshold": 0.05, "min_prior_games": 3}

    def history(self, avg_reb):
        rows = {("p%d" % i, PID): {"pid": PID, "dnp": False, "min": 30.0, "reb": avg_reb, "date": "2026-11-%02d" % (10 + i)}
                for i in range(3)}
        rows[(GID, PID)] = {"pid": PID, "dnp": False, "min": 30.0, "reb": 9.0, "date": DAY, "game": GID}
        return rows

    def row(self, side, line, why=None):
        return {"rule": "pin_solo", "pid": PID, "market": "rebounds", "line": line, "side": side, "price": -110,
                "game_id": GID, "why": why}

    def test_lva1_scores_the_unders_the_engine_skipped(self):
        rows = [self.row("under", 6.0, "LVA1: line 6.0 is 25% below rolling avg 8.0"),
                self.row("under", 6.0, "LVA1: line 6.0 is 25% below rolling avg 8.0")]
        lva1, lva2 = lf.lva_bets({DAY: rows}, self.history(8.0), self.CFG)
        self.assertEqual([b["res"] for b in lva1], ["L"])      # 9 rebounds beats the 6.0 line: the skipped under lost
        self.assertEqual(lva2, [])

    def test_lva2_flags_live_overs_five_percent_above_the_average(self):
        lva1, lva2 = lf.lva_bets({DAY: [self.row("over", 8.5)]}, self.history(8.0), self.CFG)
        self.assertEqual([b["res"] for b in lva2], ["W"])
        self.assertEqual(lva1, [])

    def test_lva2_ignores_overs_near_the_average_and_overs_that_were_not_live(self):
        near = self.row("over", 8.2)
        not_live = self.row("over", 8.5, "Hard Rock price is worse than Pinnacle's")
        self.assertEqual(lf.lva_bets({DAY: [near, not_live]}, self.history(8.0), self.CFG), ([], []))

    def test_lva2_needs_the_minimum_prior_games(self):
        thin = {k: v for k, v in self.history(8.0).items() if k[0] != "p0" and k[0] != "p1"}
        self.assertEqual(lf.lva_bets({DAY: [self.row("over", 8.5)]}, thin, self.CFG), ([], []))


class TestWriteSummary(unittest.TestCase):
    def test_rewrites_only_on_change_and_stamps_updated_at(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "research", "lab_x.json")
            first = lf.write_summary(path, {"NP1": lf.tally([])})
            self.assertIn("updated_at", first)
            stamp = lf.common.read_json(path)["updated_at"]
            again = lf.write_summary(path, {"NP1": lf.tally([])})
            self.assertEqual(again["updated_at"], stamp)
            changed = lf.write_summary(path, {"NP1": lf.tally([{"res": "W", "price": 100}])})
            self.assertEqual(changed["NP1"]["w"], 1)


if __name__ == "__main__":
    unittest.main()
