import json
import os
import re
import shutil
import subprocess
import unittest

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")


def page_source():
    with open(HTML, encoding="utf-8") as fh:
        return fh.read()


def run_page_js(body):
    """Run page functions in node and return what the snippet logs as JSON."""
    src = page_source()
    parts = [re.search(r"\nfunction %s\([^\n]*\}\n|\nfunction %s\([\s\S]*?\n}\n" % (n, n), src).group(0) for n in ("ms", "str", "addedAt", "newestFirst", "splitName")]
    parts.append(re.search(r"\nvar NAME_SUFFIX = [^\n]*\n", src).group(0))
    js = "".join(parts) + body
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30)
    return json.loads(out.stdout), out.stderr


@unittest.skipUnless(shutil.which("node"), "node not installed")
class PicksOrder(unittest.TestCase):
    def test_newest_first_by_added_at_then_price_at_undated_last_ties_in_file_order(self):
        got, err = run_page_js(
            "var P=[{id:'a',price_at:'2026-11-20T12:00:00-05:00'},{id:'none1'},"
            "{id:'b',added_at:'2026-11-20T14:00:00-05:00',price_at:'2026-11-20T09:00:00-05:00'},"
            "{id:'tie1',added_at:'2026-11-20T13:00:00-05:00'},{id:'bad',added_at:'nope',price_at:'also nope'},"
            "{id:'tie2',price_at:'2026-11-20T13:00:00-05:00'},{id:'late',added_at:'2026-11-20T13:30:00-05:00',pulled:{code:'line_gone'}}];"
            "console.log(JSON.stringify(newestFirst(P).map(function(p){return p.id})))")
        self.assertEqual(got, ["b", "late", "tie1", "tie2", "a", "none1", "bad"], err)

    def test_names_split_into_first_and_last_without_losing_words(self):
        got, err = run_page_js(
            "console.log(JSON.stringify(['Josh Giddey','Gary Trent Jr.','Shai Gilgeous-Alexander','Fred VanVleet','Karl-Anthony Towns','Nene','  Jimmy   Butler III '].map(splitName)))")
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
