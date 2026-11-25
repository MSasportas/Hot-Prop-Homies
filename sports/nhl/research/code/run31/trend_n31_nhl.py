"""T31a/T31b: Pinnacle two-step trend ported to NHL (Researcher run 31, 2026-11-25). Registered in research/HYPOTHESES.md before any run.

Stored data only: data/odds/<date>.json (pulls A, B, C, D; markets shots and points) and data/shadow/*.json (results: result.actual, toi).
Discovery = every stored odds night; forward starts 2026-11-26.
Usage: python -I research/code/run31/trend_n31_nhl.py <repo sports/nhl dir>   (writes trend_n31_nhl_results.txt next to this file)
"""
import collections, datetime, glob, json, os, random, sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
HERE = os.path.dirname(os.path.abspath(__file__))
FWD = "2026-11-26"
PRICE_MIN, PRICE_MAX = -200, 200
HOLD_MAX = 0.15
MARKETS = ("shots", "points")
OPP = {"over": "under", "under": "over"}
OUT = os.path.join(HERE, "trend_n31_nhl_results.txt")


def be(a):
    return (-a) / (-a + 100.0) if a < 0 else 100.0 / (a + 100.0)


def dec(a):
    return 1.0 + (100.0 / -a if a < 0 else a / 100.0)


def fair(q):
    if not q or q.get("over") is None or q.get("under") is None:
        return None
    h = be(q["over"]) + be(q["under"]) - 1
    if not (0 <= h <= HOLD_MAX):
        return None
    return be(q["over"]) / (be(q["over"]) + be(q["under"]))


def pairs(m):
    out = {}
    for o in (m or {}).get("outcomes") or []:
        if o.get("pid") is None or o.get("line") is None:
            continue
        out.setdefault((str(o["pid"]), float(o["line"])), {"over": None, "under": None})[o["side"]] = o["price"]
    return out


def side_p(fp, side):
    return None if fp is None else (fp if side == "over" else 1 - fp)


# results: (game, pid, market) -> actual (None if no TOI)
res = {}
for fn in glob.glob(os.path.join(ROOT, "data/shadow/*.json")):
    for r in json.load(open(fn, encoding="utf-8")).get("rows", []):
        if not r.get("result") or r["result"].get("actual") is None:
            continue
        x = r["result"]
        toi = x.get("toi")
        key = (str(r["game_id"]), str(r["pid"]), r.get("market"), float(r["line"]))
        res[key] = None if (not toi or toi in ("0:00", "00:00")) else x["actual"]


def grade(gid, pid, m, line, side):
    a = res.get((gid, pid, m, line), "missing")
    if a == "missing":
        return "?"
    if a is None:
        return "V"
    won = (a > line) if side == "over" else (a < line)
    return "W" if won else "L"


def load_days():
    days = {}
    for fn in sorted(glob.glob(os.path.join(ROOT, "data/odds/*.json"))):
        d = json.load(open(fn, encoding="utf-8"))
        byg = collections.defaultdict(list)
        for f in sorted(d["fetches"], key=lambda f: f["at"]):
            byg[str(f["game_id"])].append(f)
        days[os.path.basename(fn)[:10]] = byg
    return days


def build(days):
    follow, fade = [], []
    for day, byg in sorted(days.items()):
        for gid, fs in byg.items():
            pulls = {}
            for f in fs:
                if f.get("pull") in ("A", "B", "C", "D"):
                    pulls[f["pull"]] = f
            if not all(p in pulls for p in ("A", "B", "C")):
                continue
            A, B, C = pulls["A"], pulls["B"], pulls["C"]
            for m in MARKETS:
                if m not in (C.get("markets") or {}):
                    continue
                hc = pairs(C["markets"][m])
                pa = pairs(((A.get("others") or {}).get("pinnacle") or {}).get(m))
                pb = pairs(((B.get("others") or {}).get("pinnacle") or {}).get(m))
                pc = pairs(((C.get("others") or {}).get("pinnacle") or {}).get(m))
                seen = set()
                for k in sorted(hc):
                    pid, line = k
                    if pid in seen:
                        continue
                    h = hc[k]
                    if h.get("over") is None or h.get("under") is None:
                        continue
                    fA, fB, fC = fair(pa.get(k)), fair(pb.get(k)), fair(pc.get(k))
                    if fA is None or fB is None or fC is None:
                        continue
                    d1, d2, tot = fB - fA, fC - fB, fC - fA
                    if d1 >= 0.01 and d2 >= 0.01 and tot >= 0.03:
                        side = "over"
                    elif d1 <= -0.01 and d2 <= -0.01 and tot <= -0.03:
                        side = "under"
                    else:
                        continue
                    seen.add(pid)
                    base = dict(day=day, gid=gid, pid=pid, m=m, line=line, trend=side)
                    for tag, s, lst in (("follow", side, follow), ("fade", OPP[side], fade)):
                        price = h[s]
                        if price is None or not (PRICE_MIN <= price <= PRICE_MAX):
                            continue
                        e = dict(base, side=s, price=price, res=grade(gid, pid, m, line, s))
                        # close: Pinnacle fair on the same side at the last pull after C (D read)
                        later = [f for f in fs if f["at"] > C["at"]]
                        close = None
                        if later:
                            pl = pairs(((later[-1].get("others") or {}).get("pinnacle") or {}).get(m)).get(k)
                            close = side_p(fair(pl), s)
                        e["close_pin"] = close
                        lst.append(e)
    return follow, fade


