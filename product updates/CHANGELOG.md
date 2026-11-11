# Hot Prop Homies — Product Changelog

All changes are listed newest-first. Each entry includes the date, what changed, why, and which files were affected.

---

## 2026-11-11

### All-Mode Record — Unified Combined View
**Files:** `index.html`

Matt's directive: "All mode should be a combined view of ALL sports — not 2 separate codebases rendered one after the other."

**What changed:**
1. **Unified Record tab in All mode** — `renderRecordAll()` now renders one combined view: one scoreboard, one calendar (all picks from both sports merged by date), and one recent-picks list (entries interleaved chronologically). The old two-sport `<details>` accordion is gone.
2. **Sport badge on record entries** — `entryRow()` now shows a small NBA/NHL chip (red/blue) on each pick row when `e.sport` is set. In single-sport mode entries never carry `e.sport` so the badge never appears there — no regression.
3. **Calendar metrics** — Every calendar cell now shows W-L (e.g., "2-1") between the day number and units delta, across both single-sport and All modes. Previously the cell only showed the day number and units.

**Single-sport mode (NHL-only, NBA-only) is unchanged.** The Picks and Live tabs are unchanged.

---

### NBA Research Automation — Nightly Rescore + Auto Hypothesis
**Files:** `sports/nba/scripts/run.py`, `sports/nba/research/code/auto_hypothesis.py` (new), `sports/nba/research/HYPOTHESES.md`, `sports/nba/data/research/.gitkeep` (new)

Implements Matt's directive: "Rescore movement should be automatic nightly. With at least 1 new hypothesis a day being tested."

**What was added:**
1. **Nightly rescore** — `run.py` now calls `run8_moves.py` once per slate day after grading and publishing. Output (M1-M7 on all stored nights) is saved to `data/research/moves_<date>.txt`. Non-blocking: failure does not stop the main pipeline.
2. **Auto hypothesis** — `auto_hypothesis.py` cycles through 15 pre-registered hypothesis variants (AH1-AH15) round-robin, one per night. Each variant is a sub-split or parameter variation on the M1-M7 moves population (e.g., large unders, solo+late, stale HR+FAIR). It scores discovery and forward W-L/ROI/CLV, then prepends a compact entry to `research/LOG.md`. Pass bar: rule 4 (n >= 150 graded forward, ROI > 0, 90% CI > 0, CLV > 0).
3. **15 hypotheses registered** in `HYPOTHESES.md` Run Auto section: AH1 large unders, AH2 late+large, AH3 solo+late, AH4 stale+FAIR, AH5 large solo, AH6 90->45 window, AH7 45->20 window, AH8 unders+late, AH9 2-4 books (prior: +12.5% in discovery), AH10 large unders by band, AH11 morning by side, AH12 solo large, AH13 stale+unders, AH14 small FAIR moves, AH15 late FAIR.

Both steps run once per day (state file `data/research/research_state.json` prevents double-running on the same slate). No extra API credits used — stored odds data only.

---

### Workflow Deduplication — Reusable `sport-run.yml`
**Files:** `.github/workflows/sport-run.yml` (new), `.github/workflows/nba-run.yml`, `.github/workflows/nhl-run.yml`

Extracted shared execution logic from both timer workflows into a single reusable `workflow_call` workflow (`sport-run.yml`). `nba-run.yml` and `nhl-run.yml` are now thin ~27-line callers that own only what is sport-specific: cron offset, push paths, and secret name mapping. The reusable workflow handles checkout, Python setup, the loop step, and the self-dispatch step.

- **Maintenance surface cut in half**: a step logic change is one edit, not two.
- **Per-sport overrides are obvious and easy**: everything sport-specific lives at the top of each caller file.
- **Independent configurability preserved**: changing NBA cron, adding an NBA-only step, or wiring a new NBA secret requires editing only `nba-run.yml`.
- **No behavior change**: both timers retain their existing cron offsets (`:17` NBA, `:23` NHL), push-path triggers, concurrency groups, and secret bindings.

---

### Code Cleanup — Untangle Pass 1 (Python)
**Commits:** `37b05cb`

- **Removed misleading import alias** `import lineups as rotowire` in `sports/nba/scripts/run.py`. The lineups module has used ESPN data since before the combined repo was created; the "rotowire" alias was a leftover from an earlier data source and confused anyone reading the file. All call sites updated to `lineups.*`; the data key `"rotowire"` in published JSON is preserved.
- **Added SYNC markers** to `fail_status.py` and `guard_record.py` in both sports. These files are intentionally duplicated (GitHub Actions sparse-checkout prevents sharing); the markers make that obvious so future editors know to update both copies.
- **Documented gap_guard key-path difference** in both `common.py` files. NBA stores `gap_guard` at the top level of `rules.json`; NHL stores it under `ops.gap_guard`. Both are correct for their own config — the comment prevents a future agent from accidentally using the wrong path when modifying one sport.

**Files:** `sports/nba/scripts/run.py`, `sports/nba/scripts/common.py`, `sports/nba/scripts/fail_status.py`, `sports/nba/scripts/guard_record.py`, `sports/nhl/scripts/common.py`, `sports/nhl/scripts/fail_status.py`, `sports/nhl/scripts/guard_record.py`

---

### Code Cleanup — Untangle Pass 2 (index.html)
**Commits:** `6ca3d4d`

- **Removed dead variable** `var UI_DEF = UI_DEFS.nba` (line 403). The variable was assigned but never read — `uiVal()` reads directly from `UI_DEFS[S.sport]`.
- **Fixed uiVal() fallback**: was `|| UI_DEFS.nba`, now `|| UI_DEFS.all`. The `all` entry already exists in `UI_DEFS` with the same stale timeout (30 min). Using `nba` as a fallback for unknown sport values was misleading.
- **Added inline comment** on the NHL-only `record/resets.json` fetch to make it clear NBA doesn't have Record resets yet.

