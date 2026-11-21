"""np1_np2_np3_discovery.py: scoring for NP1-NP4 (registered 2026-11-15); lab_forward.py reuses run_np1..run_np4 for the nightly forward tally.
Reads all stored odds nights (Oct 25 - Nov 14). Writes nothing. Prints W-L counts.
Run: python research/code/np1_np2_np3_discovery.py
"""
import collections, glob, gzip, json, math, os, statistics, sys
from datetime import datetime, timezone

R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) + os.sep
sys.path.insert(0, R + "scripts")
import odds

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SHARP_BOOKS = {"pinnacle", "novig", "prophetx"}
SOFT_BOOKS  = {"draftkings", "fanduel", "betmgm", "espnbet", "betonlineag", "betrivers"}
STALE_MIN   = 60  # minutes: a book price older than this is not "fresh"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _fo(q):
    """Fair over from a {over, under} price dict. None if invalid."""
    if not q or not q.get("over") or not q.get("under"):
        return None
    h = odds.hold(q["over"], q["under"])
    return odds.fair_two_sided(q["over"], q["under"]) if 0 <= h <= 0.15 else None

def _bk_pairs(fetch, book, market):
    """Return pairs dict for a given book/market in a fetch (or {})."""
    return odds.pairs(
        ((fetch.get("others") or {}).get(book) or {}).get(market, {}).get("outcomes")
    )

def _hr_pairs(fetch, market):
    return odds.pairs((fetch["markets"].get(market) or {}).get("outcomes"))

def _last_update(fetch, book, market):
    return ((fetch.get("others") or {}).get(book) or {}).get(market, {}).get("last_update")

def _is_fresh(fetch, book, market, stale_min=STALE_MIN):
    lu = _last_update(fetch, book, market)
    if not lu:
        return False
    at = fetch["at"]
    try:
        t_lu = datetime.fromisoformat(lu.replace("Z", "+00:00"))
        t_at = datetime.fromisoformat(at.replace("Z", "+00:00"))
        return (t_at - t_lu).total_seconds() / 60.0 < stale_min
    except Exception:
        return False

def _load_box():
    box = {}
    for path in ("data/seed/players_2026-27.json.gz", "data/state/box/players_2026-27.json.gz"):
        fp = R + path
        if os.path.exists(fp):
            for row in json.load(gzip.open(fp, "rt")):
                box[(row["game"], row["pid"])] = row
    return box

STAT = {"rebounds": "reb", "points": "pts", "assists": "ast", "threes": "fg3m"}

def _grade(box, gid, pid, m, line, side):
    b = box.get((gid, pid))
    if not b:
        return "?"
    if b.get("dnp") or not b.get("min"):
        return "V"
    x = b.get(STAT.get(m))
    if x is None:
        return "?"
    return "P" if x == line else ("W" if (x > line) == (side == "over") else "L")

def _units(res, price):
    if res == "W":
        return odds.decimal(price) - 1
    if res == "L":
        return -1.0
    return 0.0

def _summarize(label, bets):
    g = [b for b in bets if b["res"] in ("W", "L")]
    w = sum(b["res"] == "W" for b in g)
    u = sum(_units(b["res"], b["price"]) for b in g)
    roi = (u / len(g) * 100) if g else None
    return {
        "label": label,
        "n": len(bets),
        "graded": len(g),
        "w": w,
        "l": len(g) - w,
        "units": round(u, 2),
        "roi": round(roi, 1) if roi is not None else None,
    }

def fmt(s):
    roi = ("%+.1f%%" % s["roi"]) if s["roi"] is not None else "-"
    return "n %d graded %d %d-%d %+.2fu ROI %s" % (
        s["n"], s["graded"], s["w"], s["l"], s["units"], roi)

# ---------------------------------------------------------------------------
# load all odds data
# ---------------------------------------------------------------------------

def load_days():
    """Returns {date: {game_id: [fetch, ...]}} sorted by date."""
    days = {}
    for p in sorted(glob.glob(R + "data/odds/2*.json")):
        d = json.load(open(p, encoding="utf-8"))
        byg = collections.defaultdict(list)
        for f in sorted(d["fetches"], key=lambda x: x["at"]):
            byg[f["game_id"]].append(f)
        days[d["date"]] = dict(byg)
    return days

