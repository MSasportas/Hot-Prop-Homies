"""2026-11-20: the stats API answers at most 100 rows per request. nhl.stats_report pages through a window and
returns every row, or None (never a partial list) when any page fails or the source comes up short of its own total."""
import json
import random
import unittest
import urllib.parse
from unittest import mock

import helpers   # noqa: F401  (puts scripts/ on the path)
import common
import nhl

CAP = 100


class FakeApi:
    """A stats API that holds `n` rows, caps every answer at CAP rows and honours start; `fail_on` fails that request number.
    Like the real one, it reshuffles the rows on every request unless the request names a sort."""

    def __init__(self, n, fail_on=None, status=200):
        self.rows = [{"playerId": i} for i in range(n)]
        self.fail_on, self.status, self.starts = fail_on, status, []

    def get(self, url, timeout=25, **kw):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        start, limit = int(q["start"][0]), int(q["limit"][0])
        self.starts.append(start)
        if len(self.starts) == self.fail_on:
            return common.Http(503, {}, b"", "HTTP 503")
        rows = self.rows if "sort" in q else random.sample(self.rows, len(self.rows))
        page = rows[start:start + min(limit, CAP)]
        return common.Http(self.status, {}, json.dumps({"data": page, "total": len(self.rows)}).encode())


def pull(api):
    with mock.patch.object(common, "http_get", api.get), mock.patch.object(nhl.time, "sleep") as nap:
        return nhl.stats_report("skater/summary", 20262027, "2026-11-12", "2026-11-18"), nap


class Paging(unittest.TestCase):
    def test_a_window_over_the_cap_comes_back_whole_and_in_order(self):
        api = FakeApi(936)
        rows, _ = pull(api)
        self.assertEqual(rows, api.rows)
        self.assertEqual(api.starts, list(range(0, 936, CAP)))

    def test_no_row_is_repeated_or_dropped_between_pages(self):
        api = FakeApi(936)
        rows, _ = pull(api)
        self.assertEqual(len({r["playerId"] for r in rows}), 936)

    def test_an_exact_multiple_of_the_cap_asks_no_extra_page(self):
        api = FakeApi(300)
        rows, _ = pull(api)
        self.assertEqual(len(rows), 300)
        self.assertEqual(api.starts, [0, 100, 200])

    def test_a_window_under_the_cap_is_one_request(self):
        api = FakeApi(96)
        rows, _ = pull(api)
        self.assertEqual(len(rows), 96)
        self.assertEqual(api.starts, [0])

    def test_an_empty_window_is_an_empty_list_not_a_failure(self):
        rows, _ = pull(FakeApi(0))
        self.assertEqual(rows, [])

    def test_every_page_is_followed_by_the_polite_pause(self):
        _, nap = pull(FakeApi(250))
        self.assertEqual(nap.call_count, 3)

    def test_a_failed_page_mid_way_returns_none_not_the_rows_so_far(self):
        rows, _ = pull(FakeApi(450, fail_on=3))
        self.assertIsNone(rows)

    def test_a_source_that_runs_dry_before_its_total_returns_none(self):
        api = FakeApi(250)
        api.rows = api.rows[:150]
        real = api.get

        def lying(url, **kw):
            r = real(url, **kw)
            js = json.loads(r.body)
            js["total"] = 250
            return common.Http(200, {}, json.dumps(js).encode())
        api.get = lying
        rows, _ = pull(api)
        self.assertIsNone(rows)

    def test_a_failed_pull_is_counted_as_a_failed_source(self):
        before = dict(nhl.SOURCES.get("nhl_stats", {"failed": 0}))["failed"]
        pull(FakeApi(450, fail_on=2))
        self.assertEqual(nhl.SOURCES["nhl_stats"]["failed"], before + 1)


if __name__ == "__main__":
    unittest.main()
