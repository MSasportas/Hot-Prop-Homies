## 2026-11-16, Run DM (Sharp; data mining 2026-11-16 — three leads registered)

Source: data_mining_2026-11-16.md. Base population: 9,176 graded sides (all Pinnacle-on-line sides with HR -200..+200, shadow reads Oct 26-Nov 15, 20 slates). Three findings reviewed; all three registered as forward lab tests (DM1, DM2, DM3).

**DM1 — Minutes down 3+, unders (registered).** Discovery: n=153 (second half, Nov 6+), 64.1% hit, +19.3% ROI, 90% CI [+7.2, +31.4]. CLV_pin -5.7% (same as base): this is a player-state filter, not a pricing-edge, so CLV gate not required. Record live picks in bucket: 4 picks 1-3 — too thin to override the shadow sample, but flagged. Mirror (minutes up 3+, overs): -15.1% ROI, CI entirely negative — tracked as the inverse. Registered as DM1 with gate: n >= 100 graded forward unders in bucket, hit rate > 55%, ROI > 0.

**DM2 — Hot-form overs fade (registered).** Last-5 output 10%+ above season avg, overs: n=361, 45.7% hit, -12.6% ROI, CI [-21.0, -4.3]. Points overs: 40.0%, -25.1%. Hot unders near breakeven — no action. LVA2 overlap check done: LVA2 (line 5%+ above rolling avg) and DM2 (output 10%+ above season avg) are different features. LVA2 says overs hit when line is high; DM2 says overs miss when player is hot. These are conceptually compatible (line being high = market already priced it correctly; hot player whose line hasn't caught up = different). DS to report overlap correlation at first scoring check. Registered as DM2 with gate: n >= 80 forward overs in hot bucket, hit rate < 50%, ROI < -5%.

**DM3 — Pinnacle 3+ pts off market, skip unders (registered).** Discovery: n=81, 32-49, 39.5% hit, -26.3% ROI, CI [-43.2, -9.5]. Both halves negative (first -18.1%, second -39.6%). Overs in same bucket +13.4% — not stable (second half only +30.6%), watch only, not registered. Registered as DM3 with gate: n >= 50 forward unders in Pinnacle-outlier bucket, hit rate < 48%.

Files changed: lab.json (3 new entries: DM1, DM2, DM3), HYPOTHESES.md (Run DM section), LOG.md.

## 2026-11-15, LVA2 (Sharp; line vs rolling avg — over signal registered)

## 2026-11-16, AH11 (auto; Morning overs vs unders)
Filter: MOVES in 11AM->90 window, split by side. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 14 nights): n 526 graded 518 274-244 -12.66u ROI -2.4% CLV_pin -4.5% (n 512)
Discovery FAIR (ev_pin>=0): n 34 graded 34 22-12 +9.64u ROI +28.4% CLV_pin -0.2% (n 34)
Forward (>=2026-11-10, 3 nights): n 74 graded 74 41-33 +0.96u ROI +1.3% CLV_pin -4.4% (n 70)
Forward FAIR: n 3 graded 3 1-2 -1.20u ROI -40.0% CLV_pin -1.1% (n 3)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating

Finding: pin_solo OVER picks where Pinnacle's line is 5%+ above the player's rolling season average hit at 100% (8-0, n=8) at min 3 prior games, vs base over rate 78.9% (15-4). Result holds across all three minimum-game cutoffs. Post-hoc discovery.
Sharp decision: Register LVA2 as forward lab test. n=8 is thin but 8-0 is notable and the logic is coherent — line set high vs recent output, overs still hitting, possible upward trend or systematic market caution. Independent from LVA1 (different side: overs, different condition: line above avg). Forward gate: n>=30 fresh forward over picks in the above-5% bucket (min 3 prior games), hit rate clearly above the base over rate (78.9%). No live rule change until gate is met and DS names the sample.
Files changed: lab.json (new LVA2 entry), HYPOTHESES.md (LVA2 added under Run LVA section). Shadow tracking begins 2026-11-16.

## 2026-11-15, LVA1 (Sharp; line vs rolling avg — under filter registered)
Finding: pin_solo UNDER picks where Pinnacle's line is 5%+ below the player's rolling season average hit at 23.5% (4-13, n=17) vs 50% base under rate. Pattern holds at min 1, 3, and 5 prior games.
Sharp decision: Register LVA1 as forward lab test. Post-hoc, so discovery numbers are informational only — no conclusion possible from them. Forward gate: n>=40 skipped under picks (below-5% bucket, min 3 prior games), hit rate above breakeven, skipped ROI below kept-unders ROI. No live rule change until gate is met and DS names the sample.
Files changed: lab.json (new LVA1 entry), HYPOTHESES.md (Run LVA section). Shadow tracking begins 2026-11-16.

## 2026-11-15, NP4 (DS; exchange move, HR unchanged)
Rule: novig AND prophetx both move fair-over >= 1 pt (0.01) same direction, HR prices unchanged, consecutive reads. Bet HR in exchange direction. No Pinnacle condition. NHL analogs: NN4/LL5. Code: scratchpad/np4_discovery.py.
Discovery Oct 25-Nov 14 (21 nights): n 861 graded 795 398-397 -46.79u ROI -5.9%
  overs: n 383 graded 355 176-179 -25.00u ROI -7.0%
  unders: n 478 graded 440 222-218 -21.78u ROI -5.0%
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: DISCOVERY - accumulating.
NOTE: Discovery shows 795 graded events over 21 nights (~38/night) — large sample base, but 50/50 W-L with negative ROI from vig. No edge visible in discovery. Forward test required; needs 150 graded.

## 2026-11-12, Run 13 (CEO; Matt: when does Pinnacle move, and how far before tip). Code: research/code/run11/when_moves.py. 18 nights, consecutive stored reads, lines Pinnacle posted at both.

