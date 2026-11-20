import shutil
import unittest

from page_js import page_source, run_page_js

PICKS_ORDER_FUNCTIONS = ("ms", "str", "addedAt", "newestFirst", "splitName")


@unittest.skipUnless(shutil.which("node"), "node not installed")
class PicksOrder(unittest.TestCase):
    def test_newest_first_by_added_at_then_price_at_undated_last_ties_in_file_order(self):
        got, err = run_page_js(
            PICKS_ORDER_FUNCTIONS, "var P=[{id:'a',price_at:'2026-11-20T12:00:00-05:00'},{id:'none1'},"
            "{id:'b',added_at:'2026-11-20T14:00:00-05:00',price_at:'2026-11-20T09:00:00-05:00'},"
            "{id:'tie1',added_at:'2026-11-20T13:00:00-05:00'},{id:'bad',added_at:'nope',price_at:'also nope'},"
            "{id:'tie2',price_at:'2026-11-20T13:00:00-05:00'},{id:'late',added_at:'2026-11-20T13:30:00-05:00',pulled:{code:'line_gone'}}];"
            "console.log(JSON.stringify(newestFirst(P).map(function(p){return p.id})))", ("NAME_SUFFIX",))
        self.assertEqual(got, ["b", "late", "tie1", "tie2", "a", "none1", "bad"], err)

    def test_names_split_into_first_and_last_without_losing_words(self):
        got, err = run_page_js(
            PICKS_ORDER_FUNCTIONS, "console.log(JSON.stringify(['Josh Giddey','Gary Trent Jr.','Shai Gilgeous-Alexander','Fred VanVleet','Karl-Anthony Towns','Nene','  Jimmy   Butler III '].map(splitName)))", ("NAME_SUFFIX",))
        self.assertEqual(got, [
            {"first": "Josh", "last": "Giddey", "core": "Giddey"},
            {"first": "Gary", "last": "Trent Jr.", "core": "Trent"},
            {"first": "Shai", "last": "Gilgeous-Alexander", "core": "Gilgeous-Alexander"},
            {"first": "Fred", "last": "VanVleet", "core": "VanVleet"},
            {"first": "Karl-Anthony", "last": "Towns", "core": "Towns"},
            {"first": "", "last": "Nene", "core": "Nene"},
            {"first": "Jimmy", "last": "Butler III", "core": "Butler"},
        ], err)


class PicksTabSource(unittest.TestCase):
    def test_page_keeps_its_guards_and_shows_the_divider(self):
        h = page_source()
        self.assertNotIn("innerHTML", h)
        self.assertIn("Seen earlier", h)
        for name in ("function isScratch(", "function counted(", "LIVE_MS = 10000"):
            self.assertIn(name, h)


if __name__ == "__main__":
    unittest.main()