def units(e):
    return (dec(e["price"]) - 1) if e["res"] == "W" else (-1.0 if e["res"] == "L" else 0.0)


def boot_ci(es, B=2000, seed=7):
    games = collections.defaultdict(list)
    for e in es:
        if e["res"] in ("W", "L"):
            games[(e["day"], e["gid"])].append(units(e))
    keys = list(games)
    if not keys:
        return None
    rng = random.Random(seed)
    rois = []
    for _ in range(B):
        samp = [rng.choice(keys) for _ in keys]
        tot = sum(sum(games[k]) for k in samp)
        n = sum(len(games[k]) for k in samp)
        rois.append(tot / n * 100)
    rois.sort()
    return round(rois[int(0.05 * B)], 1), round(rois[int(0.95 * B)], 1)


def placebo_share(es, B=500, seed=11):
    g = [e for e in es if e["res"] in ("W", "L")]
    if not g:
        return None
    actual = sum(units(e) for e in g) / len(g)
    byday = collections.defaultdict(list)
    for e in g:
        byday[e["day"]].append(e)
    rng = random.Random(seed)
    ge = 0
    for _ in range(B):
        tot = 0.0
        for lst in byday.values():
            res_ = [e["res"] for e in lst]
            rng.shuffle(res_)
            for e, r in zip(lst, res_):
                tot += (dec(e["price"]) - 1) if r == "W" else -1.0
        if tot / len(g) >= actual:
            ge += 1
    return round(ge / B, 3)


def line(label, es):
    g = [e for e in es if e["res"] in ("W", "L")]
    w = sum(e["res"] == "W" for e in g)
    u = sum(units(e) for e in g)
    roi = (u / len(g) * 100) if g else None
    clvs = [e["close_pin"] * dec(e["price"]) - 1 for e in es if e.get("close_pin") is not None]
    clv = (sum(clvs) / len(clvs) * 100) if clvs else None
    ci = boot_ci(es)
    pl = placebo_share(es)
    return ("%-22s n %4d graded %4d %4d-%4d %+7.2fu ROI %6s CI90 %-16s CLV_pin %5s (n %d) placebo>=actual %s"
            % (label, len(es), len(g), w, len(g) - w, u,
               ("%+.1f%%" % roi) if roi is not None else "-",
               ("[%+.1f, %+.1f]" % ci) if ci else "-",
               ("%+.1f%%" % clv) if clv is not None else "-",
               len(clvs), pl))


def main():
    days = load_days()
    follow, fade = build(days)
    out = ["T31 two-step Pinnacle trend, NHL. Nights: %d (%s to %s). Forward starts %s."
           % (len(days), min(days), max(days), FWD),
           "Population: follow %d, fade %d bets (shots and points, -200..+200 at read C)" % (len(follow), len(fade))]
    for tag, es in (("T31a follow", follow), ("T31b fade", fade)):
        out.append("")
        out.append(line(tag + " all", es))
        for side in ("over", "under"):
            out.append(line(tag + " " + side, [e for e in es if e["side"] == side]))
        for m in MARKETS:
            out.append(line(tag + " mkt " + m, [e for e in es if e["m"] == m]))
        out.append(line(tag + " discovery", [e for e in es if e["day"] < FWD]))
        out.append(line(tag + " forward", [e for e in es if e["day"] >= FWD]))
    txt = "\n".join(out)
    print(txt)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