## 2026-11-15, AH11 (auto; Morning overs vs unders)
Filter: MOVES in 11AM->90 window, split by side. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 14 nights): n 526 graded 518 274-244 -12.66u ROI -2.4% CLV_pin -4.5% (n 512)
Discovery FAIR (ev_pin>=0): n 34 graded 34 22-12 +9.64u ROI +28.4% CLV_pin -0.2% (n 34)
Forward (>=2026-11-10, 3 nights): n 74 graded 74 41-33 +0.96u ROI +1.3% CLV_pin -4.4% (n 70)
Forward FAIR: n 3 graded 3 1-2 -1.20u ROI -40.0% CLV_pin -1.1% (n 3)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH10 (auto; Large move unders by size band (3-4 vs 4+))
Filter: MOVES: unders, split 3-4 pts vs 4+ pts. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 19 nights): n 312 graded 307 167-140 +0.90u ROI +0.3% CLV_pin -3.1% (n 277)
Discovery FAIR (ev_pin>=0): n 44 graded 44 26-18 +6.00u ROI +13.6% CLV_pin -0.2% (n 36)
Forward (>=2026-11-10, 5 nights): n 85 graded 84 49-35 +5.99u ROI +7.1% CLV_pin -2.3% (n 75)
Forward FAIR: n 8 graded 8 3-5 -2.33u ROI -29.1% CLV_pin -0.2% (n 7)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH9 (auto; 2-4 books following (consensus middle band))
Filter: MOVES where 2-4 other books moved >= 1 pt the same way. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 18 nights): n 301 graded 296 171-125 +23.07u ROI +7.8% CLV_pin -3.9% (n 258)
Discovery FAIR (ev_pin>=0): n 28 graded 28 18-10 +8.47u ROI +30.3% CLV_pin -0.7% (n 23)
Forward (>=2026-11-10, 5 nights): n 85 graded 84 45-39 -0.67u ROI -0.8% CLV_pin -3.2% (n 76)
Forward FAIR: n 8 graded 8 4-4 -0.59u ROI -7.4% CLV_pin -0.9% (n 7)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH8 (auto; Unders in last 90 min)
Filter: MOVES where side = under AND window in last 90 min. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 15 nights): n 101 graded 101 69-32 +24.73u ROI +24.5% CLV_pin -3.0% (n 68)
Discovery FAIR (ev_pin>=0): n 20 graded 20 12-8 +2.48u ROI +12.4% CLV_pin -0.0% (n 12)
Forward (>=2026-11-10, 2 nights): n 21 graded 21 16-5 +8.08u ROI +38.5% CLV_pin -2.7% (n 14)
Forward FAIR: n 2 graded 2 1-1 -0.23u ROI -11.5% CLV_pin +1.2% (n 1)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH7 (auto; 45->20 window only)
Filter: MOVES in the 45->20 minute window. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 13 nights): n 65 graded 65 38-27 +6.06u ROI +9.3% CLV_pin - (n 0)
Discovery FAIR (ev_pin>=0): n 10 graded 10 7-3 +3.47u ROI +34.7% CLV_pin - (n 0)
Forward (>=2026-11-10, 2 nights): n 10 graded 10 4-6 -2.34u ROI -23.4% CLV_pin - (n 0)
Forward FAIR: n 1 graded 1 0-1 -1.00u ROI -100.0% CLV_pin - (n 0)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH6 (auto; 90->45 window only)
Filter: MOVES in the 90->45 minute window. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 14 nights): n 127 graded 127 77-50 +13.49u ROI +10.6% CLV_pin -4.0% (n 125)
Discovery FAIR (ev_pin>=0): n 14 graded 14 9-5 +3.14u ROI +22.4% CLV_pin -0.2% (n 14)
Forward (>=2026-11-10, 2 nights): n 20 graded 20 16-4 +8.86u ROI +44.3% CLV_pin -3.0% (n 19)
Forward FAIR: n 1 graded 1 1-0 +0.77u ROI +76.9% CLV_pin +1.2% (n 1)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH4 (auto; Stale HR + FAIR (HR stale, EV >= 0))
Filter: MOVES where HR price unchanged (stale) AND ev_pin >= 0. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 13 nights): n 19 graded 19 12-7 +3.82u ROI +20.1% CLV_pin -0.8% (n 16)
Discovery FAIR (ev_pin>=0): n 19 graded 19 12-7 +3.82u ROI +20.1% CLV_pin -0.8% (n 16)
Forward (>=2026-11-10, 4 nights): n 4 graded 4 1-3 -2.20u ROI -55.0% CLV_pin +0.1% (n 4)
Forward FAIR: n 4 graded 4 1-3 -2.20u ROI -55.0% CLV_pin +0.1% (n 4)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH3 (auto; Solo + late (solo Pinnacle, last 90 min))
Filter: MOVES where others < 1 pt AND window is 90->45 or 45->20. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 15 nights): n 103 graded 103 62-41 +11.92u ROI +11.6% CLV_pin -3.1% (n 60)
Discovery FAIR (ev_pin>=0): n 14 graded 14 11-3 +6.80u ROI +48.6% CLV_pin +0.2% (n 10)
Forward (>=2026-11-10, 2 nights): n 15 graded 15 10-5 +3.37u ROI +22.4% CLV_pin -2.5% (n 7)
Forward FAIR: n 1 graded 1 1-0 +0.77u ROI +76.9% CLV_pin +1.2% (n 1)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH2 (auto; Late + large (last 90 min, move 3+ pts))
Filter: MOVES where window is 90->45 or 45->20 AND move >= 3 pts. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 15 nights): n 134 graded 134 80-54 +14.18u ROI +10.6% CLV_pin -3.5% (n 87)
Discovery FAIR (ev_pin>=0): n 24 graded 24 16-8 +6.61u ROI +27.5% CLV_pin -0.2% (n 14)
Forward (>=2026-11-10, 2 nights): n 22 graded 22 14-8 +3.77u ROI +17.1% CLV_pin -2.7% (n 16)
Forward FAIR: n 2 graded 2 1-1 -0.23u ROI -11.5% CLV_pin +1.2% (n 1)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH1 (auto; Large unders (4+ pt move, under side))
Filter: MOVES where Pinnacle move >= 4 pts AND side = under. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 19 nights): n 191 graded 187 100-87 -4.02u ROI -2.1% CLV_pin -2.8% (n 169)
Discovery FAIR (ev_pin>=0): n 32 graded 32 18-14 +1.84u ROI +5.8% CLV_pin +0.2% (n 27)
Forward (>=2026-11-10, 5 nights): n 57 graded 57 32-25 +1.08u ROI +1.9% CLV_pin -2.3% (n 51)
Forward FAIR: n 7 graded 7 3-4 -1.33u ROI -19.0% CLV_pin -0.2% (n 6)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH15 (auto; Late + FAIR (last 90 min, ev_pin >= 0))
Filter: MOVES where window is last 90 min AND ev_pin >= 0. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 10 nights): n 24 graded 24 16-8 +6.61u ROI +27.5% CLV_pin -0.2% (n 14)
Discovery FAIR (ev_pin>=0): n 24 graded 24 16-8 +6.61u ROI +27.5% CLV_pin -0.2% (n 14)
Forward (>=2026-11-10, 1 nights): n 2 graded 2 1-1 -0.23u ROI -11.5% CLV_pin +1.2% (n 1)
Forward FAIR: n 2 graded 2 1-1 -0.23u ROI -11.5% CLV_pin +1.2% (n 1)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH14 (auto; Small FAIR moves (2-3 pt, ev_pin >= 0))
Filter: MOVES where move 2-3 pts AND ev_pin >= 0 (the small-move FAIR question). MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 5 nights): n 5 graded 5 3-2 +0.42u ROI +8.3% CLV_pin +1.6% (n 5)
Discovery FAIR (ev_pin>=0): n 5 graded 5 3-2 +0.42u ROI +8.3% CLV_pin +1.6% (n 5)
Forward (>=2026-11-10, 0 nights): n 0 graded 0 0-0 +0.00u ROI - CLV_pin - (n 0)
Forward FAIR: n 0 graded 0 0-0 +0.00u ROI - CLV_pin - (n 0)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH13 (auto; Stale HR + unders)
Filter: MOVES where HR price unchanged AND side = under. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 18 nights): n 91 graded 89 55-34 +12.21u ROI +13.7% CLV_pin -2.8% (n 75)
Discovery FAIR (ev_pin>=0): n 15 graded 15 9-6 +1.17u ROI +7.8% CLV_pin -0.2% (n 12)
Forward (>=2026-11-10, 5 nights): n 26 graded 26 17-9 +4.86u ROI +18.7% CLV_pin -2.5% (n 24)
Forward FAIR: n 4 graded 4 1-3 -2.20u ROI -55.0% CLV_pin +0.1% (n 4)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, AH12 (auto; Solo large (3+ pt, solo Pinnacle))
Filter: MOVES where move >= 3 pts AND others < 1 pt. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 18 nights): n 148 graded 148 87-61 +15.37u ROI +10.4% CLV_pin -2.8% (n 121)
Discovery FAIR (ev_pin>=0): n 26 graded 26 17-9 +7.90u ROI +30.4% CLV_pin -0.8% (n 22)
Forward (>=2026-11-10, 5 nights): n 38 graded 38 24-14 +6.79u ROI +17.9% CLV_pin -2.4% (n 35)
Forward FAIR: n 3 graded 3 1-2 -1.23u ROI -41.0% CLV_pin +0.9% (n 3)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-15, NP1-NP3 (DS; NHL parity registration — sharp/soft split, fade soft move, whole-market follow)
Registered from nhl_parity_2026-11-15.md. NHL analogs: MM2a/b (NP1), NN6 (NP2), NN5 (NP3).
Code: research/code/np1_np2_np3_discovery.py. Discovery = all 21 nights Oct 25-Nov 14. Forward from Nov 15. Gate: 150 graded.

