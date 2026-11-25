"""Run 29 NHL, DESCRIPTIVE deviation from R29a (post-hoc, not a pass test): the registered EV >= 0 gate selects 0 sides
(best open-read EV is never >= 0 on points), so this runs the same timing comparison on the highest-EV side with no sign gate.
Usage: python pts_r29_desc.py"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import pts_r29 as m

rows = m.load()
a, c, ev_list = [], [], []
for r in rows:
    o, cl = r.get('open') or {}, r.get('close') or {}
    if o.get('fair_over') is None or o.get('over') is None or cl.get('over') is None:
        continue
    fo, fc = o['fair_over'], cl.get('fair_over')
    if fc is None:
        continue
    ev_o = {'over': fo * m.dec(o['over']) - 1, 'under': (1 - fo) * m.dec(o['under']) - 1}
    side = max(ev_o, key=ev_o.get)
    po, pc = o[side], cl[side]
    if not (m.in_band(po) and m.in_band(pc)):
        continue
    res = m.side_res(r, side)
    fs = fc if side == 'over' else 1 - fc
    base = dict(game=r['game_id'], date=r['_date'], res=res, price=po)
    a.append(dict(base, price=po, u=m.units(res, po), clv=fs - 1 / m.dec(po)))
    c.append(dict(base, price=pc, u=m.units(res, pc), clv=fs - 1 / m.dec(pc)))
    ev_list.append(ev_o[side])
print('descriptive pairs:', len(a), 'median best-side EV at open', round(sorted(ev_list)[len(ev_list)//2]*100, 2), '%')
m.summarize('DESC open price (highest-EV side, no gate)', a)
m.summarize('DESC close price (same side)', c)
m.placebo(a)
diffs = [x['u'] - y['u'] for x, y in zip(a, c) if x['u'] is not None and y['u'] is not None]
print(f"  paired open-minus-close units per bet {sum(diffs)/len(diffs):+.4f}; open better on {sum(1 for d in diffs if d>0)} of {len(diffs)}")
