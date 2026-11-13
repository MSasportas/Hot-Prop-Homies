"""When does Pinnacle move? For every pair of consecutive stored reads of a game: of the Pinnacle lines seen at both, how many moved
>= 2 pts (fair chance), per hour of the window, by minutes before tip and by clock time (ET). Hard Rock follow lag alongside.
Stored reads only. From sports/nba: python research/code/run11/when_moves.py"""
import collections, os, statistics, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import moves_thr as mt
ah = mt.ah
dm = mt.days()
rows = []   # one per consecutive pair x line
for day, byg in dm.items():
    for gid, fs in byg.items():
        tip = None
        for a, b in zip(fs, fs[1:]):
            if not a.get("others") or not b.get("others"):
                continue
            ta, tb = ah.common.parse_iso(a["at"]), ah.common.parse_iso(b["at"])
            hrs = (tb - ta).total_seconds() / 3600.0
            if hrs <= 0.05:
                continue
            for m in b["markets"]:
                pa, pb = ah._bk(a, "pinnacle", m), ah._bk(b, "pinnacle", m)
                ha, hb = ah._hr(a, m), ah._hr(b, m)
                for k in pb:
                    fa, fb = ah._fo(pa.get(k)), ah._fo(pb.get(k))
                    if fa is None or fb is None or k not in ha or k not in hb:
                        continue
                    rows.append(dict(day=day, gid=gid, m=m, t0=ta, t1=tb, hrs=hrs, d=abs(fb - fa), a=a["read"], b=b["read"], key=k))
# tip time per game from the slate files is not stored in odds; recover from the D/last read: tip ~ last read + 20 min when D exists
tipof = {}
for day, byg in dm.items():
    for gid, fs in byg.items():
        d = [f for f in fs if f["read"] == "D"]
        if d:
            tipof[(day, gid)] = ah.common.parse_iso(d[-1]["at"]).timestamp() + 20 * 60
def mins_before(r):
    t = tipof.get((r["day"], r["gid"]))
    return None if t is None else ((t - r["t1"].timestamp()) / 60.0, (t - r["t0"].timestamp()) / 60.0)
def bucket(lbl, rs):
    n = len(rs); mv = sum(r["d"] >= 0.02 for r in rs); hrs = sum(r["hrs"] for r in rs)
    big = sum(r["d"] >= 0.04 for r in rs)
    print("  %-26s line-pairs %6d  moved 2+ pts: %4d (%4.1f%%)  per line-hour %5.2f%%  4+ pts: %3d" % (lbl, n, mv, 100.0 * mv / n if n else 0, 100.0 * mv / hrs if hrs else 0, big))
print("== by read window (as run today)")
for w in sorted({(r["a"], r["b"]) for r in rows}):
    rs = [r for r in rows if (r["a"], r["b"]) == w]
    if len(rs) > 300: bucket("%s -> %s (avg %.0f min)" % (w[0], w[1], 60 * statistics.mean(r["hrs"] for r in rs)), rs)
print("== by minutes before tip (window end), live reads, games with a known tip")
bk = [(0, 25), (25, 50), (50, 80), (80, 120), (120, 200), (200, 330), (330, 600)]
for lo, hi in bk:
    rs = []
    for r in rows:
        mb = mins_before(r)
        if mb and lo <= mb[0] < hi and r["hrs"] <= 1.6:
            rs.append(r)
    bucket("%3d-%3d min before tip" % (lo, hi), rs)
print("== by clock time of the window end (ET), single windows <= 1.6 h")
import datetime
for lo, hi in ((11, 14), (14, 16), (16, 17), (17, 18), (18, 19), (19, 20), (20, 22)):
    rs = [r for r in rows if r["hrs"] <= 1.6 and lo <= r["t1"].astimezone(ah.common.ET).hour + r["t1"].astimezone(ah.common.ET).minute / 60.0 < hi]
    bucket("%02d:00-%02d:00 ET" % (lo, hi), rs)
print("== the long gaps (> 1.6 h): 11 AM to first live read")
for lo, hi in ((1.6, 4), (4, 6), (6, 9)):
    rs = [r for r in rows if lo < r["hrs"] <= hi]
    bucket("%.0f-%.0f hour gap" % (lo, hi), rs)
print("== market")
for m in mt.MK:
    bucket(m, [r for r in rows if r["m"] == m and r["hrs"] <= 1.6])
