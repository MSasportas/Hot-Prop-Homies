"""auto_hypothesis.py: nightly hypothesis tester (Matt 2026-11-11 directive).
Cycles through AH1-AH15 (registered in HYPOTHESES.md, Run Auto section).
Each run tests one variant, appends a compact entry to research/LOG.md.
Reads only: data/odds/*.json, data/record/events.jsonl, box scores.
Writes: data/research/hypothesis_state.json (index), appends to research/LOG.md.
Never posts to Discord, never affects picks. No API calls.
Usage: python research/code/auto_hypothesis.py [--force AHN]
"""
import collections, glob, gzip, json, os, random, statistics, sys
from datetime import date

R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) + os.sep
sys.path.insert(0, R + "scripts")
import common, odds

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FWD = "2026-11-10"  # forward period starts here (run8 registration night)

# ---------------------------------------------------------------------------
# Data loading (mirrors run8_moves.py)
# ---------------------------------------------------------------------------

def _fo(q):
    if not q or not q.get("over") or not q.get("under"):
        return None
    h = odds.hold(q["over"], q["under"])
    return odds.fair_two_sided(q["over"], q["under"]) if 0 <= h <= 0.15 else None

def _bk(f, book, m):
    return odds.pairs(((f.get("others") or {}).get(book) or {}).get(m, {}).get("outcomes"))

def _hr(f, m):
    return odds.pairs((f["markets"].get(m) or {}).get("outcomes"))

def _side_p(fair, side):
    return None if fair is None else (fair if side == "over" else 1 - fair)

WIN = {("A", "B"): "11AM->90", ("B", "C"): "90->45", ("C", "D"): "45->20"}
STAT = {"rebounds": "reb", "points": "pts", "assists": "ast", "threes": "fg3m"}

def _load_box():
    box = {}
    for path in ("data/seed/players_2026-27.json.gz", "data/state/box/players_2026-27.json.gz"):
        fp = R + path
        if os.path.exists(fp):
            for row in json.load(gzip.open(fp, "rt")):
                box[(row["game"], row["pid"])] = row
    return box

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

def _later(days_map, day, gid, at, pid, m, line, side):
    fs = [f for f in days_map.get(day, {}).get(gid, []) if f["at"] > at]
    out = {}
    for tag, f in (("next", fs[0] if fs else None), ("close", fs[-1] if fs else None)):
        if not f:
            continue
        pin_q = _bk(f, "pinnacle", m).get((pid, line))
        out[tag + "_pin"] = _side_p(_fo(pin_q), side)
        h = _hr(f, m).get((pid, line))
        out[tag + "_hr"] = h[side] if h else None
    return out

def build_moves():
    """Return (moves_all, days_map, box). moves_all = list of dicts, one per MOVES population entry."""
    days_map = {}
    for p in sorted(glob.glob(R + "data/odds/2*.json")):
        d = json.load(open(p, encoding="utf-8"))
        byg = collections.defaultdict(list)
        for f in sorted(d["fetches"], key=lambda f: f["at"]):
            byg[f["game_id"]].append(f)
        days_map[d["date"]] = byg

    box = _load_box()
    moves = []
    for day, byg in days_map.items():
        seen = set()
        for gid, fs in byg.items():
            for a, b in zip(fs, fs[1:]):
                for m in b["markets"]:
                    ha, hb = _hr(a, m), _hr(b, m)
                    pa, pb = _bk(a, "pinnacle", m), _bk(b, "pinnacle", m)
                    oth = [x for x in (b.get("others") or {}) if x != "pinnacle"]
                    oa = {x: _bk(a, x, m) for x in oth}
                    ob = {x: _bk(b, x, m) for x in oth}
                    for k, h in hb.items():
                        if k not in ha:
                            continue
                        if not (h.get("over") and h.get("under") and ha[k].get("over") and ha[k].get("under")):
                            continue
                        fa, fb = _fo(pa.get(k)), _fo(pb.get(k))
                        if fa is None or fb is None or abs(fb - fa) < 0.02:
                            continue
                        side = "over" if fb > fa else "under"
                        price = h[side]
                        key = (k[0], m)
                        if not (-200 <= price <= 200) or key in seen:
                            continue
                        seen.add(key)
                        mv = [y - x for x, y in
                              ((_fo(oa[o].get(k)), _fo(ob[o].get(k))) for o in oth)
                              if x is not None and y is not None]
                        sm = [x if side == "over" else -x for x in mv]
                        d0 = odds.decimal(ha[k][side])
                        d1 = odds.decimal(price)
                        hr_move = "stale" if d1 == d0 else ("followed" if d1 < d0 else "against")
                        entry = dict(
                            day=day, gid=gid, pid=k[0], m=m, line=k[1], side=side, price=price,
                            size=abs(fb - fa),
                            others=statistics.median(sm) if sm else None,
                            n_follow=sum(x >= 0.01 for x in sm),
                            n_oth=len(sm),
                            hr=hr_move,
                            ev_pin=odds.ev(_side_p(fb, side), price),
                            win=WIN.get((a["read"], b["read"]), a["read"] + b["read"]),
                            pin_at=_side_p(fb, side),
                            res=_grade(box, gid, k[0], m, k[1], side),
                        )
                        entry.update(_later(days_map, day, gid, b["at"], k[0], m, k[1], side))
                        moves.append(entry)
    return moves, days_map, box

