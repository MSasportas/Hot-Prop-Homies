#!/usr/bin/env python3
"""Run 31 (NHL): PL1 points line majority (LL6 ported to points). Stored data only (data/odds + data/shadow). No API key.

Rule (registered in research/HYPOTHESES.md before this was run):
  reads B and C; Hard Rock markets.points and `others`.
  Main line per book = two-sided line (fresh < 60 min before the read, hold 0-15%) whose proportional no-vig over chance is
  closest to 0.5. Hard Rock's main line = the same rule on Hard Rock.
  Event: >= 3 other books with a main line for the player; strict majority ABOVE Hard Rock's line -> bet HR OVER;
  strict majority BELOW -> bet HR UNDER. HR price on that side -200..+120. First qualifying read per (date, game, player).
  Grade: data/shadow points result for that (date, game, player, HR line, side); void = no bet.
  CLV proxy: median no-vig over chance of the other books on the HR line at the last B/C read of that game that night, for the bet side,
  times frozen decimal price, minus 1.
Usage: python3 -I pl1_points_line_majority.py [repo_root]
"""
import glob
import json
import os
import random
import statistics
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
FWD_START = "2026-11-26"
MAXAGE = 60.0
READS = ("B", "C")
BOOT, PERM = 2000, 500
random.seed(31)


def iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def dec(a):
    return 1 + a / 100.0 if a > 0 else 1 + 100.0 / -a


def pairs(outs):
    d = {}
    for o in outs or []:
        try:
            k = (str(o["pid"]), float(o["line"]))
        except (KeyError, TypeError, ValueError):
            continue
        d.setdefault(k, {})[o.get("side")] = o
    return d


def fair_over(sd, at):
    """proportional no-vig over chance for a fresh two-sided line, or None."""
    if "over" not in sd or "under" not in sd:
        return None
    po, pu = sd["over"]["price"], sd["under"]["price"]
    ip = 1 / dec(po) + 1 / dec(pu)
    if not (1.0 <= ip <= 1.15):
        return None
    return (1 / dec(po)) / ip


def main_lines(fetch):
    """pid -> {book: (line, fair_over)} for other books; fresh only."""
    at = iso(fetch["at"])
    out = {}
    for book, bd in (fetch.get("others") or {}).items():
        pts = (bd or {}).get("points") or {}
        lu = pts.get("last_update")
        if not lu:
            continue
        age = (at - iso(lu)).total_seconds() / 60.0
        if age < 0 or age >= MAXAGE:
            continue
        best = {}
        for (pid, line), sd in pairs(pts.get("outcomes")).items():
            fo = fair_over(sd, at)
            if fo is None:
                continue
            d = abs(fo - 0.5)
            if pid not in best or d < best[pid][0]:
                best[pid] = (d, line, fo)
        for pid, (_, line, fo) in best.items():
            out.setdefault(pid, {})[book] = (line, fo)
    return out


def hr_main(fetch):
    at = iso(fetch["at"])
    hr = pairs((fetch.get("markets") or {}).get("points", {}).get("outcomes"))
    best = {}
    for (pid, line), sd in hr.items():
        fo = fair_over(sd, at)
        if fo is None:
            continue
        d = abs(fo - 0.5)
        if pid not in best or d < best[pid][0]:
            best[pid] = (d, line, sd)
    return {pid: (line, sd) for pid, (_, line, sd) in best.items()}


def load_shadow():
    res = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "shadow", "*.json"))):
        date = os.path.basename(f)[:10]
        d = json.load(open(f, encoding="utf-8"))
        for r in d.get("rows", []):
            if r.get("market") != "points" or not r.get("result"):
                continue
            res[(date, str(r["game_id"]), str(r["pid"]), float(r["line"]))] = r["result"]
    return res


