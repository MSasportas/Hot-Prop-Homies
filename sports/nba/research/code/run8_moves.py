"""Run 8 (2026-11-09): NBA line-move / book-move tests M1-M7. Reads stored data only (no API calls).
Usage: python research/code/run8_moves.py [first_forward_night]   (default 2026-11-10; nights before = discovery)"""
import json, sys, gzip, os, glob, collections, statistics, random
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) + os.sep
sys.path.insert(0, R + "scripts"); import odds
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
FWD = sys.argv[1] if len(sys.argv) > 1 else "2026-11-10"
box = {}
for f in ("data/seed/players_2026-27.json.gz", "data/state/box/players_2026-27.json.gz"):
    if os.path.exists(R + f):
        for r in json.load(gzip.open(R + f, "rt")): box[(r["game"], r["pid"])] = r
STAT = {"rebounds": "reb", "points": "pts", "assists": "ast", "threes": "fg3m"}
def grade(gid, pid, m, line, side):
    b = box.get((gid, pid))
    if not b: return "?"
    if b["dnp"] or not b["min"]: return "V"
    x = b.get(STAT[m])
    if x is None: return "?"
    return "P" if x == line else ("W" if (x > line) == (side == "over") else "L")
def fo(q):  # de-vigged over chance of a two-sided quote
    if not q or not q["over"] or not q["under"]: return None
    return odds.fair_two_sided(q["over"], q["under"]) if 0 <= odds.hold(q["over"], q["under"]) <= .15 else None
def side_p(f, side): return None if f is None else (f if side == "over" else 1 - f)
def bk(f, book, m): return odds.pairs((((f.get("others") or {}).get(book) or {}).get(m) or {}).get("outcomes"))
def hr(f, m): return odds.pairs((f["markets"].get(m) or {}).get("outcomes"))
WIN = {("A", "B"): "11AM->90", ("B", "C"): "90->45", ("C", "D"): "45->20"}

days = {}
for p in sorted(glob.glob(R + "data/odds/2*.json")):
    d = json.load(open(p, encoding="utf-8")); byg = collections.defaultdict(list)
    for f in sorted(d["fetches"], key=lambda f: f["at"]): byg[f["game_id"]].append(f)
    days[d["date"]] = byg

def later(day, gid, at, pid, m, line, side):
    """next read and last (D) read after `at`: Pinnacle chance for the side, Hard Rock price for the side"""
    fs = [f for f in days.get(day, {}).get(gid, []) if f["at"] > at]
    out = {}
    for tag, f in (("next", fs[0] if fs else None), ("close", fs[-1] if fs else None)):
        if not f: continue
        out[tag + "_pin"] = side_p(fo(bk(f, "pinnacle", m).get((pid, line))), side)
        h = hr(f, m).get((pid, line)); out[tag + "_hr"] = h[side] if h else None
    return out

moves, m2b = [], []
for day, byg in days.items():
    seen, seen2 = set(), set()
    for gid, fs in byg.items():
        for a, b in zip(fs, fs[1:]):
            for m in b["markets"]:
                ha, hb = hr(a, m), hr(b, m); pa, pb = bk(a, "pinnacle", m), bk(b, "pinnacle", m)
                oth = [x for x in (b.get("others") or {}) if x != "pinnacle"]
                oa = {x: bk(a, x, m) for x in oth}; ob = {x: bk(b, x, m) for x in oth}
                for k, h in hb.items():
                    if k not in ha or not (h["over"] and h["under"] and ha[k]["over"] and ha[k]["under"]): continue
                    mv = [y - x for x, y in ((fo(oa[o].get(k)), fo(ob[o].get(k))) for o in oth) if x is not None and y is not None]
                    fa, fb = fo(pa.get(k)), fo(pb.get(k))
                    base = dict(day=day, gid=gid, pid=k[0], who=h["name"], m=m, line=k[1], at=b["at"], win=WIN.get((a["read"], b["read"]), a["read"] + b["read"]))
                    if fa is not None and fb is not None and abs(fb - fa) >= 0.02:
                        side = "over" if fb > fa else "under"; price = h[side]; key = (k[0], m)
                        if -200 <= price <= 200 and key not in seen:
                            seen.add(key); sm = [x if side == "over" else -x for x in mv]
                            d0, d1 = odds.decimal(ha[k][side]), odds.decimal(price)
                            e = dict(base, side=side, price=price, size=abs(fb - fa), others=statistics.median(sm) if sm else None,
                                     n_follow=sum(x >= .01 for x in sm), n_oth=len(sm),
                                     hr="stale" if d1 == d0 else ("followed" if d1 < d0 else "against"),
                                     ev_pin=odds.ev(side_p(fb, side), price), res=grade(gid, k[0], m, k[1], side))
                            e.update(later(day, gid, b["at"], k[0], m, k[1], side)); e["pin_at"] = side_p(fb, side); moves.append(e)
                    if len(mv) >= 4 and abs(statistics.median(mv)) >= 0.02:
                        side = "over" if statistics.median(mv) > 0 else "under"; price = h[side]; key = (k[0], m)
                        if -200 <= price <= 200 and key not in seen2 and price == ha[k][side]:
                            seen2.add(key); e = dict(base, side=side, price=price, res=grade(gid, k[0], m, k[1], side), pin_at=side_p(fb, side))
                            e.update(later(day, gid, b["at"], k[0], m, k[1], side)); m2b.append(e)

