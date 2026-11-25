"""N31a/N31b: Pinnacle two-step trend (Researcher run 31, 2026-11-25). Registered in research/HYPOTHESES.md before any run.

Stored data only: data/odds/<date>.json (reads A, B, C, D) and data/state/box via auto_hypothesis helpers.
Discovery = every stored night; forward starts 2026-11-26 (no forward nights exist at this run).
Usage: python -I research/code/run31/trend_n31.py   (writes trend_n31_results.txt next to this file)
"""
import collections, glob, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))  # sports/nba/research/code
import auto_hypothesis as ah  # noqa: E402  (also puts sports/nba/scripts on sys.path)
import odds  # noqa: E402

FWD = "2026-11-26"
PRICE_MIN, PRICE_MAX = -200, 200
OUT = os.path.join(HERE, "trend_n31_results.txt")


def load_days():
    days = {}
    for p in sorted(glob.glob(ah.R + "data/odds/2*.json")):
        d = json.load(open(p, encoding="utf-8"))
        byg = collections.defaultdict(list)
        for f in sorted(d["fetches"], key=lambda f: f["at"]):
            byg[f["game_id"]].append(f)
        days[d["date"]] = byg
    return days


def build(days, box):
    follow, fade = [], []
    for day, byg in sorted(days.items()):
        for gid, fs in byg.items():
            reads = {}
            for f in fs:  # sorted by time; last fetch per read wins
                if f["read"] in ("A", "B", "C", "D"):
                    reads[f["read"]] = f
            if not all(r in reads for r in ("A", "B", "C")):
                continue
            A, B, C = reads["A"], reads["B"], reads["C"]
            for m in C["markets"]:
                hc = ah._hr(C, m)
                pa, pb, pc = ah._bk(A, "pinnacle", m), ah._bk(B, "pinnacle", m), ah._bk(C, "pinnacle", m)
                seen_pm = set()
                for k in sorted(hc):
                    pid, line = k
                    if (pid, m) in seen_pm:
                        continue
                    h = hc[k]
                    if not (h.get("over") and h.get("under")):
                        continue
                    fA, fB, fC = ah._fo(pa.get(k)), ah._fo(pb.get(k)), ah._fo(pc.get(k))
                    if fA is None or fB is None or fC is None:
                        continue
                    d1, d2, tot = fB - fA, fC - fB, fC - fA
                    if d1 >= 0.01 and d2 >= 0.01 and tot >= 0.03:
                        side = "over"
                    elif d1 <= -0.01 and d2 <= -0.01 and tot <= -0.03:
                        side = "under"
                    else:
                        continue
                    opp = ah.OPPOSITE[side]
                    seen_pm.add((pid, m))
                    base = dict(day=day, gid=gid, pid=pid, m=m, line=line, trend=side,
                                tot=round(tot * 100, 1), dir_fair_C=round((fC if side == "over" else 1 - fC) * 100, 1))
                    # FOLLOW: bet the trend side at Hard Rock's C price
                    p_f = h[side]
                    if PRICE_MIN <= p_f <= PRICE_MAX:
                        e = dict(base, side=side, price=p_f,
                                 res=ah._grade(box, gid, pid, m, line, side))
                        cl = ah._later(days, day, gid, C["at"], pid, m, line, side)
                        e["close_pin"] = cl.get("close_pin")
                        follow.append(e)
                    # FADE: bet the opposite side at Hard Rock's C price for that side
                    p_o = h[opp]
                    if PRICE_MIN <= p_o <= PRICE_MAX:
                        e = dict(base, side=opp, price=p_o,
                                 res=ah._grade(box, gid, pid, m, line, opp))
                        cl = ah._later(days, day, gid, C["at"], pid, m, line, opp)
                        e["close_pin"] = cl.get("close_pin")
                        fade.append(e)
    return follow, fade


def boot_ci(es, B=2000, seed=7):
    games = collections.defaultdict(list)
    for e in es:
        if e["res"] in ("W", "L"):
            games[(e["day"], e["gid"])].append(ah._units(e))
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
    actual = sum(ah._units(e) for e in g) / len(g)
    byday = collections.defaultdict(list)
    for e in g:
        byday[e["day"]].append(e)
    rng = random.Random(seed)
    ge = 0
    for _ in range(B):
        tot = 0.0
        for lst in byday.values():
            res = [e["res"] for e in lst]
            rng.shuffle(res)
            for e, r in zip(lst, res):
                tot += (odds.decimal(e["price"]) - 1) if r == "W" else -1.0
        if tot / len(g) >= actual:
            ge += 1
    return round(ge / B, 3)


def line(label, es):
    s = ah._summarize(label, es)
    ci = boot_ci(es)
    pl = placebo_share(es)
    return ("%-22s n %4d graded %4d %4d-%4d %+7.2fu ROI %6s CI90 %-16s CLV_pin %5s (n %d) placebo>=actual %s"
            % (label, s["n"], s["graded"], s["w"], s["l"], s["units"],
               ("%+.1f%%" % s["roi"]) if s["roi"] is not None else "-",
               ("[%+.1f, %+.1f]" % ci) if ci else "-",
               ("%+.1f%%" % s["clv_mean"]) if s["clv_mean"] is not None else "-",
               s["clv_n"], pl))


def main():
    box = ah._load_box()
    days = load_days()
    follow, fade = build(days, box)
    out = []
    out.append("N31 two-step Pinnacle trend. Nights: %d (%s to %s). Forward starts %s (none stored yet)."
               % (len(days), min(days), max(days), FWD))
    out.append("Population (trend up or down, Pinnacle A->B->C each step >= 1 pt, cumulative >= 3 pts, HR two-sided at C, -200..+200): "
               "follow %d, fade %d bets" % (len(follow), len(fade)))
    for tag, es in (("N31a follow", follow), ("N31b fade", fade)):
        out.append("")
        out.append(line(tag + " all", es))
        for side in ("over", "under"):
            out.append(line(tag + " " + side, [e for e in es if e["side"] == side]))
        disc = [e for e in es if e["day"] < FWD]
        fwd = [e for e in es if e["day"] >= FWD]
        out.append(line(tag + " discovery", disc))
        out.append(line(tag + " forward", fwd))
        for m in sorted({e["m"] for e in es}):
            out.append(line(tag + " mkt " + m, [e for e in es if e["m"] == m]))
    txt = "\n".join(out)
    print(txt)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
