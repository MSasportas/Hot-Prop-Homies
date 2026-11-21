"""Run 28 forward scorer (research/code/r28/score_r28.py): the four NHL rules, graded at the posted Hard Rock price on the bet side."""
import gzip
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
NHL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(NHL, "research", "code", "r28"))
import score_r28 as r28  # noqa: E402

NIGHT = "2026-11-22"
BACKUP, STARTER = "Backup", "Starter"


def read(over=-120, under=100, pull="B", goalie_opp=None, **extra):
    blk = {"at": "2026-11-22T11:30:00-05:00", "pull": pull, "over": over, "under": under,
           "goalie_opp": goalie_opp or {"name": STARTER, "status": "expected"}}
    blk.update(extra)
    return blk


def shadow_row(market="shots", line=2.5, pid=1, result=None, opened=None, close=None, opp="BBB"):
    return {"game_id": 7, "market": market, "pid": pid, "line": line, "src": "live", "ctx": {"team": "AAA", "opp": opp},
            "open": opened or read(), "close": close, "result": result}


def final(actual):
    return {"actual": actual, "toi": "18:00"}


def logs(pid, games):
    return {pid: games}


def shots_by_day(shots, last_date):
    """Six games ending on last_date, one per day, each with `shots` shots."""
    day = int(last_date[-2:])
    return [("2026-11-%02d" % (day - 5 + i), shots) for i in range(6)]


class TestPointsGap(unittest.TestCase):
    def row(self, over, under, pin, pull="C"):
        return shadow_row("points", 0.5, close=read(over, under, pull=pull, pin_fair_over=pin, cons_fair_over_med=pin), result=final(1))

    def test_bets_the_side_five_percent_better_than_pinnacle_at_its_own_price(self):
        out = r28.points_gap(NIGHT, self.row(over=110, under=-150, pin=0.55))    # over fair .55 at +110: EV +15.5%
        self.assertEqual([(v, b["side"], b["price"]) for v, b in out], [("R28a points gap", "over", 110)])
        self.assertAlmostEqual(out[0][1]["pl"], 1.1)

    def test_the_under_is_graded_on_the_under_price_not_mirrored(self):
        out = r28.points_gap(NIGHT, self.row(over=-300, under=115, pin=0.30))
        self.assertEqual([(b["side"], b["price"], b["pl"]) for _, b in out], [("under", 115, -1.0)])   # 1 point beat the 0.5 line

    def test_small_gap_wrong_read_or_price_outside_the_window_is_no_bet(self):
        self.assertEqual(r28.points_gap(NIGHT, self.row(over=-105, under=-115, pin=0.51)), [])
        self.assertEqual(r28.points_gap(NIGHT, self.row(over=110, under=-150, pin=0.55, pull="B")), [])
        self.assertEqual(r28.points_gap(NIGHT, self.row(over=130, under=-170, pin=0.60)), [])      # +130 is past the +120 cap


