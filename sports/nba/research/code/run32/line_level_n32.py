"""N32a/N32b: Pinnacle main line vs Hard Rock main line (level). Registered in HYPOTHESES.md Run 32 before any run.
Usage: python -I research/code/run32/line_level_n32.py  (from sports/nba)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "run31")); sys.path.insert(0, os.path.join(HERE, ".."))
import trend_n31 as t, auto_hypothesis as ah  # noqa
OUT = os.path.join(HERE, "line_level_n32_results.txt")

def mains(q):
    best = {}
    for (pid, line), v in q.items():
        f = ah._fo(v)
        if f is None: continue
        d = abs(f - 0.5)
        if pid not in best or d < best[pid][0]: best[pid] = (d, line)
    return {p: l for p, (d, l) in best.items()}

def build(days, box):
    A, B = [], []
    for day, byg in sorted(days.items()):
        for gid, fs in byg.items():
            reads = {}
            for f in fs:
                if f["read"] in ("A", "B", "C", "D"): reads[f["read"]] = f
            done = set()
            for rd in ("B", "C"):
                if rd not in reads: continue
                f = reads[rd]
                for m in f["markets"]:
                    hq = ah._hr(f, m); pq = ah._bk(f, "pinnacle", m)
                    hl, pl = mains(hq), mains(pq)
                    for pid, l in hl.items():
                        if pid not in pl or (pid, m) in done: continue
                        diff = pl[pid] - l
                        if abs(diff) < 0.5: continue
                        done.add((pid, m))
                        side = "over" if diff > 0 else "under"
                        h = hq[(pid, l)]
                        later = [x for x in fs if x["at"] > f["at"]]
                        for tag, s, lst in (("a", side, A), ("b", ah.OPPOSITE[side], B)):
                            p = h.get(s)
                            if p is None or not (-200 <= p <= 200): continue
                            e = dict(day=day, gid=gid, pid=pid, m=m, line=l, side=s, price=p, diff=diff,
                                     res=ah._grade(box, gid, pid, m, l, s), close_pin=None)
                            if later:
                                q = ah._bk(later[-1], "pinnacle", m).get((pid, l))
                                e["close_pin"] = ah._side_p(ah._fo(q), s)
                            lst.append(e)
    return A, B

def main():
    box = ah._load_box(); days = t.load_days(); A, B = build(days, box)
    out = ["N32 Pinnacle main line vs HR main line (>=0.5). Nights %d (%s..%s). Forward from 2026-11-26." % (len(days), min(days), max(days))]
    for tag, es in (("N32a follow Pinnacle line", A), ("N32b fade", B)):
        out.append("")
        out.append(t.line(tag + " all", es))
        for s in ("over", "under"): out.append(t.line(tag + " " + s, [e for e in es if e["side"] == s]))
        for m in sorted({e["m"] for e in es}): out.append(t.line(tag + " " + m, [e for e in es if e["m"] == m]))
        out.append(t.line(tag + " |diff|>=1", [e for e in es if abs(e["diff"]) >= 1]))
        out.append(t.line(tag + " forward", [e for e in es if e["day"] >= "2026-11-26"]))
    txt = "\n".join(out); print(txt); open(OUT, "w").write(txt + "\n")
main()
