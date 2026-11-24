import json
import os
import re
import shutil
import unittest

from page_js import page_source, run_page_js

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIXTURE = os.path.join(ROOT, "fixtures", "livelong", "slate.json")
# rules the Live tile used before it became a Picks tile
OLD_LIVE_CLASSES = ("lv .gs", "lv .pp", "lv .nm", "lv .bt")


@unittest.skipUnless(shutil.which("node"), "node not installed")
class LiveTileLogic(unittest.TestCase):
    def test_stamp_is_the_records_grade_else_hit_or_lost(self):
        got, err = run_page_js(("liveStamp",), """
          console.log(JSON.stringify([liveStamp('W', null), liveStamp('PUSH', { stamp: 'HIT' }), liveStamp('', { stamp: 'HIT' }),
            liveStamp('', { stamp: 'LOST' }), liveStamp('', { stamp: null }), liveStamp('', null)]));""", ("FINAL_STAMP",))
        self.assertEqual(err, "")
        self.assertEqual(got, [["WON", "W"], ["PUSH", ""], ["HIT", "W"], ["LOST", "L"], None, None])

    def test_fit_line_keeps_the_first_tier_that_fits(self):
        got, err = run_page_js(("fitsLine", "fitLine"), """
          var mk = function (tiers, widthFor) {
            var el = { children: [], style: {}, textContent: '', attrs: { 'data-fit': JSON.stringify(tiers) },
              getAttribute: function (k) { return this.attrs[k]; } };
            Object.defineProperty(el, 'scrollWidth', { get: function () { return widthFor(el); } });
            el.clientWidth = 100;
            return el;
          };
          var number = mk([16, 14, 13].map(function (z) { return { size: z, text: '14 / 27.5 pts' }; }).concat([{ size: 13, text: '14 / 27.5' }]),
            function (e) { return e.textContent.length * parseFloat(e.style.fontSize) * 0.6; });
          fitLine(number);
          var roomy = mk([{ size: 16, text: '9 / 7.5' }], function () { return 50; });
          fitLine(roomy);
          console.log(JSON.stringify([number.style.fontSize, number.textContent, roomy.style.fontSize]));""")
        self.assertEqual(err, "")
        self.assertIn(got[0], ("13px", "14px"))
        self.assertEqual(got[2], "16px")

    def test_old_live_rules_are_gone(self):
        css = page_source()
        for dead in OLD_LIVE_CLASSES:
            self.assertNotIn("\n." + dead + "{", css)

    def test_a_live_tile_is_a_picks_tile(self):
        src = page_source()
        self.assertIn("'tile lv'", src)
        self.assertEqual(len(re.findall(r"\bliveTile\(", src)), 3)  # definition, Live tab, Lab Today


class LongFixture(unittest.TestCase):
    def test_livelong_covers_every_state(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            slate = json.load(fh)
        names = {p["player"] for p in slate["picks"]}
        for n in ("Nickeil Alexander-Walker", "Shai Gilgeous-Alexander", "Giannis Antetokounmpo", "Collin Murray-Boyles", "Karl-Anthony Towns",
                  "Brandin Podziemski", "Isaiah Hartenstein", "Wendell Carter Jr", "Michael Porter Jr", "Victor Wembanyama", "Jaren Jackson Jr.", "Nene"):
            self.assertIn(n, names)
        results = {p["result"]["result"] for p in slate["picks"] if "result" in p}
        self.assertEqual(results, {"W", "L", "PUSH", "VOID"})
        self.assertTrue(any(p.get("pulled") for p in slate["picks"]))
        live = slate["fixture_live"]
        self.assertTrue(any(g["state"] == "pre" for g in live["games"].values()))
        self.assertTrue(any(g["period"] > 4 for g in live["games"].values()))
        self.assertTrue(any(g["away"]["score"] >= 100 and g["home"]["score"] >= 100 for g in live["games"].values()))
        self.assertTrue(any(s.get("dnp") for s in live["stats"].values()))
        self.assertTrue(os.path.exists(os.path.join(ROOT, "fixtures", "livelong-nhl", "slate.json")))


if __name__ == "__main__":
    unittest.main()