def _units(e):
    return odds.decimal(e["price"]) - 1 if e["res"] == "W" else (-1.0 if e["res"] == "L" else 0.0)

def _clv_pin(e):
    cp = e.get("close_pin")
    return None if cp is None else cp * odds.decimal(e["price"]) - 1

def _summarize(label, es):
    """Return dict with n, graded, w, l, units, roi, clv."""
    g = [e for e in es if e["res"] in ("W", "L")]
    w = sum(e["res"] == "W" for e in g)
    u = sum(_units(e) for e in g)
    clvs = [x for x in map(_clv_pin, es) if x is not None]
    roi = (u / len(g)) if g else None
    return {"label": label, "n": len(es), "graded": len(g), "w": w, "l": len(g) - w,
            "units": round(u, 2), "roi": round(roi * 100, 1) if roi is not None else None,
            "clv_mean": round(statistics.mean(clvs) * 100, 1) if clvs else None, "clv_n": len(clvs)}

def fmt_summary(s):
    roi = ("%+.1f%%" % s["roi"]) if s["roi"] is not None else "-"
    clv = ("%+.1f%%" % s["clv_mean"]) if s["clv_mean"] is not None else "-"
    return "n %d graded %d %d-%d %+.2fu ROI %s CLV_pin %s (n %d)" % (
        s["n"], s["graded"], s["w"], s["l"], s["units"], roi, clv, s["clv_n"])

# ---------------------------------------------------------------------------
# Hypothesis definitions (AH1-AH15, pre-registered in HYPOTHESES.md Run Auto)
# ---------------------------------------------------------------------------

