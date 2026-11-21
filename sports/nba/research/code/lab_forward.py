"""lab_forward.py: nightly forward tallies for the Lab tracks NP1-NP4 and LVA1-LVA2.
Reads data/odds/*.json, data/shadow/*.json and the box scores. Writes data/research/lab_np.json and lab_lva.json (research
only: never picks, never the Record). auto_hypothesis.py calls export_np() and export_lva() each night.
"""
import collections, glob, json, os, statistics, sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) + os.sep
sys.path.insert(0, R + "scripts")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import np1_np2_np3_discovery as np_disc

NP_FWD = "2026-11-15"   # NP1-NP4 forward period starts (HYPOTHESES.md, Run NP)
LVA_FWD = "2026-11-16"  # LVA1-LVA2 forward period starts (HYPOTHESES.md, Run LVA)
EPS = 1e-9              # float slack on the threshold test, as engine.py
NP_RUNNERS = {"NP1": np_disc.run_np1, "NP2": np_disc.run_np2, "NP3": np_disc.run_np3, "NP4": np_disc.run_np4}
EMPTY_TALLY = {"w": 0, "l": 0, "units": 0.0, "pending": 0, "push": 0, "void": 0}
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


if __name__ == "__main__":
    export_np()
    export_lva()
