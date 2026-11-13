# HYPOTHESES.md (NBA). Register before scoring. Status: open / forward / failed / candidate / live.

## Run 1 (2026-10-28, CEO as Researcher; descriptive, discovery nights Oct 25-27, nothing here can pass)
- R1 Gap distribution: Hard Rock main-line EV vs the median de-vigged fair of >= 4 books on the same line, by market, read,
  price band, side. Result: 3,318 sides, median -6.2%, 90th pct -3.8%, best +2.9%, 0 at >= +3%, 1 at >= +2%. Threes -5.8%
  median (no better). Unders -5.5% vs overs -6.9%; plus-money -100..+120 best band (median -5.7%, 6 of 612 >= 0). STATUS: done.
- R2 Market = Pinnacle alone (same line): 2,024 sides, median -6.2%, 27 >= 0, 10 >= +2%, 2 >= +3% (both points). STATUS: forward (F2).
- R3 Hard Rock stale prices (market moved >= 3 pts between consecutive reads, HR price unchanged): 1 event in 2,198 pairs; HR
  re-priced 29% of pairs. Hard Rock tracks the market on NBA props. STATUS: done (no lag edge at our read spacing).

## Forward ideas (registered 2026-10-28, scored from the night of 2026-10-28 on; discovery nights don't count)
- F1 Model disagreement: bet the side where our stat model's chance exceeds the market fair by >= X pts (X = 4, 6, 8), price
  -200..+200, at the C read. Metric: ROI at HR price, CLV. Prior from NHL: model-only rules lost (NHL TEAM.md item 20).
- F2 Pinnacle-only market: R2 rule (HR EV >= +3% vs Pinnacle fair, same line), C or D read. Metric: ROI, CLV vs D-read median.
  F2b same at >= +2% (Run 2 discovery: 6 distinct sides Oct 25-27, all unders, 5 points + 1 assists, graded 5-1; noise-size).
- F3 Injury-news reaction: when a top-7 rotation player is newly listed Out between two reads, teammates' lines on Hard Rock vs
  the other books at the next read (does HR move later than the median?). Metric: gap EV at the first read after news.