HYPOTHESES = [
    # (id, short label, description, filter function for MOVES)
    ("AH1",  "Large unders (4+ pt move, under side)",
     "MOVES where Pinnacle move >= 4 pts AND side = under",
     lambda e: e["size"] >= 0.04 and e["side"] == "under"),

    ("AH2",  "Late + large (last 90 min, move 3+ pts)",
     "MOVES where window is 90->45 or 45->20 AND move >= 3 pts",
     lambda e: e["win"] in ("90->45", "45->20") and e["size"] >= 0.03),

    ("AH3",  "Solo + late (solo Pinnacle, last 90 min)",
     "MOVES where others < 1 pt AND window is 90->45 or 45->20",
     lambda e: e.get("others") is not None and e["others"] < 0.01 and e["win"] in ("90->45", "45->20")),

    ("AH4",  "Stale HR + FAIR (HR stale, EV >= 0)",
     "MOVES where HR price unchanged (stale) AND ev_pin >= 0",
     lambda e: e["hr"] == "stale" and e.get("ev_pin", -1) >= 0),

    ("AH5",  "Large solo (4+ pt solo Pinnacle move)",
     "MOVES where move >= 4 pts AND others < 1 pt",
     lambda e: e["size"] >= 0.04 and e.get("others") is not None and e["others"] < 0.01),

    ("AH6",  "90->45 window only",
     "MOVES in the 90->45 minute window",
     lambda e: e["win"] == "90->45"),

    ("AH7",  "45->20 window only",
     "MOVES in the 45->20 minute window",
     lambda e: e["win"] == "45->20"),

    ("AH8",  "Unders in last 90 min",
     "MOVES where side = under AND window in last 90 min",
     lambda e: e["side"] == "under" and e["win"] in ("90->45", "45->20")),

    ("AH9",  "2-4 books following (consensus middle band)",
     "MOVES where 2-4 other books moved >= 1 pt the same way",
     lambda e: 2 <= e.get("n_follow", 0) <= 4),

    ("AH10", "Large move unders by size band (3-4 vs 4+)",
     "MOVES: unders, split 3-4 pts vs 4+ pts",
     lambda e: e["side"] == "under" and e["size"] >= 0.03),

    ("AH11", "Morning overs vs unders",
     "MOVES in 11AM->90 window, split by side",
     lambda e: e["win"] == "11AM->90"),

    ("AH12", "Solo large (3+ pt, solo Pinnacle)",
     "MOVES where move >= 3 pts AND others < 1 pt",
     lambda e: e["size"] >= 0.03 and e.get("others") is not None and e["others"] < 0.01),

    ("AH13", "Stale HR + unders",
     "MOVES where HR price unchanged AND side = under",
     lambda e: e["hr"] == "stale" and e["side"] == "under"),

    ("AH14", "Small FAIR moves (2-3 pt, ev_pin >= 0)",
     "MOVES where move 2-3 pts AND ev_pin >= 0 (the small-move FAIR question)",
     lambda e: e["size"] < 0.03 and e.get("ev_pin", -1) >= 0),

    ("AH15", "Late + FAIR (last 90 min, ev_pin >= 0)",
     "MOVES where window is last 90 min AND ev_pin >= 0",
     lambda e: e["win"] in ("90->45", "45->20") and e.get("ev_pin", -1) >= 0),
]

HYPO_IDS = [h[0] for h in HYPOTHESES]

# ---------------------------------------------------------------------------
# State + main
# ---------------------------------------------------------------------------

def load_state():
    path = R + "data/research/hypothesis_state.json"
    return common.read_json(path, {}) or {}

def save_state(st):
    os.makedirs(R + "data/research", exist_ok=True)
    common.write_json(R + "data/research/hypothesis_state.json", st)

def next_hypo_idx(st):
    last = st.get("last_id")
    if last not in HYPO_IDS:
        return 0
    return (HYPO_IDS.index(last) + 1) % len(HYPOTHESES)

def log_path():
    return os.path.join(R, "research", "LOG.md")

def prepend_log(text):
    path = log_path()
    existing = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    # Insert after the first line (header) if it starts with #
    lines = existing.splitlines(keepends=True)
    if lines and lines[0].startswith("#"):
        new = lines[0] + "\n" + text + "\n" + "".join(lines[1:])
    else:
        new = text + "\n" + existing
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)

NOUN = {"rebounds": "rebounds", "points": "points", "assists": "assists", "threes": "3-pointers"}


def _names():
    out = {}
    for p in sorted(glob.glob(R + "data/odds/2*.json")):
        for f in json.load(open(p, encoding="utf-8"))["fetches"]:
            for mk in (f.get("markets") or {}).values():
                for o in mk.get("outcomes", []):
                    if o.get("pid") and o.get("name"):
                        out[str(o["pid"])] = o["name"]
    return out


