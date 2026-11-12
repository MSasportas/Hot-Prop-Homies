#!/usr/bin/env python3
"""research/market_probe.py: ONE-TIME research read (Matt, 2026-11-12): every player-prop market Hard Rock posts for NBA, on a few
games tonight, with the same 10 books as the live reads, to find where Hard Rock is loosest. Research only: never touches picks,
the Record or the page.
Step 1: the feed's own market list for one game (1 credit): the player markets Hard Rock actually posts.
Step 2: the odds for those markets (1 credit a market a game, one region), on up to MAX_GAMES games, at most MAX_MARKETS markets.
Keys come from env ODDS_API_KEYS(_2); never printed or written. Writes research/market_probe/<date>_<HHMM>.json + summary.txt."""
import json, os, sys, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

API = "https://api.the-odds-api.com/v4/sports/basketball_nba"
BOOKS = "hardrockbet,draftkings,fanduel,betmgm,espnbet,pinnacle,betonlineag,betrivers,novig,prophetx"
MAX_GAMES, MAX_MARKETS, CHUNK = 4, 36, 12
keys = [k.strip() for v in ("ODDS_API_KEYS", "ODDS_API_KEYS_2") for k in os.environ.get(v, "").replace("\n", ",").split(",") if k.strip()]


def get(path, params):
    for i, k in enumerate(keys):
        q = urllib.parse.urlencode(dict(params, apiKey=k))
        try:
            with urllib.request.urlopen(API + path + "?" + q, timeout=40) as r:
                left = r.headers.get("x-requests-remaining")
                if left is not None and float(left) < 60:
                    continue                                   # leave that key's last credits to the live reads
                return json.loads(r.read()), r.headers.get("x-requests-last"), i + 1
        except urllib.error.HTTPError as e:
            print("key %d answered %d" % (i + 1, e.code))
            if e.code in (401, 429):
                continue
            return None, None, i + 1
    return None, None, None


now = datetime.now(timezone.utc)
events, _, _ = get("/events", {"dateFormat": "iso"})
todo = sorted([e for e in events or [] if now + timedelta(minutes=20) < datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00")) < now + timedelta(hours=9)],
              key=lambda e: e["commence_time"])[:MAX_GAMES]
if not todo:
    print("no games in the window"); sys.exit(0)
menu, cost, kn = get("/events/%s/markets" % todo[0]["id"], {"regions": "us", "bookmakers": "hardrockbet"})
hr = next((b for b in (menu or {}).get("bookmakers", []) if b.get("key") == "hardrockbet"), None)
posted = sorted({m["key"] for m in (hr or {}).get("markets", []) if m["key"].startswith("player_")})
print("Hard Rock posts %d player markets on the first game (menu cost %s)" % (len(posted), cost))
if not posted:
    print("no market list from Hard Rock; stopping"); sys.exit(0)
main = [m for m in posted if not m.endswith("_alternate")]
alt = [m for m in posted if m.endswith("_alternate")]
mk = (main + alt)[:MAX_MARKETS]
out = {"at": now.isoformat(), "books": BOOKS, "posted": posted, "asked": mk, "games": []}
spent = 0
for e in todo:
    g = {"event": e, "odds": []}
    for i in range(0, len(mk), CHUNK):
        part = mk[i:i + CHUNK]
        js, cost, kn = get("/events/%s/odds" % e["id"], {"regions": "us", "bookmakers": BOOKS, "markets": ",".join(part),
                                                         "oddsFormat": "american", "dateFormat": "iso"})
        spent += int(float(cost or 0))
        g["odds"].append(js)
    print("%s @ %s done" % (e["away_team"], e["home_team"]))
    out["games"].append(g)
out["credits"] = spent
os.makedirs("research/market_probe", exist_ok=True)
stamp = datetime.now(timezone(timedelta(hours=-5))).strftime("%Y-%m-%d_%H%M")
json.dump(out, open("research/market_probe/%s.json" % stamp, "w"), separators=(",", ":"))
# summary: per market, how many games Hard Rock priced it, how many players, which books also price it
rows = {}
for g in out["games"]:
    for js in g["odds"]:
        for b in (js or {}).get("bookmakers", []):
            for m in b.get("markets", []):
                r = rows.setdefault(m["key"], {"games": set(), "books": {}, "hr_players": set()})
                r["books"].setdefault(b["key"], set()).add(g["event"]["id"])
                if b["key"] == "hardrockbet":
                    r["games"].add(g["event"]["id"])
                    r["hr_players"].update(o.get("description") for o in m.get("outcomes", []) if o.get("description"))
lines = ["market | games HR priced | HR players | other books pricing it | Pinnacle?"]
for k in sorted(rows):
    r = rows[k]
    others = sorted(b for b in r["books"] if b != "hardrockbet")
    lines.append("%s | %d | %d | %d | %s" % (k, len(r["games"]), len(r["hr_players"]), len(others), "yes" if "pinnacle" in others else "no"))
open("research/market_probe/summary.txt", "w").write("credits spent: %d\n" % spent + "\n".join(lines) + "\n")
print("credits spent: %d" % spent)
print("\n".join(lines))