rec = {}
for l in open(R + "data/record/events.jsonl", encoding="utf-8"):
    e = json.loads(l)
    if e["t"] == "shown":
        p = e["pick"]; rec[e["id"]] = dict(day=e["slate"], gid=p["game_id"], pid=p["pid"], who=p["player"], m=p["market"], line=p["line"], side=p["side"],
            price=p["price"], at=p.get("price_at", e["at"]), size=p["pin_after"] - p["pin_before"], others=p.get("others_move"), pin_at=p["pin_after"],
            win={"B": "11AM->90", "C": "90->45", "D": "45->20"}.get(p["read"]), res="?", pulled=False)
    elif e["t"] == "graded" and e["id"] in rec: rec[e["id"]]["res"] = e["result"]
    elif e["t"] == "pulled" and e["id"] in rec: rec[e["id"]]["pulled"] = True
rec = list(rec.values())
for r in rec:
    fs = [f for f in days.get(r["day"], {}).get(r["gid"], []) if f["at"] <= r["at"]]
    r.update(later(r["day"], r["gid"], fs[-1]["at"] if fs else r["at"], r["pid"], r["m"], r["line"], r["side"]))

def units(e): return odds.decimal(e["price"]) - 1 if e["res"] == "W" else (-1.0 if e["res"] == "L" else 0.0)
def clv_pin(e): return None if e.get("close_pin") is None else e["close_pin"] * odds.decimal(e["price"]) - 1
def clv_hr(e): return None if e.get("close_hr") is None else odds.decimal(e["price"]) / odds.decimal(e["close_hr"]) - 1
def line(label, es):
    g = [e for e in es if e["res"] in ("W", "L")]; w = sum(e["res"] == "W" for e in g); u = sum(units(e) for e in g)
    c = [x for x in map(clv_pin, es) if x is not None]; ci = ""
    if len(g) >= 20:
        random.seed(8); cl = collections.defaultdict(list)
        for e in g: cl[e["gid"]].append(units(e))
        ks = list(cl); bs = []
        for _ in range(2000):
            s = [x for k in random.choices(ks, k=len(ks)) for x in cl[k]]; bs.append(sum(s) / len(s))
        bs.sort(); ci = " 90%% CI %+.0f..%+.0f%%" % (100 * bs[100], 100 * bs[1899])
    print("  %-34s n %3d graded %3d  %3d-%-3d %+7.2fu ROI %s%s | CLV_pin %s (n %d)" % (label, len(es), len(g), w, len(g) - w, u,
          ("%+.1f%%" % (100 * u / len(g))) if g else "-", ci, ("%+.1f%%" % (100 * statistics.mean(c))) if c else "-", len(c)))
def split(title, es, fn, order=None):
    print(" " + title); gs = collections.defaultdict(list)
    for e in es:
        k = fn(e)
        if k is not None: gs[k].append(e)
    for k in (order or sorted(gs)):
        if k in gs: line(str(k), gs[k])