# ---------------------------------------------------------------------------
# NP1: Sharp vs Soft split
# Single B or C reads. Need >= 2 sharp books fresh, >= 3 soft books fresh.
# Signal: abs(sf - tf) >= 0.03. Side = over if sf > tf.
# Bet HR if EV vs sf >= 0, price -200..200. First per player/market/night.
# ---------------------------------------------------------------------------

def run_np1(days, box):
    bets = []
    for day, byg in sorted(days.items()):
        seen = set()  # (pid, market) per night
        for gid, fs in byg.items():
            for f in fs:
                if f["read"] not in ("B", "C"):
                    continue
                for m in f["markets"]:
                    hr = _hr_pairs(f, m)
                    for (pid, line), hq in hr.items():
                        if not (hq.get("over") and hq.get("under")):
                            continue
                        if not (-200 <= hq["over"] <= 200 and -200 <= hq["under"] <= 200):
                            continue
                        # sharp fairs
                        sh_fairs = []
                        for bk in SHARP_BOOKS:
                            if not _is_fresh(f, bk, m):
                                continue
                            q = _bk_pairs(f, bk, m).get((pid, line))
                            fo = _fo(q)
                            if fo is not None:
                                sh_fairs.append(fo)
                        if len(sh_fairs) < 2:
                            continue
                        # soft fairs
                        sf_fairs = []
                        for bk in SOFT_BOOKS:
                            if not _is_fresh(f, bk, m):
                                continue
                            q = _bk_pairs(f, bk, m).get((pid, line))
                            fo = _fo(q)
                            if fo is not None:
                                sf_fairs.append(fo)
                        if len(sf_fairs) < 3:
                            continue
                        sharp_mean = statistics.mean(sh_fairs)
                        soft_median = statistics.median(sf_fairs)
                        diff = sharp_mean - soft_median
                        if abs(diff) < 0.03:
                            continue
                        side = "over" if diff > 0 else "under"
                        price = hq[side]
                        if not (-200 <= price <= 200):
                            continue
                        ev = odds.ev(sharp_mean if side == "over" else (1 - sharp_mean), price)
                        if ev < 0:
                            continue
                        key = (pid, m)
                        if key in seen:
                            continue
                        seen.add(key)
                        res = _grade(box, gid, pid, m, line, side)
                        bets.append({"day": day, "gid": gid, "pid": pid, "m": m,
                                     "line": line, "side": side, "price": price, "res": res})
    return bets

# ---------------------------------------------------------------------------
# NP2: Soft-book price move, sharp did not follow -> fade
# Consecutive reads. HR identical at both reads.
# >= 3 soft + >= 2 sharp fresh at both. dT = soft median change, dS = sharp mean change.
# Event: abs(dT) >= 0.02 and dS * sign(dT) < 0.005. Fade the soft direction.
# Bet if EV vs later sharp mean >= 0. First per player/market/night.
# ---------------------------------------------------------------------------

