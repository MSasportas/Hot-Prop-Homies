"""Run 10b: line disagreements with Pinnacle's price CONVERTED to Hard Rock's line.

The lower bound in line_disagree.py is too strict (a full point is worth several % of chance, and Hard Rock re-juices its price
instead of moving the line). Here Pinnacle's fair chance at its own line is carried to Hard Rock's line with a simple spread:
X ~ Normal(mu, k * sqrt(mu)), k fitted PER MARKET from the books themselves (pairs of books showing different lines for the same
player on the same read), not from game results. ev = P_converted(side at Hard Rock line) x Hard Rock decimal - 1.
Usage (from sports/nba): python research/code/run10/line_convert.py
"""
import glob, json, math, os, statistics, sys
sys.path.insert(0, "scripts")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import odds
import line_disagree as ld

BOOKS = ["pinnacle"] + ld.OTHERS


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def p_over(mu, line, k):
    return 1 - phi((line - mu) / (k * math.sqrt(max(mu, 0.05))))


def solve_mu(line, fo, k):
    lo, hi = 0.01, 80.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if p_over(mid, line, k) < fo:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def convert(line_from, fo, line_to, k):
    return p_over(solve_mu(line_from, fo, k), line_to, k)


def fit_k():
    """Per market: the k that best explains one book's fair chance at its line from another book's line and chance."""
    pairs = {m: [] for m in ld.STAT}
    for path in sorted(glob.glob("data/odds/*.json")):
        for f in json.load(open(path))["fetches"]:
            if not f.get("others"):
                continue
            for m in ld.STAT:
                per = {}
                for b in BOOKS:
                    pr = ld.bk(f, b, m)
                    for pid in {p for p, _ in pr}:
                        x = ld.main_line(pr, pid)
                        if x and 0.3 <= x[1] <= 0.7:
                            per.setdefault(pid, []).append(x)
                for xs in per.values():
                    for i in range(len(xs)):
                        for j in range(len(xs)):
                            if xs[i][0] != xs[j][0]:
                                pairs[m].append((xs[i][0], xs[i][1], xs[j][0], xs[j][1]))
    out = {}
    for m, ps in pairs.items():
        ps = ps[::max(1, len(ps) // 4000)]
        best = None
        for k in [x / 20.0 for x in range(12, 61)]:
            err = statistics.mean((convert(a, fa, b, k) - fb) ** 2 for a, fa, b, fb in ps)
            if best is None or err < best[0]:
                best = (err, k)
        out[m] = best[1]
        print("fit %-9s k %.2f  rmse %.3f  pairs %d" % (m, best[1], math.sqrt(best[0]), len(ps)))
    return out


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    K = fit_k()
    rows = ld.build()
    for r in rows:
        fo_side_pin = None
    # rebuild the Pinnacle chance at its own line from lb (lb = p_side * dec - 1)
    for r in rows:
        dec = odds.decimal(r["price"])
        p_side_pin = (r["lb"] + 1) / dec
        fo = p_side_pin if r["side"] == "over" else 1 - p_side_pin
        po = convert(r["pin_line"], fo, r["line"], K[r["market"]])
        r["p"] = po if r["side"] == "over" else 1 - po
        r["ev"] = r["p"] * dec - 1
    live = [r for r in rows if r["read"] != "A"]
    g = [r for r in live if r["res"] in "WL"]
    print("calibration (live reads, all line disagreements): converted chance vs what happened")
    for lo, hi in ((0, .45), (.45, .5), (.5, .55), (.55, .6), (.6, .65), (.65, 1)):
        b = [r for r in g if lo <= r["p"] < hi]
        if b:
            print("  p %.2f-%.2f  n %4d  said %.3f  hit %.3f" % (lo, hi, len(b), statistics.mean(r["p"] for r in b), sum(r["res"] == "W" for r in b) / len(b)))
    print("-- by converted edge (live reads B/C/D)")
    for lab, lo, hi in (("ev >= +6%", .06, 9), ("ev +4..+6%", .04, .06), ("ev +2..+4%", .02, .04), ("ev 0..+2%", 0, .02), ("ev -2..0%", -.02, 0), ("ev < -2%", -9, -.02)):
        ld.show(lab, [r for r in live if lo <= r["ev"] < hi])
    for cut in (0.02, 0.04):
        print("-- ev >= %+.0f%%" % (100 * cut))
        S = [r for r in live if r["ev"] >= cut]
        ld.show("  all", S)
        for k in ("market", "side", "read"):
            for v in sorted({r[k] for r in S}):
                ld.show("  %s=%s" % (k, v), [r for r in S if r[k] == v])
        ld.show("  3+ other books agree", [r for r in S if r["agree"] >= 3])
        ld.show("  0-2 other books agree", [r for r in S if r["agree"] < 3])
        ld.show("  nights < 11-06", [r for r in S if r["day"] < "2026-11-06"])
        ld.show("  nights >= 11-06", [r for r in S if r["day"] >= "2026-11-06"])
    print("-- 11 AM read, ev >= +2%")
    ld.show("  all", [r for r in rows if r["read"] == "A" and r["ev"] >= .02])