def band(e): return "2-3 pts" if e["size"] < .03 else ("3-4 pts" if e["size"] < .04 else "4+ pts")
def rev(e):
    if e.get("next_pin") is None: return None
    d = e["next_pin"] - e["pin_at"]; return "reversed >=1pt" if d <= -.01 else ("ran on >=1pt" if d >= .01 else "held (<1pt)")
def hrclose(e):
    if "close_hr" not in e: return None
    if e["close_hr"] is None: return "HR line gone/moved at D"
    return "HR closed shorter" if clv_hr(e) > 0 else ("HR same" if clv_hr(e) == 0 else "HR closed longer")
def pct(xs, f="%+.2f%%", fn=statistics.mean): return f % (100 * fn(xs)) if xs else "-"

for name, sel in (("DISCOVERY (nights < %s)" % FWD, lambda e: e["day"] < FWD), ("FORWARD (nights >= %s)" % FWD, lambda e: e["day"] >= FWD)):
    M = [e for e in moves if sel(e)]; F = [e for e in M if e["ev_pin"] >= 0]; RC = [e for e in rec if sel(e)]; B = [e for e in m2b if sel(e)]
    print("\n===== %s: nights %d, MOVES %d, FAIR subset %d, Record picks %d" % (name, len({e["day"] for e in M}), len(M), len(F), len(RC)))
    if not (M or RC): continue
    line("all MOVES", M); line("FAIR (HR >= Pinnacle new fair)", F); line("Record (live picks)", RC)
    print("M1 closing-line value (close = D read)")
    for lab, es in (("Record", RC), ("FAIR", F), ("MOVES", M)):
        cp = [x for x in map(clv_pin, es) if x is not None]; ch = [x for x in map(clv_hr, es) if x is not None]
        print("  %-7s picks %d, no later read %d | CLV_pin n %d mean %s median %s share>0 %s | CLV_hr n %d mean %s share>0 %s (HR line gone or moved at D: %d)" % (
            lab, len(es), sum("close_hr" not in e for e in es), len(cp), pct(cp), pct(cp, fn=statistics.median),
            ("%.0f%%" % (100 * sum(x > 0 for x in cp) / len(cp))) if cp else "-", len(ch), pct(ch),
            ("%.0f%%" % (100 * sum(x > 0 for x in ch) / len(ch))) if ch else "-", sum("close_hr" in e and e["close_hr"] is None for e in es)))
        split("%s by CLV_pin sign" % lab, es, lambda e: None if clv_pin(e) is None else ("CLV_pin > 0" if clv_pin(e) > 0 else "CLV_pin <= 0"))
        split("%s by Hard Rock close" % lab, es, hrclose)
    print("M2 Hard Rock lag"); split("MOVES by what HR's price did", M, lambda e: e["hr"]); split("FAIR by what HR's price did", F, lambda e: e["hr"])
    line("M2b others move >=2, HR unchanged", B)
    print("M3 consensus vs Pinnacle-only"); so = lambda e: None if e.get("others") is None else ("solo (others <1pt)" if e["others"] < .01 else "consensus (others >=1pt)")
    split("MOVES", M, so); split("FAIR", F, so); split("Record", RC, so)
    split("MOVES by books following >=1pt", M, lambda e: "0-1 books" if e["n_follow"] <= 1 else ("2-4 books" if e["n_follow"] <= 4 else "5+ books"))
    print("M4 move size"); split("MOVES", M, band); split("FAIR", F, band); split("Record", RC, band)
    print("M5 timing"); O = ["11AM->90", "90->45", "45->20"]; split("MOVES", M, lambda e: e["win"], O); split("FAIR", F, lambda e: e["win"], O); split("Record", RC, lambda e: e["win"], O)
    split("MOVES morning vs last 90", M, lambda e: "morning" if e["win"] == "11AM->90" else "last 90 min")
    print("M6 reverse move at the next read"); split("MOVES", M, rev); split("FAIR", F, rev); split("Record", RC, rev); split("Record pulled?", RC, lambda e: "pulled" if e["pulled"] else "not pulled")
    print("M7 side"); split("MOVES", M, lambda e: e["side"]); split("FAIR", F, lambda e: e["side"]); split("Record", RC, lambda e: e["side"])
    split("MOVES by market", M, lambda e: e["m"]); split("Record by market", RC, lambda e: e["m"])
