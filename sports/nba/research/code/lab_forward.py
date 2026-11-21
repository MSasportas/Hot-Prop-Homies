"""lab_forward.py: nightly forward tallies for the Lab tracks NP1-NP4, LVA1-LVA2 and R28a/b/d/e (HYPOTHESES.md, Run 28).
Reads data/odds/*.json, data/odds_close/*.json, data/shadow/*.json, data/state/injuries.json and the box scores. Writes
data/research/lab_np.json, lab_lva.json and lab_r28.json (research only: never picks, never the Record). run.py's nightly
research step runs this file. Every bet is graded at the Hard Rock price posted on the side actually bet.
"""
import collections, datetime, glob, json, os, statistics, sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) + os.sep
sys.path.insert(0, R + "scripts")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, odds
import np1_np2_np3_discovery as np_disc

NP_FWD = "2026-11-15"   # NP1-NP4 forward period starts (HYPOTHESES.md, Run NP)
LVA_FWD = "2026-11-16"  # LVA1-LVA2 forward period starts (HYPOTHESES.md, Run LVA)
R28_FWD = "2026-11-22"  # R28a/b/d/e forward period starts (HYPOTHESES.md, Run 28)
EPS = 1e-9              # float slack on the threshold test, as engine.py
NP_RUNNERS = {"NP1": np_disc.run_np1, "NP2": np_disc.run_np2, "NP3": np_disc.run_np3, "NP4": np_disc.run_np4}
EMPTY_TALLY = {"w": 0, "l": 0, "units": 0.0, "pending": 0, "push": 0, "void": 0}
PIN = "pinnacle"
PRICE_MIN, PRICE_MAX = -200, 200        # Matt's fixed price window for every Hard Rock side
B2B_MARKETS = ("points", "rebounds", "assists")
BUMP_MARKETS = ("points", "assists")
ROTATION_SIZE = 7                       # R28b: a "rotation player" is top 7 on the team by minutes
ROTATION_MIN_GAMES = 5
PIN_CLOSE_MOVE_MIN = 0.02               # R28e: Pinnacle fair-over move, read C to close
R28_IDS = ("R28a", "R28b", "R28d_under", "R28d_over", "R28e")
TALLY_KEY = {"W": "w", "L": "l", "P": "push", "V": "void"}


def tally(bets):
    """{w, l, units, pending, push, void} for bets that carry `res` (W/L/P/V, anything else is pending) and `price`."""
    t = dict(EMPTY_TALLY)
    for b in bets:
        t[TALLY_KEY.get(b["res"], "pending")] += 1
        t["units"] += np_disc._units(b["res"], b["price"])
    t["units"] = round(t["units"], 2)
    return t


def write_summary(path, doc):
    """Write `doc` only when it changed, stamping updated_at (the page and lab_retire.py read that stamp)."""
    try:
        old = common.read_json(path, None)
    except (OSError, ValueError):
        old = None
    if old is not None and {k: v for k, v in old.items() if k != "updated_at"} == doc:
        return old
    doc = dict(doc, updated_at=common.iso(common.now()))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump(doc, fh, separators=(",", ":"), sort_keys=True)
    return doc


def retired(summary):
    """Lab ids retired from this summary file (scripts/lab_retire.py): no longer exported."""
    try:
        sys.path.insert(0, os.path.join(R, "..", "..", "scripts"))
        import lab_retire
        return lab_retire.retired_stats(R + "config", summary)
    except Exception:                                        # retirement is optional: never let it stop the nightly run
        return set()


def np_bets(days, box):
    """{track id: forward bets} for NP1-NP4 over the stored odds nights from NP_FWD on."""
    fwd = {d: g for d, g in days.items() if d >= NP_FWD}
    return {tid: run(fwd, box) for tid, run in NP_RUNNERS.items()}


def export_np(days=None, box=None):
    days = np_disc.load_days() if days is None else days
    box = np_disc._load_box() if box is None else box
    gone = retired("research/lab_np.json")
    doc = {tid: tally(bets) for tid, bets in np_bets(days, box).items() if tid not in gone}
    return write_summary(R + "data/research/lab_np.json", doc)


