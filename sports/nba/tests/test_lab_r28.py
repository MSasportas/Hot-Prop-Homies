"""Lab forward tallies for R28a, R28b, R28d, R28e (research/code/lab_forward.py): scorers, ledger and forward-night filter."""
import datetime
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
NBA = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(NBA, "research", "code"))
sys.path.insert(0, os.path.join(NBA, "scripts"))
import lab_forward as lf  # noqa: E402

GID, DAY, PREV = "g1", "2026-11-22", "2026-11-21"
TEAM, STAR, MATE = "AAA", "10", "20"
FAIR = (-110, -110)


def quote(pid, line, over, under, team=TEAM):
    return [{"pid": pid, "name": "P" + pid, "team": team, "side": "over", "line": line, "price": over},
            {"pid": pid, "name": "P" + pid, "team": team, "side": "under", "line": line, "price": under}]


def with_links(outcomes, tag):
    return [dict(o, link="https://app.hardrock.bet/%s/%s" % (tag, o["side"])) for o in outcomes]


def market(outcomes, stamp):
    return {"last_update": stamp, "outcomes": outcomes}


def read(name, at, hr, pin, game=GID):
    """hr, pin: {market: outcomes list}. Every book's last update is 5 minutes before the read."""
    stamp = (datetime.datetime.fromisoformat(at) - datetime.timedelta(minutes=5)).astimezone(datetime.timezone.utc).isoformat()
    return {"game_id": game, "at": at, "read": name, "markets": {m: market(o, stamp) for m, o in hr.items()},
            "others": {"pinnacle": {m: market(o, stamp) for m, o in pin.items()}}}


def row(pid, date, **kw):
    base = {"pid": pid, "team": TEAM, "date": date, "game": "old" + date, "dnp": False, "min": 30.0, "pts": 20.0, "ast": 5.0}
    base.update(kw)
    return base


def box_of(*rows):
    return {(r["game"], r["pid"]): r for r in rows}


def history(pid, avg, n=6, **kw):
    return [row(pid, "2026-11-%02d" % (10 + i), game="h%s%d" % (pid, i), pts=avg, **kw) for i in range(n)]


def result_row(pid, pts):
    return row(pid, DAY, game=GID, pts=pts)


class TestB2bUnder(unittest.TestCase):
    def days(self, hr_under=105, pin_first=True):
        a = read("B", "2026-11-22T12:00:00-05:00", {"points": quote("1", 20.5, -110, -110)},
                 {"points": quote("1", 20.5, *FAIR)} if pin_first else {})
        b = read("C", "2026-11-22T12:30:00-05:00", {"points": quote("1", 20.5, -110, hr_under)}, {"points": quote("1", 20.5, *FAIR)})
        return {DAY: {GID: [a, b]}}

    def box(self, played_yesterday=True):
        rows = [result_row("1", 18.0)] + ([row("1", PREV)] if played_yesterday else [row("1", "2026-11-19")])
        return box_of(*rows)

    def test_back_to_back_under_is_bet_at_the_posted_under_price_and_graded_on_it(self):
        bets = lf.run_r28a(self.days(), self.box())
        self.assertEqual([(b["side"], b["price"], b["res"], b["m"]) for b in bets], [("under", 105, "W", "points")])

    def test_not_a_back_to_back_is_no_event(self):
        self.assertEqual(lf.run_r28a(self.days(), self.box(played_yesterday=False)), [])

    def test_pinnacle_missing_on_the_line_at_the_earlier_read_is_no_event(self):
        self.assertEqual(lf.run_r28a(self.days(pin_first=False), self.box()), [])

    def test_under_priced_worse_than_pinnacle_fair_is_no_event(self):
        self.assertEqual(lf.run_r28a(self.days(hr_under=-125), self.box()), [])

    def test_price_outside_the_window_is_no_event(self):
        self.assertEqual(lf.run_r28a(self.days(hr_under=250), self.box()), [])


