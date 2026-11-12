"""clv_record.py: closing-line value of every Record single, from stored reads only (no credits).

For each pick: take the LAST stored read of its game taken after the pick was first shown. If Pinnacle still shows both
sides of the same line, close_fair = Pinnacle's no-vig chance of our side; clv = close_fair * decimal(posted price) - 1.
Also notes Hard Rock's own last price on that line. Picks first shown on the last read (or whose line Pinnacle dropped
or moved) are "unmeasured". Usage (from sports/nba): python research/code/clv/clv_record.py [--json]
"""
import glob, json, os, sys
sys.path.insert(0, "scripts")
import odds  # noqa: E402

def find(mk, pid, line, side):
    for o in (mk or {}).get("outcomes", []):
        if str(o.get("pid")) == pid and o.get("line") == line and o.get("side") == side:
            return o.get("price")
    return None

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rec = json.load(open("data/record.json"))
    nights = list(rec["nights"])
    for m in rec.get("older") or []:
        nights += json.load(open(os.path.join("data", m)))["nights"]
    rows = []
    for n in nights:
        f = "data/odds/%s.json" % n["date"]
        if not os.path.exists(f):
            continue
        fetches = json.load(open(f))["fetches"]
        for e in n.get("entries", []):
            if e.get("kind") != "single" or e.get("result") not in ("W", "L"):
                continue
            _, gid, pid, market, line, side = e["id"].split(":")
            line = float(line); other = "under" if side == "over" else "over"
            shown = e["prices"][0]["at"] if e.get("prices") else ""
            later = [x for x in fetches if x["game_id"] == gid and x["at"] > shown]
            row = {"id": e["id"], "date": n["date"], "market": market, "side": side, "price": e["price"], "result": e["result"],
                   "units": e["units"], "window": e.get("window"), "clv": None, "hr_close": None, "why": None}
            if not later:
                row["why"] = "no later read"
            else:
                last = max(later, key=lambda x: x["at"])
                pin = (last.get("others") or {}).get("pinnacle", {}).get(market)
                a, b = find(pin, pid, line, side), find(pin, pid, line, other)
                row["hr_close"] = find((last.get("markets") or {}).get(market), pid, line, side)
                if a is None or b is None:
                    row["why"] = "pinnacle line moved or gone"
                else:
                    row["clv"] = odds.fair_two_sided(a, b) * odds.decimal(e["price"]) - 1.0
            rows.append(row)
    if "--json" in sys.argv:
        print(json.dumps(rows)); return
    def line_(label, rs):
        m = [r for r in rs if r["clv"] is not None]
        w = sum(r["result"] == "W" for r in rs); u = sum(r["units"] for r in rs)
        if m:
            print("%-22s picks %3d  %2d-%-2d %+6.2fu | measured %3d  mean CLV %+5.2f%%  beat close %3.0f%%" % (
                label, len(rs), w, len(rs) - w, u, len(m), 100 * sum(r["clv"] for r in m) / len(m),
                100 * sum(r["clv"] > 0 for r in m) / len(m)))
        else:
            print("%-22s picks %3d  %2d-%-2d %+6.2fu | measured   0" % (label, len(rs), w, len(rs) - w, u))
    line_("ALL", rows)
    for k in ("market", "side", "window"):
        for v in sorted({str(r[k]) for r in rows}):
            line_("%s=%s" % (k, v), [r for r in rows if str(r[k]) == v])
    from collections import Counter
    print("unmeasured:", dict(Counter(r["why"] for r in rows if r["clv"] is None)))
    hr = [r for r in rows if r["hr_close"] is not None]
    worse = sum(odds.decimal(r["hr_close"]) < odds.decimal(r["price"]) for r in hr)
    print("Hard Rock still had the line at the last read: %d; its price got worse for us (moved our way): %d, same: %d, better: %d" % (
        len(hr), worse, sum(r["hr_close"] == r["price"] for r in hr), sum(odds.decimal(r["hr_close"]) > odds.decimal(r["price"]) for r in hr)))

if __name__ == "__main__":
    main()
