"""Run 23 tests JJ1-JJ3 (registered run 22, 2026-11-06) and KK1-KK3 (registered run 23, commit 87a4a5c6), all before testing.
Inputs (scratch, PC_R23_DIR): h/work/shots45_lines.jsonl (hist tgz), nhl/skater_2526.jsonl + nhl/skater_rt_2526.jsonl (r23/fetch23.py,
Feb 28 cut-off). Lockbox rows (Mar 1+) never built or scored.  python3 -I kk23.py [placebo NAME [T]]"""
import contextlib, io, json, os, random, sys
from bisect import bisect_left
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rlib, wf  # noqa: E402

D = os.environ["PC_R23_DIR"]
SK = [json.loads(l) for l in open(os.path.join(D, "nhl/skater_2526.jsonl"))]
SK = [r for r in SK if r["gameDate"] < rlib.LOCKBOX]
RT = [json.loads(l) for l in open(os.path.join(D, "nhl/skater_rt_2526.jsonl"))]
RT = [r for r in RT if r["gameDate"] < rlib.LOCKBOX]

# team-game table
tg = {}  # (gid, team) -> dict
for r in SK:
    k = (r["gameId"], r["teamAbbrev"])
    x = tg.setdefault(k, {"date": r["gameDate"], "gid": r["gameId"], "team": r["teamAbbrev"], "opp": r["opponentTeamAbbrev"],
                          "home": r["homeRoad"] == "H", "sf": 0, "gv": 0, "tk": 0})
    x["sf"] += r["shots"] or 0
for r in RT:
    k = (r["gameId"], r["teamAbbrev"])
    if k in tg:
        tg[k]["gv"] += r["giveaways"] or 0
        tg[k]["tk"] += r["takeaways"] or 0
for x in tg.values():
    o = tg.get((x["gid"], x["opp"]))
    x["sa"] = o["sf"] if o else None
tlist = defaultdict(list)
for x in tg.values():
    tlist[x["team"]].append(x)
for v in tlist.values():
    v.sort(key=lambda x: x["date"])
tdates = {t: [x["date"] for x in v] for t, v in tlist.items()}
allg = sorted(tg.values(), key=lambda x: x["date"])
alld = [x["date"] for x in allg]
csf = np.cumsum([x["sf"] for x in allg]); cgv = np.cumsum([x["gv"] for x in allg]); ctk = np.cumsum([x["tk"] for x in allg])


def league_mean(c, d):
    i = bisect_left(alld, d)
    return c[i - 1] / i if i else 0.0


def prior_t(t, d):
    return tlist.get(t, [])[:bisect_left(tdates.get(t, []), d)]


plog = defaultdict(list)
for r in SK:
    plog[r["playerId"]].append((r["gameDate"], r["gameId"], r["shots"] or 0, r["points"] or 0, r["teamAbbrev"]))
for v in plog.values():
    v.sort()
pdates = {p: [x[0] for x in v] for p, v in plog.items()}