class TestInjuryBump(unittest.TestCase):
    NEWS = [{"pid": STAR, "team": TEAM, "at": "2026-11-22T17:10:00Z"}]      # 12:10 ET: between the B and C reads

    def days(self, price_at_d=105):
        pin = {"points": quote(MATE, 12.5, *FAIR)}
        reads = [read("A", "2026-11-22T11:00:00-05:00", {"points": quote(MATE, 12.5, 105, -125)}, pin),
                 read("B", "2026-11-22T12:00:00-05:00", {"points": quote(MATE, 12.5, 105, -125)}, pin),
                 read("C", "2026-11-22T12:30:00-05:00", {"points": quote(MATE, 12.5, 105, -125)}, pin),
                 read("D", "2026-11-22T13:00:00-05:00", {"points": quote(MATE, 12.5, price_at_d, -125)}, pin)]
        return {DAY: {GID: reads}}

    def box(self, star_minutes=34.0):
        rows = history(STAR, 20.0, min=star_minutes) + history(MATE, 10.0, min=20.0) + [result_row(MATE, 15.0)]
        for i in range(8):                                                  # eight other teammates, all more minutes than MATE
            rows += history("x%d" % i, 10.0, min=25.0 + i)
        return box_of(*rows)

    def test_teammate_over_is_bet_at_the_next_read_when_the_price_held_since_the_news(self):
        bets = lf.run_r28b(self.days(), self.box(), self.NEWS)
        self.assertEqual([(b["pid"], b["side"], b["price"], b["res"]) for b in bets], [(MATE, "over", 105, "W")])

    def test_the_hard_rock_price_moving_after_the_news_is_no_event(self):
        self.assertEqual(lf.run_r28b(self.days(price_at_d=-110), self.box(), self.NEWS), [])

    def test_news_outside_the_window_between_two_reads_is_no_event(self):
        early = [{"pid": STAR, "team": TEAM, "at": "2026-11-22T15:00:00Z"}]  # before the A read
        self.assertEqual(lf.run_r28b(self.days(), self.box(), early), [])

    def test_a_player_outside_the_top_seven_by_minutes_is_not_a_trigger(self):
        self.assertEqual(lf.run_r28b(self.days(), self.box(star_minutes=5.0), self.NEWS), [])

    def test_newly_out_keeps_news_after_the_player_leaves_the_injury_list(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "ledger.json")
            listed = {"list": {STAR: {"status": "out", "team": TEAM, "date": "2026-11-22T17:10Z"},
                               "99": {"status": "questionable", "team": TEAM, "date": "2026-11-22T17:10Z"},
                               "98": {"status": "out", "team": TEAM, "date": "2026-11-01T17:10Z"}}}
            self.assertEqual([n["pid"] for n in lf.newly_out(path, listed)], [STAR])
            self.assertEqual([n["pid"] for n in lf.newly_out(path, {"list": {}})], [STAR])


class TestLvaAllSides(unittest.TestCase):
    CFG = {"threshold": 0.05, "min_prior_games": 3}

    def days(self, line, with_pin=True):
        f = read("B", "2026-11-22T12:00:00-05:00", {"points": quote("1", line, -110, -110)},
                 {"points": quote("1", line, *FAIR)} if with_pin else {})
        return {DAY: {GID: [f]}}

    def box(self, avg=20.0, n=4):
        return box_of(*(history("1", avg, n=n) + [result_row("1", 25.0)]))

    def test_line_five_percent_below_the_average_bets_the_under(self):
        under, over = lf.run_r28d(self.days(19.0), self.box(), self.CFG)
        self.assertEqual([(b["side"], b["res"]) for b in under], [("under", "L")])
        self.assertEqual(over, [])

    def test_line_five_percent_above_the_average_bets_the_over(self):
        under, over = lf.run_r28d(self.days(21.0), self.box(), self.CFG)
        self.assertEqual([(b["side"], b["price"], b["res"]) for b in over], [("over", -110, "W")])
        self.assertEqual(under, [])

    def test_line_near_the_average_or_without_pinnacle_or_history_is_no_event(self):
        self.assertEqual(lf.run_r28d(self.days(20.5), self.box(), self.CFG), ([], []))
        self.assertEqual(lf.run_r28d(self.days(21.0, with_pin=False), self.box(), self.CFG), ([], []))
        self.assertEqual(lf.run_r28d(self.days(21.0), self.box(n=2), self.CFG), ([], []))


