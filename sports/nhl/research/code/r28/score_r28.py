#!/usr/bin/env python3
"""Run 28 forward scorer: R28a-R28d (research/HYPOTHESES.md, registered 2026-11-21 before testing).
Judged nights >= 2026-11-21. Reads data/shadow (the Hard Rock read log with Pinnacle fair, goalies and results) and this season's game
logs in data/state/stats. Every bet is graded at the Hard Rock price posted on the side actually bet. Read-only on data/; writes
research/fwd/r28.md and research/fwd/r28.json.  python3 -I score_r28.py [repo_root]"""
import collections, glob, gzip, json, os, statistics, sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fwd"))
import score_fwd as F  # noqa: E402

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", ".."))
F.ROOT = ROOT
START = "2026-11-21"
SEASON = "20262027"
EPS = 1e-12
PRICE_MIN = -200
POINTS_PRICE_MAX = 120
POINTS_EV_MIN = 0.05            # R28a: Hard Rock EV vs Pinnacle no-vig fair
LVA_THRESHOLD = 0.05            # R28b: line vs rolling SOG average
LVA_MIN_GAMES = 5
REST_LOW_MAX = 1                # R28c: 0-1 rest days
REST_HIGH_MIN = 3               # R28c: 3+ rest days
GOALIE_MIN_NIGHTS = 5           # R28d: team nights needed before a "most-started" goalie is named
VARS = ["R28a points gap", "R28b under", "R28b over", "R28c rest", "R28c rest mirror", "R28d backup goalie"]
F.BONF = len(VARS)


def skater_logs():
    """{pid: [(date, shots)]} oldest first, from this season's weekly game-log windows."""
    out = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(ROOT, "data/state/stats", SEASON, "*.json.gz"))):
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            doc = json.load(fh)
        idx = {name: i for i, name in enumerate(doc["skater_fields"])}
        for row in doc["skaters"]:
            out[row[idx["pid"]]].append((row[idx["date"]], row[idx["shots"]]))
    return {pid: sorted(games) for pid, games in out.items()}


def prior_games(logs, pid, night):
    return [g for g in logs.get(pid, []) if g[0] < night]


def rolling_sog(logs, pid, night):
    """Mean shots over the player's games before `night`; None under LVA_MIN_GAMES."""
    prior = prior_games(logs, pid, night)
    return statistics.mean(s for _, s in prior) if len(prior) >= LVA_MIN_GAMES else None


def rest_days(logs, pid, night):
    """Days off since the player's last game (back-to-back = 0, as the shadow log's team_rest_days); None with no prior game."""
    prior = prior_games(logs, pid, night)
    return (date.fromisoformat(night) - date.fromisoformat(prior[-1][0])).days - 1 if prior else None


def goalie_name(row):
    """Name of the row's own goalie, from the close read when it is confirmed, else the open read; None when neither is."""
    for key in ("close", "open"):
        g = (row.get(key) or {}).get("goalie_own") or {}
        if g.get("status") == "confirmed" and g.get("name"):
            return g["name"]
    return None


def most_started(starts, team):
    """The goalie with the most confirmed starting nights for `team` so far, or None under GOALIE_MIN_NIGHTS team nights."""
    counts = {name: len(nights) for name, nights in (starts.get(team) or {}).items()}
    if sum(counts.values()) < GOALIE_MIN_NIGHTS:
        return None
    return max(counts, key=counts.get)


def bet_record(night, row, blk, side, ev):
    close_cons = (row.get("close") or {}).get("cons_fair_over_med")
    price = blk[side]
    return {"date": night, "game": row["game_id"], "pid": row["pid"], "line": row["line"], "side": side, "pull": blk["pull"],
            "at": blk["at"], "price": price, "ev": round(ev, 4),
            "clv": None if close_cons is None else round(F.ev(close_cons if side == "over" else 1 - close_cons, price), 4),
            "pl": F.grade(row, side, row["line"], price)}


def points_gap(night, row):
    """R28a: the C read, Hard Rock EV vs Pinnacle no-vig fair >= POINTS_EV_MIN on a side priced PRICE_MIN..POINTS_PRICE_MAX."""
    blk = row.get("close") or {}
    pin = blk.get("pin_fair_over")
    if blk.get("pull") != "C" or pin is None:
        return []
    for side in ("over", "under"):
        e = F.ev(pin if side == "over" else 1 - pin, blk[side])
        if PRICE_MIN <= blk[side] <= POINTS_PRICE_MAX and e >= POINTS_EV_MIN - EPS:
            return [("R28a points gap", bet_record(night, row, blk, side, e))]
    return []


