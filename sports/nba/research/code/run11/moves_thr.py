"""Run 11 (2026-11-12, Matt: test what is testable now). Stored reads only. From sports/nba: python research/code/run11/moves_thr.py

T1  3-pointers on a looser trigger: the live rule's Pinnacle move bar (2 pts) lowered to 1.5 / 1 / 0.5, with and without the
    fair-price check, next to the other markets. And the no-move rule (Hard Rock X%+ over Pinnacle fair on any B/C/D read).
T2  How fast Hard Rock follows Pinnacle: for every Pinnacle move of 2+ pts seen between two reads, what Hard Rock's price had
    already done when we saw it, by window length. And the upper bound for faster checks: the same bets at Hard Rock's price
    from BEFORE the move (what a check right after Pinnacle moved would have found, if Hard Rock had not followed yet).
"""
import collections, glob, json, os, statistics, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import auto_hypothesis as ah
odds = ah.odds
MK = ("threes", "points", "rebounds", "assists")


def days():
    out = {}
    for p in sorted(glob.glob(ah.R + "data/odds/2*.json")):
        d = json.load(open(p, encoding="utf-8"))
        byg = collections.defaultdict(list)
        for f in sorted(d["fetches"], key=lambda f: f["at"]):
            if f.get("markets") is not None:
                byg[f["game_id"]].append(f)
        out[d["date"]] = byg
    return out


def moves(dm, box, thr):
    """Every Pinnacle move >= thr between consecutive reads on a line Hard Rock shows on both; first per player/market/night."""
    out = []
    for day, byg in dm.items():
        seen = set()
        for gid, fs in byg.items():
            for a, b in zip(fs, fs[1:]):
                if b["read"] == "A":
                    continue
                for m in b["markets"]:
                    ha, hb = ah._hr(a, m), ah._hr(b, m)
                    pa, pb = ah._bk(a, "pinnacle", m), ah._bk(b, "pinnacle", m)
                    for k, h in hb.items():
                        if k not in ha or not (h.get("over") and h.get("under") and ha[k].get("over") and ha[k].get("under")):
                            continue
                        fa, fb = ah._fo(pa.get(k)), ah._fo(pb.get(k))
                        if fa is None or fb is None or abs(fb - fa) < thr:
                            continue
                        side = "over" if fb > fa else "under"
                        price, old = h[side], ha[k][side]
                        if not (-200 <= price <= 200) or (k[0], m) in seen:
                            continue
                        seen.add((k[0], m))
                        p = ah._side_p(fb, side)
                        d0, d1 = odds.decimal(old), odds.decimal(price)
                        mins = (ah.common.parse_iso(b["at"]) - ah.common.parse_iso(a["at"])).total_seconds() / 60.0
                        e = dict(day=day, gid=gid, pid=k[0], m=m, line=k[1], side=side, price=price, old=old, size=abs(fb - fa),
                                 ev_pin=p * d1 - 1, ev_old=p * d0 - 1, hr="stale" if d1 == d0 else ("followed" if d1 < d0 else "against"),
                                 win=a["read"] + ">" + b["read"], mins=mins, res=ah._grade(box, gid, k[0], m, k[1], side))
                        e.update(ah._later(dm, day, gid, b["at"], k[0], m, k[1], side))
                        out.append(e)
    return out


def judge(dm, box, bar):
    """No move needed: Hard Rock's price >= bar over Pinnacle fair on the same line at a B/C/D read; first per player/market/night."""
    out = []
    for day, byg in dm.items():
        seen = set()
        for gid, fs in byg.items():
            for f in fs:
                if f["read"] == "A":
                    continue
                for m in f["markets"]:
                    pin = ah._bk(f, "pinnacle", m)
                    for k, h in ah._hr(f, m).items():
                        fo = ah._fo(pin.get(k))
                        if fo is None or not (h.get("over") and h.get("under")):
                            continue
                        for side in ("over", "under"):
                            price = h[side]
                            ev = ah._side_p(fo, side) * odds.decimal(price) - 1
                            if ev < bar or not (-200 <= price <= 200) or (k[0], m) in seen:
                                continue
                            seen.add((k[0], m))
                            e = dict(day=day, gid=gid, pid=k[0], m=m, line=k[1], side=side, price=price, ev_pin=ev,
                                     res=ah._grade(box, gid, k[0], m, k[1], side))
                            e.update(ah._later(dm, day, gid, f["at"], k[0], m, k[1], side))
                            out.append(e)
    return out