class TestLateLag(unittest.TestCase):
    def setUp(self):
        self.c = read("C", "2026-11-22T18:00:00-05:00", {"points": quote("1", 20.5, -110, -110)},
                      {"points": quote("1", 20.5, *FAIR)})
        self.box = box_of(result_row("1", 25.0))

    def close(self, pin, hr=(-110, -110)):
        return read("E", "2026-11-22T18:50:00-05:00", {"points": quote("1", 20.5, *hr)}, {"points": quote("1", 20.5, *pin)})

    def run_e(self, close):
        return lf.run_r28e({DAY: {GID: [self.c]}}, {DAY: {GID: close}}, self.box)

    def test_pinnacle_moving_toward_the_over_with_hard_rock_flat_bets_the_over(self):
        bets = self.run_e(self.close((-130, 110)))
        self.assertEqual([(b["side"], b["price"], b["res"]) for b in bets], [("over", -110, "W")])

    def test_pinnacle_moving_toward_the_under_bets_the_under_at_its_own_price(self):
        bets = self.run_e(self.close((110, -130), hr=(-110, -110)))
        self.assertEqual([(b["side"], b["price"], b["res"]) for b in bets], [("under", -110, "L")])

    def test_small_pinnacle_move_or_a_hard_rock_move_is_no_event(self):
        self.assertEqual(self.run_e(self.close((-112, -108))), [])
        self.assertEqual(self.run_e(self.close((-130, 110), hr=(-120, -100))), [])

    def test_a_night_without_a_close_read_is_skipped(self):
        self.assertEqual(lf.run_r28e({DAY: {GID: [self.c]}}, {}, self.box), [])


class TestFlatIgnoresLinks(unittest.TestCase):
    """The C read carries Hard Rock deep links and the close read does not: same prices must still count as flat."""
    def test_late_lag_and_injury_bump_treat_link_only_differences_as_flat(self):
        c = read("C", "2026-11-22T18:00:00-05:00", {"points": with_links(quote("1", 20.5, -110, -110), "c")}, {"points": quote("1", 20.5, *FAIR)})
        close = read("E", "2026-11-22T18:50:00-05:00", {"points": quote("1", 20.5, -110, -110)}, {"points": quote("1", 20.5, -130, 110)})
        bets = lf.run_r28e({DAY: {GID: [c]}}, {DAY: {GID: close}}, box_of(result_row("1", 25.0)))
        self.assertEqual([b["side"] for b in bets], ["over"])
        self.assertTrue(lf.same_prices({"over": 105, "under": -125, "link_over": "x"}, {"over": 105, "under": -125}))
        self.assertFalse(lf.same_prices({"over": 105, "under": -125}, {"over": 105, "under": -120}))
        self.assertFalse(lf.same_prices(None, {"over": 105, "under": -125}))

    def test_injury_bump_with_links_on_the_news_read_only(self):
        pin = {"points": quote(MATE, 12.5, *FAIR)}
        hr = quote(MATE, 12.5, 105, -125)
        reads = [read("A", "2026-11-22T11:00:00-05:00", {"points": hr}, pin),
                 read("B", "2026-11-22T12:00:00-05:00", {"points": hr}, pin),
                 read("C", "2026-11-22T12:30:00-05:00", {"points": with_links(hr, "c")}, pin),
                 read("D", "2026-11-22T13:00:00-05:00", {"points": hr}, pin)]
        rows = history(STAR, 20.0, min=34.0) + history(MATE, 10.0, min=20.0) + [result_row(MATE, 15.0)]
        news = [{"pid": STAR, "team": TEAM, "at": "2026-11-22T17:10:00Z"}]
        self.assertEqual(len(lf.run_r28b({DAY: {GID: reads}}, box_of(*rows), news)), 1)


class TestForwardNights(unittest.TestCase):
    def test_r28_bets_ignore_nights_before_the_forward_start(self):
        old = "2026-11-20"
        a = read("B", "2026-11-20T12:00:00-05:00", {"points": quote("1", 19.0, -110, -110)}, {"points": quote("1", 19.0, *FAIR)})
        out = lf.r28_bets({old: {GID: [a]}}, {}, box_of(*history("1", 20.0)), [], {"threshold": 0.05, "min_prior_games": 3})
        self.assertEqual({tid: len(b) for tid, b in out.items()}, {tid: 0 for tid in lf.R28_IDS})


if __name__ == "__main__":
    unittest.main()
