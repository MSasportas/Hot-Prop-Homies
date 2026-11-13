#!/usr/bin/env python3
"""Run 27 (NHL): DP1 book agreement (dispersion), shots. Stored data only (data/odds + data/shadow). No API key.

Rule (registered in research/HYPOTHESES.md before this was run):
  reads B and C; Hard Rock two-sided on a shots line at -200..+200; >= 5 other books two-sided on the same
  line, hold 0-15%, last_update < 60 min before the read. Proportional no-vig over chance per book;
  spread = max - min (pts); consensus = median.
  DP1a: side with HR EV >= 0 vs consensus AND spread <= 2 pts.  DP1b: same EV rule AND spread >= 4 pts.
  First qualifying read per (date, game, player, line). 1u at HR price, graded from data/shadow result (void if none).
  CLV = HR price vs consensus fair (that side) at the LAST B/C read of that line that night.
Usage: python3 -I disp.py [repo_root]
"""
import glob
import json
import os
import random
import statistics
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FWD_START = "2026-11-13"
MAXAGE = 60.0
BOOT = 2000
PERM = 1000


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


def consensus(fetch):
    """key (pid, line) -> (median over-chance of other books, spread pts, n books) for one read."""
    at = iso(fetch["at"])
    per = {}
    for book, bd in (fetch.get("others") or {}).items():
        sh = (bd or {}).get("shots") or {}
        lu = sh.get("last_update")
        if not lu:
            continue
        age = (at - iso(lu)).total_seconds() / 60.0
        if age < 0 or age >= MAXAGE:
            continue
        for k, sd in pairs(sh.get("outcomes")).items():
            if "over" not in sd or "under" not in sd:
                continue
            po, pu = sd["over"]["price"], sd["under"]["price"]
            ip = 1 / dec(po) + 1 / dec(pu)
            if not (1.0 <= ip <= 1.15):
                continue
            per.setdefault(k, []).append((1 / dec(po)) / ip)
    out = {}
    for k, fs in per.items():
        if len(fs) < 5:
            continue
        out[k] = (statistics.median(fs), (max(fs) - min(fs)) * 100, len(fs))
    return out


def load_shadow():
    res = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "shadow", "*.json"))):
        date = os.path.basename(f)[:10]
        d = json.load(open(f, encoding="utf-8"))
        for r in d.get("rows", []):
            if r.get("market") != "shots" or not r.get("result"):
                continue
            k = (date, str(r["game_id"]), str(r["pid"]), float(r["line"]))
            res[k] = r["result"]
    return res


def main():
    shadow = load_shadow()
    bets = {"DP1a": [], "DP1b": []}
    clv_last = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "odds", "*.json"))):
        date = os.path.basename(f)[:10]
        d = json.load(open(f, encoding="utf-8"))
        fetches = sorted([x for x in d.get("fetches", []) if x.get("pull") in ("B", "C")], key=lambda x: x["at"])
        taken = set()
        for x in fetches:
            gid = str(x["game_id"])
            hr = pairs((x.get("markets") or {}).get("shots", {}).get("outcomes"))
            cons = consensus(x)
            for k, val in cons.items():
                clv_last[(date, gid, k[0], k[1])] = val[0]  # later reads overwrite
            for k, (cmed, spread, nb) in cons.items():
                if k not in hr or "over" not in hr[k] or "under" not in hr[k]:
                    continue
                key = (date, gid, k[0], k[1])
                if key in taken:
                    continue
                tag = "DP1a" if spread <= 2 else ("DP1b" if spread >= 4 else None)
                if tag is None:
                    continue
                for side in ("over", "under"):
                    o = hr[k][side]
                    if not (-200 <= o["price"] <= 200):
                        continue
                    fair = cmed if side == "over" else 1 - cmed
                    if fair * dec(o["price"]) - 1 < 0:
                        continue
                    taken.add(key)
                    res = shadow.get((date, gid, k[0], k[1]), {}).get(side)
                    bets[tag].append({"date": date, "game": gid, "pid": k[0], "line": k[1], "side": side,
                                      "price": o["price"], "spread": round(spread, 2), "n_books": nb,
                                      "read": x["pull"], "at": x["at"], "res": res})
                    break
    results = {}
    for tag, rows in bets.items():
        graded = [r for r in rows if r["res"] in ("W", "L")]
        units = [(dec(r["price"]) - 1) if r["res"] == "W" else -1.0 for r in graded]
        n = len(graded)
        u = sum(units)
        clv = []
        for r in graded:
            last = clv_last.get((r["date"], r["game"], r["pid"], r["line"]))
            if last is not None:
                fair_last = last if r["side"] == "over" else 1 - last
                clv.append(fair_last * dec(r["price"]) - 1)
        games = sorted({r["date"] + r["game"] for r in graded})
        byg = {g: [] for g in games}
        for r, uu in zip(graded, units):
            byg[r["date"] + r["game"]].append(uu)
        rng = random.Random(27)
        boots = []
        for _ in range(BOOT if games else 0):
            pick = [rng.choice(games) for _ in games]
            tot = sum(sum(byg[g]) for g in pick)
            cnt = sum(len(byg[g]) for g in pick)
            boots.append(tot / cnt if cnt else 0.0)
        boots.sort()
        lo = boots[int(0.05 * len(boots))] if boots else 0.0
        hi = boots[int(0.95 * len(boots))] if boots else 0.0
        rng2 = random.Random(7)
        res_list = [r["res"] for r in graded]
        prices = [r["price"] for r in graded]
        ge = 0
        for _ in range(PERM if n else 0):
            rr = res_list[:]
            rng2.shuffle(rr)
            uu = sum((dec(p) - 1 if x == "W" else -1.0) for p, x in zip(prices, rr))
            if uu >= u:
                ge += 1
        pval = ge / PERM if n else 1.0
        fwd = [(r, uu) for r, uu in zip(graded, units) if r["date"] >= FWD_START]
        results[tag] = dict(bets=len(rows), graded=n, W=sum(1 for r in graded if r["res"] == "W"), units=u,
                            roi=(u / n * 100) if n else 0.0, ci=(lo * 100, hi * 100), p=pval,
                            clv=(100 * sum(clv) / len(clv)) if clv else None, n_clv=len(clv),
                            fwd_n=len(fwd), fwd_u=sum(uu for _, uu in fwd),
                            disc_n=n - len(fwd), disc_u=u - sum(uu for _, uu in fwd))
    lines = ["| variant | bets | graded | W | units | ROI | 90% CI (game-clustered) | p (shuffle) | mean CLV | n CLV | forward n / u | discovery n / u |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for tag, s in results.items():
        clv_txt = f"{s['clv']:+.2f}%" if s["clv"] is not None else "-"
        lines.append(f"| {tag} | {s['bets']} | {s['graded']} | {s['W']} | {s['units']:+.2f} | {s['roi']:+.1f}% | "
                     f"{s['ci'][0]:+.1f}..{s['ci'][1]:+.1f}% | {s['p']:.3f} | {clv_txt} | {s['n_clv']} | "
                     f"{s['fwd_n']} / {s['fwd_u']:+.2f} | {s['disc_n']} / {s['disc_u']:+.2f} |")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(HERE, "disp_results.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    with open(os.path.join(HERE, "disp_bets.json"), "w", encoding="utf-8") as fh:
        json.dump(bets, fh, indent=1, default=str)


if __name__ == "__main__":
    main()