lines = [json.loads(l) for l in open(os.path.join(D, "h/work/shots45_lines.jsonl"))]
lines = [r for r in lines if r["date"] < rlib.LOCKBOX and r["over"] is not None and r["under"] is not None]
for r in lines:
    d, t, o, pid = r["date"], r["team"], r["opp"], r["pid"]
    me = plog.get(pid, [])[:bisect_left(pdates.get(pid, []), d)]
    s = [x[2] for x in me]
    f = rlib.fair_prop(r["over"], r["under"])
    isF = float(r["pos"] != "D")
    # JJ1 mean vs median, last 20
    mm = mx = 0.0
    if len(s) >= 10:
        a = np.array(s[-20:], float); m = a.mean()
        mm = float(m - np.median(a)); mx = float((a.max() - m) / np.sqrt(max(m, 0.5)))
    r["mm"], r["mx"] = mm, mx
    # JJ2 opponent / own shots-for
    lm = league_mean(csf, d)
    og = prior_t(o, d)[-20:]; ow = prior_t(t, d)[-20:]
    r["opf"] = float(np.mean([x["sf"] for x in og]) - lm) if len(og) >= 5 else 0.0
    r["tpf"] = float(np.mean([x["sf"] for x in ow]) - lm) if len(ow) >= 5 else 0.0
    r["opfD"] = r["opf"] * (1 - isF)
    # JJ3 hit rate vs tonight's line
    hr10 = None
    if len(s) >= 10:
        hr10 = float(np.mean([v > r["line"] for v in s[-10:]]))
    r["hr10"] = hr10 if hr10 is not None else -1.0
    r["dh"] = (hr10 - f) if hr10 is not None else 0.0
    r["dhx"] = r["dh"] * float(hr10 is not None and (hr10 >= 0.8 or hr10 <= 0.2))
    # KK1 point streak
    ps, pf, sf = 0, 0.0, 0.0
    if len(me) >= 5:
        for x in reversed(me):
            if x[3] >= 1:
                ps += 1
            else:
                break
        pts = [x[3] for x in me]
        pf = float(sum(pts[-5:]) - 5 * np.mean(pts)); sf = float(np.mean(s[-5:]) - np.mean(s))
    r["ps"], r["ps8"], r["sf"], r["pfsf"] = ps, float(min(ps, 8)), sf, pf - sf
    # KK2 opponent venue split in shots against
    oall = [x for x in prior_t(o, d) if x["sa"] is not None]
    o_home_tonight = not r["home"]
    ov = [x for x in oall if x["home"] == o_home_tonight][-10:]
    o20 = oall[-20:]
    r["osv"] = float(np.mean([x["sa"] for x in ov]) - np.mean([x["sa"] for x in o20])) if len(ov) >= 5 and len(o20) >= 5 else 0.0
    m20 = me[-20:]
    if len(m20) >= 5:
        tot = sum(tg[(x[1], x[4])]["sf"] for x in m20 if (x[1], x[4]) in tg)
        r["h"] = float(sum(x[2] for x in m20) / tot) if tot else 0.0
    else:
        r["h"] = 0.0
    r["osvh"] = r["osv"] * r["h"]
    # KK3 opponent giveaways / takeaways
    if len(og) >= 5:
        r["ogv"] = float(np.mean([x["gv"] for x in og]) - league_mean(cgv, d))
        r["otk"] = float(np.mean([x["tk"] for x in og]) - league_mean(ctk, d))
    else:
        r["ogv"] = r["otk"] = 0.0
    r["ogvF"] = r["ogv"] * isF

feats = {"JJ1": lambda r: [r["mm"], r["mx"]], "JJ2": lambda r: [r["opf"], r["opfD"], r["tpf"]], "JJ3": lambda r: [r["dh"], r["dhx"]],
         "KK1": lambda r: [r["ps8"], r["pfsf"]], "KK2": lambda r: [r["osv"], r["osvh"]], "KK3": lambda r: [r["ogv"], r["ogvF"], r["otk"]]}
KEYS = {"JJ1": ["mm", "mx"], "JJ2": ["opf", "opfD", "tpf"], "JJ3": ["dh", "dhx"], "KK1": ["ps8", "pfsf"], "KK2": ["osv", "osvh"],
        "KK3": ["ogv", "ogvF", "otk"]}
RULES = {"JJ1r": (lambda r: "under" if r["mm"] >= 0.5 else None, ["mm"]),
         "JJ2r": (lambda r: "under" if r["opf"] >= 3.0 else None, ["opf"]),
         "JJ3r": (lambda r: "under" if r["hr10"] >= 0.8 else None, ["hr10"]),
         "KK1r": (lambda r: "under" if r["ps"] >= 4 and r["sf"] <= 0 else None, ["ps", "sf"]),
         "KK2r": (lambda r: "over" if r["osv"] >= 2.5 and r["h"] >= 0.08 else None, ["osv", "h"]),
         "KK3r": (lambda r: "over" if r["pos"] != "D" and r["ogv"] >= 3.0 else None, ["ogv"])}
