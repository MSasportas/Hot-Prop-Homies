"""Run 10 (2026-11-12, Matt picked idea #2): LINE disagreements. Hard Rock main line differs from Pinnacle main line.

Bet at Hard Rock toward Pinnacle: Pinnacle higher -> OVER Hard Rock lower line; Pinnacle lower -> UNDER Hard Rock higher line.
lb = a LOWER BOUND on the edge with no model: P_pin(side at Pinnacle line) x Hard Rock decimal - 1. The true chance at Hard
Rock easier line is higher than at Pinnacle line, so lb >= 0 means +EV against Pinnacle whatever the stat distribution is.
One bet per player / market / night: the first read (B, C, D; A reported apart) where it qualifies. Hard Rock price -200..+200.
Close: last later read of the game. Stored reads only. Usage (from sports/nba): python research/code/run10/line_disagree.py
"""
import glob, gzip, json, os, statistics, sys
sys.path.insert(0, "scripts")
import odds
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
STAT = {"rebounds": "reb", "points": "pts", "assists": "ast", "threes": "fg3m"}
OTHERS = ["draftkings", "fanduel", "betmgm", "espnbet", "betrivers", "betonlineag", "novig", "prophetx"]


def load_box():
    box = {}
    for p in ("data/seed/players_2026-27.json.gz", "data/state/box/players_2026-27.json.gz"):
        if os.path.exists(p):
            for r in json.load(gzip.open(p, "rt")):
                box[(str(r["game"]), str(r["pid"]))] = r
    return box


def grade(box, gid, pid, m, line, side):
    b = box.get((str(gid), str(pid)))
    if not b:
        return "?"
    if b.get("dnp") or not b.get("min"):
        return "V"
    x = b.get(STAT[m])
    if x is None:
        return "?"
    return "P" if x == line else ("W" if (x > line) == (side == "over") else "L")


def fair_over(q):
    if not q or not q.get("over") or not q.get("under"):
        return None
    return odds.fair_two_sided(q["over"], q["under"]) if 0 <= odds.hold(q["over"], q["under"]) <= 0.15 else None


def main_line(pairs, pid):
    """The main line a book shows for a player: the two-sided line closest to 50/50."""
    best = None
    for (p, line), q in pairs.items():
        if p != pid:
            continue
        f = fair_over(q)
        if f is not None and (best is None or abs(f - .5) < best[0]):
            best = (abs(f - .5), line, f)
    return None if best is None else (best[1], best[2])


def bk(f, book, m):
    return odds.pairs(((f.get("others") or {}).get(book) or {}).get(m, {}).get("outcomes"))


def build():
    box, out = load_box(), []
    for path in sorted(glob.glob("data/odds/*.json")):
        day = os.path.basename(path)[:-5]
        fs = sorted(json.load(open(path))["fetches"], key=lambda x: x["at"])
        seen = set()
        for f in fs:
            if not f.get("markets") or not f.get("others"):
                continue
            gid = str(f["game_id"])
            for m in STAT:
                hr = odds.pairs((f["markets"].get(m) or {}).get("outcomes"))
                pin = bk(f, "pinnacle", m)
                for (pid, L), q in hr.items():
                    if not q.get("over") or not q.get("under") or (pid, L) in pin:
                        continue
                    ml = main_line(pin, pid)
                    if ml is None or ml[0] == L:
                        continue
                    Lp, fo = ml
                    side = "over" if Lp > L else "under"
                    price = q[side]
                    if not (-200 <= price <= 200):
                        continue
                    key = (day, pid, m, "A" if f["read"] == "A" else "live")
                    if key in seen:
                        continue
                    seen.add(key)
                    p_side = fo if side == "over" else 1 - fo
                    lb = p_side * odds.decimal(price) - 1
                    agree = total = 0          # other books on the Pinnacle side of the Hard Rock line
                    for b in OTHERS:
                        x = main_line(bk(f, b, m), pid)
                        if x:
                            total += 1
                            agree += (x[0] > L) if side == "over" else (x[0] < L)
                    later = [x for x in fs if str(x["game_id"]) == gid and x["at"] > f["at"] and x.get("markets")]
                    c = {"hr_line_toward": None, "hr_dp": None, "clv_pin": None}
                    if later:
                        last = later[-1]
                        hml = main_line(odds.pairs((last["markets"].get(m) or {}).get("outcomes")), pid)
                        if hml:
                            d = (hml[0] > L) - (hml[0] < L)
                            c["hr_line_toward"] = d if side == "over" else -d
                            if hml[0] == L:
                                f0 = fair_over(q)
                                if f0 is not None:
                                    c["hr_dp"] = (hml[1] - f0) if side == "over" else (f0 - hml[1])
                        pf = fair_over(bk(last, "pinnacle", m).get((pid, L)))
                        if pf is not None:
                            c["clv_pin"] = (pf if side == "over" else 1 - pf) * odds.decimal(price) - 1
                    res = grade(box, gid, pid, m, L, side)
                    out.append(dict(c, day=day, gid=gid, pid=pid, market=m, line=L, pin_line=Lp, diff=abs(Lp - L), side=side,
                                    price=price, lb=lb, read=f["read"], agree=agree, books=total, res=res,
                                    units=(odds.decimal(price) - 1) if res == "W" else (-1 if res == "L" else 0)))
    return out