NP1 (sharp vs soft split, B/C reads, abs(sf-tf)>=0.03, EV>=0 vs sharp):
Discovery (21 nights): n 90 graded 87 49-38 +11.48u ROI +13.2%
  over subset: n 7 graded 6 3-3 +0.30u ROI +4.9%
  under subset: n 83 graded 81 46-35 +11.18u ROI +13.8%
Sample: 90 bets but all discovery (all 21 nights already seen). Gate at 150 graded forward.

NP2 (fade soft move, sharp not follow, HR stale, EV>=0 vs sharp):
Discovery (21 nights): 23 candidate pairs before EV gate; 0 bets after EV gate.
Sharp never prices the fade side favorably at HR's stale price — EV gate is structural.
Sample: too thin to judge. Accumulating forward.

NP3 (whole market moves >= 3 books, HR still, follow direction, not conditioned on Pinnacle):
Discovery (21 nights): n 3 graded 3 1-2 -0.85u ROI -28.3%
Sample: 3 bets. Too thin to judge. Accumulating forward.

## 2026-11-15, AH5 (auto; Large solo (4+ pt solo Pinnacle move))
Filter: MOVES where move >= 4 pts AND others < 1 pt. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 18 nights): n 66 graded 66 42-24 +12.07u ROI +18.3% CLV_pin -2.2% (n 51)
Discovery FAIR (ev_pin>=0): n 14 graded 14 10-4 +4.78u ROI +34.1% CLV_pin -0.3% (n 12)
Forward (>=2026-11-10, 5 nights): n 21 graded 21 14-7 +4.72u ROI +22.5% CLV_pin -2.0% (n 20)
Forward FAIR: n 2 graded 2 1-1 -0.23u ROI -11.5% CLV_pin +1.3% (n 2)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


## 2026-11-14, AH4 (auto; Stale HR + FAIR (HR stale, EV >= 0))
Filter: MOVES where HR price unchanged (stale) AND ev_pin >= 0. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 12 nights): n 18 graded 18 12-6 +4.82u ROI +26.8% CLV_pin -0.9% (n 15)
Discovery FAIR (ev_pin>=0): n 18 graded 18 12-6 +4.82u ROI +26.8% CLV_pin -0.9% (n 15)
Forward (>=2026-11-10, 3 nights): n 3 graded 3 1-2 -1.20u ROI -40.0% CLV_pin -0.3% (n 3)
Forward FAIR: n 3 graded 3 1-2 -1.20u ROI -40.0% CLV_pin -0.3% (n 3)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating

