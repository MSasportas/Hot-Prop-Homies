import json
import os
import re
import shutil
import unittest

from page_js import page_source, run_page_js

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LAB_FILES = {sport: os.path.join(ROOT, "sports", sport, "config", "lab.json") for sport in ("nba", "nhl")}
FIXTURE_LAB = os.path.join(ROOT, "fixtures", "lab-cards", "config", "lab.json")
OUTCOMES = {"review", "filter", "matt", "live"}
NAME_MAX, PLAIN_MAX, WHY_MAX = 28, 80, 110
# words that stay inside "Show the math"; "Sharp books" is the one allowed use on a card face
JARGON = re.compile(r"n=|\bROI\b|\bCI\b|bucket|discovery|shadow-track|base population|\bDS\b|(?-i:\bSharp\b(?! books| vs))|\bLVA|\bCLV\b|\bEV\b|de-vig|\bgate\b|hit rate|forward test", re.I)
STATUS_FUNCTIONS = ("isObj", "num", "str", "labStatus")
NIGHT_FUNCTIONS = ("isObj", "arr", "num", "str", "labNightRows", "labPer", "labFlipResult", "labNights")


def lab_tests(sport):
    with open(LAB_FILES[sport], encoding="utf-8") as fh:
        return json.load(fh)["tests"]


