#!/usr/bin/env python3
"""Run 24 forward scorer: LL1f, LL3a-b, LL4a-b, LL5, LL6 (research/HYPOTHESES.md, registered 2026-11-09 before testing).
Judged nights >= 2026-11-09; earlier nights printed as a labelled descriptive check only. Read-only on data/; writes research/fwd/ll.md
and research/fwd/ll.json.  python3 -I score_ll.py [repo_root]"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fwd"))
import score_fwd as F  # noqa: E402  (reads_for, shadow, grade, ev, summarize, pairs, fair_over, hold, dec, iso)

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", ".."))
F.ROOT = ROOT
START = "2026-11-09"
NV = 53
F.BONF = NV
EXCH = ("novig", "prophetx")
VARS = ["LL1f-follow", "LL1f-fade", "LL3a tight", "LL3b loose", "LL4a fade", "LL4b follow", "LL5 exch", "LL6 line"]


def other_mains(date):
    """{(game_id, at_iso): {pid: [main line per book]}} for B/C reads, LL6."""
    doc = F.load(os.path.join(ROOT, "data/odds", date + ".json"))
    out = {}
    for f in doc["fetches"]:
        if "others" not in f or f["pull"] not in ("B", "C"):
            continue
        at = F.iso(f["at"])
        per = {}
        for b, mks in (f.get("others") or {}).items():
            mk = (mks or {}).get("shots")
            if not mk or not mk.get("last_update") or (at - F.iso(mk["last_update"])).total_seconds() / 60 >= F.STALE_MIN:
                continue
            best = {}
            for (pid, line), p in F.pairs(mk.get("outcomes")).items():
                if not (0 <= F.hold(p["over"], p["under"]) <= 0.15):
                    continue
                dist = abs(F.fair_over(p["over"], p["under"]) - 0.5)
                if pid not in best or dist < best[pid][0]:
                    best[pid] = (dist, line)
            for pid, (_, line) in best.items():
                per.setdefault(pid, []).append(line)
        out[(f["game_id"], at.isoformat())] = per
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
        return F.ev(fair if side == "over" else 1 - fair, r[side])

    # LL1f: first A vs last C, same game/player/line
    firstA, lastC = {}, {}
    for r in pre:
        k = (r["game"], r["pid"], r["line"])
        if r["pull"] == "A" and k not in firstA:
            firstA[k] = r
        if r["pull"] == "C":
            lastC[k] = r
    for k, c in lastC.items():
        a = firstA.get(k)
        if not a:
            continue
        d = c["hr_fair"] - a["hr_fair"]
        if abs(d) < 0.01 - 1e-12:
            continue
        tow = "over" if d > 0 else "under"
        away = "under" if tow == "over" else "over"
        e = lambda s: evs(c["cons"], c, s) if c["cons"] is not None else 0.0
        add("LL1f-follow", c, tow, e(tow))
        add("LL1f-fade", c, away, e(away))
    # LL3, LL5 (B/C, first qualifying read)
    for r in pre:
        if r["pull"] not in ("B", "C"):
            continue
        if r["cons"] is not None and r["books"] >= 4:
            spread = max(r["fairs"].values()) - min(r["fairs"].values())
            for s in ("over", "under"):
                e = evs(r["cons"], r, s)
                if e >= 0.01 - 1e-12:
                    add("LL3a tight" if spread <= 0.04 + 1e-12 else "LL3b loose", r, s, e)
        ex = [r["fairs"][b] for b in EXCH if b in r["fairs"]]
        if ex:
            xf = sum(ex) / len(ex)
            for s in ("over", "under"):
                e = evs(xf, r, s)
                if e >= 0.02 - 1e-12:
                    add("LL5 exch", r, s, e)
    # LL4: consecutive reads of the same game (by pull order), same pid/line
    by_game = {}
    for r in pre:
        by_game.setdefault(r["game"], {}).setdefault(r["at"], {})[(r["pid"], r["line"])] = r
    for g, snaps in by_game.items():
        ts = sorted(snaps)
        for t1, t2 in zip(ts, ts[1:]):
            for k, r2 in snaps[t2].items():
                r1 = snaps[t1].get(k)
                if not r1:
                    continue
                common = set(r1["fairs"]) & set(r2["fairs"])
                if len(common) < 4:
                    continue
                m1 = F.median([r1["fairs"][b] for b in common]); m2 = F.median([r2["fairs"][b] for b in common])
                dhr = r2["hr_fair"] - r1["hr_fair"]; dm = m2 - m1
                if abs(dhr) < 0.02 - 1e-12 or dm * (1 if dhr > 0 else -1) >= 0.005:
                    continue
                tow = "over" if dhr > 0 else "under"; away = "under" if tow == "over" else "over"
                add("LL4a fade", r2, away, evs(m2, r2, away))
                add("LL4b follow", r2, tow, evs(m2, r2, tow))
    # LL6
    mains = other_mains(date)
    hr_main = {}
    for r in pre:
        if r["pull"] not in ("B", "C"):
            continue
        k = (r["game"], r["at"].isoformat(), r["pid"])
        dist = abs(r["hr_fair"] - 0.5)
        if k not in hr_main or dist < hr_main[k][0]:
            hr_main[k] = (dist, r)
    for (g, at, pid), (_, r) in sorted(hr_main.items(), key=lambda x: x[0][1]):
        ls = mains.get((g, at), {}).get(pid, [])
        if len(ls) < 3:
            continue
        up = sum(1 for x in ls if x > r["line"]); dn = sum(1 for x in ls if x < r["line"])
        side = "over" if up * 2 > len(ls) else ("under" if dn * 2 > len(ls) else None)
        if side:
            add("LL6 line", r, side, evs(r["cons"], r, side) if r["cons"] is not None else 0.0)
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
    out = ["# Run 24 forward (research/code/r24/score_ll.py): LL1f, LL3-LL6, nights >= %s. Bar: n >= 300 graded, ROI > 0, p < %.5f, mean CLV > 0." % (START, 0.05 / NV), "", hdr]
    out += [row(v, [b for b in allb[v] if b["date"] >= START]) for v in VARS]
    out += ["", "Descriptive, seen nights < %s (not a test, never a result):" % START, "", hdr]
    out += [row(v, [b for b in allb[v] if b["date"] < START]) for v in VARS]
    open(os.path.join(ROOT, "research/fwd/ll.md"), "w").write("\n".join(out) + "\n")
    json.dump({v: F.summarize([b for b in allb[v] if b["date"] >= START]) for v in VARS}, open(os.path.join(ROOT, "research/fwd/ll.json"), "w"), indent=1)
    print("\n".join(out))


if __name__ == "__main__":
    main()
