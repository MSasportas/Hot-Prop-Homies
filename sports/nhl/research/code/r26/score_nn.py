#!/usr/bin/env python3
"""Run 26 forward scorer: NN2fa-b, NN4, NN5, NN6 (research/HYPOTHESES.md, registered 2026-11-11 before testing).
Judged nights >= 2026-11-11; earlier nights printed as a labelled descriptive check only. Read-only on data/; writes research/fwd/nn.md
and research/fwd/nn.json.  python3 -I score_nn.py [repo_root]"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fwd"))
import score_fwd as F  # noqa: E402

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", ".."))
F.ROOT = ROOT
START = "2026-11-11"
NV = 65
F.BONF = NV
SHARP = ("pinnacle", "novig", "prophetx", "lowvig")
SOFT = ("draftkings", "fanduel", "betmgm", "espnbet", "betonlineag")
EXCH = ("novig", "prophetx")
VARS = ["NN2fa follow market", "NN2fb follow HR", "NN4 exch steam", "NN5 market moves", "NN6 fade soft"]
NAMES = {"Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF", "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR",
         "Chicago Blackhawks": "CHI", "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL", "Detroit Red Wings": "DET",
         "Edmonton Oilers": "EDM", "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montréal Canadiens": "MTL",
         "Montreal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD", "New York Islanders": "NYI", "New York Rangers": "NYR",
         "Ottawa Senators": "OTT", "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS", "Seattle Kraken": "SEA",
         "St Louis Blues": "STL", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL", "Toronto Maple Leafs": "TOR", "Utah Mammoth": "UTA",
         "Utah Hockey Club": "UTA", "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK", "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"}


def teams_of(date):
    doc = F.load(os.path.join(ROOT, "data/odds", date + ".json"))
    t = {}
    for f in doc["fetches"]:
        for o in ((f.get("markets") or {}).get("shots") or {}).get("outcomes") or []:
            if o.get("pid") is not None and o.get("team"):
                t[(f["game_id"], o["pid"])] = o["team"]
    return t


def ml_snaps(date):
    """gid -> sorted [(at, d_by_team)] with d = Hard Rock p(team) - market median p(team)."""
    p = os.path.join(ROOT, "data/featured", date + ".json")
    if not os.path.exists(p):
        return {}
    out = {}
    for s in F.load(p).get("snaps") or []:
        at = F.iso(s["at"])
        for gid, g in (s.get("games") or {}).items():
            fr = {}
            for b, mks in (g.get("books") or {}).items():
                h = (mks or {}).get("h2h")
                if not h or not h.get("last_update") or (at - F.iso(h["last_update"])).total_seconds() / 60 >= F.STALE_MIN:
                    continue
                oc = {NAMES.get(o["name"]): o["price"] for o in h.get("outcomes") or []}
                if g["home"] not in oc or g["away"] not in oc:
                    continue
                ph, pa = oc[g["home"]], oc[g["away"]]
                if 0 <= F.hold(ph, pa) <= 0.15:
                    fr[b] = F.fair_over(ph, pa)
            hr = fr.pop("hardrockbet", None)
            if hr is None or len(fr) < 4:
                continue
            m = F.median(fr.values())
            out.setdefault(int(gid), []).append((at, {g["home"]: hr - m, g["away"]: m - hr}))
    for v in out.values():
        v.sort(key=lambda z: z[0])
    return out


def run_night(date):
    reads = F.reads_for(date)
    res, start = F.shadow(date)
    team = teams_of(date)
    pre = [r for r in reads if start.get(r["game"]) and r["at"] < start[r["game"]]]
    last_cons = {}
    for r in pre:
        if r["cons"] is not None:
            last_cons[(r["game"], r["pid"], r["line"])] = r["cons"]
    bets = {v: [] for v in VARS}
    done = {v: set() for v in VARS}

    def add(v, r, side, e):
        price = r[side]
        key = (r["game"], r["pid"], r["line"], side)
        if price < -200 or key in done[v]:
            return
        done[v].add(key)
        lc = last_cons.get((r["game"], r["pid"], r["line"]))
        bets[v].append({"date": date, "game": r["game"], "pid": r["pid"], "line": r["line"], "side": side, "pull": r["pull"],
                        "at": r["at"].isoformat(), "price": price, "ev": 0.0 if e is None else round(e, 4),
                        "clv": None if lc is None else round(F.ev(lc if side == "over" else 1 - lc, price), 4),
                        "pl": F.grade(res.get((r["game"], r["pid"], r["line"])), side, r["line"], price)})

    def evs(fair, r, side):
        return F.ev(fair if side == "over" else 1 - fair, r[side])

    # NN2f
    ml = ml_snaps(date)
    for r in pre:
        if r["pull"] not in ("B", "C"):
            continue
        tm = team.get((r["game"], r["pid"]))
        sn = [z for z in ml.get(r["game"], []) if z[0] <= r["at"]]
        if not tm or not sn or tm not in sn[-1][1]:
            continue
        d = sn[-1][1][tm]
        if abs(d) < 0.02 - 1e-12:
            continue
        mk = "over" if d < 0 else "under"
        hrs = "under" if mk == "over" else "over"
        add("NN2fa follow market", r, mk, None if r["cons"] is None else evs(r["cons"], r, mk))
        add("NN2fb follow HR", r, hrs, None if r["cons"] is None else evs(r["cons"], r, hrs))
    # consecutive reads of the same game
    by = {}
    for r in pre:
        by.setdefault(r["game"], {}).setdefault(r["at"], {})[(r["pid"], r["line"])] = r
    for gid, ts in by.items():
        tl = sorted(ts)
        for t0, t1 in zip(tl, tl[1:]):
            for k, r1 in ts[t1].items():
                r0 = ts[t0].get(k)
                if not r0 or r0["over"] != r1["over"] or r0["under"] != r1["under"]:
                    continue
                both = {b: (r0["fairs"][b], r1["fairs"][b]) for b in r1["fairs"] if b in r0["fairs"]}
                # NN4
                ex = [both[b] for b in EXCH if b in both]
                if ex:
                    x0 = sum(a for a, _ in ex) / len(ex); x1 = sum(c for _, c in ex) / len(ex); dX = x1 - x0
                    if abs(dX) >= 0.03 - 1e-12:
                        s = "over" if dX > 0 else "under"
                        e = evs(x1, r1, s)
                        if e >= -1e-12:
                            add("NN4 exch steam", r1, s, e)
                # NN5
                ch = [c - a for a, c in both.values()]
                up = sum(1 for c in ch if c >= 0.015 - 1e-12); dn = sum(1 for c in ch if c <= -0.015 + 1e-12)
                if ch and r1["cons"] is not None:
                    mc = F.median(ch)
                    s = None
                    if up >= 3 and dn == 0 and mc >= 0.02 - 1e-12:
                        s = "over"
                    elif dn >= 3 and up == 0 and mc <= -0.02 + 1e-12:
                        s = "under"
                    if s:
                        e = evs(r1["cons"], r1, s)
                        if e >= -1e-12:
                            add("NN5 market moves", r1, s, e)
                # NN6
                so = [both[b] for b in SOFT if b in both]; sh = [both[b] for b in SHARP if b in both]
                if len(so) >= 3 and len(sh) >= 2:
                    dT = F.median([c for _, c in so]) - F.median([a for a, _ in so])
                    s1 = sum(c for _, c in sh) / len(sh); dS = s1 - sum(a for a, _ in sh) / len(sh)
                    if abs(dT) >= 0.02 - 1e-12 and dS * (1 if dT > 0 else -1) < 0.005:
                        s = "under" if dT > 0 else "over"
                        e = evs(s1, r1, s)
                        if e >= -1e-12:
                            add("NN6 fade soft", r1, s, e)
    return bets


def main():
    allb = {v: [] for v in VARS}
    for d in F.dates():
        for v, bl in run_night(d).items():
            allb[v].extend(bl)
    hdr = "| variant | bets | graded | W | units | ROI | 90% CI | p | mean CLV | candidate |\n|---|---|---|---|---|---|---|---|---|---|"
    def row(v, bl):
        s = F.summarize(bl)
        if not s["graded"]:
            return "| %s | %d | 0 | - | - | - | - | - | - | False |" % (v, s["bets"])
        return "| %s | %d | %d | %d | %+.2f | %+.1f%% | %+.0f..%+.0f%% | %.4f | %s | %s |" % (
            v, s["bets"], s["graded"], s["w"], s["units"], 100 * s["roi"], 100 * s["ci90"][0], 100 * s["ci90"][1], s["p_one_sided"],
            "-" if s["mean_clv"] is None else "%.4f" % s["mean_clv"], s.get("candidate", False))
    out = ["# Run 26 forward (research/code/r26/score_nn.py): NN2f, NN4-NN6, nights >= %s. Bar: n >= 300 graded, ROI > 0, p < %.5f, mean CLV > 0." % (START, 0.05 / NV), "", hdr]
    out += [row(v, [b for b in allb[v] if b["date"] >= START]) for v in VARS]
    out += ["", "Descriptive, seen nights < %s (not a test, never a result):" % START, "", hdr]
    out += [row(v, [b for b in allb[v] if b["date"] < START]) for v in VARS]
    open(os.path.join(ROOT, "research/fwd/nn.md"), "w").write("\n".join(out) + "\n")
    json.dump({v: F.summarize([b for b in allb[v] if b["date"] >= START]) for v in VARS}, open(os.path.join(ROOT, "research/fwd/nn.json"), "w"), indent=1)
    print("\n".join(out))


if __name__ == "__main__":
    main()