@unittest.skipUnless(shutil.which("node"), "node not installed")
class LabCardLogic(unittest.TestCase):
    def run_js(self, functions, body, variables=()):
        got, err = run_page_js(functions, body, variables)
        self.assertEqual(err, "")
        return got

    def test_status_follows_the_sample_floor_and_only_ready_means_passed(self):
        got = self.run_js(STATUS_FUNCTIONS, """
          var T = function (need, status) { return { need: need, status: status }; };
          var st = {};
          console.log(JSON.stringify([
            labStatus(T(300), null, 0, null),
            labStatus(T(300, 'ready_for_sharp'), st, 400, -5),
            labStatus(T(150), st, 150, 0),
            labStatus(T(300), st, 488, 24.36),
            labStatus(T(300), st, 75, 4),
            labStatus(T(300), st, 74, 4),
            labStatus(T(300), st, 80, -4),
            labStatus(T(300), st, 80, 0),
            labStatus(T(40), st, 20, 1),
            labStatus(T(40), st, 19, 1),
            labStatus(T(300), st, 12, null)
          ]));""", ("LAB_FLOOR_MIN", "LAB_FLOOR_FRAC"))
        self.assertEqual(got, ["starting", "ready", "check", "good", "good", "collecting", "bad", "collecting", "good", "collecting", "collecting"])

    def test_meter_words(self):
        got = self.run_js(("labMeterText",), "console.log(JSON.stringify([labMeterText(null, 0, 300), labMeterText({}, 120, 300), labMeterText({}, 488, 300), labMeterText({}, 7, null)]"
                          ".map(function (s) { return s.split('').map(function (c) { return c.charCodeAt(0) > 127 ? '~' : c; }).join(''); })))")
        self.assertEqual(got, ["Waiting for first picks", "120 of 300 picks", "488 picks ~ goal was 300", "7 picks"])

    def test_trend_needs_three_nights_and_reads_the_last_seven(self):
        got = self.run_js(("labTrend",), """
          var N = function (a) { return a.map(function (u) { return { u: u }; }); };
          console.log(JSON.stringify([labTrend(N([1, 2])), labTrend(N([1, 1, 1])), labTrend(N([5, -1, -1, -1])),
            labTrend(N([9, 1, -1, -1, -1, -1, -1, -1])), labTrend(N([1, -1, 0]))]));""", ("LAB_MIN_NIGHTS", "LAB_TREND_NIGHTS"))
        self.assertEqual([g and (g["word"], g["sum"], g["n"]) for g in got],
                         [None, ("Up lately", 3, 3), ("Up lately", 2, 4), ("Down lately", -5, 7), ("Flat", 0, 3)])

    def test_dollars_use_the_ten_dollar_nba_unit(self):
        got = self.run_js(("comma", "labDollars"), "console.log(JSON.stringify([labDollars(24.36), labDollars(-3.04), labDollars(125)]))", ("LAB_NBA_UNIT_USD",))
        self.assertEqual(got, ["+$244", "-$30", "+$1,250"])

    def test_sparkline_runs_left_to_right_and_marks_the_end(self):
        got = self.run_js(("labSpark",), "console.log(JSON.stringify(labSpark([1, -1, 3], 300, 56)))")
        self.assertTrue(got["line"].startswith("M0.0,"))
        self.assertIn("300.0,", got["line"])
        self.assertTrue(got["area"].endswith("L300,56 L0,56 Z"))
        self.assertLess(got["endY"], 20)      # ends at the high point
        self.assertTrue(4 < got["zero"] < 52)

    def test_nights_come_oldest_first_and_a_fade_test_counts_the_side_we_bet(self):
        got = self.run_js(NIGHT_FUNCTIONS, """
          var sm = { nights: [
            { date: '2026-11-22', bets: [{ result: 'L', units: -1 }, { result: 'W', units: 0.9 }, { result: 'L', units: -1, kind: 'bet' }] },
            { date: '2026-11-21', flags: [{ result: 'L', units: -1 }] },
            { date: '2026-11-20', bets: [] }] };
          var pick = function (n) { return [n.date, n.w, n.l, n.u]; };
          console.log(JSON.stringify([labNights(sm, {}, false).map(pick), labNights(sm, {}, true).map(pick), labNights(null, {}, false)]));""")
        self.assertEqual(got, [[["2026-11-21", 0, 1, -1], ["2026-11-22", 1, 1, -0.1]], [["2026-11-21", 1, 0, 1], ["2026-11-22", 1, 1, 0.1]], []])

    def test_nights_read_a_per_test_block_when_the_summary_has_one(self):
        got = self.run_js(NIGHT_FUNCTIONS, """
          var sm = { tests: { A: { nights: [{ date: '2026-11-20', flags: [{ result: 'W', units: 1 }] }] } }, nights: [{ date: '2026-11-19', flags: [{ result: 'L', units: -1 }] }] };
          console.log(JSON.stringify([labNights(sm, { stats: 'A' }, false).map(function (n) { return n.date; }), labNights(sm, { stats: 'B' }, false).map(function (n) { return n.date; })]));""")
        self.assertEqual(got, [["2026-11-20"], ["2026-11-19"]])

    def test_list_order_and_counts(self):
        got = self.run_js(("labSortModels", "labCounts"), """
          var M = function (id, status, u, k) { return { id: id, status: status, u: u, k: k }; };
          var ms = [M('st', 'starting', null, 0), M('bad1', 'bad', -9, 100), M('bad2', 'bad', -2, 100), M('c1', 'collecting', 0, 5), M('c2', 'collecting', 1, 30),
            M('g1', 'good', 2, 50), M('g2', 'good', 7, 50), M('ck', 'check', 0, 150), M('rd', 'ready', 5, 160)];
          console.log(JSON.stringify([labSortModels(ms).map(function (m) { return m.id; }), labCounts(ms)]));""", ("LAB_STATUS_ORDER",))
        self.assertEqual(got[0], ["rd", "ck", "g2", "g1", "c2", "c1", "bad2", "bad1", "st"])
        self.assertEqual(got[1], {"starting": 1, "bad": 2, "collecting": 2, "good": 2, "check": 1, "ready": 1})

    def test_tag_names_and_fallbacks(self):
        got = self.run_js(("str", "labName", "labIsPaper", "labTag", "labOutcome"), """
          console.log(JSON.stringify([labName({ name: 'Short', title: 'Long title' }), labName({ title: 'Long title' }), labName({}),
            labTag({}), labTag({ outcome: 'filter' }), labTag({ paper: false, outcome: 'live' }),
            labOutcome({ outcome: 'matt' }).short, labOutcome({}).short, labOutcome({ outcome: 'nope' }).short]));""",
                           ("LAB_TAG_PAPER", "LAB_TAG_FILTER", "LAB_TAG_REAL", "LAB_OUTCOME"))
        self.assertEqual(got, ["Short", "Long title", "Untitled idea", "PAPER TEST - not in your picks", "PAPER TEST - your picks are unchanged",
                               "REAL PICKS - on your Record", "You get the call.", "Goes to review.", "Goes to review."])