- 2026-11-13 (Researcher run 9, daily; NBA; books, not players). No key used, no odds pull.
  Registered BB1a/BB1b (book agreement, dispersion of other books' no-vig fairs) in HYPOTHESES.md before any test.
  NOT TESTED THIS RUN: data/odds has no read labels (pull is absent in every fetch), so the B/C reads need mapping by time, and grading needs the box-score join (data/state/box, keyed by pid and date). Neither mapping is built yet. Registration is in place; the test is queued.
  Current NBA auto-scorer (AH3 entry 2026-11-13, solo + late, forward 15 graded 10-5 +3.37u, CLV -2.5%) is below the bar (n 150 needed); no READY FOR SHARP.
  **Verdict: nothing tested, no candidate for the Sharp.**
  Next: (1) build B/C read mapping and box grading for BB1a/BB1b, script to research/code/run9/; (2) keep AH forward scoring nightly.

## 2026-11-13, AH3 (auto; Solo + late (solo Pinnacle, last 90 min))
Filter: MOVES where others < 1 pt AND window is 90->45 or 45->20. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 15 nights): n 103 graded 103 62-41 +11.92u ROI +11.6% CLV_pin -3.1% (n 60)
Discovery FAIR (ev_pin>=0): n 14 graded 14 11-3 +6.80u ROI +48.6% CLV_pin +0.2% (n 10)
Forward (>=2026-11-10, 2 nights): n 15 graded 15 10-5 +3.37u ROI +22.4% CLV_pin -2.5% (n 7)
Forward FAIR: n 1 graded 1 1-0 +0.77u ROI +76.9% CLV_pin +1.2% (n 1)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating

Share of Pinnacle lines that moved 2+ pts per read window: 11 AM -> 90 min (about 7 h): 544 of 2,334 (23%), 3.3% per line-hour, 199 moved 4+ | 90 -> 45 min: 155 of 3,082 (5.0%), 6.1% per line-hour | 45 -> 20 min: 90 of 3,136 (2.9%), 8.6% per line-hour.
By minutes before tip (window end): 25-50 min 6.2%/h; last 25 min 8.7%/h; 80-120 min about 11%/h (n 78). Rate rises toward tip: about 3%/h in the morning, 6%/h from 90 to 45, 9%/h in the last 45.
By market per line-hour: points 8.1%, rebounds 7.7%, assists 6.7%, threes 4.9% (threes move least).
Reads only bracket a move, so the exact minute is unknown; there is no time of day when Pinnacle moves and then stops. It moves all day, and fastest close to tip. Clock-time buckets are confounded by tip time and not used.
Verdict: no sweet spot to aim one check at. Because Hard Rock follows in 20-30 minutes, catching a move needs a check within about 25 minutes of it, so cover the day evenly and tighten toward tip. Tonight (2026-11-12): 24 Pinnacle moves of 2+ pts, 0 bettable when seen, 8 would have been fair at Hard Rock's earlier price, most in the 11 AM -> 90 min window.
Change shipped: reads.extra.mins now 240, 180, 135, 75, 60, 30 (new: 3 PM, 4 PM, 4:45 PM for a 7 PM game), never before the morning read. About +24 credits a game, only from credits the planned reads do not need.

## 2026-11-12, Run 12 (CEO; Matt: scan other Hard Rock markets). One snapshot at 3:22 PM ET, 4 games (DET@WAS, TOR@PHI, DAL@MIN, CHA@PHX), 83 credits. Files: research/market_probe/ (raw + summary.txt); code research/market_probe.py (workflow nba-market-probe, one-time).
Hard Rock posts 21 player markets (we use 4): points, rebounds, assists, threes + points+rebounds+assists, points+rebounds, points+assists, rebounds+assists, steals, blocks, steals+blocks, double-double, triple-double, first basket, q1 points/assists/rebounds, and alternate ladders for points, rebounds, assists, threes.
Other books and Pinnacle: Pinnacle prices only points, rebounds, assists, threes, and points+rebounds+assists. Combos (P+R, P+A, R+A): 6-7 other books, no Pinnacle. Steals 4, blocks 3-5, steals+blocks 1-2, q1 markets 0-1: almost nothing to compare against. Double-double 6, first basket 4, triple-double 6, no Pinnacle.
Hard Rock margin (avg over/under hold) vs the other books: points 6.9% vs 7.8% | rebounds 6.6% vs 7.1% | assists 6.3% vs 6.9% | threes 6.4% vs 6.8% | PRA 6.9% vs 7.7% | P+R 6.9% vs 11.8% | P+A 6.8% vs 13.6% | R+A 6.6% vs 9.8% | steals 8.3% vs 8.8% | blocks 8.3% vs 9.7%.
Verdict: Hard Rock is not loose anywhere in this snapshot: its margin is at or below the other books on every market with a comparison, including the combos. No stale-price edge visible. Where Hard Rock IS thicker (steals, blocks, q1: 8.3-8.6%) there is no Pinnacle or only 0-5 books to judge against, so we could not tell a mistake from a fair price. One snapshot, so a single night cannot rule markets out.
Next: (1) a no-model consistency test on stored combo prices: Hard Rock P+R+A vs the sum of Pinnacle's points, rebounds and assists medians (needs the combo snapshot saved nightly, about 5 credits a game); (2) steals and blocks: nightly snapshot, judge against the 4-5 books that post them.

## 2026-11-12, Run 11 (CEO; Matt: test the top-5 ideas that need no new data). Code: research/code/run11/moves_thr.py. 18 nights.
T1a 3-pointers / all markets on a smaller Pinnacle move, FAIR (Hard Rock >= Pinnacle fair): move >= 2.0 pts 58 bets 38-20 +16.25u 3.22/night CLV -0.19%; >= 1.0: 61, 38-23; >= 0.5: 61, 40-21. Threes FAIR 12-0 (2 pts) / 14-1 (0.5 pt), CLV +1.2% (n 8-11). Without the fair check threes: 147-295 bets, ROI about 0, CLV -4.3..-4.8%.
  Verdict: the move size is NOT what limits volume; the fair-price check is. A looser trigger adds 3 bets in 18 nights. Closed.