- F4 Opening read: the 11 AM A read vs the market (Run 1's best side was at A). Metric: gap distribution at A, forward.
- F5 Plus-money unders, -100..+120, best gap side per player (Run 1's least-bad band). Metric: ROI, CLV.

## Run 2 (2026-10-28 ~10:20 AM, CEO; Matt: compare books before any model)
- R4 Each single book as the only judge (latest B/C/D read, same line, -200..+200): every book median -6.1% to -6.5%; sides >= +3%:
  DraftKings 7 (0.8%), BetRivers 7, Novig 6, BetMGM 4, ProphetX 3, BetOnline 2, FanDuel 0, ESPN Bet 0, Pinnacle 0 (at the latest
  read). STATUS: done (one book's own errors, not Hard Rock's).
- F6 Pinnacle-move lag: between consecutive reads Pinnacle's fair moves >= 2 pts toward a side and Hard Rock's price does not move;
  bet that side at Hard Rock if EV vs the new Pinnacle fair >= +2%. Discovery: 9 of 1,360 pairs moved this way, 1 >= +2% (W).
  STATUS: forward from 2026-10-28.

## Run 3 (2026-10-28 ~10:30 AM, CEO; Matt: how many 'Pinnacle moves alone' examples?)
- F7 Follow Pinnacle's solo move: between two consecutive reads Pinnacle's fair moves >= 2 pts toward a side while the other books'
  median moves < 1 pt that way; bet that side at Hard Rock's price on the later read (no EV filter). Discovery Oct 25-27: 46 Pinnacle
  moves >= 2 pts, 16 alone, graded 11-5, +4.45u at HR prices; 0 of 16 were +2% vs Pinnacle's new number at HR's price.
  STATUS: forward from 2026-10-28 (discovery nights don't count). Code: research/code/run3_pin_alone.py.
- F7b Follow Pinnacle's solo LINE move (its main line changes, <= 1/3 of the other books' lines change): bet the direction it moved at
  Hard Rock's main line. Discovery: Pinnacle moved its line on only 1.7% of checks (19 times; HR 6.9%, DraftKings 12.9%); 7 solo,
  graded 3-4, -1.66u. F7 (price-only moves, same line) is the main idea. STATUS: forward from 2026-10-28.

## Run 4 (2026-10-28 ~10:45 AM, CEO; Matt: other books move the line, Hard Rock keeps its line - bet that direction?)
- F8 Follow a line move Hard Rock didn't make: between consecutive reads >= 2 of the 7 sportsbooks move their main line the same way,
  none the other way, Hard Rock keeps its line; bet the move's direction (over if lines went up) at HR's line and later price, first
  time per player/market/night. Discovery Oct 25-27: 50 bets, 19-31, -14.63u; HR odds unchanged 8-19, HR odds juiced 11-12; EV vs the
  fair at HR's line median -5.5%, 0 of 49 >= +3%. STATUS: failed in discovery (kept forward only as the mirror of F8b).
- F8b FADE that move (the opposite side at HR's line and price, same moments): discovery 31-19, +6.51u on 50. Post-hoc (found by
  flipping a loser after ~20 slices tried today), so treat as a lead only. STATUS: forward from 2026-10-28.

## Run 7 (2026-10-29 ~7:45 AM, CEO as Researcher; Matt: fewer picks a day by a CALCULATED method, no hard caps)
Matt's constraint: NO fixed limits (no max per night, per game or per player). A pick is cut only because a computed score says it
is a worse bet over the long run; a big night stays big if every pick scores well, a thin night stays thin. The goal is the same
as the judging rule: picks that hit at the posted price. Fewer is fine, worse is not.
Population: every Pinnacle >= 2 pt move at a B/C/D flag read that passed the live v2.1 base (Hard Rock same line both reads, others
< 2 pts, >= 4 other books, price -200..+200), one per player/market/night, BEFORE the v2.2 gap gate, nights Oct 25-28 (discovery
only: nothing here can pass). The live picks are the subset that also passed the v2.2 gap. Result = W/L at Hard Rock's frozen price.
Each score below is a number computed from data available at the read; the cut is "score >= bar" where the bar comes from a formula
or from the OTHER nights (leave-one-night-out), never from looking at the night being judged.
- S1 Price edge vs Pinnacle: EV of Hard Rock's price at Pinnacle's NEW fair chance (`ev_vs_pin`). Bar: >= 0%, then >= +2% (the
  break-even bars), plus the leave-night-out best bar.
- S2 Net Pinnacle edge after noise: Pinnacle's new fair minus Hard Rock's break-even, minus one standard error of a de-vigged
  two-sided price (1.5 pts, set from how much Pinnacle's fair jumps between consecutive reads when nothing happens). Keep if > 0.
- S3 Move strength: Pinnacle's move size in pts divided by the move size the other books made (bigger lead over the crowd, same
  direction). Bar by leave-night-out.
- S4 Cell track record: hit rate minus break-even of the pick's cell (market x side) on the OTHER nights, shrunk to zero with
  k = 20 bets (Bayesian shrinkage). Keep if the shrunk edge > 0. Also tested: price band (plus money / -100..-130 / -131..-200).
- S5 Overlap discount: picks in one game that ride the same game script (same team's players all overs, or both teams' unders) are one
  bet, not many. Score = S1 divided by sqrt(number of overlapping picks in that game and direction). A calculated discount, not a cap:
  a lone strong pick is untouched.
- S6 Model agreement (research only, NOT a product change; Matt said no live tag): our stat model's chance for the side is not
  below Pinnacle's new fair by more than 5 pts. Registered because the 5-pt version looked good in discovery on 43 bets; it is a lead.
- S7 Composite = the sum of the standardized S1, S3 and S4 (equal weights, no fitting). Keep the top group above the bar.
Metric per score and bar: kept n, W-L, ROI at the posted price, share of picks cut, ROI of the CUT group (must be lower than the kept
group or the score is not selecting). Plus a shuffle placebo (same count cut at random, 2,000 draws) and the leave-night-out result.
Forward: scored from the night of 2026-10-29. Pass bar as RESEARCH.md rule 4 (n >= 150 graded, kept-group ROI > 0, 90% game-clustered
bootstrap lower bound > 0, and kept ROI above the cut-group ROI).

### Run 7 results (2026-10-29 ~8:10 AM, discovery Oct 25-28, 74 bets; full write-up in LOG.md)
- S1 >= 0%: kept 16 12-4 +44.5%, cut 58 32-26 +0.7% (placebo p 0.05; live subset 0.16). STATUS: forward (F9). S1 >= +2%: 4 bets, too few.
- S2: keeps 0 of 74 (Hard Rock's price is worse than Pinnacle's new fair on nearly every pick). STATUS: done, informative only.
- S3, S5: no selection (cut groups as good or better). STATUS: failed in discovery. S4/S4b/S7: inverse. STATUS: failed.
- S6: kept 47 14.0% vs cut 3.5% on all, 31.5% vs 20.9% on live (p 0.35). STATUS: open lead, research only (no live tag, Matt 10-29).
- F9 (forward from 2026-10-29): the picks the live rule makes with ev_vs_pin >= 0 vs the rest, from the shadow `solo` rows
  (`ev_vs_pin`, graded from box scores). Metric: ROI at the posted price for each group, CLV (frozen price vs the D-read Pinnacle
  fair), games-clustered 90% bootstrap, shuffle placebo. Pass bar: RESEARCH.md rule 4 on the S1 >= 0 group AND its ROI above the
  rest. At ~4 bets a night that group reaches 150 bets in about 5 weeks (early Dec); the 2026-11-25 checkpoint gets a first read.

## Run 8 (2026-11-09 night, Researcher; Matt 2026-11-09: "line movements, book movements for both NHL and NBA. Expand to NBA.")
Registered before any of these were scored. Not committed first (this run may not commit; the CEO commits), so the order is on trust.
What NHL research does on moves that NBA did not: closing-line value on every forward idea (NHL bar: mean CLV > 0), a re-scorer for
every registered forward idea (research/code/fwd/run_all.sh -> fwd/scores.md), early read vs late read (Q6, Q15, Q16, Q21), flag
early / bet late (Q16b), Hard Rock stale events and minutes to re-price after news (Q2-desc, shadow `stale_events`), Hard Rock's own
open-to-close move (R10), Pinnacle agrees / disagrees (Q22), Pinnacle steam (Q13, Q19), and a kill gate on open-to-close movement.
NBA had: R3 / F6 Hard Rock lag (3 nights), F7 / F7b / F8 / F8b solo and line moves (3 nights), Run 7 scores (4 nights). None re-scored
since Oct 29, no CLV on the Record, no size / timing / side / reversal splits.

Data for all M ideas: `data/odds/<date>.json` (Hard Rock + 9 books: Pinnacle, DraftKings, FanDuel, BetMGM, BetRivers, ESPN Bet, BetOnline,
Novig, ProphetX; 4 markets; reads A 11 AM, B ~90, C ~45, D ~20 min before tip), `data/record/events.jsonl` (the live Record), box
scores for grading. 15 nights stored, Oct 25 - Nov 9 (no Nov 3; Oct 25, Nov 1-2 have no A read). "Close" = the D read (~20 min before
tip): the last price stored. There is no true closing price in the repo.
MOVES population (same for M2-M7): consecutive reads of a game (A->B, B->C, C->D); Pinnacle two-sided on the same line both reads
(hold 0-15%), its de-vigged chance moved >= 2 pts; Hard Rock two-sided on that line on both reads; bet the side Pinnacle moved toward
at Hard Rock's later-read price, -200..+200; first time per player/market/night. Graded like the Record. Each split is also shown on
FAIR = the subset with Hard Rock's price at or better than Pinnacle's new fair (the live v2.6 gate) and on the live Record itself.
Discovery = every night through 2026-11-09 (the Record was already seen). Forward counts from the night of 2026-11-10.
Pass bar for every M idea (RESEARCH.md rule 4): the kept group n >= 150 graded forward, ROI > 0 at Hard Rock's price with the 90%
game-clustered bootstrap lower bound > 0, mean CLV vs the D-read Pinnacle fair > 0, and for a split the kept group's ROI above the
other group's. 7 ideas, ~20 groups: expect 1-2 to look good by luck.
- M1 Closing-line value of every shown pick. CLV_pin = Pinnacle's de-vigged chance for the side at the D read (same line) x frozen
  decimal price - 1. CLV_hr = frozen decimal / Hard Rock's D-read decimal on the same side and line - 1 (above 0 = Hard Rock closed
  shorter than the price we showed). Picks made at the D read have no later price and are left out (counted). Metric: mean and
  median CLV, share > 0, and W-L / units of CLV > 0 picks vs CLV <= 0 picks. Sample: every Record pick; 150 graded with a later read.
- M2 Hard Rock lag. MOVES split by what Hard Rock's price on that side did between the two reads: unchanged (stale) / shortened
  (followed) / lengthened (went the other way). Bet the stale ones. M2b: the OTHER books lead: median de-vigged move of the non-Pinnacle
  books (>= 4 books on the line both reads) >= 2 pts, Hard Rock's price unchanged, Pinnacle not required; bet that side at Hard Rock.
  Metric: W-L, units, CLV_pin. Sample: 150 stale bets (M2), 150 (M2b).
- M3 Consensus move vs Pinnacle-only move. MOVES split by the other books' median move the same way: < 1 pt (solo) / >= 1 pt
  (consensus), and by how many of them moved >= 1 pt that way: 0-1 / 2-4 / 5+. Sample: 150 in each of solo and consensus.
- M4 Move size bands: Pinnacle's move 2-3 / 3-4 / 4+ pts. (The live Record's 2-3 pt band is what the Sharp is watching to 15 bets.)
  Sample: 150 in the 2-3 band; the question is whether 2-3 is worse than 3+.
