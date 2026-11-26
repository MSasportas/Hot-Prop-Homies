"""My Tracker: the rules (run from the page's own code in node) and the screens (fixture pages in chromium)."""
import functools
import http.server
import json
import os
import re
import shutil
import threading
import unittest

from page_js import page_source, run_page_js

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DAY = "2026-11-23"  # the fixture's slate day (fixtures/livelong/tracker.json)
TRK_KEY = "hph.tracker.fx.v1"
SEG_KEY = "hph.live.seg"
RULE_FNS = ("str", "num", "arr", "isObj", "cnt", "tri", "nhlTeam", "normName", "nhlNameKey", "trkStats", "trkStat", "trkTeam", "trkNameKey", "trkValue", "trkResult",
            "trkLineCheck", "trkStepLine", "trkSamePlayer", "trkSameStat", "trkDuplicate", "trkConflict", "trkParlayStatus", "trkDayAdd", "trkPairTeams", "trkSanitize",
            "trkBoxIndex", "trkRowFor", "trkMatches", "trkHaystack", "trkBetText", "trkInitials")
RULE_VARS = ("TRK_NBA", "TRK_NHL", "TRK_MAX_BETS", "TRK_MAX_PARLAYS", "TRK_MAX_LEGS", "TRK_KEEP_DAYS", "TRK_LINE_MIN", "TRK_LINE_MAX", "TRK_LINE_STEP", "TRK_NAME_MAX",
             "TRK_TEAMS_NBA", "TRK_TEAMS_NHL", "NBA_TRI", "NHL_TEAM")


def rules(body):
    got, err = run_page_js(RULE_FNS, body, RULE_VARS)
    assert err == "", err
    return got


def tracker_source():
    src = page_source()
    return src[src.index("/* ---------- My Tracker ---------- */"):src.index("/* ---------- /My Tracker ---------- */")]


@unittest.skipUnless(shutil.which("node"), "node not installed")
class StatMath(unittest.TestCase):
    NBA_ROW = {"dnp": False, "points": 20, "rebounds": 8, "assists": 5, "threes": 3}

    def test_every_nba_stat_and_combo_is_the_sum_of_its_box_numbers(self):
        got = rules("console.log(JSON.stringify(['points', 'rebounds', 'assists', 'threes', 'pra', 'pr', 'pa', 'ra'].map(function (k) { return trkValue('nba', k, %s); })));" % json.dumps(self.NBA_ROW))
        self.assertEqual(got, [20, 8, 5, 3, 33, 28, 25, 13])

    def test_nhl_stats_include_goals_assists_and_points_as_their_sum(self):
        row = {"dnp": False, "shots": 4, "goals": 1, "assists": 2}
        got = rules("console.log(JSON.stringify(['shots', 'goals', 'assists', 'points'].map(function (k) { return trkValue('nhl', k, %s); })));" % json.dumps(row))
        self.assertEqual(got, [4, 1, 2, 3])

    def test_a_missing_part_or_a_player_who_did_not_play_is_unavailable_never_zero(self):
        part_missing = dict(self.NBA_ROW, rebounds=None)
        got = rules("""console.log(JSON.stringify([trkValue('nba', 'pra', %s), trkValue('nba', 'pa', %s), trkValue('nba', 'points', %s),
          trkValue('nba', 'pra', { dnp: true, points: 0, rebounds: 0, assists: 0 }), trkValue('nba', 'points', null), trkValue('nba', 'bogus', %s), trkValue('nhl', 'points', { shots: 3, goals: 1 })]));"""
                    % (json.dumps(part_missing), json.dumps(part_missing), json.dumps(part_missing), json.dumps(self.NBA_ROW)))
        self.assertEqual(got, [None, 25, 20, None, None, None, None])

    def test_the_pickers_offer_exactly_the_stats_the_feed_parses(self):
        got = rules("console.log(JSON.stringify([trkStats('nba').map(function (s) { return s.label + '/' + s.grp; }), trkStats('nhl').map(function (s) { return s.label + '/' + s.grp; })]));")
        self.assertEqual(got[0], ["Points/Singles", "Rebounds/Singles", "Assists/Singles", "3-pointers made/Singles", "Pts + Reb + Ast/Combos", "Pts + Reb/Combos", "Pts + Ast/Combos", "Reb + Ast/Combos"])
        self.assertEqual(got[1], ["Shots on goal/Singles", "Goals/Singles", "Assists/Singles", "Points/Combos"])

    def test_a_combo_reads_as_its_name_and_the_sum(self):
        got = rules("console.log(JSON.stringify([trkBetText({ sport: 'nba', stat: 'pra', side: 'over', line: 38.5 }), trkBetText({ sport: 'nhl', stat: 'shots', side: 'under', line: 2.5 })]));")
        self.assertEqual(got, ["Over 38.5 PRA", "Under 2.5 shots on goal"])


@unittest.skipUnless(shutil.which("node"), "node not installed")
class Results(unittest.TestCase):
    def result(self, side, line, stat, dnp=False, final=False):
        got = rules("console.log(JSON.stringify(trkResult({ side: %s, line: %s }, %s, %s, %s)));" % (json.dumps(side), line, "null" if stat is None else stat, json.dumps(dnp), json.dumps(final)))
        return got

    def test_over_hits_the_moment_the_number_passes_the_line(self):
        self.assertEqual(self.result("over", 24.5, 25), "W")
        self.assertIsNone(self.result("over", 24.5, 24))
        self.assertEqual(self.result("over", 24.5, 24, final=True), "L")

    def test_under_is_lost_the_moment_the_number_passes_and_only_hits_at_the_final(self):
        self.assertEqual(self.result("under", 24.5, 25), "L")
        self.assertIsNone(self.result("under", 24.5, 20))
        self.assertEqual(self.result("under", 24.5, 20, final=True), "W")

    def test_a_whole_line_met_at_the_final_is_a_push_either_side(self):
        self.assertEqual(self.result("over", 24, 24, final=True), "PUSH")
        self.assertEqual(self.result("under", 24, 24, final=True), "PUSH")
        self.assertIsNone(self.result("over", 24, 24))

    def test_no_play_at_the_final_is_void_and_no_number_mid_game_is_open(self):
        self.assertEqual(self.result("over", 10.5, None, dnp=True, final=True), "VOID")
        self.assertIsNone(self.result("over", 10.5, None, dnp=True))
        self.assertIsNone(self.result("over", 10.5, None, final=False))
        self.assertIsNone(self.result("over", 10.5, None, final=True))

    def test_combo_lines_follow_the_same_rules_on_the_sum(self):
        got = rules("""var b = { sport: 'nba', stat: 'pra', side: 'over', line: 38.5 }, row = { dnp: false, points: 20, rebounds: 10, assists: 9 };
          console.log(JSON.stringify([trkResult(b, trkValue('nba', 'pra', row), false, false), trkResult({ sport: 'nba', stat: 'pra', side: 'under', line: 39 }, trkValue('nba', 'pra', row), false, true)]));""")
        self.assertEqual(got, ["W", "PUSH"])


