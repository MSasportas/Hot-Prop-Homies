"""S33n (price shop) and H33n (HR lags consensus), NBA. Registered in HYPOTHESES.md Run 33 before any run.
Usage (from sports/nba): python -I research/code/run33/nba_r33.py"""
import os, sys, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "run31")); sys.path.insert(0, os.path.join(HERE, ".."))
import trend_n31 as t, auto_hypothesis as ah  # noqa
from odds import decimal as dec  # noqa
OUT = os.path.join(HERE, "nba_r33_results.txt")

def others(f, m):
    return {b: ah._bk(f, b, m) for b in (f.get("others") or {})}

def cons(f, m, k):
    qs = [x for x in (ah._fo(o.get(k)) for o in others(f, m).values()) if x is not None]
    return statistics.median(qs) if len(qs) >= 3 else None

def close_of(fs, f, m, k, s):
    later = [x for x in fs if x["at"] > f["at"]]
    if not later: return None
    return ah._side_p(cons(later[-1], m, k), s)

def build(days, box):
    S, H = [], []
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
                    hq = ah._hr(f, m); oth = others(f, m)
                    for k, h in sorted(hq.items()):
                        pid, line = k
                        if (pid, m) in done or not (h.get("over") and h.get("under")): continue
                        books = [o[k] for o in oth.values() if k in o and ah._fo(o[k]) is not None]
                        if len(books) < 3: continue
                        for s in ("over", "under"):
                            med = statistics.median(dec(b[s]) for b in books)
                            if dec(h[s]) >= med * 1.05 and -200 <= h[s] <= 200:
                                done.add((pid, m))
                                S.append(dict(day=day, gid=gid, pid=pid, m=m, line=line, side=s, price=h[s],
                                              res=ah._grade(box, gid, pid, m, line, s), close_pin=close_of(fs, f, m, k, s)))
                                break
            if "A" in reads and "C" in reads:
                A, C = reads["A"], reads["C"]; done = set()
                for m in C["markets"]:
                    if m not in A["markets"]: continue
                    ha, hc = ah._hr(A, m), ah._hr(C, m)
                    for k, h in sorted(hc.items()):
                        pid, line = k
                        if (pid, m) in done or k not in ha: continue
                        fa, fc = ah._fo(ha[k]), ah._fo(h)
                        ca, cc = cons(A, m, k), cons(C, m, k)
                        if None in (fa, fc, ca, cc): continue
                        dc, dh = cc - ca, fc - fa
                        if dc >= 0.02 and dh < 0.005: s = "over"
                        elif dc <= -0.02 and dh > -0.005: s = "under"
                        else: continue
                        if h.get(s) is None or not (-200 <= h[s] <= 200): continue
                        done.add((pid, m))
                        H.append(dict(day=day, gid=gid, pid=pid, m=m, line=line, side=s, price=h[s],
                                      res=ah._grade(box, gid, pid, m, line, s), close_pin=close_of(fs, C, m, k, s)))
    return S, H

def main():
    box = ah._load_box(); days = t.load_days(); S, H = build(days, box)
    out = ["NBA R33. Nights %d (%s..%s). Forward from 2026-11-27." % (len(days), min(days), max(days))]
    for tag, es in (("S33n price shop", S), ("H33n HR lag", H)):
        out.append(""); out.append(t.line(tag + " all", es))
        for s in ("over", "under"): out.append(t.line(tag + " " + s, [e for e in es if e["side"] == s]))
        for m in sorted({e["m"] for e in es}): out.append(t.line(tag + " " + m, [e for e in es if e["m"] == m]))
        out.append(t.line(tag + " forward", [e for e in es if e["day"] >= "2026-11-27"]))
    txt = "\n".join(out); print(txt); open(OUT, "w").write(txt + "\n")
main()
