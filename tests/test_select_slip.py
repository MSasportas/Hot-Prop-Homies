import json
import shutil
import unittest

from page_js import page_source, run_page_js

SLIP_FUNCTIONS = ("str", "slipIdOf", "slipIds", "slipFits", "slipHref")
SLIP_VARIABLES = ("HR_SLIP", "SLIP_MAX", "SLIP_MAX_CHARS", "SLIP_IDS")
SLIP = "https://share.hardrock.bet/Pt0T/bet?deep_link_value=hardrock://betslip/"
REAL_IDS = ["2260103568635855282", "77187479825940888", "6572772606706057631"]


def hrefs(links_js):
    got, err = run_page_js(SLIP_FUNCTIONS, "console.log(JSON.stringify(slipHref(%s)))" % links_js, SLIP_VARIABLES)
    return got, err


def link(i):
    return SLIP + i


@unittest.skipUnless(shutil.which("node"), "node not installed")
class SelectToSlipLink(unittest.TestCase):
    def test_one_pick_is_its_own_link_byte_for_byte(self):
        got, err = hrefs('["%s"]' % link(REAL_IDS[0]))
        self.assertEqual(got, link(REAL_IDS[0]), err)

    def test_several_picks_are_comma_joined_in_the_order_given(self):
        got, err = hrefs("%s" % [link(i) for i in REAL_IDS[:2]])
        self.assertEqual(got, SLIP + ",".join(REAL_IDS[:2]), err)
        got, err = hrefs("%s" % [link(i) for i in reversed(REAL_IDS)])
        self.assertEqual(got, SLIP + ",".join(reversed(REAL_IDS)), err)

    def test_duplicate_ids_are_dropped_first_wins(self):
        got, err = hrefs("%s" % [link(REAL_IDS[1]), link(REAL_IDS[0]), link(REAL_IDS[1])])
        self.assertEqual(got, SLIP + REAL_IDS[1] + "," + REAL_IDS[0], err)

    def test_twenty_ids_fit_and_a_21st_does_not(self):
        ids = [str(2 * 10 ** 18 + n) for n in range(21)]
        got, err = hrefs("%s" % [link(i) for i in ids[:20]])
        self.assertEqual(got, SLIP + ",".join(ids[:20]), err)
        self.assertLessEqual(len(got), 1500)
        got, err = hrefs("%s" % [link(i) for i in ids])
        self.assertIsNone(got, err)

    def test_a_link_over_1500_characters_is_refused_even_under_twenty_ids(self):
        ids = [str(n) * 100 for n in range(1, 16)]
        got, err = hrefs("%s" % [link(i) for i in ids])
        self.assertIsNone(got, err)

    def test_ids_that_are_not_digits_only_never_enter_a_link(self):
        for bad in ("123,456", "12a", "", "12 3", "12%27"):
            got, err = hrefs('["%s"]' % (SLIP + bad))
            self.assertIsNone(got, err)

    def test_the_page_names_its_limits(self):
        h = page_source()
        self.assertIn("SLIP_MAX = 20", h)
        self.assertIn("SLIP_MAX_CHARS = 1500", h)


DK_FUNCTIONS = ("str", "dkOutcome", "dkHref")
DK_VARIABLES = ("DK_BASE", "SLIP_MAX", "SLIP_MAX_CHARS")
DK = "https://sportsbook.draftkings.com/"
DK_LINKS = [DK + "?outcomes=0QA390905561%232372938491_13L42648Q1935105358Q20",
            DK + "event/31?outcomes=0QA390910209%232372945876_13L42648Q11799469575Q20"]


def dk_href(links):
    got, err = run_page_js(DK_FUNCTIONS, "console.log(JSON.stringify(dkHref(%s)))" % json.dumps(links), DK_VARIABLES)
    return got, err


@unittest.skipUnless(shutil.which("node"), "node not installed")
class SelectToDraftKings(unittest.TestCase):
    def test_one_pick_is_its_own_link_unchanged(self):
        got, err = dk_href(DK_LINKS[:1])
        self.assertEqual(got, DK_LINKS[0], err)

    def test_several_picks_join_each_outcomes_value_as_given_in_order(self):
        got, err = dk_href(DK_LINKS)
        self.assertEqual(got, DK + "?outcomes=0QA390905561%232372938491_13L42648Q1935105358Q20,0QA390910209%232372945876_13L42648Q11799469575Q20", err)
        got, err = dk_href(list(reversed(DK_LINKS)))
        self.assertTrue(got.startswith(DK + "?outcomes=0QA390910209"), err)

    def test_duplicates_collapse_and_links_without_an_outcome_are_ignored(self):
        got, err = dk_href([DK_LINKS[0], DK + "no-outcomes", DK_LINKS[0]])
        self.assertEqual(got, DK_LINKS[0], err)
        got, err = dk_href([DK + "no-outcomes"])
        self.assertIsNone(got, err)

    def test_an_outcomes_value_with_odd_characters_is_refused(self):
        for bad in ("a,b", "a b", "a'b", 'a"b'):
            got, err = dk_href([DK + "?outcomes=" + bad])
            self.assertIsNone(got, err)

    def test_over_the_character_cap_is_refused(self):
        got, err = dk_href([DK + "?outcomes=" + str(n) * 100 for n in range(1, 16)])
        self.assertIsNone(got, err)

    def test_the_multi_pick_format_is_one_swappable_constant(self):
        self.assertIn("DK_OUTCOMES_JOIN = ','", page_source())


if __name__ == "__main__":
    unittest.main()