def export_lab(moves):
    """data/research/lab_ah.json for the page's Lab tab (Matt 2026-11-12: everything being tested shows in the Lab, with its
    picks): each registered hypothesis's FORWARD bets (nights >= FWD, Hard Rock price at or better than Pinnacle fair, the
    live rule's shape) with totals and the bets by night. Research only."""
    names = _names()
    doc = {"active": True, "note": "Research only: forward results of the registered filters on Pinnacle moves. Never picks.",
           "from": FWD, "tests": {}}
    for hid, hlabel, hdesc, hfn in HYPOTHESES:
        es = [e for e in moves if e["day"] >= FWD and e.get("ev_pin", -1) >= 0 and hfn(e)]
        nights = {}
        tot = {"w": 0, "l": 0, "push": 0, "void": 0, "units": 0.0, "pending": 0}
        for e in es:
            res = {"W": "W", "L": "L", "P": "PUSH", "V": "VOID"}.get(e["res"])
            u = _units(e) if res in ("W", "L") else (0.0 if res else None)
            tot[{"W": "w", "L": "l", "PUSH": "push", "VOID": "void", None: "pending"}[res]] += 1
            tot["units"] += u or 0.0
            nights.setdefault(e["day"], []).append({
                "player": names.get(str(e["pid"]), "Player %s" % e["pid"]), "market": e["m"], "line": e["line"], "side": e["side"],
                "bet": "%s %s %s" % ("Over" if e["side"] == "over" else "Under", e["line"], NOUN.get(e["m"], e["m"])),
                "price": e["price"], "result": res, "units": None if u is None else round(u, 2)})
        doc[hid] = dict(tot, units=round(tot["units"], 2))
        doc["tests"][hid] = {"label": hlabel, "rule": hdesc, "nights": [
            {"date": d, "w": sum(b["result"] == "W" for b in bs), "l": sum(b["result"] == "L" for b in bs),
             "units": round(sum(b["units"] or 0 for b in bs), 2), "bets": bs} for d, bs in sorted(nights.items(), reverse=True)]}
    path = R + "data/research/lab_ah.json"
    old = None
    try:
        old = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        pass
    if old is None or {k: v for k, v in old.items() if k != "updated_at"} != doc:
        doc["updated_at"] = common.iso(common.now())
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
            json.dump(doc, fh, separators=(",", ":"), sort_keys=True)
    return doc


def run(force_id=None):
    st = load_state()
    if force_id:
        idx = next((i for i, h in enumerate(HYPOTHESES) if h[0] == force_id), 0)
    else:
        idx = next_hypo_idx(st)

    hid, hlabel, hdesc, hfn = HYPOTHESES[idx]
    today = date.today().isoformat()

    moves, _, _ = build_moves()
    try:
        export_lab(moves)
    except Exception as e:                                   # the Lab file can never stop the nightly test
        print("lab export skipped: %s" % type(e).__name__)
    fwd = [e for e in moves if e["day"] >= FWD]

    all_m = [e for e in moves]
    fwd_m = [e for e in fwd]
    fair_all = [e for e in all_m if e.get("ev_pin", -1) >= 0]
    fair_fwd = [e for e in fwd_m if e.get("ev_pin", -1) >= 0]

    # Apply hypothesis filter
    sub_all = [e for e in all_m if hfn(e)]
    sub_fwd = [e for e in fwd_m if hfn(e)]
    sub_fair_all = [e for e in fair_all if hfn(e)]
    sub_fair_fwd = [e for e in fair_fwd if hfn(e)]

    disc = _summarize("discovery all", sub_all)
    fwd_sum = _summarize("forward all", sub_fwd)
    disc_fair = _summarize("discovery FAIR", sub_fair_all)
    fwd_fair = _summarize("forward FAIR", sub_fair_fwd)

    # Format LOG entry
    nights_all = len({e["day"] for e in sub_all})
    nights_fwd = len({e["day"] for e in sub_fwd})
    entry_lines = [
        "## %s, %s (auto; %s)" % (today, hid, hlabel),
        "Filter: %s. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night)." % hdesc,
        "Discovery (<2026-11-10, %d nights): %s" % (nights_all, fmt_summary(disc)),
        "Discovery FAIR (ev_pin>=0): %s" % fmt_summary(disc_fair),
        "Forward (>=%s, %d nights): %s" % (FWD, nights_fwd, fmt_summary(fwd_sum)),
        "Forward FAIR: %s" % fmt_summary(fwd_fair),
        "Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: " + (
            "FORWARD - accumulating" if fwd_sum["graded"] < 150 else
            ("CANDIDATE" if (fwd_sum["roi"] or -1) > 0 else "BELOW BAR")),
        "",
    ]
    entry = "\n".join(entry_lines)
    lp = log_path()
    if entry_lines[0] not in (open(lp, encoding="utf-8").read() if os.path.exists(lp) else ""):   # a retried run must not log twice
        prepend_log(entry)
    print(entry)

    save_state({"last_id": hid, "last_run": today, "idx": idx})
    return 0

if __name__ == "__main__":
    force = None
    if "--force" in sys.argv:
        i = sys.argv.index("--force")
        if i + 1 < len(sys.argv):
            force = sys.argv[i + 1]
    sys.exit(run(force))
