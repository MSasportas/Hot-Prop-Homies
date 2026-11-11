#!/usr/bin/env python3
"""Run 25 history test MM1 (team-wide shading), as registered in HYPOTHESES.md.
Nov 2025 - Feb 2026 only; the lockbox (Mar 1+) is never read here.  python3 -I ll_hist.py <extracted bundle dir>"""
import json, os, random, sys
B = sys.argv[1]
END = "2026-03-01"


def dec(a): return 1 + a / 100.0 if a > 0 else 1 + 100.0 / -a
def fair(o, u): a, b = 1 / dec(o), 1 / dec(u); return a / (a + b)
def hold(o, u): return 1 / dec(o) + 1 / dec(u) - 1


def rd(f):
    return [x for x in (json.loads(l) for l in open(os.path.join(B, "work", f))) if x["date"] < END and x.get("over") is not None and x.get("under") is not None]


L45 = rd("shots45_lines.jsonl")


def pl(x, side):
    if x.get("result") != "OK" or x.get("actual") is None: return None
    pr = x[side]
    if pr < -200: return "skip"
    won = x["actual"] > x["line"] if side == "over" else x["actual"] < x["line"]
    return dec(pr) - 1 if won else -1.0


def stats(bets, seed=7):
    g = [b for b in bets if isinstance(b["pl"], float)]
    if not g: return "n0"
    by = {}
    for b in g: by.setdefault(b["gid"], []).append(b["pl"])
    cl = list(by.values()); rng = random.Random(seed); sims = []
    for _ in range(2000):
        s = [cl[rng.randrange(len(cl))] for _ in cl]; sims.append(sum(map(sum, s)) / sum(map(len, s)))
    sims.sort(); roi = sum(b["pl"] for b in g) / len(g)
    folds = {}
    for b in g: folds.setdefault(b["date"][:7], []).append(b["pl"])
    fs = " ".join("%s %+.1f%% n%d" % (m[5:], 100 * sum(v) / len(v), len(v)) for m, v in sorted(folds.items()))
    p = sum(1 for x in sims if x <= 0) / 2000
    return "n%d %+.1f%% [%+.1f,%+.1f] p %.3f | folds %s" % (len(g), 100 * roi, 100 * sims[100], 100 * sims[1899], p, fs)


def placebo(bets_lines, actual_roi, k=200):
    rng = random.Random(3); hits = 0; rs = []
    for _ in range(k):
        t = []
        for x in bets_lines:
            v = pl(x, rng.choice(("over", "under")))
            if isinstance(v, float): t.append(v)
        r = sum(t) / len(t); rs.append(r); hits += r >= actual_roi
    return "placebo mean %+.1f%%, %d/%d >= actual" % (100 * sum(rs) / k, hits, k)



out = []
months = sorted({x["date"][:7] for x in L45})
for x in L45: x["f"] = fair(x["over"], x["under"])
def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))]
bets = {"MM1a fade": [], "MM1b follow": []}
for m in months:
    if m < "2025-11": continue
    prior = [x for x in L45 if x["date"][:7] < m]
    cur = [x for x in L45 if x["date"][:7] == m]
    ml = {}
    for x in prior: ml.setdefault(x["line"], []).append(x["f"])
    mL = {L: sum(v) / len(v) for L, v in ml.items() if len(v) >= 50}
    def teams(rows):
        t = {}
        for x in rows:
            if x["line"] in mL: t.setdefault((x["gid"], x["team"]), []).append(x)
        return {k: (sum(r["f"] - mL[r["line"]] for r in v) / len(v), v) for k, v in t.items() if len(v) >= 4}
    ps = [s for s, _ in teams(prior).values()]
    lo, hi = q(ps, 0.2), q(ps, 0.8)
    for (gid, tm), (s, rows) in teams(cur).items():
        if s >= hi: fade = "under"
        elif s <= lo: fade = "over"
        else: continue
        fol = "over" if fade == "under" else "under"
        for x in rows:
            for v, side in (("MM1a fade", fade), ("MM1b follow", fol)):
                r = pl(x, side)
                if r == "skip" or r is None: continue
                bets[v].append({"gid": gid, "date": x["date"], "pl": r, "x": x})
    out.append("%s: lines %d, q20 %+.4f q80 %+.4f, m(L) %s" % (m, len(cur), lo, hi, {k: round(v, 3) for k, v in sorted(mL.items())}))
for v, b in bets.items():
    out.append("%s: %s" % (v, stats(b)))
    g = [z for z in b if isinstance(z["pl"], float)]
    if g and len(g) >= 300 and sum(z["pl"] for z in g) > 0:
        out.append("  " + placebo([z["x"] for z in g], sum(z["pl"] for z in g) / len(g)))
print("\n".join(out))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mm_hist_results.txt"), "w").write("\n".join(out) + "\n")
