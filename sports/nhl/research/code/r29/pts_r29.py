"""Run 29 (NHL): points market, price timing (R29a) and low-hold favorites (R29b).
Stored data only: sports/nhl/data/shadow/*.json (points rows with open/close and graded result).
Usage: python pts_r29.py  (prints results; redirect to scratchpad, not the repo)."""
import json, glob, random, collections, os

ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'shadow')
ROOT = os.path.normpath(ROOT)
BAND = (-200, 120)

def dec(p):
    return 1 + p / 100.0 if p > 0 else 1 + 100.0 / (-p)

def in_band(p):
    return p is not None and BAND[0] <= p <= BAND[1]

def units(res, price):
    if res == 'W':
        return dec(price) - 1
    if res == 'L':
        return -1.0
    return None  # VOID / push

def load():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, '*.json'))):
        date = os.path.basename(f)[:-5]
        d = json.load(open(f, encoding='utf-8'))
        for r in d.get('rows', []):
            if r.get('market') != 'points' or not r.get('result'):
                continue
            r['_date'] = date
            out.append(r)
    return out

def side_res(r, side):
    return r['result'].get(side)

def cluster_ci(items, n_boot=4000, seed=7):
    # items: list of (game_id, units). 90% clustered bootstrap on ROI (units / n).
    games = collections.defaultdict(list)
    for g, u in items:
        games[g].append(u)
    keys = list(games)
    if not keys:
        return (None, None)
    rnd = random.Random(seed)
    rois = []
    for _ in range(n_boot):
        tot, n = 0.0, 0
        for _ in keys:
            g = rnd.choice(keys)
            tot += sum(games[g]); n += len(games[g])
        rois.append(tot / n if n else 0)
    rois.sort()
    return (rois[int(0.05 * n_boot)], rois[int(0.95 * n_boot)])

def summarize(name, bets):
    # bets: list of dict(game, date, u, clv, res)
    g = [b for b in bets if b['u'] is not None]
    n = len(g)
    if n == 0:
        print(f"{name}: n 0"); return
    w = sum(1 for b in g if b['res'] == 'W')
    tot = sum(b['u'] for b in g)
    clv = sum(b['clv'] for b in g) / n
    lo, hi = cluster_ci([(b['game'], b['u']) for b in g])
    print(f"{name}: n {n} W-L {w}-{n-w} units {tot:+.2f} ROI {tot/n*100:+.1f}% 90%CI [{lo*100:+.1f},{hi*100:+.1f}] CLV {clv*100:+.2f}pt")

def placebo(bets, draws=500, seed=11):
    # shuffle results within night among bets (keeps prices, breaks price-result pairing)
    rnd = random.Random(seed)
    g = [b for b in bets if b['u'] is not None]
    by_night = collections.defaultdict(list)
    for b in g:
        by_night[b['date']].append(b)
    actual = sum(b['u'] for b in g)
    rois = []
    for _ in range(draws):
        tot = 0.0
        for night, bs in by_night.items():
            res = [b['res'] for b in bs]
            rnd.shuffle(res)
            for b, rr in zip(bs, res):
                tot += (dec(b['price']) - 1) if rr == 'W' else -1.0
        rois.append(tot)
    share = sum(1 for x in rois if x >= actual) / draws
    print(f"  placebo share >= actual units: {share:.3f}")

def main():
    rows = load()
    print('graded points rows:', len(rows))
    # R29a: same side, same row, open-read price vs close-read price
    a_bets, c_bets = [], []
    for r in rows:
        o, c = r.get('open') or {}, r.get('close') or {}
        if not o or not c or o.get('over') is None or c.get('over') is None:
            continue
        fo = o.get('fair_over'); fc = c.get('fair_over')
        if fo is None or fc is None:
            continue
        ev_o = {'over': fo * dec(o['over']) - 1, 'under': (1 - fo) * dec(o['under']) - 1}
        # the side the open read says is +EV (highest EV, must be >= 0)
        side = max(ev_o, key=ev_o.get)
        if ev_o[side] < 0:
            continue
        po = o[side]; pc = c[side]
        if not (in_band(po) and in_band(pc)):
            continue
        res = side_res(r, side)
        fair_close_side = fc if side == 'over' else 1 - fc
        common = dict(game=r['game_id'], date=r['_date'], res=res, price=None)
        a_bets.append(dict(common, price=po, u=units(res, po), clv=fair_close_side - 1 / dec(po)))
        c_bets.append(dict(common, price=pc, u=units(res, pc), clv=fair_close_side - 1 / dec(pc)))
    print('R29a pairs (open +EV side, both prices in band):', len(a_bets))
    summarize('R29a AT OPEN price', a_bets)
    summarize('R29a AT CLOSE price', c_bets)
    placebo(a_bets); placebo(c_bets)
    # paired difference
    diffs = [a['u'] - c['u'] for a, c in zip(a_bets, c_bets) if a['u'] is not None and c['u'] is not None]
    if diffs:
        print(f"  R29a paired units diff (open - close) per bet: {sum(diffs)/len(diffs):+.4f} over {len(diffs)} bets; open price better on {sum(1 for x in diffs if x>0)}")
    # R29b: close hold <= 0.06, favorite side at close price
    b_bets = []
    for r in rows:
        c = r.get('close') or {}
        if not c or c.get('over') is None or c.get('hold') is None or c.get('fair_over') is None:
            continue
        if c['hold'] > 0.06:
            continue
        fc = c['fair_over']
        side = 'over' if fc > 0.5 else 'under'
        p = c[side]
        if not in_band(p):
            continue
        res = side_res(r, side)
        fair_side = fc if side == 'over' else 1 - fc
        b_bets.append(dict(game=r['game_id'], date=r['_date'], res=res, price=p,
                           u=units(res, p), clv=fair_side - 1 / dec(p)))
    print('R29b favorite sides, close hold <= 0.06:', len(b_bets))
    summarize('R29b low-hold favorite', b_bets)
    placebo(b_bets)
    # mirror (context only): hold >= 0.09
    m_bets = []
    for r in rows:
        c = r.get('close') or {}
        if not c or c.get('over') is None or c.get('hold') is None or c.get('fair_over') is None or c['hold'] < 0.09:
            continue
        fc = c['fair_over']; side = 'over' if fc > 0.5 else 'under'; p = c[side]
        if not in_band(p):
            continue
        res = side_res(r, side); fair_side = fc if side == 'over' else 1 - fc
        m_bets.append(dict(game=r['game_id'], date=r['_date'], res=res, price=p, u=units(res, p), clv=fair_side - 1 / dec(p)))
    summarize('mirror high-hold favorite (context only)', m_bets)

if __name__ == '__main__':
    main()