@unittest.skipUnless(shutil.which("node"), "node not installed")
class LineAndParlayRules(unittest.TestCase):
    def check(self, text):
        return rules("console.log(JSON.stringify(trkLineCheck(%s)));" % json.dumps(text))

    def test_line_messages_and_accepted_values(self):
        self.assertEqual(self.check("")["err"], "Enter a line.")
        self.assertEqual(self.check("abc")["err"], "Use a number like 24.5.")
        self.assertEqual(self.check("24.5.5")["err"], "Use a number like 24.5.")
        self.assertEqual(self.check("24.25")["err"], "Use .0 or .5 lines.")
        for bad in ("0", "200", "199.75", "0.25"):
            self.assertIn(self.check(bad)["err"], ("Pick a line from 0.5 to 199.5.", "Use .0 or .5 lines."), bad)
        self.assertEqual(self.check("0")["err"], "Pick a line from 0.5 to 199.5.")
        self.assertEqual(self.check("200")["err"], "Pick a line from 0.5 to 199.5.")
        for good, value in (("24.5", 24.5), ("25", 25), ("0.5", 0.5), ("199.5", 199.5), (" 7 ", 7)):
            self.assertEqual(self.check(good), {"value": value}, good)

    def test_stepper_moves_half_a_point_and_clamps_at_both_ends(self):
        got = rules("console.log(JSON.stringify([trkStepLine('24.5', 1), trkStepLine('24.5', -1), trkStepLine('', 1), trkStepLine('0.5', -1), trkStepLine('199.5', 1), trkStepLine('x', -1)]));")
        self.assertEqual(got, ["25", "24", "0.5", "0.5", "199.5", "0.5"])

    def test_parlay_status_truth_table(self):
        cases = {
            "[null, null]": ("ALIVE", "0 of 2 hit"),
            "['W', null, null]": ("ALIVE", "1 of 3 hit"),
            "['W', 'W']": ("ALL HIT", "2 of 2 hit"),
            "['W', 'L', null]": ("DEAD", "Leg 2 lost. Parlay is dead."),
            "['L', 'L']": ("DEAD", "Leg 1 lost. Parlay is dead."),
            "['W', 'VOID', 'W']": ("ALL HIT", "2 of 2 hit"),
            "['W', 'PUSH', null]": ("ALIVE", "1 of 2 hit"),
            "['VOID', 'PUSH']": ("PUSH", "Every leg pushed or void."),
            "['VOID', 'L']": ("DEAD", "Leg 2 lost. Parlay is dead."),
        }
        for legs, (word, text) in cases.items():
            got = rules("console.log(JSON.stringify(trkParlayStatus(%s)));" % legs)
            self.assertEqual((got["word"], got["text"]), (word, text), legs)

    def test_a_dropped_leg_leaves_a_smaller_parlay(self):
        got = rules("console.log(JSON.stringify(trkParlayStatus(['W', 'VOID', null])));")
        self.assertEqual((got["live"], got["dropped"], got["hit"]), (2, 1, 1))

    def test_the_same_player_and_stat_twice_is_refused_even_on_the_other_side(self):
        a = {"sport": "nba", "pid": "1", "name": "Nikola Jokić", "stat": "points", "side": "over", "line": 24.5}
        got = rules("""var a = %s, b = Object.assign({}, a, { side: 'under', line: 30.5 }), c = Object.assign({}, a, { stat: 'rebounds' }), d = Object.assign({}, a, { pid: '', name: 'Nikola Jokic' });
          console.log(JSON.stringify([trkConflict([a, b]), trkConflict([a, c]), trkConflict([a, d]), trkConflict([a, b, c])]));""" % json.dumps(a))
        self.assertEqual(got, [True, False, True, True])

    def test_a_duplicate_is_only_blocked_while_the_first_is_in_play(self):
        got = rules("""var a = { id: 'a', sport: 'nba', pid: '1', name: 'X Y', stat: 'points', side: 'over', line: 24.5, settled: null };
          var c = { id: 'new', sport: 'nba', pid: '1', name: 'X Y', stat: 'points', side: 'over', line: 24.5 };
          var done = Object.assign({}, a, { settled: { result: 'W' } });
          console.log(JSON.stringify([trkDuplicate([a], c), trkDuplicate([done], c), trkDuplicate([a], Object.assign({}, c, { line: 25.5 })), trkDuplicate([a], a)]));""")
        self.assertEqual(got, [True, False, False, False])

    def test_the_page_caps_a_parlay_at_three_legs_and_a_tracker_at_twenty_bets(self):
        got = rules("console.log(JSON.stringify([TRK_MAX_LEGS, TRK_MAX_BETS, TRK_MAX_PARLAYS]));")
        self.assertEqual(got, [3, 20, 6])


@unittest.skipUnless(shutil.which("node"), "node not installed")
class SavedData(unittest.TestCase):
    def bet(self, i, day, **kw):
        b = {"id": i, "sport": "nba", "gameDay": day, "gameKey": "nba|DEN@PHX", "pid": "1", "name": "Nikola Jokić", "team": "DEN", "opp": "PHX", "home": False, "stat": "points", "side": "over", "line": 24.5, "createdAt": 1}
        b.update(kw)
        return b

    def sanitize(self, raw, today=DAY):
        return rules("console.log(JSON.stringify(trkSanitize(%s, %s)));" % (json.dumps(raw), json.dumps(today)))

    def test_bets_older_than_two_days_are_dropped_at_open(self):
        raw = {"bets": [self.bet("a", "2026-11-23"), self.bet("b", "2026-11-22"), self.bet("c", "2026-11-21"), self.bet("d", "2026-11-20")], "parlays": []}
        self.assertEqual([b["id"] for b in self.sanitize(raw)["bets"]], ["a", "b", "c"])

    def test_rollover_changes_the_day_not_the_bets(self):
        raw = {"bets": [self.bet("a", "2026-11-23")], "parlays": []}
        self.assertEqual(len(self.sanitize(raw, "2026-11-24")["bets"]), 1)
        self.assertEqual(len(self.sanitize(raw, "2026-11-25")["bets"]), 1)
        self.assertEqual(len(self.sanitize(raw, "2026-11-26")["bets"]), 0)

    def test_malformed_bets_and_parlays_are_dropped_never_thrown(self):
        raw = {"bets": [self.bet("a", DAY), self.bet("b", DAY, line=24.25), self.bet("c", DAY, stat="steals"), self.bet("d", DAY, side="push"), self.bet("e", DAY, sport="mlb"),
                        self.bet("f", DAY, gameKey="x"), self.bet("a", DAY), "junk", None, self.bet("g", DAY, settled={"result": "WIN"}), self.bet("h", DAY, name="  ")],
               "parlays": [{"id": "p", "legIds": ["a", "zzz"]}, "junk"]}
        out = self.sanitize(raw)
        self.assertEqual([b["id"] for b in out["bets"]], ["a"])
        self.assertEqual(out["parlays"], [])
        self.assertEqual(self.sanitize("nonsense")["bets"], [])

    def test_a_saved_parlay_keeps_its_legs_only_when_valid(self):
        legs = [self.bet("a", DAY), self.bet("b", DAY, stat="rebounds"), self.bet("c", DAY, stat="assists"), self.bet("d", DAY, stat="threes")]
        ok = self.sanitize({"bets": legs, "parlays": [{"id": "p", "legIds": ["a", "b"]}]})
        self.assertEqual(ok["parlays"][0]["legIds"], ["a", "b"])
        self.assertEqual({b["id"]: b["parlayId"] for b in ok["bets"]}, {"a": "p", "b": "p", "c": None, "d": None})
        for parlays in ([{"id": "p", "legIds": ["a"]}], [{"id": "p", "legIds": ["a", "b", "c", "d"]}], [{"id": "p", "legIds": ["a", "a"]}],
                        [{"id": "p", "legIds": ["a", "b"]}, {"id": "q", "legIds": ["b", "c"]}]):
            out = self.sanitize({"bets": legs, "parlays": parlays})
            self.assertLessEqual(len(out["parlays"]), 1, parlays)
        same = self.sanitize({"bets": [self.bet("a", DAY), self.bet("b", DAY, side="under", line=30.5)], "parlays": [{"id": "p", "legIds": ["a", "b"]}]})
        self.assertEqual(same["parlays"], [])

    def test_only_twenty_bets_are_kept(self):
        raw = {"bets": [self.bet("b%d" % i, DAY) for i in range(30)], "parlays": []}
        self.assertEqual(len(self.sanitize(raw)["bets"]), 20)

    def test_settled_results_survive_a_round_trip(self):
        raw = {"bets": [self.bet("a", DAY, settled={"result": "W", "actual": 27, "at": 5, "manual": False})], "parlays": []}
        self.assertEqual(self.sanitize(raw)["bets"][0]["settled"], {"result": "W", "actual": 27, "at": 5, "manual": False, "why": ""})


