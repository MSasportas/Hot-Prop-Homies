"""Run 22 (JJ1-JJ3): NBA pin_solo v2.6 ported to NHL shots. Discovery only (all nights already seen).
Usage: python -I research/code/r22/jj22.py <repo sports/nhl dir>   (reads data/odds, data/shadow, data/record; writes nothing)"""
import sys, os, json, glob, collections, datetime

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
MIN_MOVE, HOLD_MAX, STALE_MIN, EPS = 0.02, 0.15, 60, 1e-9


def be(a):
    return (-a) / (-a + 100.0) if a < 0 else 100.0 / (a + 100.0)


def dec(a):
    return 1.0 + (100.0 / -a if a < 0 else a / 100.0)


def fair(q):
    if not q or q.get("over") is None or q.get("under") is None:
        return None
    h = be(q["over"]) + be(q["under"]) - 1
    if not (0 <= h <= HOLD_MAX):
        return None
    return be(q["over"]) / (be(q["over"]) + be(q["under"]))


def pairs(m):
    out = {}
    for o in (m or {}).get("outcomes") or []:
        if o.get("pid") is None or o.get("line") is None:
            continue
        out.setdefault((o["pid"], o["line"]), {"over": None, "under": None, "name": o.get("name")})[o["side"]] = o["price"]
    return out


def main_lines(p):
    best = {}
    for (pid, line), q in p.items():
        if q["over"] is None or q["under"] is None:
            continue
        g = abs(be(q["over"]) / (be(q["over"]) + be(q["under"])) - 0.5)
        if pid not in best or g < best[pid][0]:
            best[pid] = (g, line, q)
    return {pid: (line, q) for pid, (_, line, q) in best.items()}