def run_np2(days, box):
    bets = []
    for day, byg in sorted(days.items()):
        seen = set()
        for gid, fs in byg.items():
            for fa, fb in zip(fs, fs[1:]):
                for m in fb["markets"]:
                    ha = _hr_pairs(fa, m)
                    hb = _hr_pairs(fb, m)
                    for (pid, line) in hb:
                        if (pid, line) not in ha:
                            continue
                        qa, qb = ha[(pid, line)], hb[(pid, line)]
                        # HR prices must be identical at both reads
                        if not (qa.get("over") and qa.get("under") and qb.get("over") and qb.get("under")):
                            continue
                        if qa["over"] != qb["over"] or qa["under"] != qb["under"]:
                            continue
                        # sharp fairs at both reads
                        sh_a, sh_b = [], []
                        for bk in SHARP_BOOKS:
                            if not (_is_fresh(fa, bk, m) and _is_fresh(fb, bk, m)):
                                continue
                            qa2 = _bk_pairs(fa, bk, m).get((pid, line))
                            qb2 = _bk_pairs(fb, bk, m).get((pid, line))
                            fo_a, fo_b = _fo(qa2), _fo(qb2)
                            if fo_a is not None and fo_b is not None:
                                sh_a.append(fo_a)
                                sh_b.append(fo_b)
                        if len(sh_b) < 2:
                            continue
                        # soft fairs at both reads
                        sf_a, sf_b = [], []
                        for bk in SOFT_BOOKS:
                            if not (_is_fresh(fa, bk, m) and _is_fresh(fb, bk, m)):
                                continue
                            qa2 = _bk_pairs(fa, bk, m).get((pid, line))
                            qb2 = _bk_pairs(fb, bk, m).get((pid, line))
                            fo_a, fo_b = _fo(qa2), _fo(qb2)
                            if fo_a is not None and fo_b is not None:
                                sf_a.append(fo_a)
                                sf_b.append(fo_b)
                        if len(sf_b) < 3:
                            continue
                        dT = statistics.median(sf_b) - statistics.median(sf_a)
                        dS = statistics.mean(sh_b) - statistics.mean(sh_a)
                        if abs(dT) < 0.02:
                            continue
                        # sharp did NOT follow the soft direction
                        sign_dT = 1 if dT > 0 else -1
                        if dS * sign_dT >= 0.005:
                            continue
                        # fade the soft move: bet against soft's direction
                        side = "under" if dT > 0 else "over"  # soft moved over -> fade = under
                        price = qb[side]
                        if not (-200 <= price <= 200):
                            continue
                        sharp_mean_b = statistics.mean(sh_b)
                        side_prob = sharp_mean_b if side == "over" else (1 - sharp_mean_b)
                        ev = odds.ev(side_prob, price)
                        if ev < 0:
                            continue
                        key = (pid, m)
                        if key in seen:
                            continue
                        seen.add(key)
                        res = _grade(box, gid, pid, m, line, side)
                        bets.append({"day": day, "gid": gid, "pid": pid, "m": m,
                                     "line": line, "side": side, "price": price, "res": res})
    return bets

# ---------------------------------------------------------------------------
# NP3: Whole market moves, HR still: follow
# Consecutive reads, HR identical. Per-book fair-over change c.
# Event: >= 3 books with c >= +0.015 and none with c <= -0.015 (bullish), median c >= 0.02.
#   or symmetric bearish. Not conditioned on Pinnacle.
# Bet toward market if EV vs later median fair >= 0.
# ---------------------------------------------------------------------------

def run_np3(days, box):
    bets = []
    all_other_books = list(SHARP_BOOKS | SOFT_BOOKS)
    for day, byg in sorted(days.items()):
        seen = set()
        for gid, fs in byg.items():
            for fa, fb in zip(fs, fs[1:]):
                for m in fb["markets"]:
                    ha = _hr_pairs(fa, m)
                    hb = _hr_pairs(fb, m)
                    for (pid, line) in hb:
                        if (pid, line) not in ha:
                            continue
                        qa, qb = ha[(pid, line)], hb[(pid, line)]
                        # HR identical at both reads
                        if not (qa.get("over") and qa.get("under") and qb.get("over") and qb.get("under")):
                            continue
                        if qa["over"] != qb["over"] or qa["under"] != qb["under"]:
                            continue
                        # collect per-book changes
                        changes = []
                        all_fair_b = []
                        for bk in all_other_books:
                            if not (_is_fresh(fa, bk, m) and _is_fresh(fb, bk, m)):
                                continue
                            qa2 = _bk_pairs(fa, bk, m).get((pid, line))
                            qb2 = _bk_pairs(fb, bk, m).get((pid, line))
                            fo_a, fo_b = _fo(qa2), _fo(qb2)
                            if fo_a is not None and fo_b is not None:
                                changes.append(fo_b - fo_a)
                                all_fair_b.append(fo_b)
                        if len(changes) < 3:
                            continue
                        # bullish: >= 3 books moved up >= 0.015 and none moved down <= -0.015
                        bullish = [c for c in changes if c >= 0.015]
                        bearish_neg = [c for c in changes if c <= -0.015]
                        # bearish: >= 3 books moved down <= -0.015 and none moved up >= 0.015
                        bearish = [c for c in changes if c <= -0.015]
                        bullish_pos = [c for c in changes if c >= 0.015]

                        direction = None
                        if len(bullish) >= 3 and not bearish_neg and statistics.median(changes) >= 0.02:
                            direction = "over"
                        elif len(bearish) >= 3 and not bullish_pos and statistics.median(changes) <= -0.02:
                            direction = "under"
                        if direction is None:
                            continue

                        price = qb[direction]
                        if not (-200 <= price <= 200):
                            continue
                        if not all_fair_b:
                            continue
                        median_fair_b = statistics.median(all_fair_b)
                        side_prob = median_fair_b if direction == "over" else (1 - median_fair_b)
                        ev = odds.ev(side_prob, price)
                        if ev < 0:
                            continue
                        key = (pid, m)
                        if key in seen:
                            continue
                        seen.add(key)
                        res = _grade(box, gid, pid, m, line, direction)
                        bets.append({"day": day, "gid": gid, "pid": pid, "m": m,
                                     "line": line, "side": direction, "price": price, "res": res})
    return bets