class LabCopy(unittest.TestCase):
    def test_every_live_test_has_plain_copy_within_the_limits(self):
        for sport in LAB_FILES:
            for t in lab_tests(sport):
                where = "%s/%s" % (sport, t["id"])
                for key in ("name", "plain", "why", "outcome"):
                    self.assertTrue(t.get(key), "%s has no %s" % (where, key))
                self.assertLessEqual(len(t["name"]), NAME_MAX, where)
                self.assertLessEqual(len(t["plain"]), PLAIN_MAX, where)
                self.assertLessEqual(len(t["why"]), WHY_MAX, where)
                self.assertIn(t["outcome"], OUTCOMES, where)

    def test_only_fast_checks_is_real_picks(self):
        for sport in LAB_FILES:
            real = [t["id"] for t in lab_tests(sport) if t.get("paper") is False]
            self.assertEqual(real, ["fast_checks"] if sport == "nba" else [])
            for t in lab_tests(sport):
                self.assertEqual(t["outcome"] == "live", t.get("paper") is False, t["id"])

    def test_plain_and_why_keep_the_jargon_out_and_never_use_dashes_or_promises(self):
        for sport in LAB_FILES:
            for t in lab_tests(sport):
                for key in ("name", "plain", "why"):
                    text = t[key]
                    self.assertIsNone(JARGON.search(text), "%s/%s %s: %s" % (sport, t["id"], key, text))
                    self.assertNotIn("—", text)
                    self.assertNotRegex(text, r"\b(will|guaranteed|free money)\b")

    def test_researcher_text_is_untouched(self):
        for sport in LAB_FILES:
            for t in lab_tests(sport):
                for key in ("title", "rule", "gate", "summary", "need"):
                    self.assertIn(key, t, "%s/%s lost %s" % (sport, t["id"], key))

    def test_fixture_lab_covers_every_card_state(self):
        with open(FIXTURE_LAB, encoding="utf-8") as fh:
            tests = json.load(fh)["tests"]
        self.assertTrue(any(t.get("direction") == "fade" for t in tests))
        self.assertTrue(any(t.get("paper") is False for t in tests))
        self.assertTrue(any(t.get("status") == "ready_for_sharp" for t in tests))
        self.assertTrue(any("name" not in t for t in tests))
        self.assertEqual({t["outcome"] for t in tests if "outcome" in t}, OUTCOMES)


class LabPageSource(unittest.TestCase):
    def setUp(self):
        self.src = page_source()

    def test_the_drawer_prints_the_researcher_fields_untouched(self):
        for field in ("t.rule", "t.discovery", "t.gate"):
            self.assertIn("str(%s)" % field, self.src)

    def test_card_face_reads_only_the_plain_fields(self):
        face = re.search(r"function labFace\([\s\S]*?\n}\n", self.src).group(0)
        for field in ("rule", "discovery", "gate"):
            self.assertNotIn("t.%s" % field, face)

    def test_tonight_card_shows_no_technical_text(self):
        row = re.search(r"function labLiveRow\([\s\S]*?\n}\n", self.src).group(0)
        for field in ("test.rule", "test.discovery", "test.gate", "test.title"):
            self.assertNotIn(field, row)
        self.assertIn("See this test", row)

    def test_motion_is_switched_off_for_reduced_motion(self):
        block = re.search(r"@media \(prefers-reduced-motion:reduce\)\{\s*\.lc-meter i\.anim[^}]*\}", self.src)
        self.assertIsNotNone(block)
        for cls in (".lc-grow.anim", ".lc-spark.anim svg"):
            self.assertIn(cls, block.group(0))

    def test_fixture_mode_reads_its_own_lab_file(self):
        self.assertIn("BASE_FIX + 'config/lab.json'", self.src)


if __name__ == "__main__":
    unittest.main()
