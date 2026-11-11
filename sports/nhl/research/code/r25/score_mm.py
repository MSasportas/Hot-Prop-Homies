#!/usr/bin/env python3
"""Run 25 forward scorer: MM2a-b, MM3a-b, MM4, MM5a-b (research/HYPOTHESES.md, registered 2026-11-10 before testing).
Judged nights >= 2026-11-10; earlier nights printed as a labelled descriptive check only. Read-only on data/; writes research/fwd/mm.md
and research/fwd/mm.json.  python3 -I score_mm.py [repo_root]"""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fwd"))
import score_fwd as F  # noqa: E402

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", ".."))
F.ROOT = ROOT
START = "2026-11-10"
NV = 60
F.BONF = NV
SHARP = ("pinnacle", "novig", "prophetx", "lowvig")
SOFT = ("draftkings", "fanduel", "betmgm", "espnbet", "betonlineag")
VARS = ["MM2a split", "MM2b split 2%", "MM3a persist", "MM3b confirm", "MM4 total", "MM5a follow", "MM5b fade"]


def pois_over(lam, pt):
    k = int(math.floor(pt))
    cdf = sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k + 1))
    if abs(pt - round(pt)) < 1e-9:
        pe = math.exp(-lam) * lam ** k / math.factorial(k)
        return (1 - cdf) / (1 - pe)
    return 1 - cdf


def lam_for(fo, pt):
    lo, hi = 0.5, 15.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if pois_over(mid, pt) < fo:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def snap_lams(snap, gid):
    g = (snap.get("games") or {}).get(str(gid)) or (snap.get("games") or {}).get(gid)
    if not g:
        return {}
    at = F.iso(snap["at"])
    out = {}
    for b, mks in (g.get("books") or {}).items():
        if b == "hardrockbet":
            continue
        t = (mks or {}).get("totals")
        if not t or not t.get("last_update") or (at - F.iso(t["last_update"])).total_seconds() / 60 >= F.STALE_MIN:
            continue
        oc = {o["name"]: o for o in t.get("outcomes") or []}
        if "Over" not in oc or "Under" not in oc or oc["Over"].get("point") != oc["Under"].get("point"):
            continue
        o, u = oc["Over"]["price"], oc["Under"]["price"]
        if not (0 <= F.hold(o, u) <= 0.15):
            continue
        out[b] = lam_for(F.fair_over(o, u), float(oc["Over"]["point"]))
    return out


def total_moves(date, start):
    p = os.path.join(ROOT, "data/featured", date + ".json")
    if not os.path.exists(p):
        return {}
    snaps = sorted(F.load(p).get("snaps") or [], key=lambda s: s["at"])
    out = {}
    gids = set()
    for s in snaps:
        gids |= {str(g) for g in (s.get("games") or {})}
    for gid in gids:
        st = start.get(int(gid)) if gid.isdigit() else None
        mine = [s for s in snaps if gid in {str(g) for g in (s.get("games") or {})} and (st is None or F.iso(s["at"]) < st)]
        if not mine:
            continue
        a = next((s for s in mine if gid + ":A" in (s.get("pulls") or [])), mine[0])
        c = next((s for s in reversed(mine) if gid + ":C" in (s.get("pulls") or [])), mine[-1])
        if a is c:
            continue
        la, lc = snap_lams(a, gid), snap_lams(c, gid)
        if len(la) < 3 or len(lc) < 3:
            continue
        out[int(gid)] = F.median(lc.values()) - F.median(la.values())
    return out