- M5 Move timing: the window the move happened in: 11 AM -> 90 min / 90 -> 45 / 45 -> 20 (and "last 90 min" = the last two together).
  Sample: 150 per group (morning vs last 90 min).
- M6 Reverse move after we post, as a pull signal. For each bet with a later read: Pinnacle's chance for the side at the NEXT read
  moved back >= 1 pt (reversed) / stayed within 1 pt / ran on >= 1 pt more. Metric: W-L and units per group at the frozen price. A pull
  rule would only be proposed if reversed picks lose money AND the rest stay ahead. Sample: 60 reversed bets (they are rare).
- M7 Unders vs overs. MOVES and the Record split by side. Sample: 150 per side.
Code: research/code/run8_moves.py (one script scores M1-M7 on every stored night; re-run it each run).

## Run Auto (2026-11-11, CEO; Matt: "rescore movement should be automatic nightly, at least 1 new hypothesis a day")
Automated nightly hypothesis tester. Each night one variant is selected from AH1-AH15 (round-robin), scored against all
stored nights (discovery through 2026-11-09, forward from 2026-11-10), and appended to LOG.md. Base population = same MOVES
as Run 8 (Pinnacle 2+ pt move, Hard Rock on line, -200..+200, 1/player/market/night). Code: research/code/auto_hypothesis.py.
Pass bar for all: rule 4 (n >= 150 graded forward, ROI > 0, 90% game-clustered bootstrap lower bound > 0, CLV > 0).
- AH1  Large unders: MOVES where Pinnacle move >= 4 pts AND side = under. Metric: W-L, ROI, CLV_pin. Hypothesis: large
  moves on unders may carry stronger signal (run8 M4+M7 combination).