class TestShotsRules(unittest.TestCase):
    def sides(self, row, game_logs, starts=None):
        return [(v, b["side"], b["price"]) for v, b in r28.shots_sides(NIGHT, row, game_logs, starts or {})]

    def test_line_below_the_rolling_average_bets_the_under_above_bets_the_over(self):
        log = logs(1, shots_by_day(3, "2026-11-21"))                              # average 3.0, so 2.5 is 16.7% below
        self.assertIn(("R28b under", "under", 100), self.sides(shadow_row(line=2.5), log))
        self.assertIn(("R28b over", "over", -120), self.sides(shadow_row(line=3.5), log))
        self.assertEqual([s for s in self.sides(shadow_row(line=3.0), log) if s[0].startswith("R28b")], [])

    def test_rolling_average_needs_five_prior_games_and_ignores_the_night_itself(self):
        short = logs(1, shots_by_day(3, "2026-11-21")[2:])
        self.assertEqual([s for s in self.sides(shadow_row(), short) if s[0].startswith("R28b")], [])
        with_today = logs(1, shots_by_day(3, "2026-11-21")[2:] + [(NIGHT, 9)])
        self.assertIsNone(r28.rolling_sog(with_today, 1, NIGHT))

    def test_rest_splits_over_and_under_with_the_mirror_on_the_other_side(self):
        rested = logs(1, shots_by_day(3, "2026-11-18"))                           # last game Nov 18, three days off
        tired = logs(1, shots_by_day(3, "2026-11-21"))                            # last game Nov 21: back-to-back
        self.assertEqual(r28.rest_days(rested, 1, NIGHT), 3)
        self.assertEqual(r28.rest_days(tired, 1, NIGHT), 0)
        rested_sides = self.sides(shadow_row(line=3.0), rested)
        self.assertIn(("R28c rest", "over", -120), rested_sides)
        self.assertIn(("R28c rest mirror", "under", 100), rested_sides)
        tired_sides = self.sides(shadow_row(line=3.0), tired)
        self.assertIn(("R28c rest", "under", 100), tired_sides)
        self.assertIn(("R28c rest mirror", "over", -120), tired_sides)

    def test_two_days_off_is_in_neither_rest_bucket(self):
        mid = logs(1, shots_by_day(3, "2026-11-19"))
        self.assertEqual([s for s in self.sides(shadow_row(line=3.0), mid) if s[0].startswith("R28c")], [])

    def test_a_price_worse_than_minus_200_is_never_bet(self):
        log = logs(1, shots_by_day(3, "2026-11-21"))
        row = shadow_row(line=3.5, opened=read(over=-230, under=180))
        self.assertEqual([s for s in self.sides(row, log) if s[0] == "R28b over"], [])

    def test_confirmed_backup_goalie_bets_the_over(self):
        starts = {"BBB": {STARTER: {"a", "b", "c", "d"}, BACKUP: {"e"}}}
        backup = {"name": BACKUP, "status": "confirmed"}
        row = shadow_row(line=3.0, opened=read(goalie_opp=backup))
        self.assertIn(("R28d backup goalie", "over", -120), self.sides(row, {}, starts))

    def test_usual_starter_unconfirmed_backup_or_thin_history_is_no_bet(self):
        starts = {"BBB": {STARTER: {"a", "b", "c", "d"}, BACKUP: {"e"}}}
        usual = shadow_row(opened=read(goalie_opp={"name": STARTER, "status": "confirmed"}))
        unconfirmed = shadow_row(opened=read(goalie_opp={"name": BACKUP, "status": "expected"}))
        confirmed_backup = shadow_row(opened=read(goalie_opp={"name": BACKUP, "status": "confirmed"}))
        self.assertEqual(self.sides(usual, {}, starts), [])
        self.assertEqual(self.sides(unconfirmed, {}, starts), [])
        self.assertEqual(self.sides(confirmed_backup, {}, {"BBB": {STARTER: {"a", "b"}}}), [])

    def test_backup_confirmed_only_at_the_close_read_is_bet_at_the_close_price(self):
        starts = {"BBB": {STARTER: {"a", "b", "c", "d"}, BACKUP: {"e"}}}
        row = shadow_row(line=3.0, close=read(over=-110, pull="C", goalie_opp={"name": BACKUP, "status": "confirmed"}))
        self.assertIn(("R28d backup goalie", "over", -110), self.sides(row, {}, starts))

    def test_most_started_counts_nights_per_goalie_and_waits_for_enough_nights(self):
        self.assertIsNone(r28.most_started({"BBB": {STARTER: {"a", "b"}}}, "BBB"))
        self.assertEqual(r28.most_started({"BBB": {STARTER: {"a", "b", "c"}, BACKUP: {"d", "e"}}}, "BBB"), STARTER)


class TestScoreEndToEnd(unittest.TestCase):
    def write(self, root, night, rows):
        os.makedirs(os.path.join(root, "data/shadow"), exist_ok=True)
        with open(os.path.join(root, "data/shadow", night + ".json"), "w", encoding="utf-8") as fh:
            json.dump({"date": night, "rows": rows}, fh)

    def test_forward_nights_are_judged_and_earlier_nights_stay_descriptive(self):
        with tempfile.TemporaryDirectory() as root:
            win = shadow_row("points", 0.5, close=read(110, -150, pull="C", pin_fair_over=0.55, cons_fair_over_med=0.55), result=final(1))
            self.write(root, "2026-11-20", [win])
            self.write(root, "2026-11-22", [win])
            window = os.path.join(root, "data/state/stats", r28.SEASON)
            os.makedirs(window)
            with gzip.open(os.path.join(window, "2026-11-17.json.gz"), "wt", encoding="utf-8") as fh:
                json.dump({"skater_fields": ["pid", "date", "shots"], "skaters": []}, fh)
            old_root, r28.ROOT, r28.F.ROOT = r28.ROOT, root, root
            try:
                judged, descriptive = r28.score()
            finally:
                r28.ROOT = r28.F.ROOT = old_root
        self.assertEqual([len(judged[v]) for v in r28.VARS], [1, 0, 0, 0, 0, 0])
        self.assertEqual(len(descriptive["R28a points gap"]), 1)
        self.assertEqual(judged["R28a points gap"][0]["date"], "2026-11-22")


if __name__ == "__main__":
    unittest.main()
