"""DM2 and DM3 are fade tests tallied as the real bet on the other side (research/code/auto_hypothesis.py export_dm)."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
NBA = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(NBA, "research", "code"))
sys.path.insert(0, os.path.join(NBA, "scripts"))
import auto_hypothesis as ah  # noqa: E402

PID, GID, DAY, LINE = "1", "g1", "2026-11-18", 5.5
COLD_GAMES, HOT_GAMES = 3, 5            # season avg 6.5 rebounds vs last five 8.0: 23% hot, past the 10% bar


def quote(over, under):
    outcomes = [{"pid": PID, "name": "A Player", "team": "AAA", "side": side, "line": LINE, "price": price}
                for side, price in (("over", over), ("under", under)) if price is not None]
    return {"last_update": "2026-11-18T15:00:00Z", "outcomes": outcomes}


def night(hr_over, hr_under):
    fetch = {"game_id": GID, "at": "2026-11-18T12:00:00-05:00", "read": "B", "markets": {"rebounds": quote(hr_over, hr_under)},
             "others": {"pinnacle": {"rebounds": quote(-110, -110)}}}
    return {DAY: {GID: [fetch]}}


def box(rebounds):
    rows = {}
    for i in range(COLD_GAMES + HOT_GAMES):
        reb = 4.0 if i < COLD_GAMES else 8.0
        rows[("p%d" % i, PID)] = {"pid": PID, "dnp": False, "min": 30.0, "reb": reb, "date": "2026-11-%02d" % (5 + i)}
    rows[(GID, PID)] = {"pid": PID, "dnp": False, "min": 30.0, "reb": rebounds, "date": DAY, "game": GID}
    return rows


class TestFadeBet(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root, ah.R = ah.R, self.tmp.name + os.sep
        self.addCleanup(setattr, ah, "R", self.root)

    def export(self, hr_over, hr_under, rebounds):
        doc = ah.export_dm(night(hr_over, hr_under), box(rebounds))
        with open(self.tmp.name + "/data/research/lab_dm_bets.jsonl", encoding="utf-8") as fh:
            return doc["DM2"], [json.loads(line) for line in fh]

    def test_the_under_is_graded_at_its_own_price_not_the_overs_mirror(self):
        dm2, rows = self.export(-110, -110, 5.0)
        self.assertEqual((dm2["w"], dm2["l"], dm2["units"]), (1, 0, 0.91))     # mirroring the over's -1.0 would say +1.0
        self.assertEqual((rows[0]["bet"], rows[0]["under"], rows[0]["under_res"], rows[0]["over_res"]), ("under", -110, "W", "L"))

    def test_a_losing_under_costs_a_full_unit_whatever_the_over_paid(self):
        dm2, _ = self.export(150, -180, 7.0)
        self.assertEqual((dm2["w"], dm2["l"], dm2["units"]), (0, 1, -1.0))

    def test_under_worse_than_minus_200_or_unpriced_is_excluded_not_bet(self):
        for under, reason in ((-250, "worse_than_200"), (None, "no_price")):
            dm2, rows = self.export(150, under, 5.0)
            self.assertEqual((dm2["w"], dm2["l"], dm2["units"], dm2["excluded"]), (0, 0, 0.0, 1), under)
            self.assertEqual(rows[0]["skip"], reason)

    def test_player_nights_count_the_bet_rows(self):
        dm2, _ = self.export(-110, -110, 5.0)
        self.assertEqual(dm2["player_nights"], 1)

    def test_a_push_is_neither_win_nor_loss(self):
        dm2, rows = self.export(-110, -110, LINE)
        self.assertEqual((dm2["w"], dm2["l"], dm2["push"]), (0, 0, 1))
        self.assertEqual(rows[0]["under_res"], "P")


if __name__ == "__main__":
    unittest.main()