def rolling_avg(player_games, day, stat, min_games):
    """Mean of `stat` over the player's prior played games (same rule as engine.rolling_season_avg); None under min_games."""
    prior = [g for g in player_games if g["date"] < day and not g.get("dnp") and (g.get("min") or 0) > 0 and g.get(stat) is not None]
    return statistics.mean(g[stat] for g in prior) if len(prior) >= min_games else None


def lva_bets(shadow_days, box, cfg):
    """({LVA1 bets}, {LVA2 bets}) from the pin_solo rows in data/shadow/<night>.json, first row per player/market/side/night.
    LVA1: unders the engine skipped for sitting `threshold` below the rolling average (their why starts with "LVA1:").
    LVA2: live overs whose line sits `threshold` above it."""
    hist = collections.defaultdict(list)
    for (_, pid), row in box.items():
        hist[str(pid)].append(row)
    lva1, lva2 = [], []
    for day, rows in sorted(shadow_days.items()):
        seen = set()
        for r in rows:
            key = (r["pid"], r["market"], r["side"])
            if r.get("rule") != "pin_solo" or key in seen:
                continue
            skipped = str(r.get("why") or "").startswith("LVA1:")
            if not (skipped or (not r.get("why") and r["side"] == "over")):
                continue
            bet = {"day": day, "price": r["price"],
                   "res": np_disc._grade(box, r["game_id"], r["pid"], r["market"], r["line"], r["side"])}
            if skipped:
                seen.add(key)
                lva1.append(bet)
                continue
            avg = rolling_avg(hist[str(r["pid"])], day, np_disc.STAT[r["market"]], cfg["min_prior_games"])
            if avg and (r["line"] - avg) / avg >= cfg["threshold"] - EPS:
                seen.add(key)
                lva2.append(bet)
    return lva1, lva2


def load_shadow_days():
    out = {}
    for p in sorted(glob.glob(R + "data/shadow/2*.json")):
        d = common.read_json(p, None) or {}
        if d.get("slate", "") >= LVA_FWD:
            out[d["slate"]] = d.get("solo") or []
    return out


def export_lva(box=None):
    box = np_disc._load_box() if box is None else box
    cfg = common.read_json(R + "config/rules.json", {})["pin_solo"]["lva1"]
    lva1, lva2 = lva_bets(load_shadow_days(), box, cfg)
    gone = retired("research/lab_lva.json")
    doc = {tid: tally(bets) for tid, bets in (("LVA1", lva1), ("LVA2", lva2)) if tid not in gone}
    return write_summary(R + "data/research/lab_lva.json", doc)


# ---------------------------------------------------------------- R28 (HYPOTHESES.md, Run 28)
def parse_at(stamp):
    return datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def r28_bet(box, day, gid, pid, market, line, side, price):
    return {"day": day, "gid": gid, "pid": pid, "m": market, "line": line, "side": side, "price": price,
            "res": np_disc._grade(box, gid, pid, market, line, side)}


def in_window(price):
    return PRICE_MIN <= price <= PRICE_MAX


def side_ev(fair_over, side, price):
    return odds.ev(fair_over if side == "over" else 1 - fair_over, price)


def pin_fair(fetch, market, key):
    """Pinnacle's fair over chance for (pid, line) at this read, or None when it is missing, stale or too high-hold."""
    if not np_disc._is_fresh(fetch, PIN, market):
        return None
    return np_disc._fo(np_disc._bk_pairs(fetch, PIN, market).get(key))


def complete(quote):
    return bool(quote and quote.get("over") and quote.get("under"))


def same_prices(a, b):
    """True when both quotes exist and post the same over and under prices (deep links and names are not prices)."""
    return bool(a and b) and all(a.get(side) == b.get(side) for side in ("over", "under"))


def player_teams(fetch):
    """{pid: team} from every Hard Rock market in this read."""
    return {o["pid"]: o["team"] for m in fetch["markets"].values() for o in m.get("outcomes") or []}


def consecutive_reads(days):
    """(day, game id, earlier read, later read) for each pair of neighbouring stored reads of a game."""
    for day, byg in sorted(days.items()):
        for gid, fs in byg.items():
            for fa, fb in zip(fs, fs[1:]):
                yield day, gid, fa, fb