def summarize(rows, label):
    g = [r for r in rows if r["res"] in ("W", "L")]
    if not g:
        return f"| {label} | {len(rows)} | 0 | - | - | - | - | - |"
    u = sum((dec(r["price"]) - 1) if r["res"] == "W" else -1.0 for r in g)
    w = sum(1 for r in g if r["res"] == "W")
    games = sorted({r["date"] + r["game"] for r in g})
    byg = {x: [] for x in games}
    for r in g:
        byg[r["date"] + r["game"]].append((dec(r["price"]) - 1) if r["res"] == "W" else -1.0)
    rng = random.Random(31)
    boots = []
    for _ in range(BOOT):
        pick = [rng.choice(games) for _ in games]
        tot = sum(sum(byg[x]) for x in pick)
        cnt = sum(len(byg[x]) for x in pick)
        boots.append(tot / cnt if cnt else 0.0)
    boots.sort()
    lo, hi = boots[int(0.05 * BOOT)], boots[int(0.95 * BOOT)]
    clv = [r["clv"] for r in g if r["clv"] is not None]
    clv_txt = f"{100 * statistics.mean(clv):+.2f}% (n{len(clv)})" if clv else "-"
    return (f"| {label} | {len(rows)} | {len(g)} | {w}-{len(g) - w} | {u:+.2f}u | {100 * u / len(g):+.1f}% | "
            f"{100 * lo:+.1f}..{100 * hi:+.1f}% | {clv_txt} |")


def main():
    shadow = load_shadow()
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "odds", "*.json"))):
        date = os.path.basename(f)[:10]
        d = json.load(open(f, encoding="utf-8"))
        fetches = sorted([x for x in d.get("fetches", []) if x.get("pull") in READS], key=lambda x: x["at"])
        last_fair = {}
        seen = set()
        for x in fetches:
            gid = str(x["game_id"])
            om = main_lines(x)
            hr = hr_main(x)
            for pid, (hl, _) in hr.items():
                pass
            for pid, (hl, sd) in hr.items():
                key = (gid, pid)
                books = om.get(pid, {})
                # consensus on the HR line for CLV proxy (other books quoting that same line)
                same = [fo for (ln, fo) in books.values() if ln == hl]
                if same:
                    last_fair[(gid, pid, hl)] = (statistics.median(same), date)
                if key in seen:
                    continue
                n = len(books)
                if n < 3:
                    continue
                above = sum(1 for (ln, _) in books.values() if ln > hl)
                below = sum(1 for (ln, _) in books.values() if ln < hl)
                if above > n / 2:
                    side = "over"
                elif below > n / 2:
                    side = "under"
                else:
                    continue
                o = sd[side]
                if not (-200 <= o["price"] <= 120):
                    continue
                seen.add(key)
                rows.append({"date": date, "game": gid, "pid": pid, "line": hl, "side": side,
                             "price": o["price"], "n_books": n, "above": above, "below": below,
                             "read": x["pull"], "res": None})
    # grade + CLV
    for r in rows:
        r["res"] = (shadow.get((r["date"], r["game"], r["pid"], r["line"])) or {}).get(r["side"])
        lf = last_fair.get((r["game"], r["pid"], r["line"]))
        r["clv"] = None
        if lf is not None:
            fo = lf[0]
            fs = fo if r["side"] == "over" else 1 - fo
            r["clv"] = fs * dec(r["price"]) - 1
    disc = [r for r in rows if r["date"] < FWD_START]
    fwd = [r for r in rows if r["date"] >= FWD_START]
    lines = ["| set | bets | graded | W-L | units | ROI | 90% CI (game-clustered) | CLV proxy |",
             "|---|---|---|---|---|---|---|---|"]
    lines.append(summarize(rows, "ALL"))
    lines.append(summarize(disc, "Discovery (< 2026-11-26, labelled check)"))
    lines.append(summarize(fwd, "Forward (>= 2026-11-26)"))
    for s in ("over", "under"):
        lines.append(summarize([r for r in disc if r["side"] == s], f"Discovery {s}"))
    by_night = {}
    for r in disc:
        if r["res"] in ("W", "L"):
            by_night.setdefault(r["date"], []).append(r)
    actual = sum((dec(r["price"]) - 1) if r["res"] == "W" else -1.0 for rs in by_night.values() for r in rs)
    ge = 0
    for _ in range(PERM):
        tot = 0.0
        for rs in by_night.values():
            res = [r["res"] for r in rs]
            random.shuffle(res)
            tot += sum((dec(r["price"]) - 1) if x == "W" else -1.0 for r, x in zip(rs, res))
        if tot >= actual:
            ge += 1
    lines.append(f"\nPlacebo (discovery, within-night shuffle, {PERM} draws): share of placebo units >= actual = {ge / PERM:.3f}")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(HERE, "pl1_results.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
