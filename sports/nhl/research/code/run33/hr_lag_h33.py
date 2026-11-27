"""H33a: Hard Rock lags the other books' consensus move (shots). Registered in HYPOTHESES.md Run 33 before any run.
Usage: python -I research/code/run33/hr_lag_h33.py <sports/nhl dir>"""
import os, sys, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "run31"))
import trend_n31_nhl as t  # noqa
OUT = os.path.join(HERE, "hr_lag_h33_results.txt")
MKT = "shots"

def cons(f, k):
    qs = []
    for b, v in (f.get("others") or {}).items():
        x = t.fair(t.pairs((v or {}).get(MKT)).get(k))
        if x is not None: qs.append(x)
    return (statistics.median(qs), len(qs)) if len(qs) >= 3 else (None, len(qs))

def build(days):
    rows = []
    for day, byg in sorted(days.items()):
        for gid, fs in byg.items():
            pulls = {}
            for f in fs:
                if f.get("pull") in ("A", "B", "C", "D"): pulls[f["pull"]] = f
            if "A" not in pulls or "C" not in pulls: continue
            A, C = pulls["A"], pulls["C"]
            if MKT not in (A.get("markets") or {}) or MKT not in (C.get("markets") or {}): continue
            ha, hc = t.pairs(A["markets"][MKT]), t.pairs(C["markets"][MKT])
            seen = set()
            for k in sorted(hc):
                pid, line = k
                if pid in seen or k not in ha: continue
                hfa, hfc = t.fair(ha[k]), t.fair(hc[k])
                if hfa is None or hfc is None: continue
                ca, na = cons(A, k); cc, nc = cons(C, k)
                if ca is None or cc is None: continue
                dc, dh = cc - ca, hfc - hfa
                if dc >= 0.02 and dh < 0.005: side = "over"
                elif dc <= -0.02 and dh > -0.005: side = "under"
                else: continue
                p = hc[k][side]
                if p is None or not (t.PRICE_MIN <= p <= t.PRICE_MAX): continue
                seen.add(pid)
                later = [x for x in fs if x["at"] > C["at"]]
                close = None
                if later:
                    cl, n = cons(later[-1], k)
                    if cl is not None: close = t.side_p(cl, side)
                rows.append(dict(day=day, gid=gid, pid=pid, m=MKT, line=line, side=side, price=p,
                                 res=t.grade(gid, pid, MKT, line, side), close_pin=close))
    return rows

def main():
    days = t.load_days(); es = build(days)
    out = ["H33a HR lags consensus move >=2pts A->C (shots). Nights %d (%s..%s). Forward from 2026-11-27." % (len(days), min(days), max(days))]
    for tag, sub in (("H33a all", es), ("over", [e for e in es if e["side"] == "over"]), ("under", [e for e in es if e["side"] == "under"]),
                     ("forward", [e for e in es if e["day"] >= "2026-11-27"])):
        out.append(t.line(tag, sub))
    txt = "\n".join(out); print(txt); open(OUT, "w").write(txt + "\n")
main()