# ---------------------------------------------------------------------------
# NP4: Exchange move, HR unchanged
# Consecutive reads, HR prices identical. novig AND prophetx both move fair-over >= 0.01
# in the same direction. No Pinnacle condition. Bet HR in the exchange direction, first per
# player/market/night.
# ---------------------------------------------------------------------------

EXCHANGE_BOOKS = ("novig", "prophetx")
EXCHANGE_MOVE_MIN = 0.01

def run_np4(days, box):
    bets = []
    for day, byg in sorted(days.items()):
        seen = set()
        for gid, fs in byg.items():
            for fa, fb in zip(fs, fs[1:]):
                for m in fb["markets"]:
                    ha = _hr_pairs(fa, m)
                    hb = _hr_pairs(fb, m)
                    for (pid, line) in hb:
                        if (pid, line) not in ha:
                            continue
                        qa, qb = ha[(pid, line)], hb[(pid, line)]
                        if not (qa.get("over") and qa.get("under") and qb.get("over") and qb.get("under")):
                            continue
                        if qa["over"] != qb["over"] or qa["under"] != qb["under"]:
                            continue
                        moves = []
                        for bk in EXCHANGE_BOOKS:
                            fo_a = _fo(_bk_pairs(fa, bk, m).get((pid, line)))
                            fo_b = _fo(_bk_pairs(fb, bk, m).get((pid, line)))
                            if fo_a is None or fo_b is None:
                                break
                            moves.append(fo_b - fo_a)
                        if len(moves) < len(EXCHANGE_BOOKS):
                            continue
                        if all(c >= EXCHANGE_MOVE_MIN for c in moves):
                            side = "over"
                        elif all(c <= -EXCHANGE_MOVE_MIN for c in moves):
                            side = "under"
                        else:
                            continue
                        price = qb[side]
                        if not (-200 <= price <= 200):
                            continue
                        key = (pid, m)
                        if key in seen:
                            continue
                        seen.add(key)
                        bets.append({"day": day, "gid": gid, "pid": pid, "m": m, "line": line, "side": side,
                                     "price": price, "res": _grade(box, gid, pid, m, line, side)})
    return bets

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    days = load_days()
    box  = _load_box()
    print("Nights loaded: %d" % len(days))

    for label, bets in [("NP1", run_np1(days, box)), ("NP2", run_np2(days, box)), ("NP3", run_np3(days, box)), ("NP4", run_np4(days, box))]:
        s = _summarize(label, bets)
        print("%s: %s" % (label, fmt(s)))
        # Also show FAIR subset (ev >= 0 already enforced, so all bets are "fair" - print by-side breakdown)
        for side in ("over", "under"):
            sub = [b for b in bets if b["side"] == side]
            ss = _summarize(label + " " + side, sub)
            print("  %s" % fmt(ss))