def show(label, es, nights, price_key="price"):
    g = [e for e in es if e["res"] in ("W", "L")]
    if not g:
        print("  %-34s n   0" % label)
        return
    w = sum(e["res"] == "W" for e in g)
    u = sum((odds.decimal(e[price_key]) - 1) if e["res"] == "W" else -1.0 for e in g)
    cl = [e["close_pin"] * odds.decimal(e[price_key]) - 1 for e in g if e.get("close_pin") is not None]
    print("  %-34s n %4d %3d-%-3d %+7.2fu ROI %+6.1f%% %5.2f/night | CLV %s beat %s (n %d)" % (
        label, len(g), w, len(g) - w, u, 100 * u / len(g), len(g) / float(nights),
        "%+.2f%%" % (100 * statistics.mean(cl)) if cl else "-", "%d%%" % (100 * sum(x > 0 for x in cl) / len(cl)) if cl else "-", len(cl)))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    dm, box = days(), ah._load_box()
    N = len(dm)
    print("nights", N)
    print("== T1a Pinnacle-move trigger by size, FAIR (Hard Rock price >= Pinnacle fair) = the live rule's shape")
    for thr in (0.02, 0.015, 0.01, 0.005):
        mv = moves(dm, box, thr)
        print(" move >= %.1f pts" % (100 * thr))
        for m in MK:
            show("%s FAIR" % m, [e for e in mv if e["m"] == m and e["ev_pin"] >= 0], N)
        show("ALL markets FAIR", [e for e in mv if e["ev_pin"] >= 0], N)
        show("threes, no fair check", [e for e in mv if e["m"] == "threes"], N)
    print("== T1b no move needed: Hard Rock X%+ over Pinnacle fair (B/C/D reads)")
    for bar in (0.0, 0.01, 0.02, 0.03):
        jg = judge(dm, box, bar)
        print(" bar >= %+.0f%%" % (100 * bar))
        for m in MK:
            show(m, [e for e in jg if e["m"] == m], N)
    print("== T2 how fast Hard Rock follows a 2+ pt Pinnacle move (what its price had done when we saw the move)")
    mv = moves(dm, box, 0.02)
    for lab, lo, hi in (("checks <= 30 min apart", 0, 30), ("31-50 min apart", 30, 50), ("51-120 min apart", 50, 120), ("over 2 hours apart", 120, 99999)):
        s = [e for e in mv if lo < e["mins"] <= hi]
        if s:
            c = collections.Counter(e["hr"] for e in s)
            print("  %-24s moves %4d | Hard Rock already followed %2d%%  unchanged %2d%%  went the other way %2d%% | still fair-or-better %2d%%" % (
                lab, len(s), 100 * c["followed"] / len(s), 100 * c["stale"] / len(s), 100 * c["against"] / len(s),
                100 * sum(e["ev_pin"] >= 0 for e in s) / len(s)))
    print(" picks the rule gets now vs the most a faster check could get (same bets at Hard Rock's price from before the move)")
    show("now: fair at the price we saw", [e for e in mv if e["ev_pin"] >= 0], N)
    show("upper bound: fair at old price", [e for e in mv if e["ev_old"] >= 0], N, "old")
    show("  of those, Hard Rock followed", [e for e in mv if e["ev_old"] >= 0 and e["hr"] == "followed"], N, "old")
    show("  of those, missed today", [e for e in mv if e["ev_old"] >= 0 and e["ev_pin"] < 0], N, "old")
    for m in MK:
        show("  missed today: %s" % m, [e for e in mv if e["m"] == m and e["ev_old"] >= 0 and e["ev_pin"] < 0], N, "old")
