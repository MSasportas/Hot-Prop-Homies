"""Run 9 (2026-11-10): NHL's live Gap + Guard (v3.5, sports/nhl/config/rules.json ops.gap_guard) ported to NBA stored data.
Discovery only (every night already seen). Reads stored data only (no API calls).
Usage: python research/code/run9_nhl_port.py
NHL rule as ported (all thresholds inclusive, EV = fair x Hard Rock decimal - 1):
  sides checked: Hard Rock side with both sides quoted, price -200 or better, Pinnacle + >= 4 other books (Pinnacle counts) quoting
                 the same player/line both sides, each book hold 0-15%. market fair = median of proportionally de-vigged books.
  step 1 (gap):  gap EV vs market fair >= +3.0% AND Pinnacle-fair EV >= 0.
  step 2 (guard): final = 0.8 market fair + 0.2 model (offset 0: NBA model uncalibrated for offsets, like NHL points watch);
                 final EV >= +2.0% AND model chance >= Hard Rock break-even. Model = shadow log model_p (sports/nba/scripts/model.py).
  picks: only reads B (90 min) and C (45 min); first passing read freezes the price; 1 side per player per night (best final EV
         at that read). Looser bars (gap 2/1/0%) reported too. CLV = Pinnacle fair at the last read (D) x decimal(price) - 1."""
import json, sys, gzip, os, glob, collections, statistics
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) + os.sep
sys.path.insert(0, R + "scripts"); import odds
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
box = {}
for f in ("data/seed/players_2026-27.json.gz", "data/state/box/players_2026-27.json.gz"):
    if os.path.exists(R + f):
        for r in json.load(gzip.open(R + f, "rt")): box[(r["game"], r["pid"])] = r
STAT = {"rebounds": "reb", "points": "pts", "assists": "ast", "threes": "fg3m"}
MK = {"rebounds": "reb", "points": "pts", "assists": "ast", "threes": "3pm"}
def grade(gid, pid, m, line, side):
    b = box.get((gid, pid))
    if not b: return "?"
    if b["dnp"] or not b["min"]: return "V"
    x = b.get(STAT[m])
    if x is None: return "?"
    return "P" if x == line else ("W" if (x > line) == (side == "over") else "L")
def fo(q):
    if not q or not q["over"] or not q["under"]: return None
    return odds.fair_two_sided(q["over"], q["under"]) if 0 <= odds.hold(q["over"], q["under"]) <= .15 else None
def sp(f, side): return None if f is None else (f if side == "over" else 1 - f)
def bk(f, book, m): return odds.pairs((((f.get("others") or {}).get(book) or {}).get(m) or {}).get("outcomes"))
def hr(f, m): return odds.pairs((f["markets"].get(m) or {}).get("outcomes"))
def units(e): return odds.decimal(e["price"]) - 1 if e["res"] == "W" else (-1.0 if e["res"] == "L" else 0.0)

# model chance from the shadow log, keyed by read
model = {}
for p in glob.glob(R + "data/shadow/2*.json"):
    s = json.load(open(p, encoding="utf-8"))
    for rd in s.get("reads") or []:
        for r in rd.get("rows") or []:
            if r.get("model_p") is not None:
                model[(r["game_id"], r["read"], r["pid"], r["market"], r["line"], r["side"])] = r["model_p"]

days = {}
for p in sorted(glob.glob(R + "data/odds/2*.json")):
    d = json.load(open(p, encoding="utf-8")); byg = collections.defaultdict(list)
    for f in sorted(d["fetches"], key=lambda f: f["at"]): byg[f["game_id"]].append(f)
    days[d["date"]] = byg

sides = []   # every checked side at every read
for day, byg in days.items():
    for gid, fs in byg.items():
        last = fs[-1]
        for f in fs:
            if not f.get("others"): continue
            for m in f["markets"]:
                H = hr(f, m); books = {b: bk(f, b, m) for b in f["others"]}; LP = bk(last, "pinnacle", m)
                for k, h in H.items():
                    if not (h["over"] and h["under"]): continue
                    fairs = {b: fo(q.get(k)) for b, q in books.items()}; fairs = {b: x for b, x in fairs.items() if x is not None}
                    if "pinnacle" not in fairs or len(fairs) < 4: continue
                    mf = statistics.median(fairs.values()); pf = fairs["pinnacle"]
                    for side in ("over", "under"):
                        price = h[side]
                        if price < -200: continue
                        mp = model.get((gid, f["read"], k[0], m, k[1], side))
                        fair = sp(mf, side); gap = odds.ev(fair, price); be = odds.break_even(price)
                        e = dict(day=day, gid=gid, read=f["read"], pid=k[0], who=h["name"], m=m, line=k[1], side=side, price=price,
                                 gap=gap, pin_ev=odds.ev(sp(pf, side), price), model=mp, n=len(fairs), last=f is last,
                                 final_ev=None if mp is None else odds.ev(.8 * fair + .2 * mp, price),
                                 model_ok=None if mp is None else mp >= be)
                        lp = sp(fo(LP.get(k)), side); e["clv"] = None if lp is None or f is last else odds.ev(lp, price)
                        e["res"] = grade(gid, k[0], m, k[1], side); sides.append(e)

