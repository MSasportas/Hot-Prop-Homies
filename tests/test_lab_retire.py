import datetime
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import lab_retire as lr  # noqa: E402

NOW = datetime.datetime(2026, 12, 1, 5, 0, tzinfo=datetime.timezone.utc)


def track(**kw):
    return dict({"id": "T1", "title": "T", "rule": "r", "summary": "research/s.json", "stats": "T1", "need": 150}, **kw)


def block(w, l, units, **kw):
    return dict({"w": w, "l": l, "push": 0, "void": 0, "pending": 0, "units": units}, **kw)


class Evaluate(unittest.TestCase):
    def verdict(self, k, units, need=150, **kw):
        return lr.evaluate(track(need=need, **kw.pop("track", {})), block(k // 2, k - k // 2, units, **kw))

    def test_cutoff_table(self):
        cases = [(30, 30, -9.5, "retire"), (30, 30, -8.0, "keep"), (50, 50, -12.0, "retire"), (50, 50, -10.0, "keep"),
                 (150, 150, -21.0, "retire"), (150, 150, -19.0, "keep"), (300, 300, -29.0, "retire"), (300, 300, -27.0, "keep"),
                 (75, 150, -21.0, "retire"), (75, 150, -19.0, "keep")]
        for k, need, units, expected in cases:
            v = self.verdict(k, units, need=need)
            self.assertEqual(v["verdict"], expected, (k, need, units, v["reason"]))

    def test_full_sample_retire_and_keep(self):
        self.assertEqual(self.verdict(150, -25)["reason"], lr.FAIL_FULL)
        self.assertEqual(self.verdict(150, -15)["verdict"], "keep")

    def test_early_futility(self):
        self.assertEqual(self.verdict(80, -30)["reason"], lr.FAIL_EARLY)
        self.assertEqual(self.verdict(29, -29)["verdict"], "skip")

    def test_positive_clv_vetoes_retirement(self):
        self.assertEqual(self.verdict(150, -25, clv=0.01)["verdict"], "keep")
        self.assertEqual(self.verdict(150, -25, clv=-0.01)["verdict"], "retire")

    def test_pending_heavy_and_void_heavy_are_skipped(self):
        self.assertEqual(self.verdict(150, -25, pending=40)["verdict"], "skip")
        self.assertEqual(self.verdict(150, -25, void=90)["reason"], "data_quality")

    def test_pass_is_ready_for_sharp(self):
        self.assertEqual(self.verdict(150, 30)["verdict"], "ready")
        self.assertEqual(self.verdict(150, 5)["verdict"], "keep")
        self.assertEqual(self.verdict(150, 5, clv=0.02)["verdict"], "ready")

    def test_inconclusive_retires_at_twice_need(self):
        self.assertEqual(self.verdict(300, 0)["reason"], lr.CAP)
        self.assertEqual(self.verdict(299, 0)["verdict"], "keep")

    def test_fade_track_mirrors_roi(self):
        direct = self.verdict(150, -25)
        fade = self.verdict(150, -25, track={"direction": "fade"})
        self.assertEqual(direct["verdict"], "retire")
        self.assertEqual(fade["verdict"], "ready")
        self.assertEqual(fade["final"]["units"], 25)
        self.assertEqual(self.verdict(150, 25, track={"direction": "fade"})["reason"], lr.FAIL_FULL)

    def test_fade_mirrors_clv(self):
        v = self.verdict(150, 25, clv=0.03, track={"direction": "fade"})
        self.assertEqual(v["reason"], lr.FAIL_FULL)
        self.assertEqual(v["final"]["clv"], -0.03)


class Pages(unittest.TestCase):
    def test_the_page_defines_the_redraw_its_lab_calls(self):
        with open(os.path.join(os.path.dirname(lr.__file__), "..", "index.html"), encoding="utf-8") as fh:
            html = fh.read()
        if "LAB_REDRAW(" in html:
            self.assertIn("function LAB_REDRAW()", html)


class Run(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.cfg = os.path.join(self.root, "sports", "nba", "config")
        os.makedirs(self.cfg)
        os.makedirs(os.path.join(self.root, "sports", "nba", "data", "research"))

    def tearDown(self):
        self.tmp.cleanup()

    def setup_tracks(self, tests, blocks):
        with open(os.path.join(self.cfg, "lab.json"), "w") as fh:
            json.dump({"updated": "2026-11-12", "tests": tests}, fh)
        with open(os.path.join(self.root, "sports", "nba", "data", "research", "s.json"), "w") as fh:
            json.dump(blocks, fh)

    def read_lab(self):
        with open(os.path.join(self.cfg, "lab.json")) as fh:
            return json.load(fh)

    def lab_ids(self):
        return [t["id"] for t in self.read_lab()["tests"]]

    def archive(self):
        with open(os.path.join(self.cfg, "lab_retired.jsonl")) as fh:
            return [json.loads(line) for line in fh]

    def run_night(self, day=0):
        return lr.run("nba", self.root, NOW + datetime.timedelta(days=day))

    def test_one_failing_night_does_not_retire_two_do(self):
        self.setup_tracks([track()], {"T1": block(62, 88, -25)})
        self.assertEqual(self.run_night(0), [])
        self.assertEqual(self.lab_ids(), ["T1"])
        events = self.run_night(1)
        self.assertEqual([e["event"] for e in events], ["retired"])
        self.assertEqual(self.lab_ids(), [])
        line = self.archive()[0]
        self.assertEqual((line["id"], line["reason"], line["final"]["units"]), ("T1", lr.FAIL_FULL, -25))
        self.assertEqual(self.read_lab()["retired_count"], 1)

    def test_a_clean_night_resets_the_streak(self):
        self.setup_tracks([track()], {"T1": block(62, 88, -25)})
        self.run_night(0)
        self.setup_tracks([track()], {"T1": block(75, 75, -5)})
        self.run_night(1)
        self.setup_tracks([track()], {"T1": block(62, 88, -25)})
        self.assertEqual(self.run_night(2), [])
        self.assertEqual(self.lab_ids(), ["T1"])

    def test_at_most_five_retire_per_run(self):
        tests = [track(id="T%d" % i, stats="T%d" % i) for i in range(8)]
        self.setup_tracks(tests, {"T%d" % i: block(62, 88, -25) for i in range(8)})
        self.run_night(0)
        self.assertEqual(len(self.run_night(1)), lr.MAX_RETIRE_PER_RUN)
        self.assertEqual(len(self.lab_ids()), 3)
        self.assertEqual(len(self.run_night(2)), 3)

    def test_rerun_is_idempotent(self):
        self.setup_tracks([track()], {"T1": block(62, 88, -25)})
        self.run_night(0)
        self.run_night(1)
        self.assertEqual(self.run_night(2), [])
        self.assertEqual(len(self.archive()), 1)

    def test_fast_checks_never_retire(self):
        self.setup_tracks([track(id="fast_checks", stats="T1", no_auto_retire=True)], {"T1": block(62, 88, -40)})
        for day in range(3):
            self.assertEqual(self.run_night(day), [])
        self.assertEqual(self.lab_ids(), ["fast_checks"])

    def test_pass_sets_status_once_and_stays_on_the_lab(self):
        self.setup_tracks([track()], {"T1": block(90, 60, 30)})
        self.assertEqual([e["event"] for e in self.run_night(0)], ["ready"])
        self.assertEqual(self.run_night(1), [])
        lab = self.read_lab()
        self.assertEqual((lab["tests"][0]["status"], lab["tests"][0]["ready_at"]), (lr.READY, "2026-12-01"))

    def test_stalled_track_retires_as_ran_out_of_picks(self):
        self.setup_tracks([track(first_seen="2026-10-01")], {"T1": block(5, 5, 0)})
        self.run_night(0)
        self.assertEqual(self.run_night(22), [])
        self.assertEqual(self.run_night(23)[0]["reason"], lr.STALLED)

    def test_seasonal_track_never_stalls(self):
        self.setup_tracks([track(first_seen="2026-10-01", seasonal=True)], {"T1": block(5, 5, 0)})
        for day in (0, 30, 31):
            self.assertEqual(self.run_night(day), [])

    def test_unreadable_summary_does_nothing(self):
        self.setup_tracks([track(summary="research/missing.json")], {})
        for day in range(3):
            self.assertEqual(self.run_night(day), [])
        self.assertEqual(self.lab_ids(), ["T1"])

    def test_retired_stats_hides_only_retired_from_that_summary(self):
        self.setup_tracks([track()], {"T1": block(62, 88, -25)})
        self.run_night(0)
        self.run_night(1)
        self.assertEqual(lr.retired_stats(self.cfg, "research/s.json"), {"T1"})
        self.assertEqual(lr.retired_stats(self.cfg, "research/other.json"), set())


if __name__ == "__main__":
    unittest.main()