def shots_sides(night, row, logs, starts):
    """R28b, R28c and R28d on one shots row: the open read's Hard Rock price on the side each rule names (R28d: the first of
    open and close that has the opposing goalie confirmed)."""
    blk, out = row["open"], []

    def add(variant, side, on=blk):
        if on[side] >= PRICE_MIN:
            out.append((variant, bet_record(night, row, on, side, 0.0)))

    avg = rolling_sog(logs, row["pid"], night)
    if avg:
        gap = (row["line"] - avg) / avg
        if gap <= -LVA_THRESHOLD + EPS:
            add("R28b under", "under")
        elif gap >= LVA_THRESHOLD - EPS:
            add("R28b over", "over")
    rest = rest_days(logs, row["pid"], night)
    if rest is not None and rest >= REST_HIGH_MIN:
        add("R28c rest", "over")
        add("R28c rest mirror", "under")
    elif rest is not None and rest <= REST_LOW_MAX:
        add("R28c rest", "under")
        add("R28c rest mirror", "over")
    usual = most_started(starts, row["ctx"]["opp"])
    for read in (row["open"], row.get("close") or {}):
        g = read.get("goalie_opp") or {}
        if usual and g.get("status") == "confirmed" and g.get("name") != usual:
            add("R28d backup goalie", "over", read)
            break
    return out


def shadow_nights():
    """[(night, rows)] for every stored shadow night, oldest first."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data/shadow", "2*.json"))):
        doc = F.load(p)
        out.append((doc["date"], doc.get("rows") or []))
    return out


def score():
    """{variant: bets} over the judged nights, plus {variant: bets} over the earlier nights as a labelled descriptive check."""
    logs = skater_logs()
    starts = collections.defaultdict(lambda: collections.defaultdict(set))     # team -> goalie -> nights confirmed in goal
    judged = {v: [] for v in VARS}
    descriptive = {v: [] for v in VARS}
    for night, rows in shadow_nights():
        live = [r for r in rows if r.get("src") == "live" and r.get("open")]
        target = judged if night >= START else descriptive
        done = set()
        for r in live:
            variants = points_gap(night, r) if r["market"] == "points" else shots_sides(night, r, logs, starts) if r["market"] == "shots" else []
            for variant, b in variants:
                key = (variant, r["game_id"], r["pid"], r["line"], r["market"])
                if key not in done:
                    done.add(key)
                    target[variant].append(b)
        for r in rows:
            name = goalie_name(r)
            if name and r.get("ctx"):
                starts[r["ctx"]["team"]][name].add(night)
    return judged, descriptive


def table_row(variant, bets):
    s = F.summarize(bets)
    if not s["graded"]:
        return "| %s | %d | 0 | - | - | - | - | - | - | False |" % (variant, s["bets"])
    return "| %s | %d | %d | %d | %+.2f | %+.1f%% | %+.0f..%+.0f%% | %.4f | %s | %s |" % (
        variant, s["bets"], s["graded"], s["w"], s["units"], 100 * s["roi"], 100 * s["ci90"][0], 100 * s["ci90"][1],
        s["p_one_sided"], "-" if s["mean_clv"] is None else "%.4f" % s["mean_clv"], s.get("candidate", False))


def main():
    judged, descriptive = score()
    hdr = "| variant | bets | graded | W | units | ROI | 90% CI | p | mean CLV | candidate |\n|---|---|---|---|---|---|---|---|---|---|"
    out = ["# Run 28 forward (research/code/r28/score_r28.py): R28a-R28d, nights >= %s. Bar: n >= 300 graded, ROI > 0, p < %.4f, mean CLV > 0." % (
        START, 0.05 / len(VARS)), "", hdr]
    out += [table_row(v, judged[v]) for v in VARS]
    out += ["", "Descriptive, seen nights < %s (not a test, never a result):" % START, "", hdr]
    out += [table_row(v, descriptive[v]) for v in VARS]
    with open(os.path.join(ROOT, "research/fwd/r28.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    with open(os.path.join(ROOT, "research/fwd/r28.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({v: F.summarize(judged[v]) for v in VARS}, fh, indent=1)
    print("\n".join(out))


if __name__ == "__main__":
    main()
