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
VIEWS = ("picks", "live", "games", "record", "lab", "info")
FIXTURES = ("livelong", "livelong-nhl", "lab-cards")
SPORTS = ("all", "nba", "nhl")
RENDER_MS = 700
SWITCH_MIN_TAP_PX = 36
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
        page.goto("http://127.0.0.1:%d/index.html?fixture=%s#%s" % (self.server.server_address[1], fixture, view))
        page.wait_for_timeout(RENDER_MS)
        if tap:
            page.evaluate(TAP_ALL)
            page.wait_for_timeout(RENDER_MS // 2)
        return page

    def test_no_tile_has_cut_off_words_at_any_phone_width(self):
        problems = []
        for width in WIDTHS:
            ctx = self.browser.new_context(viewport={"width": width, "height": 900})
            for fixture in FIXTURES:
                for view in VIEWS:
                    sports = SPORTS if (fixture, view) in (("livelong", "picks"), ("livelong", "live"), ("livelong-nhl", "live")) else ("all",)
                    for sport in sports:
                        page = self.render(ctx, fixture, view, sport)
                        for p in page.evaluate(self.check):
                            problems.append("%dpx %s %s %s: %s in %s %s %s" % (width, fixture, view, sport, p["kind"], p["where"], repr(p["text"]), p["detail"]))
                        page.close()
            ctx.close()
        self.assertEqual(sorted(set(problems)), [])

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