def teams_played(box):
    """{(team, date)} for every team-game in the box scores (the schedule file only keeps a few days)."""
    return {(row["team"], row["date"]) for row in box.values()}


def previous_day(day):
    return (datetime.date.fromisoformat(day) - datetime.timedelta(days=1)).isoformat()


def run_r28a(days, box):
    """R28a back-to-back under: team played the previous day, Pinnacle's line unchanged over the last two reads, Under at Hard Rock
    when EV vs Pinnacle fair >= 0. First qualifying read per player/market/night."""
    played, bets, seen = teams_played(box), [], set()
    for day, gid, fa, fb in consecutive_reads(days):
        teams = player_teams(fb)
        for m in B2B_MARKETS:
            for (pid, line), q in np_disc._hr_pairs(fb, m).items():
                key = (day, pid, m)
                if key in seen or not complete(q) or not in_window(q["under"]) or (teams.get(pid), previous_day(day)) not in played:
                    continue
                if pin_fair(fa, m, (pid, line)) is None:
                    continue
                fair = pin_fair(fb, m, (pid, line))
                if fair is None or side_ev(fair, "under", q["under"]) < 0:
                    continue
                seen.add(key)
                bets.append(r28_bet(box, day, gid, pid, m, line, "under", q["under"]))
    return bets


def top_rotation(box, team, day):
    """The team's top ROTATION_SIZE players by average minutes over games before `day` (players under the minimum games sit out)."""
    mins = collections.defaultdict(list)
    for row in box.values():
        if row["team"] == team and row["date"] < day and not row.get("dnp") and (row.get("min") or 0) > 0:
            mins[row["pid"]].append(row["min"])
    ranked = sorted((pid for pid, v in mins.items() if len(v) >= ROTATION_MIN_GAMES), key=lambda p: -statistics.mean(mins[p]))
    return set(ranked[:ROTATION_SIZE])


def newly_out(path, injuries):
    """The Out news items seen from R28_FWD on, kept in a ledger at `path` so a player who later returns does not leave the
    tally: [{pid, team, at}]. injuries.json only holds today's list; the ledger is how R28b remembers earlier nights."""
    old = common.read_json(path, None) or {}
    ledger = dict(old)
    for pid, e in (injuries.get("list") or {}).items():
        if e.get("status") == "out" and e.get("date", "") >= R28_FWD:
            ledger.setdefault("%s|%s" % (pid, e["date"]), {"pid": pid, "team": e["team"], "at": e["date"]})
    if ledger != old:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        common.write_json(path, ledger)
    return list(ledger.values())


def run_r28b(days, box, news):
    """R28b injury usage bump: a top-7 rotation player newly Out between two reads. At the next read, bet a teammate's Over on points or
    assists at Hard Rock when its price is unchanged since the news read and EV vs Pinnacle fair >= 0. First read per player/market/night."""
    bets, seen, rotation = [], set(), {}
    for day, byg in sorted(days.items()):
        for gid, fs in byg.items():
            for fa, fb, fc in zip(fs, fs[1:], fs[2:]):
                lo, hi = parse_at(fa["at"]), parse_at(fb["at"])
                teams = player_teams(fc)
                for item in news:
                    out_pid, team = item["pid"], item["team"]
                    if not lo < parse_at(item["at"]) <= hi:
                        continue
                    if (day, team) not in rotation:
                        rotation[(day, team)] = top_rotation(box, team, day)
                    if out_pid not in rotation[(day, team)]:
                        continue
                    for m in BUMP_MARKETS:
                        held = np_disc._hr_pairs(fb, m)
                        for (pid, line), q in np_disc._hr_pairs(fc, m).items():
                            key = (day, pid, m)
                            if key in seen or pid == out_pid or teams.get(pid) != team or not same_prices(held.get((pid, line)), q) or not complete(q):
                                continue
                            fair = pin_fair(fc, m, (pid, line))
                            if not in_window(q["over"]) or fair is None or side_ev(fair, "over", q["over"]) < 0:
                                continue
                            seen.add(key)
                            bets.append(r28_bet(box, day, gid, pid, m, line, "over", q["over"]))
    return bets