def run_night(date):
    reads = F.reads_for(date)
    res, start = F.shadow(date)
    pre = [r for r in reads if start.get(r["game"]) and r["at"] < start[r["game"]]]
    last_cons = {}
    for r in pre:
        if r["cons"] is not None:
            last_cons[(r["game"], r["pid"], r["line"])] = r["cons"]
    bets = {v: [] for v in VARS}
    done = {v: set() for v in VARS}

    def add(v, r, side, e):
        price = r[side]
        key = (r["game"], r["pid"], r["line"], side)
        if price < -200 or key in done[v]:
            return
        done[v].add(key)
        lc = last_cons.get((r["game"], r["pid"], r["line"]))
        bets[v].append({"date": date, "game": r["game"], "pid": r["pid"], "line": r["line"], "side": side, "pull": r["pull"],
                        "at": r["at"].isoformat(), "price": price, "ev": round(e, 4),
                        "clv": None if lc is None else round(F.ev(lc if side == "over" else 1 - lc, price), 4),
                        "pl": F.grade(res.get((r["game"], r["pid"], r["line"])), side, r["line"], price)})

    def evs(fair, r, side):
        if fair is None:
            return 0.0
        return F.ev(fair if side == "over" else 1 - fair, r[side])

    # MM2
    for r in pre:
        if r["pull"] not in ("B", "C"):
            continue
        sh = [r["fairs"][b] for b in SHARP if b in r["fairs"]]
        so = [r["fairs"][b] for b in SOFT if b in r["fairs"]]
        if len(sh) < 2 or len(so) < 3:
            continue
        sf = sum(sh) / len(sh); tf = F.median(so)
        if abs(sf - tf) < 0.03 - 1e-12:
            continue
        side = "over" if sf > tf else "under"
        e = evs(sf, r, side)
        if e >= -1e-12:
            add("MM2a split", r, side, e)
        if e >= 0.02 - 1e-12:
            add("MM2b split 2%", r, side, e)
    # MM3, MM5: per game/player/line first A, last B, first C, last C
    firstA, lastB, firstC, lastC = {}, {}, {}, {}
    for r in pre:
        k = (r["game"], r["pid"], r["line"])
        if r["pull"] == "A":
            firstA.setdefault(k, r)
        elif r["pull"] == "B":
            lastB[k] = r
        elif r["pull"] == "C":
            firstC.setdefault(k, r); lastC[k] = r
    for k, b in lastB.items():
        c = firstC.get(k)
        if not c or b["books"] < 4 or c["books"] < 4 or b["over"] != c["over"] or b["under"] != c["under"]:
            continue
        for s in ("over", "under"):
            eb, ec = evs(b["cons"], b, s), evs(c["cons"], c, s)
            if eb < 0.01 - 1e-12:
                continue
            if ec >= 0.01 - 1e-12:
                add("MM3a persist", c, s, ec)
            mv = (c["cons"] - b["cons"]) * (1 if s == "over" else -1)
            if mv >= 0.01 - 1e-12:
                add("MM3b confirm", c, s, ec)
    # MM4
    tm = total_moves(date, start)
    for k, c in lastC.items():
        a = firstA.get(k)
        dG = tm.get(k[0])
        if not a or dG is None or abs(dG) < 0.15 - 1e-12 or a["over"] != c["over"] or a["under"] != c["under"]:
            continue
        s = "over" if dG > 0 else "under"
        add("MM4 total", c, s, evs(c["cons"], c, s))
    # MM5: main line per player at first A read and at last C read
    def mains(rows, pull, last):
        per = {}
        for r in rows:
            if r["pull"] != pull:
                continue
            per.setdefault((r["game"], r["pid"]), {}).setdefault(r["at"], []).append(r)
        out = {}
        for gp, by in per.items():
            t = max(by) if last else min(by)
            out[gp] = min(by[t], key=lambda r: abs(r["hr_fair"] - 0.5))
        return out
    mA, mC = mains(pre, "A", False), mains(pre, "C", True)
    for gp, c in mC.items():
        a = mA.get(gp)
        if not a or a["line"] == c["line"]:
            continue
        fol = "over" if c["line"] > a["line"] else "under"
        fad = "under" if fol == "over" else "over"
        add("MM5a follow", c, fol, evs(c["cons"], c, fol))
        add("MM5b fade", c, fad, evs(c["cons"], c, fad))
    return bets


def main():
    allb = {v: [] for v in VARS}
    for d in F.dates():
        for v, bl in run_night(d).items():
            allb[v].extend(bl)
    hdr = "| variant | bets | graded | W | units | ROI | 90% CI | p | mean CLV | candidate |\n|---|---|---|---|---|---|---|---|---|---|"
    def row(v, bl):
        s = F.summarize(bl)
        if not s["graded"]:
            return "| %s | %d | 0 | - | - | - | - | - | - | False |" % (v, s["bets"])
        return "| %s | %d | %d | %d | %+.2f | %+.1f%% | %+.0f..%+.0f%% | %.4f | %s | %s |" % (
            v, s["bets"], s["graded"], s["w"], s["units"], 100 * s["roi"], 100 * s["ci90"][0], 100 * s["ci90"][1], s["p_one_sided"],
            "-" if s["mean_clv"] is None else "%.4f" % s["mean_clv"], s.get("candidate", False))
    out = ["# Run 25 forward (research/code/r25/score_mm.py): MM2-MM5, nights >= %s. Bar: n >= 300 graded, ROI > 0, p < %.5f, mean CLV > 0." % (START, 0.05 / NV), "", hdr]
    out += [row(v, [b for b in allb[v] if b["date"] >= START]) for v in VARS]
    out += ["", "Descriptive, seen nights < %s (not a test, never a result):" % START, "", hdr]
    out += [row(v, [b for b in allb[v] if b["date"] < START]) for v in VARS]
    open(os.path.join(ROOT, "research/fwd/mm.md"), "w").write("\n".join(out) + "\n")
    json.dump({v: F.summarize([b for b in allb[v] if b["date"] >= START]) for v in VARS}, open(os.path.join(ROOT, "research/fwd/mm.json"), "w"), indent=1)
    print("\n".join(out))


if __name__ == "__main__":
    main()