DESC = {"JJ1r": "UNDER when mean - median (last 20) >= .5", "JJ2r": "UNDER when opponent SOG-for >= league +3",
        "JJ3r": "UNDER when 8+ of last 10 cleared tonight's line", "KK1r": "UNDER on 4+ game point streak with SOG form <= 0",
        "KK2r": "OVER when opponent allows 2.5+ more SOG at tonight's venue type, his share >= 8%",
        "KK3r": "OVER forwards vs opponents with giveaways >= league +3/game"}


def fixed(name, rule, quiet=False):
    b = []
    for r in lines:
        if r["date"][:7] not in rlib.TEST_MONTHS or r["result"] != "OK" or not r["ok"]:
            continue
        side = rule(r)
        if side is None or r[side] < -200:
            continue
        b.append(rlib.bet(r["gid"], r["date"], r[side], (r["actual"] > r["line"]) == (side == "over"), side=side, line=r["line"]))
    s = rlib.summ(b)
    if not quiet:
        print("%s %s | %s | p_one %s" % (name, rlib.fmt(s), rlib.by_month(b), s.get("p_one")))
    return b


def shuffle_run(ks, fn, reps=200):
    rng = random.Random(7); grp = defaultdict(list); out = []
    for r in lines:
        grp[(r["date"], r["line"])].append(r)
    orig = {k: [r[k] for r in lines] for k in ks}
    for _ in range(reps):
        for gg in grp.values():
            idx = list(range(len(gg))); rng.shuffle(idx)
            vals = {k: [gg[j][k] for j in idx] for k in ks}
            for j, r in enumerate(gg):
                for k in ks:
                    r[k] = vals[k][j]
        with contextlib.redirect_stdout(io.StringIO()):
            out.append(fn())
        for k in ks:
            for r, x in zip(lines, orig[k]):
                r[k] = x
    return np.array(out)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "placebo":
        name = sys.argv[2]
        if name in RULES:
            rule, ks = RULES[name]
            real = rlib.summ(fixed(name, rule, True))["roi"]
            out = shuffle_run(ks, lambda: rlib.summ(fixed(name, rule, True))["roi"] or 0.0)
            print("placebo %s real %+.2f%% shuffled mean %+.2f%% >= real %d/200" % (name, 100 * real, 100 * out.mean(), int((out >= real).sum())))
        else:
            T = float(sys.argv[3])
            run = lambda: rlib.summ(wf.run(name, lines, feats[name], Ts=(T,), verbose=False)[T])["roi"] or 0.0
            with contextlib.redirect_stdout(io.StringIO()):
                real = run()
            out = shuffle_run(KEYS[name], run)
            print("placebo %s T=%.2f real %+.2f%% shuffled mean %+.2f%% >= real %d/200" % (name, T, 100 * real, 100 * out.mean(), int((out >= real).sum())))
        sys.exit()
    te = [r for r in lines if r["date"][:7] in rlib.TEST_MONTHS and r["result"] == "OK"]
    print("lines", len(lines), "graded Nov-Feb lines", len(te), "team-games", len(tg))
    for k in ["mm", "mx", "opf", "tpf", "dh", "hr10", "ps", "pfsf", "osv", "h", "ogv", "otk"]:
        a = np.array([r[k] for r in te], float)
        print("feature %s mean %.4f sd %.4f nonzero %d" % (k, a.mean(), a.std(), int((a != 0).sum())))
    for n in ("JJ1", "JJ2", "JJ3", "KK1", "KK2", "KK3"):
        wf.run(n, lines, feats[n])
    for n, (rule, _) in RULES.items():
        fixed("%s %s" % (n, DESC[n]), rule)
