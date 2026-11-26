"""S32a: Hard Rock longest price vs other books' median raw price (shots). Registered in HYPOTHESES.md Run 32 before any run.
Usage: python -I research/code/run32/price_shop_s32.py <sports/nhl dir>"""
import os, sys, statistics, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "run31"))
import trend_n31_nhl as t  # noqa  (loads shadow results from sys.argv[1])
OUT = os.path.join(HERE, "price_shop_s32_results.txt")

def build(days):
    rows = []
    for day, byg in sorted(days.items()):
        for gid, fs in byg.items():
            done = set()
            for rd in ("B", "C"):
                fl = [f for f in fs if f.get("pull") == rd]
                if not fl: continue
                f = fl[-1]
                if "shots" not in (f.get("markets") or {}): continue
                hc = t.pairs(f["markets"]["shots"])
                others = {b: t.pairs((v or {}).get("shots")) for b, v in (f.get("others") or {}).items() if b != "pinnacle" or True}
                for (pid, line), h in sorted(hc.items()):
                    if pid in done or h.get("over") is None or h.get("under") is None: continue
                    books = [o[(pid, line)] for o in others.values() if (pid, line) in o and t.fair(o[(pid, line)]) is not None]
                    if len(books) < 3: continue
                    for s in ("over", "under"):
                        med = statistics.median(t.dec(b[s]) for b in books)
                        if t.dec(h[s]) >= med * 1.05 and t.PRICE_MIN <= h[s] <= t.PRICE_MAX:
                            done.add(pid)
                            nv = statistics.median(t.side_p(t.fair(b), s) for b in books)
                            later = [x for x in fs if x["at"] > f["at"]]
                            close = None
                            if later:
                                lo = {b: t.pairs((v or {}).get("shots")) for b, v in (later[-1].get("others") or {}).items()}
                                q = [t.side_p(t.fair(o[(pid, line)]), s) for o in lo.values() if (pid, line) in o and t.fair(o[(pid, line)]) is not None]
                                if len(q) >= 3: close = statistics.median(q)
                            rows.append(dict(day=day, gid=gid, pid=pid, m="shots", line=line, side=s, price=h[s],
                                             res=t.grade(gid, pid, "shots", line, s), close_pin=close, nbooks=len(books)))
                            break
    return rows

def main():
    days = t.load_days(); es = build(days)
    out = ["S32a HR price >= 5%% above median raw decimal of >=3 other books (shots). Nights %d (%s..%s). Forward from 2026-11-26." % (len(days), min(days), max(days))]
    for tag, sub in (("S32a all", es), ("over", [e for e in es if e["side"] == "over"]), ("under", [e for e in es if e["side"] == "under"]),
                     ("discovery", [e for e in es if e["day"] < "2026-11-26"]), ("forward", [e for e in es if e["day"] >= "2026-11-26"])):
        out.append(t.line(tag, sub) if hasattr(t, "line") else "")
    txt = "\n".join(out); print(txt); open(OUT, "w").write(txt + "\n")
main()