@unittest.skipUnless(shutil.which("node"), "node not installed")
class BoxMatching(unittest.TestCase):
    def match(self, sport, bet, rows):
        return rules("""var idx = trkBoxIndex(%s, %s), r = trkRowFor(%s, idx); console.log(JSON.stringify(r ? r.name : null));""" % (json.dumps(sport), json.dumps(rows), json.dumps(bet)))

    def test_nba_matches_by_athlete_id_then_by_team_and_name_ignoring_accents_and_suffixes(self):
        rows = [{"id": "11", "name": "Nikola Jokić", "team": "DEN"}, {"id": "12", "name": "Jaren Jackson Jr.", "team": "MEM"}, {"id": "", "name": "Wendell Carter Jr", "team": "ORL"}]
        self.assertEqual(self.match("nba", {"sport": "nba", "pid": "11", "name": "Whoever", "team": "DEN"}, rows), "Nikola Jokić")
        self.assertEqual(self.match("nba", {"sport": "nba", "pid": "", "name": "Nikola Jokic", "team": "DEN"}, rows), "Nikola Jokić")
        self.assertEqual(self.match("nba", {"sport": "nba", "pid": "", "name": "Jaren Jackson", "team": "MEM"}, rows), "Jaren Jackson Jr.")
        self.assertEqual(self.match("nba", {"sport": "nba", "pid": "", "name": "Wendell Carter Jr.", "team": "ORL"}, rows), "Wendell Carter Jr")

    def test_a_player_who_is_not_in_the_box_is_unmatched_not_someone_else(self):
        rows = [{"id": "11", "name": "Nikola Jokić", "team": "DEN"}]
        self.assertIsNone(self.match("nba", {"sport": "nba", "pid": "99", "name": "Zzyzx Nomatch", "team": "DEN"}, rows))
        self.assertIsNone(self.match("nba", {"sport": "nba", "pid": "", "name": "Nikola Jokic", "team": "PHX"}, rows))

    def test_nhl_matches_by_team_and_first_initial_plus_last_name_and_two_of_a_kind_match_nobody(self):
        rows = [{"id": "5", "name": "Nikita Kucherov", "team": "TBL"}, {"id": "6", "name": "Sam Reinhart", "team": "FLA"}, {"id": "7", "name": "Sam Roy", "team": "FLA"},
                {"id": "8", "name": "Elias Pettersson", "team": "VAN"}, {"id": "9", "name": "Emil Pettersson", "team": "VAN"}]
        self.assertEqual(self.match("nhl", {"sport": "nhl", "pid": "8476453", "name": "Nikita Kucherov", "team": "TB"}, rows), "Nikita Kucherov")
        self.assertIsNone(self.match("nhl", {"sport": "nhl", "pid": "1", "name": "Elias Pettersson", "team": "VAN"}, rows))

    def test_search_matches_names_without_accents_team_codes_and_team_names(self):
        def hit(p, q):
            return rules("console.log(JSON.stringify(trkMatches(%s, %s)));" % (json.dumps(p), json.dumps(q)))
        jokic = {"sport": "nba", "name": "Nikola Jokić", "team": "DEN"}
        tatum = {"sport": "nba", "name": "Jayson Tatum", "team": "BOS"}
        bruin = {"sport": "nhl", "name": "David Pastrnak", "team": "BOS"}
        self.assertTrue(hit(jokic, "jokic"))
        self.assertTrue(hit(jokic, "NIKOLA jok"))
        self.assertTrue(hit(jokic, "den"))
        self.assertTrue(hit(jokic, "nuggets"))
        self.assertTrue(hit(tatum, "bos") and hit(bruin, "bos"))
        self.assertTrue(hit(tatum, "celtics") and not hit(bruin, "celtics") and hit(bruin, "bruins"))
        self.assertFalse(hit(jokic, "tatum"))


@unittest.skipUnless(shutil.which("node"), "node not installed")
class PollingRules(unittest.TestCase):
    FNS = ("trkWanted", "trkPlan", "trkGo", "trkClear", "trkStop", "trkPast")

    def run_js(self, body):
        got, err = run_page_js(self.FNS, body, ("LIVE_MS",))
        self.assertEqual(err, "")
        return got

    def test_it_polls_without_any_pick_slate_and_both_sports_at_once(self):
        got = self.run_js("""var S = { view: 'live', slate: null }, document = { hidden: false }, TK = { bets: [{ sport: 'nba', gameKey: 'nba|A@B', gameDay: '2026-11-23', settled: null }, { sport: 'nhl', gameKey: 'nhl|C@D', gameDay: '2026-11-23', settled: null }], done: {}, sheet: null };
          function trkDay() { return '2026-11-23'; }
          console.log(JSON.stringify(trkPlan().sports));""")
        self.assertEqual(got, ["nba", "nhl"])

    def test_a_game_that_is_done_or_a_manually_marked_bet_is_not_polled(self):
        got = self.run_js("""var TK = { bets: [{ sport: 'nba', gameKey: 'nba|A@B', gameDay: '2026-11-23', settled: null }, { sport: 'nhl', gameKey: 'nhl|C@D', gameDay: '2026-11-23', settled: { manual: true } },
            { sport: 'nba', gameKey: 'nba|E@F', gameDay: '2026-11-22', settled: null }], done: { 'nba|A@B': 1 }, sheet: null };
          function trkDay() { return '2026-11-23'; }
          console.log(JSON.stringify(trkPlan().sports));""")
        self.assertEqual(got, [])

    def test_the_create_sheet_reads_the_scoreboards_for_its_game_list(self):
        got = self.run_js("""var TK = { bets: [], done: {}, sheet: { player: null } }; function trkDay() { return '2026-11-23'; }
          console.log(JSON.stringify(trkPlan().sports));""")
        self.assertEqual(got, ["nba", "nhl"])

    def test_nothing_polls_off_the_live_tab_or_while_the_page_is_hidden(self):
        got = self.run_js("""var polls = 0, S = { view: 'picks' }, document = { hidden: false }, TK = { bets: [{ sport: 'nba', gameKey: 'nba|A@B', gameDay: '2026-11-23', settled: null }], done: {}, sheet: null, busy: false, next: null, lastTry: null };
          function trkDay() { return '2026-11-23'; } function trkPoll() { polls++; }
          trkGo(true); var offLive = polls; S.view = 'live'; document.hidden = true; trkGo(true); var hidden = polls; document.hidden = false; trkGo(true);
          console.log(JSON.stringify([offLive, hidden, polls]));""")
        self.assertEqual(got, [0, 0, 1])

    def test_never_more_than_one_poll_in_flight_and_the_cadence_is_the_pick_polls_ten_seconds(self):
        got = self.run_js("""var polls = 0, S = { view: 'live' }, document = { hidden: false }, TK = { bets: [{ sport: 'nba', gameKey: 'nba|A@B', gameDay: '2026-11-23', settled: null }], done: {}, sheet: null, busy: true, next: null, lastTry: null };
          function trkDay() { return '2026-11-23'; } function trkPoll() { polls++; }
          trkGo(true); console.log(JSON.stringify([polls, LIVE_MS]));""")
        self.assertEqual(got, [0, 10000])
        self.assertIn("var LIVE_MS = 10000", page_source())
        self.assertIn("setTimeout(trkPoll, LIVE_MS)", tracker_source())