**Files:** `index.html`

---

### QA Wording & Continuity Review
**Commits:** `67da6bd`  17 fixes

Sport-specific terminology was wrong throughout the page — the site was originally NBA-only and many NBA terms survived the merge into the combined site.

Key fixes:
- NHL games showed "Tipped off" (basketball term) → now shows "Dropped the puck"
- Quarters (Q1/Q2) and "Half" labels appeared for NHL games → now shows period numbers
- NBA stat market labels (rebounds, assists, 3-pointers) no longer appear in NHL UI text
- General wording and capitalization made consistent across both sports in the shared All-sport path

**Files:** `index.html`

---

### Live Tab Fix — NHL not updating in All mode
**Commits:** `0699716`

**Bug:** When the sport filter was set to "All", the Live tab only polled the NBA feed (ESPN basketball). NHL picks in the Live tab showed no live stats or score updates. Switching to the NHL filter worked correctly.

**Root cause:** `livePoll()` in `index.html` branched on `S.sport === 'nhl' ? pollNHL : pollESPN`. In "all" mode `S.sport === 'all'`, which fell into the NBA-only else branch.

**Fix:** When `S.sport === 'all'`, the plan is now split by sport (`subPlan()`) and both `pollNHL` and `pollESPN/pollNBA` run in parallel. Results (games, stats, done) are merged before rendering.

**Files:** `index.html`

---

## 2026-11-10 and earlier (from previous sessions)

### Combined Site — Hot Prop Homies repo created
- Single unified repo `MSasportas/Hot-Prop-Homies` replaced the two standalone repos
- Live page: https://msasportas.github.io/Hot-Prop-Homies/
- Both sports run under `sports/nba/` and `sports/nhl/` with one shared `index.html`
- The two standalone repos (`prop-check-nhl`, `prop-check-nba`) should have GitHub Actions disabled by Matt (Settings → Actions → General → Disable)

### Remote Control Enabled
- CEO session accessible from Matt's phone via Claude AI app Remote Control feature

### App Icon — Hot Prop Homies logo
- Home-screen icon set to the hooded flame figure with 4-sport shield
- iOS: `icons/apple-touch-icon-v3.png` (versioned to bust cache)
- Root-level fallback files added for iOS home screen detection

### Lab Tab — All mode now shows both sports
**Commit:** earlier session  
Both `sports/nba/config/lab.json` and `sports/nhl/config/lab.json` are fetched in All mode. Each idea is tagged with its sport (`_sp`) and prefixed with "NBA ·" or "NHL ·" in the title. Lab was previously empty in All mode.

### Live Tab — 2-column layout
Picks on the Live tab now render in a 2-column CSS grid (`.lvlist`) so more fits on the phone screen.

### Picks Tab — count badge
A red pill badge on the Picks tab icon shows the number of open picks. Hidden when zero.

### NHL Hard Rock button fix
NHL picks were missing the Hard Rock bet button. Fixed by extending `betRow()` to allow the `lineup` state and `p.graded` condition, and making `stateChip()` NHL-aware (`lineup`, `locked_unconfirmed`).

### NHL v3.5 guard — model agreement gate
New picks are only posted when `model_side >= break_even(price) + model_min_edge`. Failures are logged as veto events. Picks already shown are never pulled by the guard.  
**Config key:** `ops.gap_guard.thresholds.model_min_edge: 0.0`  
**Files:** `sports/nhl/scripts/engine.py`, `sports/nhl/scripts/paper.py`, `sports/nhl/scripts/guard_paper.py`, `sports/nhl/config/rules.json`

### guard_paper.py path fix (NHL)
`guard_paper.py` was using a git path without the `sports/nhl/` prefix, causing the CLV log to silently fail every run since the consolidation on Nov 5. Fixed by applying the same prefix helper used in `guard_record.py`.

### NBA Research expanded — line/book movements
Runs 8 and 9 added to NBA research log:
- **Run 8** (`run8_moves.py`): movement scorer — measures how much books move after Pinnacle
- **Run 9** (`run9_nhl_port.py`): tested whether NHL's gap rule works on NBA data. Result: No. Only 2 sides ever cleared the bar in 15 nights.

### NHL Research — Run 22
Tested whether NBA's Pinnacle-move rule works on NHL data. Result: No. 27 new bets 11-16, -5.55u.  
**File:** `sports/nhl/research/code/r22/jj22.py`

---

## Known Pending Items

| Item | Owner | Notes |
|---|---|---|
| Workflow deduplication (`nhl-run.yml` ≈ `nba-run.yml`) | Builder | The two timer files are near-identical; editing one means editing both. Low urgency — timers work fine. Own pass when convenient. |
| `stateChip()` restructure — NHL states patched over NBA base | Builder | Needs a rewrite, not a quick edit |
| NBA closing-price read (extra read ~2 min before tip) | Matt's call | ~850 credits/month; on hold until more keys available |
| NBA daily re-score of movement ideas (`run8_moves.py`) | Builder | Research script (Run 8); wire into nightly timer only when research says the signal is worth tracking live |

## Resolved Items

| Item | Resolved | Notes |
|---|---|---|
| Disable GitHub Actions on `prop-check-nhl` and `prop-check-nba` | 2026-11-11 | Done by Matt |
| NHL API key #1 invalid | 2026-11-11 | Was a paid key no longer in use — ignored |
| NBA credits tight end of November | 2026-11-11 | Matt added 4-5 new keys; alert Matt again if pool drops below 750 credits |
