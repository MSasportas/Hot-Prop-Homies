# Lab auto-retirement spec (Data Scientist, 2026-11-20)

SPEC ONLY, for the Engineer. A dead test retires on its own; a passing test is only ever handed to the Sharp.

## 0. Facts this builds on
- Tracks: `sports/{nba,nhl}/config/lab.json` -> `tests[]` with `id, title, rule, summary, stats, need, gate, discovery, base`. NBA has 27 tracks (need 150 for most; LVA1 40, LVA2 30, DM1 100, DM2 80, DM3 50, fast_checks 100). NHL has 21, all need 300, all read from `sports/nhl/research/fwd/lab.json` (written by `research/code/fwd/lab_export.py`) plus `q24.json`.
- Numbers: summary file block `summary[stats]` = `{w, l, push, void, pending, units, clv?}`. `units` is already graded at posted price, so ROI per bet = `units / (w + l)`. Hit rate vs break-even is NOT used (break-even moves with price).
- Consumers: Lab tab (`renderLab` in the root `index.html`) draws every entry in `tests[]`; HQ "Lab - on the radar" reads the same configs (`labCfg`, `hqGate`).
- `fast_checks` is a live trial of real Record picks: excluded from auto-retire (`no_auto_retire: true`).

## 1. Definitions
Per track: `k = w + l` (pushes and voids excluded), `u = units`, `roi = u / k`, `clv` = mean CLV if present (NBA AH/NP/DM/LVA blocks carry none today; NHL fwd blocks do).
Noise model: SD of one bet's unit result is about 1.0, so `se = 1 / sqrt(k)`.

