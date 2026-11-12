"""notify_live.py: send this cycle's Discord pings only once the live page shows the new slate.

cycle.sh runs run.py with PC_DEFER_NOTIFY=1 (no pings), pushes, then runs this. We poll the live site's
data/slate.json until it matches the file we just pushed (GitHub Pages takes 1-3 minutes), then call
notify.notify(). If the page has not caught up after WAIT_MAX seconds we send anyway: a late page beats
a missing ping. Never raises; exits 0.
"""
import hashlib
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import notify  # noqa: E402

SPORT = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WAIT_MAX = int(os.environ.get("PC_NOTIFY_WAIT", "360"))
STEP = 15


def _digest(b):
    try:
        import json
        return hashlib.sha256(json.dumps(json.loads(b), sort_keys=True).encode()).hexdigest()
    except Exception:
        return hashlib.sha256(b or b"").hexdigest()


def page_caught_up(local_bytes, fetch=None):
    url = "%ssports/%s/data/slate.json?t=%d" % (notify.PAGE, SPORT, int(time.time() * 1000))
    try:
        if fetch:
            live = fetch(url)
        else:
            req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "hph-runner"})
            with urllib.request.urlopen(req, timeout=10) as r:
                live = r.read()
    except Exception:
        return False
    return _digest(live) == _digest(local_bytes)


def main():
    try:
        if notify.endpoint() and os.environ.get("PC_NOTIFY_NO_WAIT") != "1":
            with open(common.dpath("slate.json"), "rb") as f:
                local = f.read()
            end = time.monotonic() + WAIT_MAX
            while not page_caught_up(local):
                if time.monotonic() >= end:
                    print("notify_live: page still behind after %ds, sending anyway" % WAIT_MAX)
                    break
                time.sleep(STEP)
        n = notify.notify()
        print("notify_live: %d discord message(s)" % n)
    except Exception as e:
        print("notify_live: skipped (%s)" % type(e).__name__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
