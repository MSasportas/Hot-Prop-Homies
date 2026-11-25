"""Run 30 (2026-11-24): MK1-MK4, MOVES population split by market. Discovery only (through 2026-11-25).
Uses research/code/auto_hypothesis.py build_moves() unchanged. Output: printed table (saved to mk_results.txt beside this file)."""
import os, random, statistics, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))  # research/code
import auto_hypothesis as ah

FWD_START = "2026-11-26"  # forward starts here; everything below is discovery
DISC_END = "2026-11-25"
MARKETS = ["points", "rebounds", "assists", "threes"]
B, PERM = 2000, 2000
rng = random.Random(20261124)

moves, days_map, box = ah.build_moves()
graded = [e for e in moves if e["res"] in ("W", "L", "P") and e["day"] <= DISC_END]

def units(e):
    if e["res"] == "W":
        return ah.odds.decimal(e["price"]) - 1
    if e["res"] == "L":
        return -1.0
    return 0.0

def roi_of(es):
    g = [e for e in es if e["res"] in ("W", "L")]
    return (sum(units(e) for e in g) / len(g)) if g else None

def boot_ci(es):
    games = collections.defaultdict(list)
    for e in es:
        if e["res"] in ("W", "L"):
            games[e["gid"]].append(e)
    keys = list(games)
    if not keys:
        return None
    vals = []
    for _ in range(B):
        samp = [x for k in rng.choices(keys, k=len(keys)) for x in games[k]]
        r = roi_of(samp)
        if r is not None:
            vals.append(r)
    vals.sort()
    return vals[int(0.05 * len(vals))], vals[int(0.95 * len(vals))]

def placebo(es):
    """Permute results within the set (prices and games fixed). Share of placebo ROI >= actual."""
    g = [e for e in es if e["res"] in ("W", "L")]
    if not g:
        return None
    actual = roi_of(g)
    res = [e["res"] for e in g]
    hits = 0
    for _ in range(PERM):
        rng.shuffle(res)
        u = 0.0
        for e, r in zip(g, res):
            u += (ah.odds.decimal(e["price"]) - 1) if r == "W" else (-1.0 if r == "L" else 0.0)
        if u / len(g) >= actual:
            hits += 1
    return hits / PERM

def clv(es):
    c = [x for x in map(ah._clv_pin, es) if x is not None]
    return (statistics.mean(c) * 100, len(c)) if c else (None, 0)

out = []
out.append("Run 30 MK1-MK4 discovery (all stored nights through %s). Population: all MOVES graded W/L/P." % DISC_END)
out.append("All-market reference: " + ah.fmt_summary(ah._summarize("all", graded)))
for i, m in enumerate(MARKETS, 1):
    es = [e for e in graded if e["m"] == m]
    s = ah._summarize(m, es)
    ci = boot_ci(es)
    cm, cn = clv(es)
    rest = [e for e in graded if e["m"] != m]
    pl = placebo(es)
    ci_s = ("[%+.1f%%, %+.1f%%]" % (ci[0] * 100, ci[1] * 100)) if ci else "-"
    cm_s = ("%+.1f%%" % cm) if cm is not None else "-"
    out.append("MK%d %-9s %s | 90%% CI %s | CLV_pin mean %s (n %d) | rest-of-market ROI %s | placebo share >= actual %s" % (
        i, m, ah.fmt_summary(s), ci_s, cm_s, cn,
        ("%+.1f%%" % (roi_of(rest) * 100)) if roi_of(rest) is not None else "-",
        ("%.3f" % pl) if pl is not None else "-"))

txt = "\n".join(out)
print(txt)
with open(os.path.join(HERE, "mk_results.txt"), "w", encoding="utf-8") as fh:
    fh.write(txt + "\n")