def picks(rule, reads=("B", "C")):
    """first passing read freezes; 1 side per player per night (best final EV / gap at that read)"""
    out, done = [], set()
    by = collections.defaultdict(list)
    for e in sides:
        if e["read"] in reads and rule(e): by[(e["day"], e["pid"])].append(e)
    for key, es in by.items():
        first = min(es, key=lambda e: e["read"]); same = [e for e in es if e["read"] == first["read"]]
        out.append(max(same, key=lambda e: (e["final_ev"] if e["final_ev"] is not None else e["gap"])))
    return out
def row(label, es):
    g = [e for e in es if e["res"] in ("W", "L")]; w = sum(e["res"] == "W" for e in g); u = sum(units(e) for e in g)
    c = [e.get("clv") for e in es if e.get("clv") is not None]
    print("  %-28s n %4d  %3d-%-3d %+7.2fu ROI %6s | CLV_pin %6s (n %d)" % (label, len(es), w, len(g) - w, u,
          ("%+.1f%%" % (100 * u / len(g))) if g else "-", ("%+.1f%%" % (100 * statistics.mean(c))) if c else "-", len(c)))
def split(title, es, fn):
    print(" " + title); gs = collections.defaultdict(list)
    for e in es: gs[fn(e)].append(e)
    for k in sorted(gs): row(str(k), gs[k])
era = lambda e: "early Oct25-Nov2" if e["day"] <= "2026-11-02" else "late Nov4-9"

print("== 1. sides checked (all reads; B/C are pickable)")
BC = [e for e in sides if e["read"] in ("B", "C")]
print(" all reads %d sides, B/C %d, with model %d" % (len(sides), len(BC), sum(e["model"] is not None for e in BC)))
bars = [(">=+3% & pin>=0 (NHL step1)", lambda e: e["gap"] >= .03 and e["pin_ev"] >= 0),
        (">=+2% & pin>=0", lambda e: e["gap"] >= .02 and e["pin_ev"] >= 0), (">=+1% & pin>=0", lambda e: e["gap"] >= .01 and e["pin_ev"] >= 0),
        (">=0% & pin>=0", lambda e: e["gap"] >= 0 and e["pin_ev"] >= 0), (">=0% gap only", lambda e: e["gap"] >= 0)]
print(" B/C sides clearing each bar (raw side-reads):")
for lab, fn in bars: print("   %-28s %d" % (lab, sum(fn(e) for e in BC)))
full = lambda e: e["gap"] >= .03 and e["pin_ev"] >= 0 and e["final_ev"] is not None and e["final_ev"] >= .02 and e["model_ok"]
print("   %-28s %d" % ("FULL NHL rule (gap+guard)", sum(full(e) for e in BC)))
for g in (.02, .01, 0):
    fn = lambda e, g=g: e["gap"] >= g and e["pin_ev"] >= 0 and e["final_ev"] is not None and e["final_ev"] >= .02 and e["model_ok"]
    print("   %-28s %d" % ("gap>=%d%%+guard" % (100 * g), sum(fn(e) for e in BC)))

print("\n== 2. picks (first passing B/C read, 1/player/night), graded at HR price")
P = {}
for lab, fn in bars + [("FULL NHL rule", full)] + [("gap>=%d%%+pin+guard" % (100 * g), (lambda e, g=g: e["gap"] >= g and e["pin_ev"] >= 0 and e["final_ev"] is not None and e["final_ev"] >= .02 and e["model_ok"])) for g in (.02, .01, 0)]:
    P[lab] = picks(fn); row(lab, P[lab])
for lab in (">=0% & pin>=0", ">=0% gap only"):
    es = P[lab]; print(" -- splits for", lab)
    split("by night", es, lambda e: e["day"]); split("by market", es, lambda e: MK[e["m"]]); split("by side", es, lambda e: e["side"])
    split("by read", es, lambda e: e["read"]); split("by era", es, era)

print("\n== 3. median HR gap vs market fair, by night (all checked sides, all reads) and best side")
for day in sorted({e["day"] for e in sides}):
    es = [e["gap"] for e in sides if e["day"] == day]
    print("  %s n %5d median %+.1f%%  p90 %+.1f%%  max %+.1f%%  share>=0 %.2f%%" % (day, len(es), 100 * statistics.median(es),
          100 * sorted(es)[int(.9 * len(es))], 100 * max(es), 100 * sum(x >= 0 for x in es) / len(es)))
for lab, fn in (("by era", era), ("by market", lambda e: MK[e["m"]]), ("by read", lambda e: e["read"]), ("by side", lambda e: e["side"])):
    gs = collections.defaultdict(list)
    for e in sides: gs[fn(e)].append(e["gap"])
    print(" " + lab + ": " + "; ".join("%s %+.1f%% (n %d, >=0: %d)" % (k, 100 * statistics.median(v), len(v), sum(x >= 0 for x in v)) for k, v in sorted(gs.items())))