@unittest.skipUnless(shutil.which("node"), "node not installed")
class Recheck(unittest.TestCase):
    FNS = ("trkRecheck", "trkRowFor", "trkValue", "trkResult", "trkBoxIndex", "trkStat", "trkStats", "trkNameKey", "trkTeam", "tri", "nhlTeam", "normName", "nhlNameKey", "str", "num", "arr", "isObj")

    def run_js(self, feed):
        body = """var FIX = false, TK = { demo: false, rechecked: false, bets: [
            { id: 'a', sport: 'nba', gameDay: '2026-11-22', gameKey: 'nba|DEN@PHX', pid: '1', name: 'A One', team: 'DEN', stat: 'points', side: 'over', line: 20.5, settled: null },
            { id: 'b', sport: 'nba', gameDay: '2026-11-22', gameKey: 'nba|DEN@PHX', pid: '2', name: 'B Two', team: 'DEN', stat: 'points', side: 'over', line: 10.5, settled: null },
            { id: 'c', sport: 'nba', gameDay: '2026-11-22', gameKey: 'nba|BOS@MIA', pid: '3', name: 'C Three', team: 'BOS', stat: 'points', side: 'over', line: 10.5, settled: null },
            { id: 'd', sport: 'nba', gameDay: '2026-11-22', gameKey: 'nba|NYK@WAS', pid: '4', name: 'D Four', team: 'NYK', stat: 'points', side: 'over', line: 10.5, settled: null },
            { id: 'e', sport: 'nba', gameDay: '2026-11-23', gameKey: 'nba|LAL@DAL', pid: '5', name: 'E Five', team: 'LAL', stat: 'points', side: 'over', line: 10.5, settled: null }] };
          function trkDay() { return '2026-11-23'; } function trkSave() {} function trkRerender() {}
          var calls = []; function trkEspnFeed(sp, day, need) { calls.push(day + ':' + need.join()); return %s; }
          trkRecheck(); trkRecheck();
          setTimeout(function () { console.log(JSON.stringify({ calls: calls, bets: TK.bets.map(function (b) { return [b.id, b.settled && b.settled.result, b.settled && b.settled.actual, b.settled && b.settled.why]; }) })); }, 20);""" % feed
        got, err = run_page_js(self.FNS, body, ("TRK_NBA", "TRK_NHL", "NBA_TRI", "NHL_TEAM"))
        self.assertEqual(err, "")
        return got

    def test_an_unsettled_bet_from_an_earlier_day_is_rechecked_once_against_that_days_box(self):
        feed = """Promise.resolve({ games: { 'nba|DEN@PHX': { state: 'post' }, 'nba|BOS@MIA': { state: 'in' }, 'nba|NYK@WAS': { state: 'post' } },
          boxes: { 'nba|DEN@PHX': trkBoxIndex('nba', [{ id: '1', name: 'A One', team: 'DEN', dnp: false, points: 25 }, { id: '2', name: 'B Two', team: 'DEN', dnp: true }]), 'nba|NYK@WAS': trkBoxIndex('nba', [{ id: '9', name: 'Other', team: 'NYK', points: 3 }]) } })"""
        got = self.run_js(feed)
        self.assertEqual(got["calls"], ["2026-11-22:nba|DEN@PHX,nba|BOS@MIA,nba|NYK@WAS"])
        by = {b[0]: b[1:] for b in got["bets"]}
        self.assertEqual(by["a"], ["W", 25, ""])
        self.assertEqual(by["b"], ["VOID", None, "dnp"])
        self.assertEqual(by["c"], ["VOID", None, "unfinished"])
        self.assertEqual(by["d"], [None, None, None])  # final, but he is not in the box: stays unresolved for Matt to mark
        self.assertEqual(by["e"], [None, None, None])  # today's bet is not part of the recheck

    def test_a_feed_that_cannot_confirm_leaves_every_bet_unresolved(self):
        got = self.run_js("Promise.reject(new Error('net'))")
        self.assertTrue(all(b[1] is None for b in got["bets"]))


class IsolationInSource(unittest.TestCase):
    def test_the_tracker_never_touches_picks_the_record_discord_or_workflows(self):
        src = re.sub(r"/\*.*?\*/", "", tracker_source(), flags=re.S)
        for banned in ("S.record", "S.rules", "record.json", "slate.json", "rules.json", "discord", "Discord", "status.json", "S.slate.picks", "split()", "livePlan", "writeSeen", "L.stats", "L.games"):
            self.assertNotIn(banned, src, banned)

    def test_the_only_things_it_stores_are_its_own_two_keys(self):
        src = tracker_source()
        self.assertEqual(sorted(set(re.findall(r"localStorage\.(?:setItem|removeItem)\(([A-Za-z_]+)", src))), ["TRK_KEY", "TRK_SEG_KEY"])
        self.assertIn("var TRK_KEY = FIX ? 'hph.tracker.fx.v1' : 'hph.tracker.v1';", src)
        self.assertIn("var TRK_SEG_KEY = 'hph.live.seg';", src)

    def test_the_only_data_file_it_reads_is_the_odds_list_and_it_never_writes_to_the_network(self):
        src = tracker_source()
        self.assertEqual(re.findall(r"getJSON\(([^)]*)\)", src), ["BASE_FIX + 'tracker.json'", "SPORT_BASES[sp] + 'data/odds/' + day + '.json'"])
        self.assertNotRegex(src, r"method\s*:\s*['\"](POST|PUT|PATCH|DELETE)")
        self.assertNotIn("sendBeacon", src)

    def test_the_pick_poll_and_its_cadence_are_not_changed(self):
        src = page_source()
        self.assertIn("function liveWanted() { return (S.view === 'live' || S.view === 'lab') && !document.hidden && !!S.slate && !expired(); }", src)
        self.assertIn("if (pl.need.length) { L.stopped = false; L.next = setTimeout(livePoll, LIVE_MS); return; }", src)


def seed(bets, parlays=(), day=DAY):
    """An init script that puts a saved tracker on the phone once (a reload keeps what the page saved since)."""
    data = json.dumps({"v": 1, "bets": list(bets), "parlays": list(parlays), "day": day})
    return "if (!localStorage.getItem('%s')) localStorage.setItem('%s', %s);" % (TRK_KEY, TRK_KEY, json.dumps(data))


def bet(i, name, team, opp, key, stat, side, line, pid="", sport="nba", day=DAY, settled=None, home=False):
    return {"id": i, "sport": sport, "gameDay": day, "gameKey": key, "pid": pid, "name": name, "team": team, "opp": opp, "home": home, "stat": stat, "side": side, "line": line,
            "createdAt": 1795400000000 + len(i), "settled": settled}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@unittest.skipUnless(sync_playwright, "playwright not installed")