**Fade tests are graded on the bet they imply.** A fade or mirror test (DM2, DM3, the NHL "fade" tracks) is tallied by its exporter as the OTHER side's bet: same line, Hard Rock's own posted price for that side, that side's own result. Its `units`, `w`, `l` and `clv` are therefore real bet-side numbers and `lab_retire.py` never flips a sign. Mirroring the tracked side's units assumed the opposite side pays the same price and ignored the vig (DM2: +24.36u mirrored, -26.4u real). A bet with no price, or worse than -200 (Matt's fixed rule), is skipped and counted in the block's `excluded`. NBA DM2 and DM3 also write one row per event to `data/research/lab_dm_bets.jsonl` (both prices, both results, `skip` when excluded); the block's `player_nights` counts distinct player-nights among the bets.

**CLV caveat.** The Lab's CLV is measured against the vig-free close, but Hard Rock's price carries its own vig. Betting both sides of one pair would show negative CLV on both, so `clv <= 0` is nearly automatic for a Hard Rock-priced track and the rule "retire needs `clv` missing or <= 0" barely filters. The rule is left as written: the Sharp and DS decide whether CLV should be measured against Hard Rock's own close or given a vig allowance.

## 2. Retire criteria
Retire when A or B holds and all guards pass.
- **A. Full-sample fail:** `k >= need` AND `roi + 1.645*se < 0` (one-sided 95%: even the optimistic end is below break-even) AND (`clv` missing OR `clv <= 0`).
- **B. Early futility:** `k >= max(30, ceil(need/2))` AND `roi + 2.33*se < 0` (one-sided 99%) AND (`clv` missing OR `clv <= 0`).

Reference cutoffs (retire if ROI is below):

| k | Test | ROI cutoff |
|---|---|---|
| 30 | A (LVA2) | -30% |
| 50 | A (DM3) | -23% |
| 75 | B (need 150) | -27% |
| 100 | A (DM1, fast) | -16% |
| 150 | A (most NBA) | -13.4% |
| 150 | B (NHL half-way) | -19% |
| 300 | A (all NHL) | -9.5% |

Why this conservative: about 48 tracks, many correlated (AH1-15 are filters of the same live picks), so a loose cutoff will kill real edges by chance. Requiring the upper 95% bound below zero only kills clearly negative tracks. A CLV above zero vetoes retirement. Never retire on hit rate, a streak, or `units < 0` alone.

Guards:
1. Skip the run if `pending > 0.25 * k` (late grades can flip it).
2. Recompute from the summary every run; the only carried state is `fail_streak`.
3. Retire only when the fail condition is true on TWO consecutive nightly runs (`fail_streak >= 2`, in `config/lab_state.json`, owned by the script). Any non-fail run resets it.
4. Max 5 retirements per sport per run (a bad data night cannot wipe the Lab).
5. Unreadable or missing summary / `stats` key: do nothing, log a warning.

## 3. Passing and in-between tracks
- **Pass:** `k >= need` AND `u > 0` AND (`clv > 0` when CLV exists; otherwise `roi - 1.645*se > 0`). Action: set `status: "ready_for_sharp"` and `ready_at` on the entry, append a `ready` event to the archive (section 4), show a "Ready for Sharp" badge. It stays on the Lab. NEVER edit live rules; the Sharp reviews with a DS sample note and Matt says go, per the existing `gate` text.
- **Inconclusive:** `k >= need`, neither pass nor fail: keep running to a hard cap of `2 x need`. At the cap, if still not a pass, retire with `reason: "inconclusive_cap"`.

## 4. Archive (append-only)
- `sports/{nba,nhl}/config/lab_retired.jsonl`, one line per event, never edited.
- Line: `{"ts", "event": "retired"|"ready", "id", "title", "rule", "summary", "stats", "need", "reason": "fail_full"|"fail_early"|"inconclusive_cap"|"stalled", "final": {w,l,push,void,pending,units,roi,clv,se}, "roi_upper95", "first_seen"}`.
- On `retired`: remove the entry from `lab.json` `tests[]` in the same write, set `retired_count` and `updated`. Idempotent: skip an `id` already retired. Ids are never reused.
- Summary files keep the block (history stays). Exporters (`lab_export.py`; NBA `lab_*.json` writers) should skip retired ids so the pipeline stops computing dead tracks.

## 5. Stalled tracks
Stalled = 45 days since `first_seen` AND `k < need/2` AND no new graded pick in 21 days. Retire with `reason: "stalled"` and final stats; the page says "ran out of picks", not "failed". `first_seen` is new and optional; backfill 2026-11-12 (Lab config date) when absent. `seasonal: true` on an entry exempts it.

## 6. Edge cases
- Push/void: excluded from `k` and ROI. If `void > 0.5*k`, log `data_quality`, do not retire on it.
- Ties: strict inequalities; at equality keep running.
- `k < 30`: never evaluated.
- Correlated AH tracks: judged individually; the Sharp is told the set is correlated.
- Record reset by Matt: clears `lab_state.json` streaks only; the archive stays.

## 7. Engineer build list
1. New `scripts/lab_retire.py --sport {nba|nhl}` (stdlib only, one shared copy). Reads `config/lab.json`, each summary, `config/lab_state.json`; writes `lab.json`, `lab_retired.jsonl`, `lab_state.json`. Pure function `evaluate(track, block)` returning verdict and final stats so it is unit-testable.
2. Run once daily, as the last step after grading and summary refresh (NBA: after the `lab_*.json` writers; NHL: after `lab_export.py` in `run_all.sh`). Grades only change nightly; two-run confirmation makes the earliest retire 2 days.
3. Optional new `tests[]` fields: `first_seen`, `no_auto_retire` (true on `fast_checks`), `seasonal`, `status`, `ready_at`. Existing files stay valid.
4. Page (root `index.html`): retired tracks vanish automatically (they leave `tests[]`). Add one muted line at the Lab bottom, "N retired", shown only when `retired_count > 0`; tap expands a list (title, record, units, plain-words reason, date) from `lab_retired.jsonl`. "Ready for Sharp" badge on the tile. HQ "Lab - on the radar" lists only remaining entries plus the same one-line count. Check 380px: single line, no new tiles. `hqGate` already returns null for a missing id.
5. Tests for `evaluate`: the cutoff table; k=150 units -25 retires, -15 does not; CLV > 0 vetoes; pending > 25% skips; one-run fail does not retire; mass cap; idempotent rerun; `fast_checks` never retires.
6. Do not touch `data/record/` or live rules.

## 8. Today's picture (what fires first)
- NBA DM1: 31-43, -15.84u, k=74, roi -21.4%, need 100. Not yet (B needs ROI < -27% at 99%... actual bound +5.6%). At k=100 it retires if ROI is below -16%; about 2-3 weeks at the current rate.
- NBA DM2: 134-132, -8.88u, k=266, roi -3.3%, upper-95 +6.1%: not a fail. But k is already past its cap (2 x need = 160), so the first run would retire it as `inconclusive_cap`. Sharp should see this before launch; either accept the retirement or reset its `need` (DS suggests 300 given the flat record).
- NBA AH tracks: all k <= 31; nothing is judged for weeks. NP1-4: k = 0.
- NHL: not checked here, all need 300.

## Five-line summary
1. Judge on units/ROI at posted price only; `se = 1/sqrt(k)`, k = w+l, pushes/voids out.
2. Retire at k >= need when ROI + 1.645*se < 0 and CLV <= 0/missing; early futility at k >= max(30, need/2) with z 2.33.
3. Needs two consecutive nightly runs, max 5 per run, skip on pending-heavy or unreadable data; `fast_checks` exempt.
4. Pass (k >= need, units up, CLV > 0 or lower-95 ROI > 0) = "Ready for Sharp" badge only; inconclusive retires at 2 x need; stalled (45 days, none for 21) retires as "ran out of picks".
5. Retired tracks append to `config/lab_retired.jsonl` with final stats and reason, leave `lab.json`; the page shows only "N retired".