def show(label, rs):
    g = [r for r in rs if r["res"] in "WL"]
    if not g:
        print("%-28s n    0" % label)
        return
    w = sum(r["res"] == "W" for r in g)
    u = sum(r["units"] for r in g)
    cp = [r["clv_pin"] for r in g if r["clv_pin"] is not None]
    lt = [r["hr_line_toward"] for r in g if r["hr_line_toward"] is not None]
    dp = [r["hr_dp"] for r in g if r["hr_dp"] is not None]
    nights = len({r["day"] for r in g})
    print("%-28s n %4d %3d-%-3d %+7.2fu ROI %+6.1f%% %4.1f/night | HR line our way %2d%% against %2d%% (n %d) | HR same-line chance %s | CLV Pin %s (n %d)" % (
        label, len(g), w, len(g) - w, u, 100 * u / len(g), len(g) / nights,
        100 * sum(x > 0 for x in lt) / len(lt) if lt else 0, 100 * sum(x < 0 for x in lt) / len(lt) if lt else 0, len(lt),
        "%+.2f pts" % (100 * statistics.mean(dp)) if dp else "-",
        "%+.2f%%" % (100 * statistics.mean(cp)) if cp else "-", len(cp)))


if __name__ == "__main__":
    rows = build()
    if "--json" in sys.argv:
        print(json.dumps(rows))
        sys.exit(0)
    live = [r for r in rows if r["read"] != "A"]
    print("nights:", len({r["day"] for r in rows}), "| line disagreements, live reads:", len(live), "| 11 AM:", len(rows) - len(live))
    show("ALL live reads", live)
    show("11 AM read", [r for r in rows if r["read"] == "A"])
    print("-- by lower-bound edge (live reads)")
    for lab, lo, hi in (("lb >= +3%", .03, 9), ("lb 0..+3%", 0, .03), ("lb -3..0%", -.03, 0), ("lb -6..-3%", -.06, -.03), ("lb < -6%", -9, -.06)):
        show(lab, [r for r in live if lo <= r["lb"] < hi])
    for cut in (0.0, -0.03):
        print("-- lb >= %+.0f%%" % (100 * cut))
        S = [r for r in live if r["lb"] >= cut]
        show("  all", S)
        for k in ("market", "side", "read"):
            for v in sorted({r[k] for r in S}):
                show("  %s=%s" % (k, v), [r for r in S if r[k] == v])
        show("  diff 1.0", [r for r in S if r["diff"] == 1.0])
        show("  diff 2.0+", [r for r in S if r["diff"] >= 2.0])
        show("  3+ other books agree", [r for r in S if r["agree"] >= 3])
        show("  0-2 other books agree", [r for r in S if r["agree"] < 3])
        show("  nights < 11-06", [r for r in S if r["day"] < "2026-11-06"])
        show("  nights >= 11-06", [r for r in S if r["day"] >= "2026-11-06"])
