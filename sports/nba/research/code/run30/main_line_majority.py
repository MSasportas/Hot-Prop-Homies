#!/usr/bin/env python3
"""Run 30 (NBA): R30a main-line majority. Stored data only (data/odds + data/state/box). No API calls.

Rule (registered in research/HYPOTHESES.md before this was run):
  reads B and C; markets points, rebounds, assists, threes.
  Main line per book = two-sided line (fresh < 60 min, hold 0-15%) whose proportional no-vig over chance is closest to 0.5.
  Event: >= 4 other books with a main line; strict majority ABOVE Hard Rock's main line -> bet HR OVER;
  strict majority BELOW -> bet HR UNDER. HR price on that side -200..+200. First qualifying read per (night, game, player, market).
  Grade: box scores via auto_hypothesis._grade (DNP = void, exact = push). CLV_pin = Pinnacle no-vig chance for the side on the
  same HR line at the last read of that game that night, times frozen decimal price, minus 1.
Usage: python3 -I main_line_majority.py <repo_root>
"""
import collections
import glob
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import auto_hypothesis as ah  # noqa: E402  helpers: _fo, _bk, _hr, _load_box, _grade
odds = ah.odds

FWD_START = "2026-11-26"
MARKETS = ("points", "rebounds", "assists", "threes")
READS = ("B", "C")
BOOT, PERM = 2000, 500


def dec(p):
    return odds.decimal(p)


def main_lines(fetch, m):
    """pid -> {book: line} main line per other book (fair over closest to 0.5, fresh two-sided)."""
    out = collections.defaultdict(dict)
    for book in (fetch.get("others") or {}):
        pr = ah._bk(fetch, book, m)
        best = {}
        for (pid, line), q in pr.items():
            fo = ah._fo(q)
            if fo is None:
                continue
            d = abs(fo - 0.5)
            if pid not in best or d < best[pid][0]:
                best[pid] = (d, line)
        for pid, (_, line) in best.items():
            out[pid][book] = line
    return out


def hr_main(fetch, m):
    pr = ah._hr(fetch, m)
    best = {}
    for (pid, line), q in pr.items():
        if not (q.get("over") and q.get("under")):
            continue
        fo = ah._fo(q)
        if fo is None:
            continue
        d = abs(fo - 0.5)
        if pid not in best or d < best[pid][0]:
            best[pid] = (d, line, q)
    return {pid: (line, q) for pid, (_, line, q) in best.items()}


def collect(box):
    rows = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "odds", "2*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        day = d["date"]
        seen = set()
        fetches = sorted([f for f in d.get("fetches", []) if f.get("read") in READS], key=lambda f: f["at"])
        last_by_game = {}
        for f in fetches:
            last_by_game[f["game_id"]] = f
        for f in fetches:
            gid = f["game_id"]
            for m in MARKETS:
                if not (f.get("markets") or {}).get(m):
                    continue
                hr = hr_main(f, m)
                if not hr:
                    continue
                om = main_lines(f, m)
                for pid, (hl, hq) in hr.items():
                    key = (gid, pid, m)
                    if key in seen:
                        continue
                    books = om.get(pid, {})
                    n = len(books)
                    if n < 4:
                        continue
                    above = sum(1 for v in books.values() if v > hl)
                    below = sum(1 for v in books.values() if v < hl)
                    if above > n / 2:
                        side = "over"
                    elif below > n / 2:
                        side = "under"
                    else:
                        continue
                    price = hq[side]
                    if not (-200 <= price <= 200):
                        continue
                    seen.add(key)
                    res = ah._grade(box, gid, pid, m, hl, side)
                    clv = None
                    lf = last_by_game.get(gid)
                    if lf is not None:
                        pq = ah._bk(lf, "pinnacle", m).get((pid, hl))
                        fp = ah._fo(pq) if pq else None
                        if fp is not None:
                            clv = (fp if side == "over" else 1 - fp) * dec(price) - 1
                    rows.append(dict(day=day, gid=gid, pid=pid, m=m, line=hl, side=side, price=price,
                                     n_books=n, above=above, below=below, read=f["read"], res=res, clv=clv))
    return rows


def summ(rs, label):
    g = [r for r in rs if r["res"] in ("W", "L")]
    if not g:
        return f"| {label} | {len(rs)} | 0 | - | - | - | - | - |"
    u = sum((dec(r["price"]) - 1) if r["res"] == "W" else -1.0 for r in g)
    w = sum(1 for r in g if r["res"] == "W")
    games = sorted({r["day"] + r["gid"] for r in g})
    byg = collections.defaultdict(list)
    for r in g:
        byg[r["day"] + r["gid"]].append((dec(r["price"]) - 1) if r["res"] == "W" else -1.0)
    rng = random.Random(30)
    boots = []
    for _ in range(BOOT):
        pick = [rng.choice(games) for _ in games]
        tot = sum(sum(byg[x]) for x in pick)
        cnt = sum(len(byg[x]) for x in pick)
        boots.append(tot / cnt if cnt else 0.0)
    boots.sort()
    lo, hi = boots[int(0.05 * BOOT)], boots[int(0.95 * BOOT)]
    clvs = [r["clv"] for r in g if r["clv"] is not None]
    clv_txt = f"{100 * statistics.mean(clvs):+.2f}% (n{len(clvs)})" if clvs else "-"
    return (f"| {label} | {len(rs)} | {len(g)} | {w}-{len(g) - w} | {u:+.2f}u | {100 * u / len(g):+.1f}% | "
            f"{100 * lo:+.1f}..{100 * hi:+.1f}% | {clv_txt} |")


def main():
    box = ah._load_box()
    rows = collect(box)
    disc = [r for r in rows if r["day"] < FWD_START]
    lines = ["| set | bets | graded | W-L | units | ROI | 90% CI (game-clustered) | CLV_pin |",
             "|---|---|---|---|---|---|---|---|"]
    lines.append(summ(rows, "ALL"))
    lines.append(summ(disc, "Discovery (< 2026-11-26)"))
    lines.append(summ([r for r in rows if r["day"] >= FWD_START], "Forward (>= 2026-11-26)"))
    for m in MARKETS:
        lines.append(summ([r for r in disc if r["m"] == m], f"Discovery {m}"))
    for s in ("over", "under"):
        lines.append(summ([r for r in disc if r["side"] == s], f"Discovery {s}"))
    for nb in (4, 5):
        lines.append(summ([r for r in disc if (r["above"] if r["side"] == "over" else r["below"]) >= nb and r["n_books"] >= nb],
                          f"Discovery majority count >= {nb}"))
    by_night = collections.defaultdict(list)
    for r in disc:
        if r["res"] in ("W", "L"):
            by_night[r["day"]].append(r)
    actual = sum((dec(r["price"]) - 1) if r["res"] == "W" else -1.0
                 for rs in by_night.values() for r in rs)
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
    with open(os.path.join(HERE, "main_line_majority_results.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    with open(os.path.join(HERE, "main_line_majority_rows.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, default=str)


if __name__ == "__main__":
    main()
