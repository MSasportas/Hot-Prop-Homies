#!/usr/bin/env python3
"""Run 26 history tests NN1 (props lean vs sides market) and NN2 (Hard Rock moneyline off the market), as registered in HYPOTHESES.md.
Nov 2025 - Feb 2026 only; the lockbox (Mar 1+) is never read.
python3 -I nn_hist.py <extracted hist bundle dir> <extracted h2h addon dir>"""
import glob, json, os, random, sys
from datetime import datetime
B, A = sys.argv[1], sys.argv[2]
END = "2026-03-01"
NAMES = {"Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF", "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR",
         "Chicago Blackhawks": "CHI", "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL", "Detroit Red Wings": "DET",
         "Edmonton Oilers": "EDM", "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montréal Canadiens": "MTL",
         "Nashville Predators": "NSH", "New Jersey Devils": "NJD", "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT",
         "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS", "Seattle Kraken": "SEA", "St Louis Blues": "STL",
         "Tampa Bay Lightning": "TBL", "Toronto Maple Leafs": "TOR", "Utah Mammoth": "UTA", "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK",
         "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"}


def iso(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))
def dec(a): return 1 + a / 100.0 if a > 0 else 1 + 100.0 / -a
def fair(o, u): a, b = 1 / dec(o), 1 / dec(u); return a / (a + b)
def hold(o, u): return 1 / dec(o) + 1 / dec(u) - 1
def med(v): v = sorted(v); n = len(v); return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
def q(v, p): v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))]


L45 = [x for x in (json.loads(l) for l in open(os.path.join(B, "work", "shots45_lines.jsonl")))
       if x["date"] < END and x.get("over") is not None and x.get("under") is not None]
for x in L45: x["f"] = fair(x["over"], x["under"])

# moneyline snapshots (only files dated before the lockbox are opened)
ML = {}  # (home, away, commence) -> list of (ts, {book: p_home})
for f in sorted(glob.glob(os.path.join(A, "feat", "*.json"))):
    if os.path.basename(f).split("_")[1][:10] >= END: continue
    d = json.load(open(f)); ts = iso(d["timestamp"])
    for g in d["data"]:
        h, a = NAMES.get(g["home_team"]), NAMES.get(g["away_team"])
        if not h or not a: continue
        bk = {}
        for b in g["bookmakers"]:
            for m in b["markets"]:
                if m["key"] != "h2h": continue
                oc = {o["name"]: o["price"] for o in m["outcomes"]}
                if g["home_team"] not in oc or g["away_team"] not in oc: continue
                ph, pa = oc[g["home_team"]], oc[g["away_team"]]
                if 0 <= hold(ph, pa) <= 0.15: bk[b["key"]] = fair(ph, pa)
        ML.setdefault((h, a, iso(g["commence_time"])), []).append((ts, bk))

games = {}
for x in L45: games.setdefault(x["gid"], []).append(x)
gml = {}  # gid -> {team: (market p, hr p or None)}
nomatch = 0
for gid, rows in games.items():
    x0 = rows[0]
    home = x0["team"] if x0["home"] else x0["opp"]; away = x0["opp"] if x0["home"] else x0["team"]
    snaps = ML.get((home, away, iso(x0["start"])))
    at = min(iso(r["at"]) for r in rows)
    ok = [s for s in (snaps or []) if s[0] < at]
    if not ok: nomatch += 1; continue
    ts, bk = max(ok, key=lambda s: s[0])
    oth = [v for k, v in bk.items() if k != "hardrockbet"]
    if len(oth) < 4: nomatch += 1; continue
    ph = med(oth); hr = bk.get("hardrockbet")
    gml[gid] = {home: (ph, hr), away: (1 - ph, None if hr is None else 1 - hr)}


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


def placebo(lines, actual, k=200):
    rng = random.Random(3); hits = 0; rs = []
    for _ in range(k):
        t = [v for v in (pl(x, rng.choice(("over", "under"))) for x in lines) if isinstance(v, float)]
        r = sum(t) / len(t); rs.append(r); hits += r >= actual
    return "placebo mean %+.1f%%, %d/%d >= actual" % (100 * sum(rs) / k, hits, k)


V = ["NN1a fade", "NN1b follow", "NN2a follow market", "NN2b follow HR"]
bets = {v: [] for v in V}
out = ["games with a usable moneyline snapshot before the -45 read: %d of %d (dropped %d)" % (len(gml), len(games), nomatch)]
months = sorted({x["date"][:7] for x in L45})


def add(v, x, side):
    r = pl(x, side)
    if r is None or r == "skip": return
    bets[v].append({"gid": x["gid"], "date": x["date"], "pl": r, "x": x})


for m in months:
    if m < "2025-11": continue
    prior = [x for x in L45 if x["date"][:7] < m]; cur = [x for x in L45 if x["date"][:7] == m]
    ml = {}
    for x in prior: ml.setdefault(x["line"], []).append(x["f"])
    mL = {L: sum(v) / len(v) for L, v in ml.items() if len(v) >= 50}

    def teams(rows):
        t = {}
        for x in rows:
            if x["line"] in mL and x["gid"] in gml: t.setdefault((x["gid"], x["team"]), []).append(x)
        return {k: (sum(r["f"] - mL[r["line"]] for r in v) / len(v), v) for k, v in t.items() if len(v) >= 4}
    tp = teams(prior)
    xs = [gml[g][tm][0] - 0.5 for (g, tm) in tp]; ys = [s for s, _ in tp.values()]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs); a0 = my - b * mx
    res = [c - (a0 + b * a) for a, c in zip(xs, ys)]
    lo, hi = q(res, 0.2), q(res, 0.8)
    for (g, tm), (s, rows) in teams(cur).items():
        r = s - (a0 + b * (gml[g][tm][0] - 0.5))
        if r >= hi: fade = "under"
        elif r <= lo: fade = "over"
        else: continue
        fol = "over" if fade == "under" else "under"
        for x in rows: add("NN1a fade", x, fade); add("NN1b follow", x, fol)
    nev = 0
    for x in cur:
        if x["gid"] not in gml: continue
        p, h = gml[x["gid"]][x["team"]]
        if h is None: continue
        d = h - p
        if abs(d) < 0.02 - 1e-12: continue
        nev += 1
        mk = "over" if d < 0 else "under"
        add("NN2a follow market", x, mk); add("NN2b follow HR", x, "under" if mk == "over" else "over")
    out.append("%s: lines %d, fit s = %+.4f %+.4f*(p-.5) on %d prior game-teams, r q20 %+.4f q80 %+.4f; NN2 event lines %d" % (m, len(cur), a0, b, len(xs), lo, hi, nev))
for v in V:
    out.append("%s: %s" % (v, stats(bets[v])))
    g = [z for z in bets[v] if isinstance(z["pl"], float)]
    if len(g) >= 300 and sum(z["pl"] for z in g) > 0:
        out.append("  " + placebo([z["x"] for z in g], sum(z["pl"] for z in g) / len(g)))
print("\n".join(out))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "nn_hist_results.txt"), "w").write("\n".join(out) + "\n")
