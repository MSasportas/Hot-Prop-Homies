"""Run 30 (2026-11-24): PT1 (EV >= +2%) and PT2 (EV >= 0%) on NHL points shadow rows vs the other books' median fair.
Discovery only (shadow nights through 2026-11-25). Output saved to pt_results.txt beside this file."""
import glob, json, os, random, statistics, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))  # repo root
DISC_END = "2026-11-25"
B, PERM = 2000, 2000
rng = random.Random(20261124)

def dec(p):
    return 1 + (p / 100.0) if p > 0 else 1 + (100.0 / -p)

rows = []
for f in sorted(glob.glob(os.path.join(ROOT, "sports", "nhl", "data", "shadow", "2*.json"))):
    day = os.path.basename(f)[:10]
    if day > DISC_END:
        continue
    for r in json.load(open(f, encoding="utf-8")).get("rows", []):
        if r.get("market") != "points":
            continue
        o = r.get("open") or {}
        res = r.get("result") or {}
        cons = o.get("cons_fair_over_med")
        over, under = o.get("over"), o.get("under")
        if cons is None or over is None or under is None:
            continue
        if not (-200 <= over <= 200 and -200 <= under <= 200):
            continue
        ev_o = cons * dec(over) - 1
        ev_u = (1 - cons) * dec(under) - 1
        side, ev, price = ("over", ev_o, over) if ev_o >= ev_u else ("under", ev_u, under)
        hr_close_fair = None
        c = r.get("close") or {}
        if c.get("fair_over") is not None:
            hr_close_fair = c["fair_over"] if side == "over" else 1 - c["fair_over"]
        rows.append(dict(day=day, gid=r.get("game_id"), side=side, ev=ev, price=price,
                         res=res.get(side), clv_hr=(hr_close_fair * dec(price) - 1) if hr_close_fair is not None else None))

def units(e):
    if e["res"] == "W":
        return dec(e["price"]) - 1
    if e["res"] == "L":
        return -1.0
    return 0.0

def summarize(es):
    g = [e for e in es if e["res"] in ("W", "L")]
    if not g:
        return "n 0"
    u = sum(units(e) for e in g)
    w = sum(e["res"] == "W" for e in g)
    clv = [e["clv_hr"] for e in g if e["clv_hr"] is not None]
    return "n %d graded %d %d-%d %+.2fu ROI %+.1f%% CLV_HR %s (n %d)" % (
        len(es), len(g), w, len(g) - w, u, 100 * u / len(g),
        ("%+.1f%%" % (100 * statistics.mean(clv))) if clv else "-", len(clv))

def boot(es):
    games = collections.defaultdict(list)
    for e in es:
        if e["res"] in ("W", "L"):
            games[e["gid"]].append(e)
    keys = list(games)
    vals = []
    for _ in range(B):
        samp = [x for k in rng.choices(keys, k=len(keys)) for x in games[k]]
        if samp:
            vals.append(sum(units(x) for x in samp) / len(samp))
    vals.sort()
    if not vals:
        return float('nan'), float('nan')
    return vals[int(0.05 * len(vals))], vals[int(0.95 * len(vals))]

def placebo(es):
    g = [e for e in es if e["res"] in ("W", "L")]
    if not g:
        return None
    actual = sum(units(e) for e in g) / len(g)
    res = [e["res"] for e in g]
    hits = 0
    for _ in range(PERM):
        rng.shuffle(res)
        u = sum((dec(e["price"]) - 1) if r == "W" else (-1.0 if r == "L" else 0.0) for e, r in zip(g, res))
        if u / len(g) >= actual:
            hits += 1
    return hits / PERM

print("rows", len(rows), "graded", sum(e["res"] in ("W","L") for e in rows), "ev>=2%", sum(e["ev"]>=0.02 for e in rows), "ev>=0", sum(e["ev"]>=0 for e in rows))
out = ["Run 30 PT1/PT2 discovery (NHL points shadow rows, all nights through %s; %d rows with consensus and both sides)." % (DISC_END, len(rows))]
for name, bar in (("PT1", 0.02), ("PT2", 0.0)):
    es = [e for e in rows if e["ev"] >= bar]
    lo, hi = boot(es)
    pl = placebo(es)
    out.append("%s EV >= %+.0f%%: %s | 90%% CI %+.1f%%, %+.1f%% | placebo share >= actual %.3f" % (
        name, bar * 100, summarize(es), lo * 100, hi * 100, pl if pl is not None else -1))
    out.append("   by side: " + " | ".join("%s %s" % (s, summarize([e for e in es if e["side"] == s])) for s in ("over", "under")))
txt = "\n".join(out)
print(txt)
with open(os.path.join(HERE, "pt_results.txt"), "w", encoding="utf-8") as fh:
    fh.write(txt + "\n")