gs = collections.defaultdict(list)
for e in sides: gs[(era(e), MK[e["m"]])].append(e["gap"])
print(" era x market: " + "; ".join("%s/%s %+.1f%%" % (k[0][:5], k[1], 100 * statistics.median(v)) for k, v in sorted(gs.items())))
# hold
hs = collections.defaultdict(list)
for e in sides:
    if e["side"] == "over": hs[e["day"]].append(None)
print("\n== 4. Pinnacle 2+ pt moves: share of the eventual move (to the last read) done at first sight")
mv = []
for day, byg in days.items():
    seen = set()
    for gid, fs in byg.items():
        last = fs[-1]
        for a, b in zip(fs, fs[1:]):
            for m in b["markets"]:
                ha, hb = hr(a, m), hr(b, m); pa, pb, pl = bk(a, "pinnacle", m), bk(b, "pinnacle", m), bk(last, "pinnacle", m)
                for k, h in hb.items():
                    if k not in ha or not (h["over"] and h["under"] and ha[k]["over"] and ha[k]["under"]): continue
                    fa, fb = fo(pa.get(k)), fo(pb.get(k))
                    if fa is None or fb is None or abs(fb - fa) < .02: continue
                    side = "over" if fb > fa else "under"; price = h[side]
                    if not (-200 <= price <= 200) or (k[0], m) in seen: continue
                    seen.add((k[0], m)); fl = fo(pl.get(k)) if b is not last else fb
                    jump = abs(fb - fa); tot = None if fl is None else (fl - fa) * (1 if side == "over" else -1)
                    mv.append(dict(day=day, gid=gid, m=m, side=side, price=price, jump=jump, tot=tot, at_last=b is last,
                                   res=grade(gid, k[0], m, k[1], side), ev_pin=odds.ev(sp(fb, side), price), fl=fl))
print(" moves %d (at last read, no later price: %d; Pinnacle line gone by last read: %d)" % (len(mv), sum(e["at_last"] for e in mv),
      sum(e["tot"] is None for e in mv)))
L = [e for e in mv if not e["at_last"] and e["tot"] is not None]
fr = [e["jump"] / e["tot"] for e in L if e["tot"] > 0]
print(" with a later read n %d: median share done at first sight %.0f%% (n %d with net move >0)" % (len(L), 100 * statistics.median(fr), len(fr)))
def drift(e):
    d = e["tot"] - e["jump"]
    return "c ran on >=1pt" if d >= .01 else ("a reversed >=1pt" if d <= -.01 else "b held (<1pt)")
for e in L: e["clv"] = odds.ev(sp(e["fl"], e["side"]), e["price"]) if e["fl"] is not None else None
split("drift after first sight (all moves)", L, drift)
split("drift, HR >= Pinnacle new fair only", [e for e in L if e["ev_pin"] >= 0], drift)
print(" mean drift after first sight %+.2f pts (n %d)" % (100 * statistics.mean(e["tot"] - e["jump"] for e in L), len(L)))

print("\n== 5. overlap with the Record (pin_solo picks)")
rec = {}
for l in open(R + "data/record/events.jsonl", encoding="utf-8"):
    e = json.loads(l)
    if e["t"] == "shown": p = e["pick"]; rec[e["id"]] = dict(day=e["slate"], gid=p["game_id"], pid=p["pid"], m=p["market"], line=p["line"], side=p["side"], read=p["read"], price=p["price"], res="?")
    elif e["t"] == "graded" and e["id"] in rec: rec[e["id"]]["res"] = e["result"]
rec = list(rec.values()); idx = {(e["day"], e["gid"], e["read"], e["pid"], e["m"], e["line"], e["side"]): e for e in sides}
anyr = collections.defaultdict(list)
for e in sides: anyr[(e["day"], e["pid"], e["m"], e["line"], e["side"])].append(e)
row("Record all", rec)
gaps = [idx[k]["gap"] for k in ((r["day"], r["gid"], r["read"], r["pid"], r["m"], r["line"], r["side"]) for r in rec) if k in idx]
print(" Record picks found in checked sides at their read: %d of %d; median gap %+.1f%%, max %+.1f%%, >=3%%: %d, >=0%%: %d" % (
    len(gaps), len(rec), 100 * statistics.median(gaps), 100 * max(gaps), sum(g >= .03 for g in gaps), sum(g >= 0 for g in gaps)))
for lab in ("FULL NHL rule", ">=+1% & pin>=0", ">=0% & pin>=0", ">=0% gap only", "gap>=0%+pin+guard"):
    ks = {(e["day"], e["pid"], e["m"], e["line"], e["side"]) for e in P[lab]}
    ov = [r for r in rec if (r["day"], r["pid"], r["m"], r["line"], r["side"]) in ks]
    print(" %-22s picks %d, same bet as a Record pick: %d" % (lab, len(P[lab]), len(ov)))


big = sorted(sides, key=lambda e: -e['gap'])[:6]
for e in big: print(' top gap', e['day'], e['read'], e['who'], e['m'], e['line'], e['side'], e['price'], '%+.1f%%' % (100*e['gap']), 'pin %+.1f%%' % (100*e['pin_ev']), 'n', e['n'], e['res'])