def iso(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def hr(f):
    return (f.get("markets") or {}).get("shots") or {}


def pin(f):
    return ((f.get("others") or {}).get("pinnacle") or {}).get("shots") or {}


# results
res = {}
for fn in glob.glob(os.path.join(ROOT, "data/shadow/*.json")):
    for r in json.load(open(fn, encoding="utf-8")).get("rows", []):
        if r.get("market") != "shots" or not r.get("result"):
            continue
        x = r["result"]
        if x.get("actual") is None:
            continue
        toi = x.get("toi")
        res[(r["game_id"], r["pid"])] = None if (not toi or toi in ("0:00", "00:00")) else x["actual"]


def grade(gid, pid, line, side, price):
    a = res.get((gid, pid), "missing")
    if a == "missing":
        return None, None
    if a is None:
        return "V", 0.0
    won = (a > line) if side == "over" else (a < line)
    return ("W", dec(price) - 1) if won else ("L", -1.0)


# record (NHL rule)
rec = {}
for ln in open(os.path.join(ROOT, "data/record/events.jsonl"), encoding="utf-8"):   # append-only Record log
    e = json.loads(ln)
    if e.get("t") == "shown" and e.get("kind") == "single":
        d, gid, pid, mk, line, side = e["id"].split(":")
        if mk == "shots":
            rec[(d, int(gid), int(pid))] = {"id": e["id"], "line": float(line), "side": side, "price": e["pick"]["price"],
                                           "result": None, "units": 0.0}
    elif e.get("t") in ("graded", "regraded"):
        d, gid, pid = e["id"].split(":")[:3]
        x = rec.get((d, int(gid), int(pid)))
        if x and x["id"] == e["id"]:
            x["result"], x["units"] = e["result"], e.get("units") or 0.0

picks, moves = [], []
for fn in sorted(glob.glob(os.path.join(ROOT, "data/odds/*.json"))):
    night = os.path.basename(fn)[:10]
    if night < "2026-10-19":
        continue
    d = json.load(open(fn, encoding="utf-8"))
    games = collections.defaultdict(list)
    for f in d["fetches"]:
        games[f["game_id"]].append(f)
    for gid, fs in games.items():
        fs.sort(key=lambda f: f["at"])
        last_pin = pairs(pin(fs[-1]))
        seen = set()
        for i in range(1, len(fs)):
            a, b = fs[i - 1], fs[i]
            pa, pb = pairs(pin(a)), pairs(pin(b))
            if not pb:
                continue
            ha, hb = pairs(hr(a)), pairs(hr(b))
            nxt = pairs(hr(fs[i + 1])) if i + 1 < len(fs) else None
            stale = True
            lu = hr(b).get("last_update")
            if lu:
                stale = (iso(b["at"]) - iso(lu)).total_seconds() / 60 >= STALE_MIN
            for pid, (line, q) in main_lines(hb).items():
                k = (pid, line)
                if k not in ha:
                    continue
                fa, fb = fair(pa.get(k)), fair(pb.get(k))
                if fa is None or fb is None or abs(fb - fa) < MIN_MOVE - EPS:
                    continue
                side = "over" if fb > fa else "under"
                s = 1 if side == "over" else -1
                pin_b = fb if side == "over" else 1 - fb
                # Hard Rock lag (JJ3)
                hfa, hfb = fair(ha.get(k)), fair(hb.get(k))
                hr_mv = s * (hfb - hfa) if hfa is not None and hfb is not None else None
                hr_next = None
                if nxt is not None and k in nxt and fair(nxt[k]) is not None and hfa is not None:
                    hr_next = s * (fair(nxt[k]) - hfa)
                moves.append({"night": night, "pair": a["pull"] + b["pull"], "mv": abs(fb - fa), "hr_mv": hr_mv, "hr_next": hr_next})
                if b["pull"] not in ("B", "C"):
                    continue
                price = q.get(side)
                if price is None or stale or price < -200 or price > 200:
                    continue
                ev = pin_b * dec(price) - 1
                if ev < -EPS:
                    continue
                if pid in seen:
                    continue
                seen.add(pid)
                lf = fair(last_pin.get(k))
                clv = None
                if lf is not None and fs[-1]["at"] >= b["at"]:
                    clv = (lf if side == "over" else 1 - lf) * dec(price) - 1
                r, u = grade(gid, pid, line, side, price)
                picks.append({"night": night, "gid": gid, "pid": pid, "name": q.get("name"), "line": line, "side": side,
                              "price": price, "ev": ev, "mv": abs(fb - fa), "pair": a["pull"] + b["pull"], "res": r, "u": u,
                              "clv": clv})


def summ(rows, label):
    g = [r for r in rows if r["res"] in ("W", "L")]
    w = sum(r["res"] == "W" for r in g)
    u = sum(r["u"] for r in g)
    c = [r["clv"] for r in rows if r.get("clv") is not None]
    print("%-34s n %3d  %3d-%-3d %+7.2fu  ROI %+6.1f%%  CLV %+5.1f%% (n %d)  ungraded %d" % (
        label, len(g), w, len(g) - w, u, 100 * u / len(g) if g else 0, 100 * sum(c) / len(c) if c else 0, len(c),
        len(rows) - len(g)))


print("JJ1 faithful NBA port, nights Oct 19 - Nov 9")
summ(picks, "ALL")
for lab, f in [("over", lambda r: r["side"] == "over"), ("under", lambda r: r["side"] == "under"),
               ("line 1.5", lambda r: r["line"] == 1.5), ("line 2.5", lambda r: r["line"] == 2.5),
               ("line 3.5+", lambda r: r["line"] >= 3.5),
               ("move 2-3 pts", lambda r: r["mv"] < 0.03), ("move 3-5 pts", lambda r: 0.03 <= r["mv"] < 0.05),
               ("move 5+ pts", lambda r: r["mv"] >= 0.05),
               ("A->B (flag at B)", lambda r: r["pair"] == "AB"), ("B->C (flag at C)", lambda r: r["pair"] == "BC"),
               ("Oct 19-31", lambda r: r["night"] <= "2026-10-31"), ("Nov 1-9", lambda r: r["night"] >= "2026-11-01"),
               ("Oct 19-27 (pre-Q13 reg)", lambda r: r["night"] <= "2026-10-27"),
               ("Oct 28-Nov 9", lambda r: r["night"] >= "2026-10-28")]:
    summ([r for r in picks if f(r)], lab)

print("\nJJ3 Pinnacle 2+ pt moves on Hard Rock main lines (any price)")
mc = collections.Counter(m["pair"] for m in moves)
print("moves by pair:", dict(mc), "total", len(moves), "nights", len(set(m["night"] for m in moves)))
for p in sorted(mc):
    mm = [m for m in moves if m["pair"] == p and m["hr_mv"] is not None]
    lag = [m for m in mm if m["hr_mv"] < 0.01]
    cu = [m for m in lag if m["hr_next"] is not None]
    cu1 = [m for m in cu if m["hr_next"] >= 0.01]
    print("  %s: HR two-sided both reads %d; HR moved < 1 pt same way (lag) %d (%.0f%%); of lagged with a next read %d, caught up >= 1 pt %d"
          % (p, len(mm), len(lag), 100 * len(lag) / max(1, len(mm)), len(cu), len(cu1)))
allm = [m for m in moves if m["hr_mv"] is not None]
print("  all: lag %d of %d (%.0f%%); median HR move toward side %.3f" % (
    sum(m["hr_mv"] < 0.01 for m in allm), len(allm), 100 * sum(m["hr_mv"] < 0.01 for m in allm) / max(1, len(allm)),
    sorted(m["hr_mv"] for m in allm)[len(allm) // 2] if allm else 0))
print("  pin moves per night (nights with reads):", round(len(moves) / max(1, len(set(m["night"] for m in moves))), 1))

print("\nJJ2 overlap with the NHL Record (shots singles)")
recn = {k: v for k, v in rec.items() if k[0] >= "2026-10-19"}
cat = collections.defaultdict(list)
for r in picks:
    x = recn.get((r["night"], r["gid"], r["pid"]))
    if x is None:
        cat["new"].append(r)
    elif x["side"] == r["side"] and x["line"] == r["line"]:
        cat["same"].append(r)
    elif x["line"] == r["line"]:
        cat["opposite"].append(r)
    else:
        cat["other line"].append(r)
for c in ("same", "opposite", "other line", "new"):
    summ(cat[c], "JJ1 " + c)
for r in cat["opposite"]:
    print("   opposite:", r["night"], r["name"], r["side"], r["line"], r["price"], r["res"])
rg = [v for v in recn.values() if v["result"] in ("W", "L")]
rw = sum(v["result"] == "W" for v in rg)
ru = sum(v["units"] for v in rg)
nights = sorted(set(m["night"] for m in moves) | set(k[0] for k in recn))
print("NHL Record Oct 19+: n %d %d-%d %+.2fu ROI %+.1f%%  picks/night %.2f (%d nights)" % (
    len(rg), rw, len(rg) - rw, ru, 100 * ru / max(1, len(rg)), len(recn) / len(nights), len(nights)))
new = [r for r in cat["new"] if r["res"] in ("W", "L")]
nw = sum(r["res"] == "W" for r in new)
nu = sum(r["u"] for r in new)
cn = len(rg) + len(new)
print("Record OR JJ1-new: n %d %d-%d %+.2fu ROI %+.1f%%  picks/night %.2f" % (
    cn, rw + nw, cn - rw - nw, ru + nu, 100 * (ru + nu) / max(1, cn), (len(recn) + len(cat["new"])) / len(nights)))
print("\nJJ1 picks:")
for r in picks:
    print("  %s %-22s %-5s %.1f %+4d ev %+.3f mv %.3f %s %s clv %s" % (r["night"], r["name"], r["side"], r["line"], r["price"],
          r["ev"], r["mv"], r["pair"], r["res"], "%+.3f" % r["clv"] if r["clv"] is not None else "-"))