class Screens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(QuietHandler, directory=ROOT)
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.play = sync_playwright().start()
        try:
            cls.browser = cls.play.chromium.launch()
        except Exception as err:
            cls.play.stop()
            cls.server.shutdown()
            raise unittest.SkipTest("chromium not available: %s" % str(err).splitlines()[0])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.play.stop()
        cls.server.shutdown()

    def open(self, init="", query="", seg="tracker", sport="nba", width=380, hash_="#live"):
        ctx = self.browser.new_context(viewport={"width": width, "height": 900})
        page = ctx.new_page()
        page.errors = []
        page.on("pageerror", lambda e: page.errors.append(str(e)))
        page.requests = []
        page.on("request", lambda r: page.requests.append(r.url))
        seg_js = "localStorage.setItem('%s', '%s');" % (SEG_KEY, seg) if seg else ""
        page.add_init_script("localStorage.setItem('pc_sport', '%s');%s%s" % (sport, seg_js, init))
        page.goto("http://127.0.0.1:%d/index.html?fixture=livelong%s%s" % (self.server.server_address[1], query, hash_))
        page.wait_for_selector(".trkseg")
        page.wait_for_timeout(900)
        self.addCleanup(ctx.close)
        return page

    def text(self, page, sel="#app"):
        return page.inner_text(sel)

    def open_sheet(self, page):
        page.click(".trkadd")
        page.wait_for_selector("#trk-sheet .trkpr")

    def pick(self, page, name):
        page.locator("#trk-sheet .trkpr", has_text=name).first.click()
        page.wait_for_selector("#trk-sheet .trkchip[aria-pressed]")

    def build(self, page, name, stat_label, side, line):
        self.open_sheet(page)
        self.pick(page, name)
        page.locator("#trk-sheet .trkchip", has_text=re.compile("^%s$" % re.escape(stat_label))).click()
        page.locator("#trk-sheet .trkseg2 button", has_text=side).click()
        page.fill("#trk-sheet input[aria-label=Line]", line)

    def add(self, page):
        page.click("#trk-sheet .trks-f .trkadd")
        page.wait_for_selector("#trk-sheet", state="detached")
        page.wait_for_timeout(300)

    # placement and separation
    def test_live_opens_on_our_picks_and_remembers_the_last_choice(self):
        page = self.open(seg=None)
        self.assertEqual(page.get_attribute(".trkseg button:nth-child(1)", "aria-pressed"), "true")
        self.assertEqual(page.locator("#app .mine").count(), 0)
        self.assertIn("Tonight", self.text(page, ".tonight"))
        page.click(".trkseg button:nth-child(2)")
        page.wait_for_selector(".trkban")
        self.assertEqual(page.evaluate("localStorage.getItem('%s')" % SEG_KEY), "tracker")
        page.reload()
        page.wait_for_selector(".trkban")
        page.click(".trkseg button:nth-child(1)")
        page.wait_for_selector(".tonight")
        self.assertEqual(page.evaluate("localStorage.getItem('%s')" % SEG_KEY), "picks")

    def test_the_tracker_deep_link_opens_my_tracker(self):
        page = self.open(seg=None, hash_="#tracker")
        self.assertEqual(page.get_attribute(".trkseg button:nth-child(2)", "aria-pressed"), "true")
        self.assertEqual(page.locator(".tonight").count(), 0)

    def test_the_banner_and_the_one_line_note_and_no_pick_numbers(self):
        page = self.open(query="&trk=demo")
        self.assertIn("MY TRACKER. Your own notes. Not a Hot Prop Homies pick. Not on the Record.", self.text(page, ".trkban"))
        self.assertIn("My Tracker shows both sports.", self.text(page))
        page = self.open(query="&trk=demo", sport="all")
        self.assertNotIn("My Tracker shows both sports.", self.text(page))
        app = self.text(page)
        self.assertEqual(page.locator("#app .tile.trk, #app .pcard").first.evaluate("e => getComputedStyle(e).borderTopStyle"), "dashed")
        for word in ("EV", "units", "Hard Rock", "%"):
            self.assertNotRegex(app, r"\b%s\b" % re.escape(word) if word.isalpha() else re.escape(word), word)
        self.assertEqual(page.locator("#app .trk:not(.pcard .trk) .mine").count(), page.locator("#app .tile.trk").count())

    def test_the_header_sport_switch_does_not_filter_my_tracker(self):
        texts = []
        for sport in ("all", "nba", "nhl"):
            page = self.open(query="&trk=demo", sport=sport)
            texts.append(re.sub(r"\s+", " ", re.sub(r"Updated \d+s ago", "", self.text(page).replace("My Tracker shows both sports.", ""))))
        self.assertEqual(texts[0], texts[1])
        self.assertEqual(texts[1], texts[2])

    def test_our_picks_and_the_tonight_line_are_unchanged_with_a_tracker_full_of_bets(self):
        plain = self.open(seg="picks")
        full = self.open(seg="picks", query="&trk=demo")
        self.assertEqual(self.text(plain, ".tonight"), self.text(full, ".tonight"))
        self.assertEqual(full.locator("#app .tile.trk, #app .pcard, .trkban").count(), 0)
        self.assertEqual(plain.locator("#app .tile").count(), full.locator("#app .tile").count())

    # the states the demo seed shows
    def test_the_demo_seed_shows_every_state(self):
        page = self.open(query="&trk=demo")
        app = self.text(page)
        for want in ("Not started yet", "No stats yet" if False else "Can't find him in the live numbers.", "HIT", "LOST", "PUSH", "VOID", "Did not play", "ALIVE", "DEAD", "Leg 3 lost. Parlay is dead.",
                     "Over 38.5 PRA", "26 / 38.5 PRA", "Under 40.5 PR", "Over 1.5 points", "Yesterday (2)", "Tonight's tracker: 2 hit, 2 missed."):
            self.assertIn(want, app, want)
        self.assertEqual(page.locator("#app .pcard").count(), 2)
        self.assertEqual(page.evaluate("localStorage.getItem('%s')" % TRK_KEY), None)  # the demo is never saved

    def test_a_demo_is_inert_without_the_fixture_flag(self):
        page = self.open(query="")
        self.assertIn("Nothing tracked yet.", self.text(page))
        self.assertIn("Stays on this phone only.", self.text(page))
        self.assertIn("var TRK_KEY = FIX", page_source())
        self.assertIn("if (FIX) {", tracker_source())

    def test_yesterday_is_collapsed_and_opens_read_only(self):
        page = self.open(query="&trk=demo")
        self.assertEqual(page.locator(".trkyd").get_attribute("aria-expanded"), "false")
        self.assertNotIn("Luka", self.text(page))
        page.click(".trkyd")
        page.wait_for_selector("#app .trklist:last-of-type .tile")
        self.assertIn("Luka Dončić", self.text(page))
        self.assertIn("Final not saved. Mark it yourself.", self.text(page))
        self.assertEqual(page.locator(".trklist:last-of-type .tile button.trkn").count(), 0)

    def test_marking_an_unresolved_bet_saves_hit_or_missed(self):
        luka = bet("y1", "Luka Dončić", "LAL", "DAL", "nba|LAL@DAL", "points", "over", 29.5, day="2026-11-22")
        page = self.open(init=seed([luka]))
        page.click(".trkyd")
        page.click("text=Hit")
        page.wait_for_selector(".stmp.W")
        page.wait_for_timeout(500)
        self.assertEqual(json.loads(page.evaluate("localStorage.getItem('%s')" % TRK_KEY))["bets"][0]["settled"]["result"], "W")
        self.assertTrue(json.loads(page.evaluate("localStorage.getItem('%s')" % TRK_KEY))["bets"][0]["settled"]["manual"])

    # rollover and expiry
    def test_rollover_groups_yesterday_and_the_open_drops_what_is_older_than_two_days(self):
        done = {"result": "W", "actual": 13, "at": 1, "manual": False, "why": ""}
        bets = [bet("t1", "Jalen Brunson", "NYK", "WAS", "nba|NYK@WAS", "assists", "over", 5.5, pid="3934672"),
                bet("y1", "Nikola Jokić", "DEN", "UTA", "nba|DEN@UTA", "rebounds", "over", 11.5, day="2026-11-22", settled=done),
                bet("y2", "Devin Booker", "PHX", "DEN", "nba|DEN@PHX", "points", "over", 20.5, day="2026-11-21", settled=done),
                bet("old", "Old Timer", "DEN", "UTA", "nba|DEN@UTA", "points", "over", 20.5, day="2026-11-20", settled=done)]
        page = self.open(init=seed(bets))
        self.assertIn("Yesterday (2)", self.text(page))
        self.assertNotIn("Old Timer", self.text(page))
        page.click(".trkyd")
        self.assertIn("Nikola Jokić", self.text(page))
        saved = json.loads(page.evaluate("localStorage.getItem('%s')" % TRK_KEY))
        self.assertEqual(sorted(b["id"] for b in saved["bets"]), ["t1", "y1", "y2"])

    def test_clear_finished_removes_them_and_undo_brings_them_back(self):
        done = {"result": "W", "actual": 13, "at": 1, "manual": False, "why": ""}
        bets = [bet("t1", "Jalen Brunson", "NYK", "WAS", "nba|NYK@WAS", "assists", "over", 5.5, pid="3934672"),
                bet("t2", "Nikola Jokić", "DEN", "PHX", "nba|DEN@PHX", "assists", "over", 9.5, pid="3112335"),
                bet("y1", "Nikola Jokić", "DEN", "UTA", "nba|DEN@UTA", "rebounds", "over", 11.5, day="2026-11-22", settled=done)]
        page = self.open(init=seed(bets))
        page.click("text=Clear finished")
        page.wait_for_selector("#trk-toast:not([hidden])")
        self.assertIn("Cleared.", self.text(page, "#trk-toast"))
        self.assertNotIn("Yesterday", self.text(page))
        self.assertEqual(page.locator("#app .tile.trk").count(), 1)
        page.click("#trk-toast .trkt-u")
        page.wait_for_selector(".trkyd")
        self.assertEqual(page.locator("#app .tile.trk").count(), 2)

    # creating
    def test_the_picker_lists_games_live_first_then_upcoming_then_final_and_filters(self):
        page = self.open()
        self.open_sheet(page)
        heads = page.locator("#trk-sheet .trkgh").all_inner_texts()
        self.assertEqual([h.split(".")[1].strip().split(",")[0].split(" ")[0] for h in heads], ["Live", "Live", "Live", "Starts", "Starts", "Final"])
        self.assertIn("Final", heads[-1])
        page.fill("#trk-sheet .srch", "jokic")
        self.assertEqual(page.locator("#trk-sheet .trkpname").all_inner_texts(), ["Nikola Jokić"])
        page.fill("#trk-sheet .srch", "bos")
        self.assertEqual(sorted(page.locator("#trk-sheet .trkpname").all_inner_texts()), ["Jayson Tatum"])
        page.fill("#trk-sheet .srch", "bruins")
        self.assertEqual(page.locator("#trk-sheet .trkpname").count(), 0)
        page.fill("#trk-sheet .srch", "zzzz")
        self.assertIn("No player named that tonight. Check the spelling, or try a team.", self.text(page, "#trk-sheet"))
        page.click("text=Clear search")
        page.click("#trk-sheet .trkchip:has-text('NHL')")
        names = page.locator("#trk-sheet .trkpname").all_inner_texts()
        self.assertEqual(sorted(names), ["Auston Matthews", "Nikita Kucherov", "Sebastian Aho"])

    def test_a_finished_game_cannot_be_added(self):
        page = self.open()
        self.open_sheet(page)
        page.locator("#trk-sheet .trkpr", has_text="Jalen Brunson").click()
        self.assertIn("That game is over.", self.text(page, "#trk-sheet"))
        self.assertEqual(page.locator("#trk-sheet .trkchip[aria-pressed]").count(), 3)  # still the sport chips on step one

    def test_each_sport_offers_only_its_own_stats_grouped_singles_and_combos(self):
        page = self.open()
        self.open_sheet(page)
        self.pick(page, "Nikola Jokić")
        self.assertEqual(page.locator("#trk-sheet .trkchip").all_inner_texts(), ["Points", "Rebounds", "Assists", "3-pointers made", "Pts + Reb + Ast", "Pts + Reb", "Pts + Ast", "Reb + Ast"])
        self.assertEqual(page.locator("#trk-sheet .trkgl").all_inner_texts(), ["Singles", "Combos"])
        page.click("#trk-sheet .trks-bk")
        page.fill("#trk-sheet .srch", "kucherov")
        self.pick(page, "Nikita Kucherov")
        self.assertEqual(page.locator("#trk-sheet .trkchip").all_inner_texts(), ["Shots on goal", "Goals", "Assists", "Points"])
        self.assertEqual(page.locator("#trk-sheet .trkgl").all_inner_texts(), ["Singles", "Combos"])

    def test_add_stays_disabled_until_a_stat_a_side_and_a_line_are_set(self):
        page = self.open()
        self.open_sheet(page)
        self.pick(page, "Nikola Jokić")
        add = page.locator("#trk-sheet .trks-f .trkadd")
        self.assertTrue(add.is_disabled())
        self.assertIn("Pick a stat, Over or Under, and a line.", self.text(page, "#trk-sheet .trks-f"))
        page.locator("#trk-sheet .trkchip", has_text=re.compile("^Points$")).click()
        self.assertIn("Pick Over or Under and a line.", self.text(page, "#trk-sheet .trks-f"))
        page.locator("#trk-sheet .trkseg2 button", has_text="Over").click()
        self.assertTrue(add.is_disabled())
        page.fill("#trk-sheet input[aria-label=Line]", "24.5")
        self.assertFalse(add.is_disabled())

    def test_the_line_field_shows_each_message_and_the_stepper_moves_half_a_point(self):
        page = self.open()
        self.open_sheet(page)
        self.pick(page, "Nikola Jokić")
        line = page.locator("#trk-sheet input[aria-label=Line]")
        for typed, msg in (("abc", "Use a number like 24.5."), ("24.25", "Use .0 or .5 lines."), ("0", "Pick a line from 0.5 to 199.5."), ("200", "Pick a line from 0.5 to 199.5."), ("24.5.5", "Use a number like 24.5.")):
            line.fill(typed)
            self.assertEqual(self.text(page, "#trk-sheet .trkerr"), msg, typed)
        line.fill("")
        self.assertEqual(self.text(page, "#trk-sheet .trkerr"), "Enter a line.")
        for ok in ("24.5", "25", "0.5", "199.5"):
            line.fill(ok)
            self.assertEqual(self.text(page, "#trk-sheet .trkerr"), "", ok)
        line.fill("24.5")
        page.click("#trk-sheet .trkstp:has-text('+')")
        self.assertEqual(line.input_value(), "25")
        page.click("#trk-sheet .trkstp:has-text('-')")
        page.click("#trk-sheet .trkstp:has-text('-')")
        self.assertEqual(line.input_value(), "24")
        line.fill("0.5")
        page.click("#trk-sheet .trkstp:has-text('-')")
        self.assertEqual(line.input_value(), "0.5")
        line.fill("199.5")
        page.click("#trk-sheet .trkstp:has-text('+')")
        self.assertEqual(line.input_value(), "199.5")

    def test_a_combo_previews_its_name_and_the_sum_of_the_parts(self):
        page = self.open()
        self.build(page, "Shai Gilgeous-Alexander", "Pts + Reb + Ast", "Over", "38.5")
        preview = self.text(page, "#trk-sheet .trkprev")
        self.assertIn("Over 38.5 PRA", preview)
        self.assertIn("26 / 38.5 PRA", preview)
        self.assertIn("needs 13 more", preview)

    def test_adding_creates_one_tile_with_a_toast_and_undo_and_it_survives_a_reload(self):
        page = self.open()
        self.build(page, "Nikola Jokić", "Points", "Under", "30.5")
        self.assertIn("Right now: 27 points", self.text(page, "#trk-sheet"))
        self.add(page)
        self.assertEqual(page.locator("#app .tile.trk").count(), 1)
        self.assertIn("Added. Tracking Jokić points.", self.text(page, "#trk-toast"))
        page.click("#trk-toast .trkt-u")
        page.wait_for_timeout(200)
        self.assertEqual(page.locator("#app .tile.trk").count(), 0)
        self.build(page, "Nikola Jokić", "Points", "Under", "30.5")
        self.add(page)
        page.wait_for_timeout(400)
        page.reload()
        page.wait_for_selector(".tile.trk")
        self.assertEqual(page.locator("#app .tile.trk").count(), 1)
        self.assertIn("Under 30.5 points", self.text(page))
        self.assertEqual(page.errors, [])

    def test_a_duplicate_is_blocked_and_changing_one_value_unblocks_it(self):
        page = self.open()
        self.build(page, "Nikola Jokić", "Points", "Over", "30.5")
        self.add(page)
        self.build(page, "Nikola Jokić", "Points", "Over", "30.5")
        self.assertEqual(self.text(page, "#trk-sheet .trkerr"), "You're already tracking that.")
        self.assertTrue(page.locator("#trk-sheet .trks-f .trkadd").is_disabled())
        page.fill("#trk-sheet input[aria-label=Line]", "31.5")
        self.assertFalse(page.locator("#trk-sheet .trks-f .trkadd").is_disabled())

    def test_the_twenty_first_bet_is_blocked(self):
        bets = [bet("b%02d" % i, "Jalen Brunson", "NYK", "WAS", "nba|NYK@WAS", "points", "over", 10.5 + i, pid="3934672") for i in range(20)]
        page = self.open(init=seed(bets))
        self.assertEqual(page.locator("#app .tile.trk").count(), 20)
        self.build(page, "Nikola Jokić", "Points", "Over", "24.5")
        self.assertEqual(self.text(page, "#trk-sheet .trkerr"), "20 is the max. Delete one to add another.")
        self.assertTrue(page.locator("#trk-sheet .trks-f .trkadd").is_disabled())

    def test_adding_a_bet_already_past_the_line_shows_hit_and_the_note(self):
        page = self.open()
        self.build(page, "Nikola Jokić", "Points", "Over", "20.5")
        self.add(page)
        tile = self.text(page, "#app .tile.trk")
        self.assertIn("HIT", tile)
        self.assertIn("Already past the line when added.", tile)

    def test_a_game_that_has_not_started_can_be_added(self):
        page = self.open()
        self.build(page, "Jayson Tatum", "Rebounds", "Over", "8.5")
        self.add(page)
        tile = self.text(page, "#app .tile.trk")
        self.assertIn("Not started yet", tile)
        self.assertIn("Starts 10:30 PM", tile)

    def test_the_sheet_closes_on_escape_and_on_the_scrim_and_keeps_focus_inside(self):
        page = self.open()
        self.open_sheet(page)
        self.assertEqual(page.get_attribute("#trk-sheet .trks-p", "aria-modal"), "true")
        page.keyboard.press("Escape")
        page.wait_for_selector("#trk-sheet", state="detached")
        self.open_sheet(page)
        page.mouse.click(190, 20)
        page.wait_for_selector("#trk-sheet", state="detached")
        self.open_sheet(page)
        for _ in range(40):
            page.keyboard.press("Tab")
            self.assertTrue(page.evaluate("!!document.activeElement.closest('#trk-sheet')"))

    def test_backing_out_of_step_two_saves_nothing_and_the_phone_back_button_closes_the_sheet(self):
        page = self.open()
        self.build(page, "Nikola Jokić", "Points", "Over", "30.5")
        page.click("#trk-sheet .trks-bk")
        self.assertEqual(page.locator("#app .tile.trk").count(), 0)
        page.go_back()
        page.wait_for_selector("#trk-sheet", state="detached")
        self.assertEqual(page.evaluate("location.hash"), "#live")

    # edit, delete
    def test_a_tile_opens_in_place_one_at_a_time_and_edits_the_line_and_side(self):
        bets = [bet("a", "Nikola Jokić", "DEN", "PHX", "nba|DEN@PHX", "points", "over", 30.5, pid="3112335"), bet("b", "Devin Booker", "PHX", "DEN", "nba|DEN@PHX", "points", "over", 30.5, pid="3136193", home=True)]
        page = self.open(init=seed(bets))
        tiles = page.locator("#app .tile.trk .trkn")
        tiles.nth(0).click()
        self.assertEqual(page.locator("#app .trkx").count(), 1)
        tiles.nth(1).click()
        self.assertEqual(page.locator("#app .trkx").count(), 1)
        self.assertIn("To change the player or the stat, delete this and add a new one.", self.text(page))
        page.fill("#app .trkx input[aria-label=Line]", "abc")
        page.click("#app .trkx .trkbtn.solid")
        self.assertEqual(self.text(page, "#app .trkx .trkerr"), "Use a number like 24.5.")
        page.fill("#app .trkx input[aria-label=Line]", "26.5")
        page.locator("#app .trkx .trkseg2 button", has_text="Under").click()
        page.click("#app .trkx .trkbtn.solid")
        page.wait_for_timeout(500)
        saved = {b["id"]: b for b in json.loads(page.evaluate("localStorage.getItem('%s')" % TRK_KEY))["bets"]}
        self.assertEqual((saved["b"]["line"], saved["b"]["side"]), (26.5, "under"))
        self.assertEqual([b["id"] for b in json.loads(page.evaluate("localStorage.getItem('%s')" % TRK_KEY))["bets"]], ["a", "b"])

    def test_editing_is_blocked_once_the_game_is_over(self):
        page = self.open(query="&trk=demo")
        page.locator("#app .tile.trk .trkn", has_text="Karl-Anthony Towns").click()
        self.assertIn("Game is over. Delete it or leave it.", self.text(page, "#app .trkx"))
        self.assertEqual(page.locator("#app .trkx input").count(), 0)

    def test_delete_has_no_confirm_a_five_second_undo_and_restores_the_slot(self):
        bets = [bet("a", "Nikola Jokić", "DEN", "PHX", "nba|DEN@PHX", "points", "over", 30.5, pid="3112335"), bet("b", "Devin Booker", "PHX", "DEN", "nba|DEN@PHX", "points", "over", 30.5, pid="3136193", home=True)]
        page = self.open(init=seed(bets))
        before = page.locator("#app .tile.trk .trkn").all_inner_texts()
        page.locator("#app .tile.trk .trkn").first.click()
        page.click("#app .trkx .trkbtn.del")
        self.assertEqual(page.locator("#app .tile.trk").count(), 1)
        self.assertIn("Deleted.", self.text(page, "#trk-toast"))
        page.click("#trk-toast .trkt-u")
        page.wait_for_timeout(200)
        self.assertEqual(page.locator("#app .tile.trk .trkn").all_inner_texts(), before)

    def test_delete_everything_asks_once_and_cancel_keeps_all(self):
        page = self.open(query="&trk=demo")
        page.click("text=Delete everything in My Tracker")
        self.assertIn("Delete all 18? This can't be undone.", self.text(page))
        page.click("#app .trkconf >> text=Cancel")
        self.assertEqual(page.locator("#app .trkconf").count(), 0)
        self.assertGreater(page.locator("#app .tile.trk").count(), 5)
        page.click("text=Delete everything in My Tracker")
        page.click("#app .trkconf .trkbtn.del")
        page.wait_for_selector("text=Nothing tracked yet.")

    # parlays
    def make_parlay(self, page, names):
        page.click("text=Make a parlay")
        page.wait_for_selector("#trk-bar")
        for n in names:
            page.locator("#app .tile.trk", has_text=n).first.click()

    PARLAY_BETS = [bet("a", "Nikola Jokić", "DEN", "PHX", "nba|DEN@PHX", "points", "over", 30.5, pid="3112335"), bet("b", "Nikola Jokić", "DEN", "PHX", "nba|DEN@PHX", "points", "under", 35.5, pid="3112335"),
                   bet("c", "Jayson Tatum", "BOS", "MIA", "nba|BOS@MIA", "rebounds", "over", 8.5, pid="4066338"), bet("d", "Nikita Kucherov", "TBL", "TOR", "nhl|TBL@TOR", "shots", "over", 4.5, sport="nhl", pid="8476453"),
                   bet("e", "Devin Booker", "PHX", "DEN", "nba|DEN@PHX", "assists", "over", 7.5, pid="3136193", home=True)]

    def test_make_a_parlay_needs_two_eligible_singles_and_selects_two_or_three(self):
        page = self.open(init=seed(self.PARLAY_BETS[:1]))
        self.assertEqual(page.locator("text=Make a parlay").count(), 0)
        page = self.open(init=seed(self.PARLAY_BETS))
        page.click("text=Make a parlay")
        self.assertIn("Pick 2 or 3 bets for your parlay.", self.text(page, ".trkban"))
        self.assertTrue(page.locator("#trk-bar .trkbtn.solid").is_disabled())
        page.locator("#app .tile.trk", has_text="Tatum").click()
        self.assertTrue(page.locator("#trk-bar .trkbtn.solid").is_disabled())
        page.locator("#app .tile.trk", has_text="Kucherov").click()
        self.assertIn("2 picked", self.text(page, "#trk-bar"))
        self.assertFalse(page.locator("#trk-bar .trkbtn.solid").is_disabled())
        page.locator("#app .tile.trk", has_text="Booker").click()
        page.locator("#app .tile.trk", has_text="Jokić").first.click()
        self.assertIn("Parlays max out at 3 legs.", self.text(page, "#trk-toast"))
        self.assertIn("3 picked", self.text(page, "#trk-bar"))
        self.assertEqual(page.locator("#app .tile.trk.nosel").count(), 2)
        self.assertEqual(page.locator("#app input[type=checkbox]:checked").count(), 3)
        page.click("#trk-bar >> text=Cancel")
        self.assertEqual(page.locator("#trk-bar").count(), 0)
        self.assertEqual(page.locator("#app .pcard").count(), 0)

    def test_the_same_player_and_stat_twice_is_refused_with_a_toast(self):
        page = self.open(init=seed(self.PARLAY_BETS))
        self.make_parlay(page, ["Over 30.5 points"])
        page.locator("#app .tile.trk", has_text="Under 35.5 points").click()
        self.assertIn("That's the same stat twice.", self.text(page, "#trk-toast"))
        self.assertIn("1 picked", self.text(page, "#trk-bar"))

    def test_a_mixed_sport_parlay_shows_each_leg_and_one_overall_status(self):
        page = self.open(init=seed(self.PARLAY_BETS))
        self.make_parlay(page, ["Tatum", "Kucherov"])
        page.click("#trk-bar .trkbtn.solid")
        page.wait_for_selector("#app .pcard")
        card = self.text(page, "#app .pcard")
        for want in ("MY PARLAY", "2 legs", "ALIVE", "0 of 2 hit", "Jayson Tatum", "Nikita Kucherov", "NBA", "NHL", "No price. Just tracking.", "Ungroup"):
            self.assertIn(want, card, want)
        self.assertIn("Parlay made. 2 legs.", self.text(page, "#trk-toast"))
        self.assertEqual(page.locator("#app .pcard .leg").count(), 2)
        page.wait_for_timeout(500)
        saved = json.loads(page.evaluate("localStorage.getItem('%s')" % TRK_KEY))
        self.assertEqual(len(saved["parlays"]), 1)

    def test_grouped_bets_are_not_selectable_for_a_second_parlay(self):
        page = self.open(init=seed(self.PARLAY_BETS))
        self.make_parlay(page, ["Tatum", "Kucherov"])
        page.click("#trk-bar .trkbtn.solid")
        page.wait_for_selector("#app .pcard")
        page.click("text=Make a parlay") if page.locator("text=Make a parlay").count() else None
        names = page.locator("#app .tile.trk .trkn").all_inner_texts() if page.locator("#trk-bar").count() else []
        self.assertNotIn("Jayson Tatum", names)
        self.assertNotIn("Nikita Kucherov", names)

    def test_ungroup_returns_the_singles_with_undo_and_deleting_a_leg_auto_ungroups(self):
        page = self.open(init=seed(self.PARLAY_BETS))
        self.make_parlay(page, ["Tatum", "Kucherov"])
        page.click("#trk-bar .trkbtn.solid")
        page.wait_for_selector("#app .pcard")
        page.click("#app .pcard >> text=Ungroup")
        page.wait_for_selector("#app .pcard", state="detached")
        self.assertIn("Ungrouped.", self.text(page, "#trk-toast"))
        page.click("#trk-toast .trkt-u")
        page.wait_for_selector("#app .pcard")
        page.locator("#app .pcard .trkn").first.click()
        page.click("#app .pcard .trkbtn.del")
        page.wait_for_selector("#app .pcard", state="detached")
        self.assertIn("Parlay needs 2 legs. Ungrouped.", self.text(page, "#trk-toast"))
        self.assertEqual(page.locator("#app .tile.trk").count(), 4)

    def test_deleting_a_leg_from_a_three_leg_parlay_leaves_a_two_leg_parlay(self):
        page = self.open(init=seed(self.PARLAY_BETS))
        self.make_parlay(page, ["Tatum", "Kucherov", "Booker"])
        page.click("#trk-bar .trkbtn.solid")
        page.wait_for_selector("#app .pcard")
        self.assertIn("3 legs", self.text(page, "#app .pcard"))
        page.locator("#app .pcard .trkn").first.click()
        page.click("#app .pcard .trkbtn.del")
        page.wait_for_timeout(300)
        self.assertEqual(page.locator("#app .pcard .leg").count(), 2)
        self.assertIn("2 legs", self.text(page, "#app .pcard"))

    def test_the_demo_parlays_follow_the_status_table_on_the_page(self):
        page = self.open(query="&trk=demo")
        cards = page.locator("#app .pcard")
        self.assertIn("DEAD", cards.nth(0).inner_text())
        self.assertIn("Leg 3 lost. Parlay is dead.", cards.nth(0).inner_text())
        self.assertEqual(cards.nth(0).evaluate("e => e.classList.contains('dead')"), True)
        self.assertIn("ALIVE", cards.nth(1).inner_text())
        self.assertIn("0 of 2 hit", cards.nth(1).inner_text())

    # feeds
    def test_all_feeds_down_keeps_the_tiles_and_says_so(self):
        page = self.open(query="&trk=demo&feed=allfail")
        self.assertIn("Live scores unavailable. Trying again every 10 seconds.", self.text(page, "#trkupd"))
        self.assertIn("Live stats unavailable", self.text(page))
        self.assertEqual(page.get_attribute("#trkupd", "class"), "lvupd bad")

    def test_the_nba_backup_feed_is_named_and_the_tiles_still_work(self):
        page = self.open(query="&trk=demo&feed=espnfail")
        self.assertIn("via NBA.com", self.text(page, "#trkupd"))
        self.assertIn("27 / 24.5 points", self.text(page))

    def test_the_updated_line_counts_in_seconds(self):
        page = self.open(query="&trk=demo")
        self.assertRegex(self.text(page, "#trkupd"), r"^Updated \d+s ago")

    # storage
    def test_blocked_storage_keeps_the_tracker_in_memory_with_a_banner(self):
        blocked = "Storage.prototype.getItem = function () { throw new DOMException('blocked', 'SecurityError'); }; Storage.prototype.setItem = function () { throw new DOMException('blocked', 'SecurityError'); };"
        page = self.open(init=blocked, seg=None, hash_="#tracker")
        self.assertIn("Can't save on this browser. Your tracker will be gone when you close this tab.", self.text(page))
        self.build(page, "Nikola Jokić", "Points", "Over", "30.5")
        self.add(page)
        page.wait_for_timeout(500)
        self.assertEqual(page.locator("#app .tile.trk").count(), 1)
        self.assertEqual(page.errors, [])

    def test_a_full_phone_says_so_and_the_page_keeps_working(self):
        full = ("(function () { var set = Storage.prototype.setItem; Storage.prototype.setItem = function (k, v) { if (k === '%s') throw new DOMException('full', 'QuotaExceededError'); return set.call(this, k, v); }; })();" % TRK_KEY)
        page = self.open(init=full)
        self.build(page, "Nikola Jokić", "Points", "Over", "30.5")
        self.add(page)
        page.wait_for_selector("#trk-toast:not([hidden])")
        page.wait_for_timeout(500)
        self.assertIn("Phone storage is full. That one wasn't saved.", self.text(page, "#trk-toast"))
        self.assertEqual(page.locator("#app .tile.trk").count(), 1)
        self.assertEqual(page.errors, [])

    def test_a_corrupt_save_is_cleared_with_a_toast_and_no_error(self):
        page = self.open(init="localStorage.setItem('%s', '{not json');" % TRK_KEY)
        self.assertIn("Your saved tracker couldn't be read, so it was cleared.", self.text(page, "#trk-toast"))
        self.assertIn("Nothing tracked yet.", self.text(page))
        self.assertEqual(page.errors, [])
        self.assertIsNone(page.evaluate("localStorage.getItem('%s')" % TRK_KEY))

    # isolation
    def test_the_tracker_only_writes_its_own_keys_and_only_asks_for_its_own_feed(self):
        spy = "(function () { window.__keys = []; var set = Storage.prototype.setItem; Storage.prototype.setItem = function (k, v) { window.__keys.push(k); return set.call(this, k, v); }; })();"
        page = self.open(init=spy)
        settled = len(page.requests)
        self.build(page, "Nikola Jokić", "Points", "Over", "30.5")
        self.add(page)
        page.click("text=Delete everything in My Tracker")
        page.click("#app .trkconf .trkbtn.del")
        page.wait_for_timeout(600)
        new = [u for u in page.requests[settled:] if "espncdn" not in u and "/fonts/" not in u]
        self.assertTrue(all("tracker.json" in u for u in new), new)
        writes = set(page.evaluate("window.__keys"))
        self.assertLessEqual(writes - {"pc_seen_fx"}, {TRK_KEY, SEG_KEY, "pc_sport"})

    def test_the_odds_player_list_reads_the_committed_file_and_does_not_write_it(self):
        src = tracker_source()
        self.assertIn("'data/odds/' + day + '.json'", src)
        self.assertEqual(len(re.findall(r"\bfetch\(", src)), 0)


if __name__ == "__main__":
    unittest.main()
