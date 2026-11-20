"""lab_retire.py: retire dead Lab tests on their own and flag passing ones for the Sharp (research/lab-retirement-spec.md).

Run once a night after the Lab summaries refresh (a second run the same day does nothing; PC_NOW sets the clock like the pipeline):  python3 -I scripts/lab_retire.py --sport nba|nhl
Reads  sports/<sport>/config/lab.json, each track's summary file and config/lab_state.json.
Writes lab.json (retired tracks leave tests[]), config/lab_retired.jsonl (append-only archive) and lab_state.json.
It never touches live rules or the Record: a passing track only gets status "ready_for_sharp".
"""
import argparse
import datetime
import json
import math
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

Z_FULL = 1.645              # one-sided 95%
Z_EARLY = 2.33              # one-sided 99%
MIN_K = 30                  # fewer graded bets than this is never judged
PENDING_MAX = 0.25          # skip a run while more than this share of graded bets is still open
VOID_MAX = 0.5              # voids above this share of graded bets is a data-quality problem, not a verdict
STREAK_NEEDED = 2           # consecutive nightly fails before a retirement
MAX_RETIRE_PER_RUN = 5
CAP_MULT = 2                # a track still undecided at this many times `need` is retired
STALL_AGE_DAYS = 45
STALL_IDLE_DAYS = 21
DEFAULT_FIRST_SEEN = "2026-11-12"     # the Lab config date: tracks without first_seen started then
READY = "ready_for_sharp"

