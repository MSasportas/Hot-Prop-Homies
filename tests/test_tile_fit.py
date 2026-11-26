"""Render every tab of the root page, in the long-name fixtures, at the phone widths, and fail on any tile whose words are cut off."""
import functools
import http.server
import os
import re
import threading
import unittest

from page_js import page_source

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CHECK_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tile_check.js")
WIDTHS = (320, 340, 380, 430)
ALL_VIEWS = ("picks", "live", "games", "record", "lab", "info")
REAL_DATA_VIEWS = ALL_VIEWS + ("hq",)  # HQ reads the committed data files directly, so it has no fixture
# the long-name and lab fixtures run every tab; the open-pick fixtures cover Picks tiles in each settled state,
# the record fixtures hold the real NBA and NHL Record files (market, side, edge and price cuts)
REAL_DATA = ""  # no ?fixture: the page reads the committed sports/*/data files, as the live site does
FIXTURE_VIEWS = {
    REAL_DATA: REAL_DATA_VIEWS,
    "livelong": ALL_VIEWS,
    "livelong-nhl": ALL_VIEWS,
    "lab-cards": ALL_VIEWS,
    "open-picks": ("picks", "games"),
    "open-picks-nhl": ("picks", "games"),
    "record-nba": ("record",),
    "record-nhl": ("record",),
}
SPORTS = ("all", "nba", "nhl")
RECORD_SPORT = {"record-nba": "nba", "record-nhl": "nhl"}  # the breakdown tables show for one sport at a time
# the page renders differently for All, NBA and NHL: the committed data is swept for each, the fixtures where it matters
WIDE_SPORT_RUNS = tuple((REAL_DATA, v) for v in REAL_DATA_VIEWS) + (("livelong", "picks"), ("livelong", "live"), ("livelong-nhl", "live"), ("open-picks", "picks"), ("open-picks-nhl", "picks"))
RENDER_MS = 700
SWITCH_MIN_TAP_PX = 40
TAP_ALL = """() => {
  for (let pass = 0; pass < 3; pass++) {
    document.querySelectorAll('#app [aria-expanded="false"], #app button.tr:not(.open), #app .lc-more').forEach((b) => b.click());
  }
}"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@unittest.skipUnless(sync_playwright, "playwright not installed")
class EveryTileFits(unittest.TestCase):
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
        with open(CHECK_JS, encoding="utf-8") as fh:
            cls.check = fh.read()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.play.stop()
        cls.server.shutdown()

    def render(self, ctx, fixture, view, sport, tap=True):
        page = ctx.new_page()
        page.add_init_script("localStorage.setItem('pc_sport', '%s')" % sport)
        query = "?fixture=" + fixture if fixture else ""
        page.goto("http://127.0.0.1:%d/index.html%s#%s" % (self.server.server_address[1], query, view))
        page.wait_for_timeout(RENDER_MS)
        if tap:
            page.evaluate(TAP_ALL)
            page.wait_for_timeout(RENDER_MS // 2)
        return page

    def found(self, page, view):
        """Problems on the view as it stands; on Record, once for each breakdown table behind the switcher, with its rows opened."""
        out = page.evaluate(self.check)
        if view != "record":
            return out
        for i in range(page.locator(".cswb").count()):
            page.locator(".cswb").nth(i).click()
            page.wait_for_timeout(RENDER_MS // 2)
            page.evaluate(TAP_ALL)
            page.wait_for_timeout(RENDER_MS // 2)
            out += page.evaluate(self.check)
        return out

    def test_no_tile_has_cut_off_words_at_any_phone_width(self):
        problems = []
        for width in WIDTHS:
            ctx = self.browser.new_context(viewport={"width": width, "height": 900})
            for fixture, views in FIXTURE_VIEWS.items():
                for view in views:
                    sports = SPORTS if (fixture, view) in WIDE_SPORT_RUNS else (RECORD_SPORT.get(fixture, "all"),)
                    for sport in sports:
                        page = self.render(ctx, fixture, view, sport)
                        for p in self.found(page, view):
                            problems.append("%dpx %s %s %s: %s in %s %s %s" % (width, fixture or "real-data", view, sport, p["kind"], p["where"], repr(p["text"]), p["detail"]))
                        page.close()
            ctx.close()
        self.assertEqual(sorted(set(problems)), [])

    def tracker_screens(self, ctx, sport):
        """My Tracker as Matt meets it, one check per screen: the list, an opened tile, Yesterday, parlay select, the create sheet (search, no match, stat form, preview, errors) and a toast."""
        page = ctx.new_page()
        page.add_init_script("localStorage.setItem('pc_sport', '%s'); localStorage.setItem('hph.live.seg', 'tracker')" % sport)
        page.goto("http://127.0.0.1:%d/index.html?fixture=livelong&trk=demo#live" % self.server.server_address[1])
        page.wait_for_selector(".trkban")
        page.wait_for_timeout(RENDER_MS)
        screens = {}
        screens["list"] = page.evaluate(self.check)
        page.evaluate(TAP_ALL)
        page.wait_for_timeout(RENDER_MS // 2)
        screens["opened tile"] = page.evaluate(self.check)
        page.click(".trkyd")
        page.wait_for_timeout(RENDER_MS // 2)
        screens["yesterday"] = page.evaluate(self.check)
        page.click("text=Make a parlay")
        page.wait_for_timeout(RENDER_MS // 2)
        page.locator("#app .tile.trk").nth(0).click()
        page.locator("#app .tile.trk").nth(1).click()
        page.wait_for_timeout(RENDER_MS // 2)
        screens["parlay select"] = page.evaluate(self.check)
        page.click("#trk-bar >> text=Cancel")
        page.click(".trkadd")
        page.wait_for_selector("#trk-sheet .trkpr")
        screens["sheet players"] = page.evaluate(self.check)
        page.fill("#trk-sheet .srch", "zzzz")
        screens["sheet no match"] = page.evaluate(self.check)
        page.fill("#trk-sheet .srch", "shai")
        page.locator("#trk-sheet .trkpr").first.click()
        page.wait_for_selector("#trk-sheet .trkchip[aria-pressed]")
        screens["sheet stat"] = page.evaluate(self.check)
        page.locator("#trk-sheet .trkchip", has_text="Pts + Reb + Ast").click()
        page.locator("#trk-sheet .trkseg2 button", has_text="Over").click()
        page.fill("#trk-sheet input[aria-label=Line]", "38.5")
        page.wait_for_timeout(RENDER_MS // 2)
        screens["sheet preview"] = page.evaluate(self.check)
        page.fill("#trk-sheet input[aria-label=Line]", "24.25")
        screens["sheet error"] = page.evaluate(self.check)
        page.keyboard.press("Escape")
        page.locator("#app .tile.trk .trkn").first.click()
        page.click("#app .trkx .trkbtn.del")
        page.wait_for_selector("#trk-toast:not([hidden])")
        screens["toast"] = page.evaluate(self.check)
        page.close()
        return screens

    def test_my_tracker_has_no_cut_off_words_on_any_screen_at_any_phone_width(self):
        problems = []
        for width in WIDTHS:
            ctx = self.browser.new_context(viewport={"width": width, "height": 900})
            for sport in SPORTS:
                for screen, found in self.tracker_screens(ctx, sport).items():
                    for p in found:
                        problems.append("%dpx my-tracker %s %s: %s in %s %s %s" % (width, sport, screen, p["kind"], p["where"], repr(p["text"]), p["detail"]))
            ctx.close()
        self.assertEqual(sorted(set(problems)), [])

    def test_my_tracker_text_is_at_least_13px_and_tap_targets_are_44px(self):
        ctx = self.browser.new_context(viewport={"width": 320, "height": 900})
        page = ctx.new_page()
        page.add_init_script("localStorage.setItem('pc_sport', 'all'); localStorage.setItem('hph.live.seg', 'tracker')")
        page.goto("http://127.0.0.1:%d/index.html?fixture=livelong&trk=demo#live" % self.server.server_address[1])
        page.wait_for_selector(".trkban")
        page.wait_for_timeout(RENDER_MS)
        page.evaluate(TAP_ALL)
        page.click(".trkyd")
        page.wait_for_timeout(RENDER_MS // 2)
        small = page.evaluate("""() => Array.from(document.querySelectorAll('#app .tile.trk *, #app .pcard *, .trkban, .trkseg *')).filter((e) => e.children.length === 0 && e.textContent.trim()
          && parseFloat(getComputedStyle(e).fontSize) < 13 && getComputedStyle(e).display !== 'none').map((e) => e.className + ':' + e.textContent.trim().slice(0, 20) + ':' + getComputedStyle(e).fontSize)""")
        self.assertEqual(small, [])
        short = page.evaluate("""() => Array.from(document.querySelectorAll('#app button, #app input[type=checkbox]')).filter((e) => e.getBoundingClientRect().height < 44 && !e.closest('.tile.trk .trkx')
          && !e.classList.contains('trkn') && !e.classList.contains('rowbtn') && !e.closest('.sport-sw')).map((e) => e.className + ':' + e.textContent.trim().slice(0, 20) + ':' + e.getBoundingClientRect().height)""")
        self.assertEqual(short, [])
        ctx.close()

    def test_the_record_fixtures_really_render_the_breakdown_labels(self):
        ctx = self.browser.new_context(viewport={"width": 320, "height": 900})
        for fixture, label in (("record-nba", "Rebounds"), ("record-nhl", "Under 1.5")):
            page = self.render(ctx, fixture, "record", RECORD_SPORT[fixture], tap=False)
            labels = page.evaluate("Array.from(document.querySelectorAll('.tbl .lbl')).map((e) => e.textContent)")
            self.assertTrue(any(label in t for t in labels), (fixture, labels))
            self.assertTrue(page.evaluate("Array.from(document.querySelectorAll('.tbl .lbl small')).length > 0"), fixture)
            page.close()
        ctx.close()

    def test_records_and_the_helpline_are_held_whole_at_every_width(self):
        for width in WIDTHS:
            ctx = self.browser.new_context(viewport={"width": width, "height": 900})
            page = self.render(ctx, "livelong-nhl", "live", "all", tap=False)
            held = page.evaluate("Array.from(document.querySelectorAll('.nb')).map((e) => [e.textContent, e.getClientRects().length === 1])")
            texts = [t for t, _ in held]
            self.assertTrue(any(re.fullmatch(r"\d+-\d+", t) for t in texts), (width, texts))
            self.assertIn("1-800-GAMBLER.", texts)
            self.assertTrue(all(one_line for _, one_line in held), (width, held))
            ctx.close()

    def test_sport_switch_buttons_are_a_real_tap_size(self):
        ctx = self.browser.new_context(viewport={"width": 320, "height": 900})
        page = self.render(ctx, "livelong", "picks", "all", tap=False)
        heights = page.evaluate("Array.from(document.querySelectorAll('.sport-sw button')).map((b) => b.getBoundingClientRect().height)")
        self.assertEqual(len(heights), 3)
        for hgt in heights:
            self.assertGreaterEqual(hgt, SWITCH_MIN_TAP_PX)
        ctx.close()


class NoClippingStyles(unittest.TestCase):
    def test_the_page_never_asks_for_an_ellipsis(self):
        src = page_source()
        self.assertNotIn("text-overflow", src)
        self.assertNotIn("…", src)
        self.assertIsNone(re.search(r"line-clamp", src))


if __name__ == "__main__":
    unittest.main()
