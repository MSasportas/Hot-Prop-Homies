#!/usr/bin/env python3
"""Run 24 history tests LL1 (Hard Rock own move 1 PM -> -45) and LL2 (hold shape), as registered in HYPOTHESES.md.
Nov 2025 - Feb 2026 only; the lockbox (Mar 1+) is never read here.  python3 -I ll_hist.py <extracted bundle dir>"""
import json, os, random, sys
B = sys.argv[1]
END = "2026-03-01"


def dec(a): return 1 + a / 100.0 if a > 0 else 1 + 100.0 / -a
def fair(o, u): a, b = 1 / dec(o), 1 / dec(u); return a / (a + b)
def hold(o, u): return 1 / dec(o) + 1 / dec(u) - 1


def rd(f):
    return [x for x in (json.loads(l) for l in open(os.path.join(B, "work", f))) if x["date"] < END and x.get("over") is not None and x.get("under") is not None]


L45 = rd("shots45_lines.jsonl"); L13 = rd("shots13_lines.jsonl")


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
# LL1
k45 = {(x["gid"], x["pid"], x["line"]): x for x in L45}
pairs = [(a, k45[(a["gid"], a["pid"], a["line"])]) for a in L13 if a["date"] >= "2025-11-01" and (a["gid"], a["pid"], a["line"]) in k45]
out.append("LL1 matched 1 PM/-45 same-line pairs Nov-Feb: %d" % len(pairs))
for cut in (0.01, 0.03):
    for mode in ("follow", "fade"):
        bets = []; lines = []
        for a, b in pairs:
            d = fair(b["over"], b["under"]) - fair(a["over"], a["under"])
            if abs(d) < cut - 1e-12: continue
            side = "over" if d > 0 else "under"
            if mode == "fade": side = "under" if side == "over" else "over"
            v = pl(b, side)
            if v == "skip" or v is None: continue
            bets.append({"gid": b["gid"], "date": b["date"], "pl": v}); lines.append(b)
        out.append("LL1 %s |d|>=%.2f: %s" % (mode, cut, stats(bets)))
# LL2 walk-forward quantile cuts
months = ["2025-11", "2025-12", "2026-01", "2026-02"]
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))]
allh = [(x["date"][:7], hold(x["over"], x["under"]), x) for x in L45]
for name, side, rule in (("LL2a U h>=p80", "under", ("hi", .8)), ("LL2b U h>=p90", "under", ("hi", .9)),
                         ("LL2c O h<=p20", "over", ("lo", .2)), ("LL2d U h<=p20", "under", ("lo", .2))):
    bets = []; lines = []; cuts = []
    for m in months:
        prior = [h for mm, h, _ in allh if mm < m]
        c = q(prior, rule[1]); cuts.append("%s %.3f" % (m[5:], c))
        for mm, h, x in allh:
            if mm != m: continue
            if (rule[0] == "hi" and h >= c - 1e-12) or (rule[0] == "lo" and h <= c + 1e-12):
                v = pl(x, side)
                if v == "skip" or v is None: continue
                bets.append({"gid": x["gid"], "date": x["date"], "pl": v}); lines.append(x)
    s = stats(bets)
    out.append("%s (cuts %s): %s" % (name, ", ".join(cuts), s))
    g = [b["pl"] for b in bets]
    if len(g) >= 300 and sum(g) > 0: out.append("   " + placebo(lines, sum(g) / len(g)))
hs = sorted(h for _, h, _ in allh); out.append("hold distribution Nov-Feb (incl Oct): p10 %.3f p50 %.3f p90 %.3f" % (q(hs, .1), q(hs, .5), q(hs, .9)))
print("\n".join(out))