- AH2  Late + large: MOVES where window is 90->45 or 45->20 AND move >= 3 pts. Metric: W-L, ROI, CLV_pin.
- AH3  Solo + late: MOVES where others < 1 pt (Pinnacle solo) AND window is last 90 min. Metric: W-L, ROI, CLV_pin.
- AH4  Stale HR + FAIR: MOVES where HR price unchanged AND ev_pin >= 0. Metric: W-L, ROI, CLV_pin.
- AH5  Large solo (4+ pt): MOVES where move >= 4 pts AND others < 1 pt. Metric: W-L, ROI, CLV_pin.
- AH6  90->45 window: MOVES in the 90->45 minute window only. Metric: W-L, ROI, CLV_pin.
- AH7  45->20 window: MOVES in the 45->20 minute window only. Metric: W-L, ROI, CLV_pin.
- AH8  Unders + late: MOVES where side = under AND window is last 90 min. Metric: W-L, ROI, CLV_pin.
- AH9  2-4 books following (consensus middle band): MOVES where 2-4 other books moved >= 1 pt same way. Metric: W-L, ROI.
  Prior: M3 found this group won +12.5% in discovery on 201 bets; forward test here.
- AH10 Large unders by band: MOVES where side = under AND move >= 3 pts. Sub-split 3-4 vs 4+. Metric: W-L, ROI, CLV_pin.
- AH11 Morning by side: MOVES in 11AM->90 window, split by side. Metric: W-L, ROI, CLV_pin.
- AH12 Solo large (3+ pt): MOVES where move >= 3 pts AND others < 1 pt. Metric: W-L, ROI, CLV_pin.
- AH13 Stale HR unders: MOVES where HR price unchanged AND side = under. Metric: W-L, ROI, CLV_pin.
- AH14 Small FAIR moves: MOVES where move 2-3 pts AND ev_pin >= 0. Metric: W-L, ROI, CLV_pin.
  Prior: M4 found 2-3 pt band was the only losing band in the Record (15 bets); this is the FAIR subset question.
- AH15 Late FAIR: MOVES where window is last 90 min AND ev_pin >= 0. Metric: W-L, ROI, CLV_pin.

## Run 9 (2026-11-13, Researcher; Matt: books, not players). Registered before any of these were tested.
Discovery only: every stored night through 2026-11-12 was already seen by the AH series, so nothing below can pass. Forward collection starts with the 2026-11-13 reads. Code: to be written at research/code/run9/ (not built yet; see LOG 2026-11-13).

- BB1 Book agreement (dispersion). Reads B and C (about 90 and 45 min before tip) of data/odds. For each (game, player, market, line) where Hard Rock posts both sides on that line at -200..+200 and at least 5 other books have both sides on the same line (hold 0-15%, last update < 60 min before the read): each book's proportional no-vig over chance; spread = max minus min; consensus = median. BB1a TIGHT: bet the side where Hard Rock EV vs consensus >= 0 AND spread <= 2 pts. BB1b DISPUTED: same, spread >= 4 pts. First qualifying read per player/market/line/night. 1u flat at Hard Rock's price; graded from box scores (DNP = void, whole-number line exact = push). CLV = frozen price vs consensus fair at the last read. 2 variants. Status: DISCOVERY, judged forward from 2026-11-13. Forward bar = RESEARCH.md rule 4 (n >= 150 graded, ROI > 0, 90% game-clustered CI > 0, CLV > 0).