T1b no move, Hard Rock X%+ over Pinnacle (B/C/D): threes >= 0%: 45, 26-19 +10.07u, 2.5/night, CLV -0.03% (beat 81%); >= 1%: 17, 10-7, CLV +0.93%; >= 2%: 11, 7-4, CLV +2.69% (7/7). Points/rebounds/assists: CLV negative at every bar.
  Verdict: threes >= 1% is a small lead (about 1 a night). Forward-track, do not go live on n 17.
T2 HOW FAST HARD ROCK FOLLOWS a 2+ pt Pinnacle move (state of Hard Rock's price when our next read saw the move):
  reads <= 30 min apart: 65 moves, Hard Rock already followed 52%, unchanged 40%, still fair-or-better 15%
  31-50 min: 102 moves, followed 76%, still fair 11% | 51-120 min: 34, followed 76%, fair 8% | over 2 h: 498, followed 82%, fair 6%
  Upper bound for faster reads = the same bets at Hard Rock's price from BEFORE the move: 333 bets, 177-156 +20.13u ROI +6.0%, 18.5/night, CLV +3.30%, beat close 91% (n 306). The rule today gets 58 of them (3.2/night).
  Missed today: 280 bets (15.6/night) 142-138 +3.32u, CLV +3.58%.
  Verdict: LEAD, the biggest so far. Hard Rock follows Pinnacle in roughly 20-30 minutes; our reads are 25-45+ minutes apart, so about 5 of 6 moves are gone when we look. The edge is speed, not a new filter. Caveats: upper bound (assumes every move is seen before Hard Rock reacts; some reactions are near-instant); CLV at the old price is partly by construction; ROI +6% on 333 has a wide interval.
Next: forward trial of tighter reads in the last 90 minutes (every 15 min), measure the real catch rate and CLV. Needs engine work (reads are fixed A/B/C/D) and about +100 credits a night.

## 2026-11-12, Run 10 (CEO; Matt picked idea #2 of the 100: LINE disagreements, Hard Rock main line != Pinnacle main line)
Code: research/code/run10/line_disagree.py, line_convert.py. 18 nights, reads B/C/D, one bet per player/market/night, Hard Rock -200..+200, bet toward Pinnacle (Pinnacle higher = over, lower = under).
Volume: 1,028 graded disagreements, 60.5 a night. Bet blind: 546-482 -68.07u ROI -6.6%. Hard Rock's line moved our way by the close 11%, against 1%.
No-model lower bound (Pinnacle's chance at ITS line x Hard Rock price): 1 of 1,028 >= 0%.
Converted (Pinnacle chance carried to Hard Rock's line; Normal(mu, k sqrt(mu)), k fitted per market from book-vs-book line pairs, rmse 0.022-0.026; calibration said .483/.522/.566 -> hit .488/.540/.575):
ev >= +2%: 10 bets in 18 nights, 5-5 -0.52u. ev >= +4%: 7, 3-4. ev < -2%: 997 of 1,028.
Verdict: NO CANDIDATE. When Hard Rock's line differs it has already re-juiced the price (same finding as Run 4 F8, now on 18 nights). A different line is not a stale line. No volume here. Do not re-test on main lines.
Note: the side toward Pinnacle hit 1-2 pts more often than the converted chance across ~700 bets, far short of the ~7% price handicap.

## 2026-11-12, CLV2 (CEO; closing-line value of the Lab track pin_judge = Hard Rock 2%+ over Pinnacle fair, no move needed)
Matt asked to put a "2%+ edge" bar in the Lab: it is already there (pin_judge, since 2026-10-28). Scored it against the close from stored reads.
pin_judge 55 graded: 30-25 +6.71u, 4.2 a night. CLV measured 27 (D-read flags have no later read yet): mean -1.05%, beat close 55%.
By market (n, W-L, CLV n / mean): threes 10 7-3 +2.69% (7/7 beat) | assists 9 4-5 -0.40% | points 17 8-9 -1.13% | rebounds 19 11-8 -4.26% (2/9 beat).
Edge size: pin_ev >= 3%: 26, 16-10, CLV -2.93% (n 8). 2-3%: 29, 14-15, CLV -0.25% (n 19). A bigger gap to Pinnacle does NOT hold to the close: Pinnacle tends to come back toward Hard Rock.
Entry edge of the live Record picks: mean +1.60%, median +1.01% (n 55); 27 under 1%.
Verdict: raising the live bar to 2% is not supported. Only threes beat the close in both the Record (+1.15%, n 8) and pin_judge (+2.69%, n 7). Tiny samples.
Next (volume, Matt 2026-11-12 "we need more picks a night"): (1) NOT the NHL Gap + Guard port: already closed twice (Oct 28 and Run 9, 2026-11-10: about 2 sides in 15 nights; Hard Rock NBA is priced too tight to the other books). Do not re-test. (2) H: threes-only variants of pin_solo and pin_judge; (3) the late closing read (reads.close, live today) will give D-read flags a close; (4) new NBA markets are the open volume route (needs credits: CEO/Matt).

## 2026-11-12, CLV1 (CEO; closing-line value of the live Record, stored reads only)
Code: research/code/clv/clv_record.py. Close = last stored read of the game after the pick was first shown (usually D, 20 min); close_fair = Pinnacle no-vig on the same line; CLV = close_fair x decimal(posted price) - 1.
Record singles 58: 37-21 +14.27u. Measured 46: mean CLV +0.01%, median +0.67%, beat close 74% (one -12.6% outlier).
By market (measured n, mean CLV): points 17 +0.80% | threes 8 +1.15% | rebounds 13 -1.33% | assists 8 -0.64%.
Unmeasured 12: picks first shown on the last read (window 45->20: 10 picks, 7-3) have no later read.
Hard Rock on the same line at the last read (42): moved our way 12, same 28, moved against 2.
Verdict: the +14u is running well ahead of the price edge (about zero vs the close so far; NHL shots measure +4.7%, n 42). Small sample; watch rebounds and assists. No rule change.
Next: a late read (about 8-10 min before tip) for games holding a pick, so the 45->20 picks get a close too (needs the 2 extra keys Matt is adding).

## 2026-11-11, AH1 (auto; Large unders (4+ pt move, under side))

## 2026-11-12, AH2 (auto; Late + large (last 90 min, move 3+ pts))
Filter: MOVES where window is 90->45 or 45->20 AND move >= 3 pts. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 15 nights): n 134 graded 134 80-54 +14.18u ROI +10.6% CLV_pin -3.5% (n 87)
Discovery FAIR (ev_pin>=0): n 24 graded 24 16-8 +6.61u ROI +27.5% CLV_pin -0.2% (n 14)
Forward (>=2026-11-10, 2 nights): n 22 graded 22 14-8 +3.77u ROI +17.1% CLV_pin -2.7% (n 16)
Forward FAIR: n 2 graded 2 1-1 -0.23u ROI -11.5% CLV_pin +1.2% (n 1)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating


Filter: MOVES where Pinnacle move >= 4 pts AND side = under. MOVES population (Pinnacle >= 2 pt move, HR on line, -200..+200, 1/player/market/night).
Discovery (<2026-11-10, 15 nights): n 143 graded 139 72-67 -6.74u ROI -4.8% CLV_pin -3.0% (n 127)
Discovery FAIR (ev_pin>=0): n 27 graded 27 15-12 +1.17u ROI +4.3% CLV_pin +0.0% (n 23)
Forward (>=2026-11-10, 1 nights): n 9 graded 9 4-5 -1.64u ROI -18.3% CLV_pin -2.7% (n 9)
Forward FAIR: n 2 graded 2 0-2 -2.00u ROI -100.0% CLV_pin -2.7% (n 2)
Pass bar: n>=150 graded fwd, ROI>0, CI>0, CLV>0. Status: FORWARD - accumulating

﻿# LOG.md (NBA research, newest first)

## 2026-11-10, Run 9 (Researcher; owner: re-test NHL's live Gap + Guard on NBA with all stored data)
Code: research/code/run9_nhl_port.py. DISCOVERY ONLY (15 nights Oct 25 - Nov 9, no Nov 3, all already seen). Port of NHL v3.5:
gap EV vs median de-vigged fair of >= 4 books incl. Pinnacle (hold 0-15%) >= +3%, Pinnacle-fair EV >= 0, price -200 or better;
guard = 0.8 fair + 0.2 NBA model (shadow model_p, offset 0) final EV >= +2% and model >= break-even; picks at B/C only, first passing
read, 1 side per player per night. CLV = Pinnacle fair at the last read.
- Sides checked: 21,774 (all reads), 11,376 at B/C. Clearing at B/C: NHL bar 2, 2% 2, 1% 4, 0% (+Pinnacle) 8, 0% gap-only 13.
  Full NHL rule (gap + guard): 2 picks, 1-1 +0.10u, both Nov 2 (Daniels U5.5 ast +110 at a +17.5% gap = one bad/stale quote; McCollum
  U3.5 ast +120). 0% + Pinnacle: 8 picks 3-5 -2.11u, CLV -0.1% (n 5). 0% gap-only: 12 picks 5-7 -1.81u, CLV -1.4% (n 9).
  Late nights (Nov 4-9): NHL bar 0 picks; 0% bar 2 picks 1-1.
- Hard Rock median gap per night: -6.1% to -6.3% every night; early -6.2% (n 11,797), late -6.2% (n 9,977). By market: pts -6.5%, reb
  -6.2%, ast/3pm -6.1%; overs -6.8%, unders -5.6%; every read -6.2/-6.3%. Share of sides at gap >= 0: 0.16% early, 0.06% late. The
  ~6% hold has NOT narrowed.
- Pinnacle 2+ pt moves (614; 548 with a later read): median share of the eventual move done at first sight 100%; mean drift after
  -0.11 pts. Held 466 (241-214 -9.67u, CLV -4.1%), reversed 1+ pt 47 (26-20 +2.15u), ran on 1+ pt 35 (16-18 -5.58u). It is a one-time
  jump; drift direction does not predict results. In the FAIR subset, held 34 bets 23-10 +12.33u, CLV +1.1%.
- Record overlap (66 pin_solo picks, 40-25 +12.29u): at their own read the median gap vs market is -4.6% (max +1.3%; 0 at >= 3%,
  2 at >= 0%). The NHL rule picks 0 of them; the 0% bar shares 2.
- Verdict: NO CANDIDATE. NHL's Gap + Guard has nothing to bet on NBA at Hard Rock: ~2 sides in 15 nights, same as Oct 28. The NBA
  Record's edge comes from Pinnacle's new fair price after a move, not from Hard Rock beating the market.
- Next 3: (1) DraftKings as the priced book under the same gap test (rule now allows HR or DK); (2) gap vs Pinnacle-only fair on the
  held-move subset forward; (3) flag single-book stale quotes like Daniels Nov 2 as a data check, not an edge.
## 2026-11-09 night, Run 8 (Researcher; Matt: line moves and book moves for NBA like NHL)
Code: research/code/run8_moves.py (M1-M7, re-run any day; splits discovery / forward at 2026-11-10). DISCOVERY ONLY: 14 nights with
moves (Oct 26 - Nov 9, no Nov 3), all already seen through the Record. Nothing here can pass; forward counts from 2026-11-10.
Populations: MOVES = every Pinnacle 2+ pt move, Hard Rock on the line, bet at Hard Rock: 614 bets, 316-260, +7.65u (+1.3%, 90% CI
-6..+8%). FAIR = Hard Rock at or better than Pinnacle's new fair (the live gate): 53 bets, 36-15, +19.68u (+38.6%, CI +18..+60%).
Record (live picks as shown): 66 picks, 40-24, +13.29u. The fair-price gate is the whole edge: moves without it are break-even.
- M1 CLV (close = the 20-min read; 9 Record picks made at that read have no later price). Record: n 57, mean CLV vs Pinnacle's close
  -0.8%, median +0.1%, 54% above 0. CLV > 0 picks 19-11 +7.35u; CLV <= 0 picks 15-10 +2.80u. Vs Hard Rock's own close: Hard Rock closed
  shorter on 13 (9-4 +4.66u), same price on 37 (21-14 +5.65u), longer on 3, line gone on 4. Plain words: the Record wins but is NOT
  beating the close on average; on NHL the lead idea runs CLV +3.4%. That is the weak spot to watch. All MOVES: CLV -4.4% (7% above 0).
- M2 Hard Rock lag. Hard Rock re-priced with Pinnacle on 484 of 614 moves (79%), stale on 109 (18%). Stale: 56-45 +3.37u (+3.3%, CI
  -11..+19%); followed: 251-205 +6.20u (+1.4%). In FAIR: stale 11-3 +7.02u (n 15), followed 22-10 +11.80u (n 33). M2b (other books
  move 2+ pts, Hard Rock unchanged): 32 bets, 15-14 +0.16u, CLV -5.5%. No lag edge by itself; same answer as R3.
- M3 Consensus vs Pinnacle-only. MOVES: solo 112-90 +7.73u (+3.8%) vs consensus 204-170 -0.09u. FAIR: solo 18-7 +10.68u vs consensus
  18-8 +9.00u. Record: solo 24-16 +6.80u vs consensus 16-8 +6.49u. No difference. By books following 1+ pt (MOVES): 0-1 books 45-49
  -10.82u, 2-4 books 121-80 +25.20u (+12.5%, CI +2..+23%), 5+ books 150-131 -6.73u. A middle-band bump with no story: likely luck.
- M4 Move size. Record: 2-3 pts 7-8 -2.74u (n 15), 3-4 pts 13-6 +7.32u (n 19), 4+ pts 20-10 +8.71u (n 30). FAIR: 2-3 pts 3-2 (n 5),
  3-4 11-3, 4+ 22-10. All MOVES: flat (+2.8% / +3.0% / -1.3%). The Record's 2-3 band is the only losing band, on 15 bets; the big
  population does not back "small moves are worse" and the FAIR 2-3 group is 5 bets. Lead, not a finding. Keep the Sharp's watch.
- M5 Timing. MOVES: 11 AM -> 90 min 224-194 -4.08u (-1.0%); last 90 min 92-66 +11.73u (+7.4%, CI -4..+19%); 45 -> 20 alone 34-21
  +8.40u (n 55). FAIR: morning 21-9 +11.84u, 90->45 8-4, 45->20 7-2. Record: 23-13 / 11-8 / 6-3. Late moves look a bit better on all
  moves, but with the fair gate every window wins. 74% of moves come from the long 11 AM window.
- M6 Reverse move at the next read (Pinnacle comes back 1+ pt). Record: reversed 6-2 +3.73u (n 8), held 28-16 +9.42u (n 46), ran on
  0-2. MOVES: reversed 19-14 +2.40u (n 33), held 246-205 +3.92u, ran on 12-15 -5.85u. A reversal is NOT a pull signal so far.
  Side note: the 7 picks the page pulled ("Hard Rock took the line down") went 2-5 -3.67u vs 38-19 +16.96u not pulled. 7 bets.
- M7 Side. MOVES: unders 188-143 +14.67u (+4.4%), overs 128-117 -7.02u (-2.9%). FAIR: overs 10-1 +9.93u (n 11), unders 26-14 +9.75u
  (n 40). Record: overs 13-6 +7.42u, unders 27-18 +5.87u. 77% of FAIR picks are unders; both sides win. No asymmetry to act on.
- Count: 7 ideas x 3 populations, ~60 groups looked at on nights already seen. Expect ~3-6 "significant" by luck.
- Verdict: NO CANDIDATE FOR SHARP. Nothing to change live. Most useful fact: the live rule's edge is the fair-price gate, not the move's
  size, timing, side or how many books followed; and its CLV vs the 20-min Pinnacle price is ~0, not positive.
- Missing data: (1) no true close (last read is ~20 min before tip; 9 of 66 picks have no later price); (2) no historical NBA prop
  odds (paid, Matt only); (3) reads are 20-45 min apart (11 AM -> 90 min is hours), so "which book moves first" can only be seen as
  who had moved by the next read; (4) no A read on Oct 25, Nov 1-2; no Nov 3.
- Builder request (not made; outside research/): see the report to the CEO. (a) a daily step that runs run8_moves.py after grading and
  saves the output under research/fwd/; (b) an optional closing read ~2 min before tip for games with a shown pick (costs credits:
  CEO / Matt decide).
- Next 3: (1) re-run run8 weekly; first forward read at ~60 forward Record picks; (2) use each book's `last_update` stamp inside a read
  to order who moved first (free, already stored); (3) M1 by pick state (early / clear / starters) once n allows.

## 2026-10-29 ~8:10 AM, Run 7 (CEO as Researcher; Matt: fewer picks a day by a calculated method, no hard limits)
Code: research/code/run7_reduce.py; the 74 scored bets: research/run7_population.json. Discovery only (Oct 25-28), nothing can pass.
- Population: every Pinnacle 2+ pt move at B/C/D passing the v2.1 base, before the v2.2 gap gate: 74 bets, 44-30, +7.53u. Live-rule
  subset (gap >= 2 pts): 40 bets, 27-13, +10.80u. By night (all / live): Oct 26 26 / 11, Oct 27 3 / 2, Oct 28 45 / 27.
- Only one score separated winners from the rest: **S1, Hard Rock's price is at or better than Pinnacle's NEW fair price (EV vs
  Pinnacle >= 0%)**. All 74: kept 16 bets 12-4 +7.12u (+44.5%), cut 58 bets 32-26 +0.41u (+0.7%), random-cut placebo p = 0.05.
  Live subset: kept 16 12-4, cut 24 15-9 +3.68u (+15.3%), placebo p = 0.16. Kept by night: Oct 26 2 of 26, Oct 27 1 of 3, Oct 28
  13 of 45 (9-4). So a quiet night leaves 1-2 picks and a busy one ~13. The edge threshold is not a smooth gradient (>= -1%: +30.9%,
  >= 0%: +44.5%, >= +1%: +35.6% on 10 bets), and the picks it cuts still made money, so on units alone cutting costs ~3.7u of
  discovery profit; the case for it is per-pick quality and theory, not units.
- S2 (Pinnacle's new fair minus Hard Rock's break-even minus 1.5 pts of noise > 0): keeps NOTHING. In plain words: Pinnacle's POSTED
  price carries its own margin, so beating it by 2 pts (the v2.2 gate) lands near its FAIR number, not past it. Of the 40 live-rule
  bets, 16 are at or better than fair (S1) and 24 are 0-3 pts under it (all 40 within 3 pts). Those 24 win only if Pinnacle's move keeps
  running (the book catching up to news), not because the price is a bargain. S2 keeps none because it asks for 1.5 pts of cushion
  past fair. (First version of this line said 'almost every live pick'; that fit the 74-bet population, not the 40 live-rule bets.)
- No selection power: S3 (move vs others) cut groups did as well or better; S4/S4b (cell track record) and S7 (composite) came out
  INVERSE (the picks they drop did better): noise at this n; S5 overlap discount cut nothing in the live subset (no pile-ups big
  enough); S6 model (cut model 5+ pts below Pinnacle) kept 23 bets 16-7 +31.5% vs cut 17 bets 11-6 +20.9% (placebo p 0.35): a lead
  at best, same as the earlier look at 43 bets.
- Caveat in one line: 11 rules x 2 populations = ~22 looks at 4 nights; one at p = 0.05 is what chance alone gives. 13 of the 16 kept
  bets are from one night. Treat S1 as the one lead worth a forward test, not as a finding.
- Verdict: NO CANDIDATE FOR SHARP. Nothing to change live. Forward test needs no code: the shadow `solo` rows already carry
  `ev_vs_pin` for every move, so F9 scores itself from Oct 29 on.
- Next 3: (1) F9 forward (below); (2) after ~60 live bets, check whether S1 >= 0 picks beat the rest on CLV (Pinnacle's D-read fair
  vs the frozen price), which tests "still +EV after the move stopped" directly; (3) separate quiet nights from busy ones: does the
  hit rate fall on nights with 20+ picks (more moves on thin news)? A calculated version of "bad nights" without a cap.

## 2026-10-28 ~10:55 AM, Run 5 (CEO; Matt: Pinnacle as judge on alt lines)
- Pinnacle posts NO alt lines, so each HR alt rung was judged against Pinnacle's main line converted with our stat distributions (an
  estimate). One snapshot, 3 games (Oct 26 alt probe). HR alt overs -200..+200: n 102, median -10.8%, 5 >= +3% (all points), graded
  42-60 -16.9u. HR overs on Pinnacle's exact line: median -7.0%, 0 >= +3%. All 35 alt rungs >= +3% vs converted Pinnacle: 24-11 but
  -3.8u (mostly -200 to -550 favorites, outside Matt's -200 limit; low points rungs are where the conversion is least reliable).
  Verdict: no case for alt lines. Testing more needs nightly alt pulls (+4 credits a game per read), not in the November budget.

## 2026-10-28 ~10:45 AM, Run 4 (CEO)
- F8 (bet toward other books' line move when HR keeps its line): 19-31, -14.6u on 50 in discovery. Price check agrees: HR's price at its
  old line was already ~5.5% worse than the fair price at that line (HR re-juices instead of moving the line). F8b fade: 31-19, +6.5u,
  post-hoc. Today's runs tried ~20 slices on 3 nights; expect 1-2 to look good by chance. Forward nights decide.

## 2026-10-28 ~10:30 AM, Run 3 (CEO)
- Pinnacle moved >= 2 pts between reads 46 times in 3 nights; 16 of those the other books didn't follow (median < 1 pt). Betting the
  side Pinnacle moved toward, at Hard Rock: 11-5, +4.45u. 16 bets = could easily be luck (11-5 vs ~50% is p ~0.1). Registered F7 forward.

## 2026-10-28 ~10:20 AM, Run 2 (CEO; Matt: find it by comparing books before any model)
- Pinnacle alone: 6 distinct sides >= +2% in 3 nights (only 1 >= +3%, Reaves U23.5 pts -120, lost), all unders, graded 5-1.
  Against the 8-9 book median the same sides were -0.6% to -4.4%: Pinnacle was the outlier, not Hard Rock.
- Each book alone as the judge: <= 0.9% of sides clear +3%, every book's median -6.1 to -6.5%. No single book is a better judge.
- Pinnacle moves, Hard Rock doesn't: 9 of 1,360 read pairs; 1 cleared +2% (Collins U15.5, W).
Verdict: book comparison finds nothing bettable yet; F2b and F6 tracked forward. Code: research/code/run2_books.py.

## 2026-10-28 ~10:30 AM, Run 1 (CEO as Researcher, set up the role)
Matt: 0 picks in 2+ full nights, "figure it out". Data: shadow log Oct 25-27 (3,318 sides with >= 4 books on Hard Rock's line).
- R1: Hard Rock sits a steady ~6% below the market on every market, read, band and side. Best side +2.9% (bar +3%). Zero
  qualifying. Threes are not softer (median -5.8%).
- R2: vs Pinnacle alone, 2 points sides cleared +3% in 3 nights (median still -6.2%).
- R3: Hard Rock re-prices with the market (1 stale event in 2,198 pairs): no "slow book" edge at 20-45 min spacing.
Verdict: the main-line Gap + Guard rule has nothing to bet at Hard Rock NBA. Not a bug: Hard Rock's NBA props are priced at
market with ~6-7% hold. Next: F1 model disagreement, F2 Pinnacle-only, F3 injury-news reaction (all forward from tonight).
Blocker for anything faster than weeks: no historical NBA prop prices (paid; Matt's call).

