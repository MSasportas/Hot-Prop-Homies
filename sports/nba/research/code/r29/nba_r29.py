"""Run 29 (NBA): R29a read timing (A price vs C price, paired) and R29b low-hold favorites at read C.
Stored data only: sports/nba/data/shadow/<date>.json (reads[].rows) and sports/nba/data/state/box/players_2026-27.json.gz (grading).
Usage: python nba_r29.py"""
import json, glob, gzip, os, random, collections

HERE = os.path.dirname(__file__)
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', '..'))
SHADOW = os.path.join(REPO, 'sports', 'nba', 'data', 'shadow')
BOX = os.path.join(REPO, 'sports', 'nba', 'data', 'state', 'box', 'players_2026-27.json.gz')
MKT = {'points': 'pts', 'rebounds': 'reb', 'assists': 'ast', 'threes': 'fg3m'}
BAND = (-200, 200)

def dec(p):
    return 1 + p / 100.0 if p > 0 else 1 + 100.0 / (-p)

def in_band(p):
    return p is not None and BAND[0] <= p <= BAND[1]

def load_box():
    box = {}
    for r in json.load(gzip.open(BOX)):
        box[(str(r['pid']), str(r['game']))] = r
    return box

def grade(row, box):
    b = box.get((str(row['pid']), str(row['game_id'])))
    if b is None or b.get('dnp') or b.get(MKT[row['market']]) is None:
        return None  # void
    stat = float(b[MKT[row['market']]])
    line = float(row['line'])
    if stat == line:
        return 'P'
    if row['side'] == 'over':
        return 'W' if stat > line else 'L'
    return 'W' if stat < line else 'L'

def units(res, price):
    if res == 'W':
        return dec(price) - 1
    if res == 'L':
        return -1.0
    return 0.0  # push

def cluster_ci(items, n_boot=4000, seed=7):
    games = collections.defaultdict(list)
    for g, u in items:
        games[g].append(u)
    keys = list(games)
    if not keys:
        return (0, 0)
    rnd = random.Random(seed)
    rois = []
    for _ in range(n_boot):
        tot = n = 0
        for _k in keys:
            g = rnd.choice(keys)
            tot += sum(games[g]); n += len(games[g])
        rois.append(tot / n if n else 0)
    rois.sort()
    return rois[int(0.05 * n_boot)], rois[int(0.95 * n_boot)]

def summarize(name, bets):
    g = [b for b in bets if b['res'] in ('W', 'L', 'P')]
    n = len([b for b in g if b['res'] != 'P'])
    if n == 0:
        print(f"{name}: n 0"); return
    w = sum(1 for b in g if b['res'] == 'W'); l = sum(1 for b in g if b['res'] == 'L')
    tot = sum(b['u'] for b in g)
    lo, hi = cluster_ci([(b['game'], b['u']) for b in g if b['res'] != 'P'])
    clv = sum(b['clv'] for b in g) / len(g)
    print(f"{name}: n {n} W-L {w}-{l} units {tot:+.2f} ROI {tot/n*100:+.1f}% 90%CI [{lo*100:+.1f},{hi*100:+.1f}] CLV {clv*100:+.2f}pt")

def placebo(bets, draws=500, seed=11):
    rnd = random.Random(seed)
    g = [b for b in bets if b['res'] in ('W', 'L')]
    by_night = collections.defaultdict(list)
    for b in g:
        by_night[b['date']].append(b)
    actual = sum(b['u'] for b in g)
    ge = 0
    for _ in range(draws):
        tot = 0.0
        for night, bs in by_night.items():
            res = [b['res'] for b in bs]; rnd.shuffle(res)
            for b, rr in zip(bs, res):
                tot += (dec(b['price']) - 1) if rr == 'W' else -1.0
        if tot >= actual:
            ge += 1
    print(f"  placebo share >= actual units: {ge/draws:.3f}")

def main():
    box = load_box()
    letters = collections.Counter()
    A, C = [], []
    for f in sorted(glob.glob(os.path.join(SHADOW, '*.json'))):
        date = os.path.basename(f)[:-5]
        d = json.load(open(f, encoding='utf-8'))
        seen_a, seen_c = {}, set()
        for rd in d.get('reads', []):
            letter = rd.get('read')
            letters[letter] += 1
            for r in rd.get('rows', []):
                if r.get('market') not in MKT:
                    continue
                key = (r['pid'], r['market'], r['line'], r['side'])
                rec = dict(r, _date=date, _key=key)
                if letter == 'A' and key not in seen_a:
                    seen_a[key] = rec
                if letter == 'C' and key not in seen_c:
                    seen_c.add(key)
                    C.append(rec)
        A.extend(seen_a.values())
    print('read letters seen:', dict(letters))
    c_index = {(rec['_date'],) + rec['_key']: rec for rec in C}
    a_bets, c_bets = [], []
    for ra in A:
        rc = c_index.get((ra['_date'],) + ra['_key'])
        if rc is None or not (in_band(ra['price']) and in_band(rc['price'])):
            continue
        res = grade(ra, box)
        if res is None or rc.get('market_fair') is None:
            continue
        fa = rc['market_fair']
        base = dict(game=str(ra['game_id']), date=ra['_date'], res=res)
        a_bets.append(dict(base, price=ra['price'], u=units(res, ra['price']), clv=fa - 1 / dec(ra['price'])))
        c_bets.append(dict(base, price=rc['price'], u=units(res, rc['price']), clv=fa - 1 / dec(rc['price'])))
    print('R29a paired sides:', len(a_bets))
    summarize('R29a AT A price', a_bets)
    summarize('R29a AT C price', c_bets)
    placebo(a_bets)
    diffs = [a['u'] - c['u'] for a, c in zip(a_bets, c_bets) if a['res'] in ('W', 'L') and c['res'] in ('W', 'L')]
    if diffs:
        print(f"  paired units A-minus-C per bet {sum(diffs)/len(diffs):+.4f} over {len(diffs)}; A better on {sum(1 for d in diffs if d > 0)}")
    b_bets, m_bets = [], []
    for rc in C:
        if rc.get('hold') is None or rc.get('market_fair') is None or not in_band(rc['price']) or rc['market_fair'] <= 0.5:
            continue
        res = grade(rc, box)
        if res is None:
            continue
        base = dict(game=str(rc['game_id']), date=rc['_date'], res=res, price=rc['price'])
        clv = rc['market_fair'] - 1 / dec(rc['price'])
        if rc['hold'] <= 0.045:
            b_bets.append(dict(base, u=units(res, rc['price']), clv=clv))
        if rc['hold'] >= 0.07:
            m_bets.append(dict(base, u=units(res, rc['price']), clv=clv))
    print('R29b favorite sides, hold <= 0.045:', len(b_bets))
    summarize('R29b low-hold favorite', b_bets)
    placebo(b_bets)
    summarize('mirror favorite hold >= 0.07 (context only)', m_bets)

if __name__ == '__main__':
    main()