FAIL_FULL, FAIL_EARLY, CAP, STALLED = "fail_full", "fail_early", "inconclusive_cap", "stalled"
RETIRE_REASONS = (FAIL_FULL, FAIL_EARLY, CAP, STALLED)


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(path, doc):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def archive_events(arch_path):
    try:
        with open(arch_path, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
    except (OSError, ValueError):
        return []


def retired_ids(arch_path):
    return {ev["id"] for ev in archive_events(arch_path) if ev.get("event") == "retired"}


def retired_stats(config_dir, summary):
    """The stats keys of retired tracks read from this summary file: exporters skip them."""
    events = archive_events(os.path.join(config_dir, "lab_retired.jsonl"))
    return {ev["stats"] for ev in events if ev.get("event") == "retired" and ev.get("summary") == summary}


def block_clv(block):
    clv = block.get("clv")
    if clv is None and isinstance(block.get("clv_flags"), dict):
        clv = block["clv_flags"].get("mean")
    return clv if isinstance(clv, (int, float)) else None


def final_stats(track, block):
    """Graded-bet numbers for a track. A fade track (a pass means the bet side loses) is mirrored."""
    w, l = int(block.get("w") or 0), int(block.get("l") or 0)
    k = w + l
    sign = -1 if track.get("direction") == "fade" else 1
    units = sign * float(block.get("units") or 0)
    clv = block_clv(block)
    return {"w": w, "l": l, "push": int(block.get("push") or 0), "void": int(block.get("void") or 0),
            "pending": int(block.get("pending") or 0), "units": round(units, 2), "k": k,
            "roi": units / k if k else 0.0, "se": 1 / math.sqrt(k) if k else None,
            "clv": None if clv is None else sign * clv}


def evaluate(track, block):
    """One night's verdict for a track: {"verdict": retire|ready|keep|skip, "reason", "final", "roi_upper95"}.
    `retire` here is the single-night condition; run() applies the two-night streak."""
    f = final_stats(track, block)
    k, need = f["k"], track["need"]
    out = {"verdict": "skip", "reason": None, "final": f, "roi_upper95": None}
    if k < MIN_K:
        return out
    if f["pending"] > PENDING_MAX * k:
        out["reason"] = "pending"
        return out
    if f["void"] > VOID_MAX * k:
        out["reason"] = "data_quality"
        return out
    out["roi_upper95"] = round(f["roi"] + Z_FULL * f["se"], 4)
    clv = f["clv"]
    clv_ok_to_retire = clv is None or clv <= 0
    if k >= need and f["roi"] + Z_FULL * f["se"] < 0 and clv_ok_to_retire:
        return dict(out, verdict="retire", reason=FAIL_FULL)
    if k >= max(MIN_K, math.ceil(need / 2)) and f["roi"] + Z_EARLY * f["se"] < 0 and clv_ok_to_retire:
        return dict(out, verdict="retire", reason=FAIL_EARLY)
    if k >= need:
        proven = clv > 0 if clv is not None else f["roi"] - Z_FULL * f["se"] > 0
        if f["units"] > 0 and proven:
            return dict(out, verdict="ready")
        if k >= CAP_MULT * need:
            return dict(out, verdict="retire", reason=CAP)
    return dict(out, verdict="keep")


def is_stalled(track, k, entry, today):
    """Ran out of picks: old, under half its sample, and no new graded bet for weeks."""
    if track.get("seasonal"):
        return False
    first_seen = datetime.date.fromisoformat(track.get("first_seen") or DEFAULT_FIRST_SEEN)
    idle_since = datetime.date.fromisoformat(entry.get("k_changed") or today.isoformat())
    return ((today - first_seen).days >= STALL_AGE_DAYS and k < track["need"] / 2
            and (today - idle_since).days >= STALL_IDLE_DAYS)


def read_block(sport_dir, track):
    base = sport_dir if track.get("base") == "root" else os.path.join(sport_dir, "data")
    doc = read_json(os.path.join(base, track["summary"]))
    block = doc.get(track["stats"]) if isinstance(doc, dict) else None
    return block if isinstance(block, dict) and "units" in block else None


def archive_event(ts, event, track, verdict, reason=None):
    f = verdict["final"]
    final = {key: f[key] for key in ("w", "l", "push", "void", "pending", "units")}
    final.update(roi=round(f["roi"], 4), clv=f["clv"], se=None if f["se"] is None else round(f["se"], 4))
    return {"ts": ts, "event": event, "id": track["id"], "title": track.get("title"), "rule": track.get("rule"),
            "summary": track["summary"], "stats": track["stats"], "need": track["need"], "reason": reason, "final": final,
            "roi_upper95": verdict["roi_upper95"], "first_seen": track.get("first_seen") or DEFAULT_FIRST_SEEN}


def run(sport, root=REPO, now=None):
    now = now or (datetime.datetime.fromisoformat(os.environ["PC_NOW"]) if os.environ.get("PC_NOW") else datetime.datetime.now(datetime.timezone.utc))
    today = now.date()
    sport_dir = os.path.join(root, "sports", sport)
    cfg_dir = os.path.join(sport_dir, "config")
    lab_path, state_path = os.path.join(cfg_dir, "lab.json"), os.path.join(cfg_dir, "lab_state.json")
    arch_path = os.path.join(cfg_dir, "lab_retired.jsonl")
    lab = read_json(lab_path)
    if not isinstance(lab, dict) or not isinstance(lab.get("tests"), list):
        print("lab_retire: %s lab.json unreadable, nothing done" % sport)
        return []
    state = read_json(state_path, {}) or {}
    if state.get("day") == today.isoformat():
        return []                                   # once a day: a second run the same day must not count as another night
    tracks_state = state.get("tracks") or {}
    already = retired_ids(arch_path)
    ts = now.isoformat(timespec="seconds")
    events, retiring, new_state = [], [], {}
    for track in lab["tests"]:
        if track.get("no_auto_retire"):
            continue
        block = read_block(sport_dir, track)
        if block is None:
            print("lab_retire: %s %s summary unreadable, skipped" % (sport, track["id"]))
            new_state[track["id"]] = tracks_state.get(track["id"], {})
            continue
        verdict = evaluate(track, block)
        k = verdict["final"]["k"]
        entry = tracks_state.get(track["id"], {})
        changed = entry.get("k") != k
        reason = verdict["reason"] if verdict["verdict"] == "retire" else None
        if reason is None and (verdict["verdict"] != "skip" or verdict["reason"] is None) and is_stalled(track, k, entry, today):
            reason = STALLED
        streak = entry.get("fail_streak", 0) + 1 if reason else 0
        new_state[track["id"]] = {"fail_streak": streak, "k": k, "k_changed": today.isoformat() if changed else entry.get("k_changed", today.isoformat())}
        if reason and streak >= STREAK_NEEDED and track["id"] not in already:
            retiring.append((track, verdict, reason))
        elif verdict["verdict"] == "ready" and track.get("status") != READY:
            track["status"], track["ready_at"] = READY, today.isoformat()
            events.append(archive_event(ts, "ready", track, verdict))
    for track, verdict, reason in retiring[:MAX_RETIRE_PER_RUN]:
        events.append(archive_event(ts, "retired", track, verdict, reason))
        lab["tests"].remove(track)
        new_state.pop(track["id"], None)
    if events:
        with open(arch_path, "a", encoding="utf-8", newline="\n") as fh:
            for ev in events:
                fh.write(json.dumps(ev, ensure_ascii=False, separators=(",", ":")) + "\n")
        retired_total = len(already) + sum(ev["event"] == "retired" for ev in events)
        lab["retired_count"], lab["updated"] = retired_total, today.isoformat()
        write_json(lab_path, lab)
    write_json(state_path, {"updated": ts, "day": today.isoformat(), "tracks": new_state})
    return events


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sport", required=True, choices=("nba", "nhl"))
    args = ap.parse_args(argv)
    for ev in run(args.sport):
        print("lab_retire: %s %s %s" % (args.sport, ev["event"], ev["id"]))


if __name__ == "__main__":
    sys.exit(main())