def run_r28d(days, box, cfg):
    """({R28d_under bets}, {R28d_over bets}): LVA1/LVA2's line-vs-rolling-average rule on every Hard Rock side with a Pinnacle quote on the
    same line. Under when the line sits `threshold` below the player's rolling average, Over when it sits that far above. First read
    per player/market/night."""
    hist = collections.defaultdict(list)
    for (_, pid), row in box.items():
        hist[str(pid)].append(row)
    under, over, seen = [], [], set()
    for day, byg in sorted(days.items()):
        for gid, fs in byg.items():
            for f in fs:
                for m in np_disc.STAT:
                    for (pid, line), q in np_disc._hr_pairs(f, m).items():
                        key = (day, pid, m)
                        if key in seen or not complete(q) or pin_fair(f, m, (pid, line)) is None:
                            continue
                        avg = rolling_avg(hist[str(pid)], day, np_disc.STAT[m], cfg["min_prior_games"])
                        if not avg:
                            continue
                        gap = (line - avg) / avg
                        side = "under" if gap <= -cfg["threshold"] + EPS else "over" if gap >= cfg["threshold"] - EPS else None
                        if side is None or not in_window(q[side]):
                            continue
                        seen.add(key)
                        (under if side == "under" else over).append(r28_bet(box, day, gid, pid, m, line, side, q[side]))
    return under, over


def load_closes():
    """{day: {game id: close read}} from data/odds_close (read E)."""
    out = {}
    for p in sorted(glob.glob(R + "data/odds_close/2*.json")):
        d = common.read_json(p, None) or {}
        out[d.get("date")] = {f["game_id"]: f for f in d.get("fetches") or []}
    return out


def run_r28e(days, closes, box):
    """R28e late lag to close: between read C and the close read, Pinnacle's fair over moves PIN_CLOSE_MOVE_MIN or more toward a side while
    Hard Rock's line and prices do not change. Bet that side at Hard Rock (the C and close prices are the same). First per player/market/night."""
    bets, seen = [], set()
    for day, byg in sorted(days.items()):
        for gid, fs in byg.items():
            close = closes.get(day, {}).get(gid)
            c_read = next((f for f in fs if f["read"] == "C"), None)
            if not close or not c_read:
                continue
            for m in np_disc.STAT:
                at_close = np_disc._hr_pairs(close, m)
                for (pid, line), q in np_disc._hr_pairs(c_read, m).items():
                    key = (day, pid, m)
                    fc, fe = pin_fair(c_read, m, (pid, line)), pin_fair(close, m, (pid, line))
                    if key in seen or not complete(q) or not same_prices(at_close.get((pid, line)), q) or fc is None or fe is None:
                        continue
                    side = "over" if fe - fc >= PIN_CLOSE_MOVE_MIN - EPS else "under" if fc - fe >= PIN_CLOSE_MOVE_MIN - EPS else None
                    if side is None or not in_window(q[side]):
                        continue
                    seen.add(key)
                    bets.append(r28_bet(box, day, gid, pid, m, line, side, q[side]))
    return bets


def r28_bets(days, closes, box, news, cfg):
    """{track id: forward bets} for R28a/b/d/e over the stored odds nights from R28_FWD on."""
    fwd = {d: g for d, g in days.items() if d >= R28_FWD}
    d_under, d_over = run_r28d(fwd, box, cfg)
    return {"R28a": run_r28a(fwd, box), "R28b": run_r28b(fwd, box, news), "R28d_under": d_under, "R28d_over": d_over,
            "R28e": run_r28e(fwd, {d: c for d, c in closes.items() if d >= R28_FWD}, box)}


def export_r28(days=None, box=None):
    days = np_disc.load_days() if days is None else days
    box = np_disc._load_box() if box is None else box
    cfg = common.read_json(R + "config/rules.json", {})["pin_solo"]["lva1"]
    news = newly_out(R + "data/research/r28b_news.json", common.read_json(R + "data/state/injuries.json", {}) or {})
    gone = retired("research/lab_r28.json")
    bets = r28_bets(days, load_closes(), box, news, cfg)
    doc = {tid: tally(bets[tid]) for tid in R28_IDS if tid not in gone}
    return write_summary(R + "data/research/lab_r28.json", doc)


if __name__ == "__main__":
    export_np()
    export_lva()
    export_r28()
