# Live tab tiles: match Picks, never clip (spec)

Author: UX Expert. For: Engineer (build), QA (380 / 340 px sign-off). Spec only, no code.
Scope: root `index.html` (serves NBA + NHL + All). Lab "Today" live rows use the same card, so they get the fix too.
Matt's report (phone): Live tiles do not match Picks tiles, player names are cut off, scores are cut off.

Numbers and meanings do not change: same posted price, same W/L/HIT/LOST logic, same pips/meter thresholds, same sort order.

---

## 1. What is wrong today (reproduced)

Method: a copy of `origin/main:index.html` served locally with the `liveon` fixture, then the page's own `liveRow()` run on 12 real long names with live, OT, 2OT, 3-digit-score and final games, in a 380 and a 340 px viewport. The same names were run through the Picks `pickCard()` on the same page for comparison. Note: at 380 px the left tab rail takes ~55 px, so a tile is 144 px wide at 380 and 126 px at 340. Inner width after padding: Live today 126 / 108, Picks 122 / 104.

### 1a. Clipping, with causes

| What clips | Seen as | Why (CSS) |
|---|---|---|
| Player name, 12 of 12 long names at both widths | "Giannis Antetok...", "Shai Gilgeo...", "Nickeil ..." (340) | `.lv .nm` is `white-space:nowrap; overflow:hidden; text-overflow:ellipsis`, one line, 15 px, beside a 26 px photo. At 380 the name has 91 px, at 340 it has 73 px. It never tries a smaller size, never drops the photo or suffix, never stacks first/last, never wraps after a hyphen. |
| Game line, 12 of 12 at both widths | "Q2 3:45 · LAL 48-5…", "Final · LAL 131-128…", "Final (2OT) · NYK 140-1…" | `.lv .gs` is `nowrap; overflow:hidden; text-overflow:ellipsis`, status + score on ONE 12.5 px line in 124 px (380) / 106 px (340). Needed width: 139 to 181 px. The score is the part that gets cut, and it is the part Matt wants. |
| No-feed state | "Started 8:00 PM · …" (matchup replaced by "…") | Same rule. The matchup (own-team pill + opp) is the part cut. |
| Bet text | "Over 1.5 / threes" 2 lines at 380, "Over / 27.5 / points" 3 lines at 340 | Live prints `p.bet` (long form) instead of `betShort(p)` ("O 27.5 pts") that Picks uses. |
| Progress text | "14 / 27.5 pts, needs 14 more" wraps to 2 lines at 380 and 3 lines at 340 ("14 / 27.5 / pts, needs 14 / more") | `.trk2 .msg` is `flex:1 0 100%` with `overflow-wrap:anywhere`: it does not clip, but it breaks the number across lines, which reads as cut off. |
| Stamp (HIT / LOST / WON) | Pinned to the right of the meter, fine at 380; at 340 the meter squeezes to ~50 px | `flex:none` stamp + `flex:1 1 56px` meter. OK but cramped; moves to its own spot in the new layout. |

### 1b. Why the tiles do not match Picks

| Part | Picks tile (`.tile`) | Live tile (`.lv`) today |
|---|---|---|
| Class / shell | `.tile`, padding 10/10/9 | separate `.lv`, padding 9/9/8 |
| Name | stacked: first name 12 px muted over last name 15 px 600, `fitNames()` tiers (15/14/13 px, drop suffix, drop photo, initial, wrap after hyphen, ellipsis last) | one line 15 px 600, ellipsis |
| Photo | 26 px, same | 26 px, same, but the broken-image handler has a dead `.lv` "grid first column" branch (line ~757) |
| Bet | `betShort` 13.5 px mono | `p.bet` long form 13 px mono |
| Price | 21 px 600 mono, `--fg`, "No price" fallback | 14 px mono, `--muted` |
| Sport badge (All scope) | `.sp-badge` bottom right | none on the tile (separate section header) |
| Footer | `.ft` 11.5 px tags | `.gs` 12.5 px nowrap line |

Dead code to remove in the same pass: `.lv .nm`, `.lv .top`, `.lv .row2`, `.lv .bt`, `.lv .pp`, `.lv .hs`, `.lv .gs` rules and the `.lv` branch in `headshot()`'s error handler.

---

## 2. The design

One tile, two jobs. A Live tile IS a Picks tile (`class="tile lv"`): same shell, same photo, same stacked name with the same fit tiers, same bet line, same price. The only differences are the two things Live exists to show: a progress block (replaces the "chance vs price" line) and a game block (replaces the footer tags). Keep the dark / cyan / magenta Flame Night look. No new colors. No new motion.

### 2.1 Anatomy (top to bottom)

```
 TILE (.tile.lv)  padding 10 10 9, radius 8, border --line, bg --surface
 +------------------------------------------+
 | [photo 26]  first name   (12/14 muted)   |  1. TOP: tileTop() -- same as Picks, closed form
 |             Last name    (15/19 600)     |
 | O 27.5 pts                        -115   |  2. PRICE ROW: tilePrice() -- same as Picks
 | [=====|====----]  [HIT]                  |  3. TRACKER: bar/pips + stamp
 | 14 / 27.5 pts                            |     number line (never wraps)
 | needs 14 more                            |     helper line (muted)
 | TOO LATE                            NBA  |  4. FOOT TAGS (only when needed)
 | Q2 3:45                                  |  5. GAME: status (bold) over score
 | LAL 48 - 51 MIN                          |
 +------------------------------------------+
```

Order inside the tile is fixed; blocks 3 and 4 are optional. Block 5 is pinned to the bottom (`margin-top:auto`) so tiles in a row line up.

### 2.2 Block 1: TOP (shared, no new rules)

Use `tileTop(p, false)` exactly (closed form: `nameBlock(full, true)`, `.fn` + `.ln`, `data-first/last/core`). `fitNames()` already selects `.tile .nm[data-last]`, so Live tiles are fitted by the same function the moment they carry `.tile`. Tier order stays as Picks: 15 / 14 / 13 px, drop suffix (Jr, Sr, II, III, IV, V), drop photo, first name to an initial, wrap after a hyphen, ellipsis only as the last resort. Live tiles are not tappable and have no open state, so the open-tile name style and the select circle (`.ck`) never apply here. No NEW tag and no "Seen earlier" divider on Live.

Re-fit: Live re-paints every ~10 s; `fitNames()` already runs at the end of `render()`, plus on resize and when fonts load. Confirm the Live repaint path goes through `render()` (or call `fitNames()` + the new `fitLines()` after any Live-only repaint). A name must never flash clipped after an update.

### 2.3 Block 2: PRICE ROW (shared)

Use `tilePrice(p)`: `betShort(p)` left (13.5 px mono, wraps at spaces, `overflow-wrap:anywhere` as the safety), posted Hard Rock price right (21 px / 24 px 600 mono, `--fg`, nowrap). Same "No price" fallback (15 px muted). Final tiles: name and price dim to `--fg2` as today (`.lv.fin`). The price is the frozen posted price, same as Picks; do not recolor it by result (the stamp does that).

### 2.4 Block 3: TRACKER (live only)

Rows, tight (`margin-top:8px` before, `gap:4px` between):

- Row A: the tracker graphic left, stamp right.
  - Line under 6: pips, `.lv .pips{gap:3px}`, pip 11 px (as today).
  - Line 6 or more: meter, `flex:1 1 0; min-width:48px`, 8 px high (as today).
  - Stamp (`.stmp`, HIT / LOST / WON / PUSH / VOID) right-aligned, `flex:none`, 12 px 700 Plex Sans, letter-spacing .1em, colors unchanged (`.W` good, `.L` bad, neutral muted).
  - Row A may never wrap. If the graphic cannot keep 48 px beside the stamp, the stamp drops to its own right-aligned line under the graphic (this should not occur at 340: inner 104 = 48 + 6 + 50 for "LOST").
- Row B, the NUMBER line: `14 / 27.5 pts`. Font `600 16px/20px var(--num)`, `--fg` (final: `--fg2`). `white-space:nowrap`. Never wraps, never ellipsis. Fit rule (new helper, section 3): try 16 px, 14 px, 13 px; if still too wide at 13 px, drop the noun ("14 / 27.5"). 13 px is the minimum. Worked widths (IBM Plex Mono is 0.6 em per character, tile inner 104 px at 340): "14 / 27.5 pts" is 13 chars = 101 px at 13 px, fits; "9 / 7.5 reb" fits at 14 px. "27 / 28.5" fits at 16 px (9 chars = 86 px). At 380 (inner 122) "14 / 27.5 pts" fits at 14 px.
- Row C, the HELPER line, only while the pick is still open: `12px/16px var(--body)`, `--muted`, nowrap. Copy tiers (pick the first that fits, never wrap): over: "needs 14 more" then "14 to go"; under: "2 to spare" then "2 left". Under that has lost shows no helper (stamp says LOST). Over that has hit shows no helper (stamp says HIT).
- No stats / no number yet: Row B shows the status copy below instead of a number, same font as the helper line but `--fg2` and 13 px; pips/meter empty as today.

Tracker copy (exact):

| State | Row B / C |
|---|---|
| Live, has stat | "14 / 27.5 pts" + "needs 14 more" (over) or "2 to spare" (under) |
| Hit (over, stat past line) | "29 / 27.5 pts", stamp HIT, no helper |
| Lost early (under, stat past line) | "29 / 27.5 pts", stamp LOST, no helper |
| Final, graded | actual from the Record, e.g. "31 / 27.5 pts", stamp WON / LOST / PUSH / VOID |
| Void | Row B shows `r.actual` or "Void", stamp VOID |
| Waiting on feed | "Getting stats..." (existing "Getting live stats..." is too long for 340; shorten) |
| Feed failed | "Stats unavailable" (was "Live stats unavailable") |
| No stat yet | "No stats yet" |
| Not played yet / DNP | "Not played yet" live, "Did not play" final |

Short copy rule: if a row of status text does not fit at 13 px, use the shorter form listed; there is never a third line.

### 2.5 Block 4: FOOT TAGS (only when something to say)

Same `.ft` row as Picks (`flex-wrap`, gap 4 px 8 px, 11.5 px / 15 px). Contents, left to right:
- Pulled pick that Live shows (the "TOO LATE, then counts on the Record" case, `p.pulled` set and counted): tag `TOO LATE` in `--warn`, 700, letter-spacing .06em, `title="Came off the board before tip. Still counts on the Record."`. Quiet text tag, not the solid navy stamp (that stamp is for the board; here the pick is simply a live pick with a note).
- Sport badge, All scope only, `.sp-badge` pushed right with `margin-left:auto` (`.tile .ft .sp-badge` rule already does this).
If neither applies, omit the row entirely (no empty gap).

### 2.6 Block 5: GAME (live only) -- never ellipsis

Two lines, pinned bottom, `margin-top:auto; padding-top:8px`.

- Line 1, STATUS: `600 13px/17px var(--body)`, `--fg` (final: `--fg2`). Nowrap. Copy (exact):
  - Live: "Q2 3:45", "P2 14:05", "OT 1:02", "2OT 0:35", clock "0.4" as is.
  - Break: "Half" (NBA), "Intermission" (NHL), "End Q1", "End P2", "End OT".
  - Pre / waiting: "Starting".
  - Final: "Final", "Final (OT)", "Final (2OT)".
  - No feed: "Started 8:00 PM". If it does not fit: "Started".
  - If "Intermission" does not fit at 13 px (it is 12 chars, ~87 px in Plex Sans, fits at 340): fall back to "Int." only if QA finds a miss.
- Line 2, SCORE: `400 12.5px/17px var(--body)`, tabular numbers (`font-variant-numeric:tabular-nums`), `--muted` for team abbreviations, `--fg` 600 for the numbers. Format: `LAL 48 - 51 MIN` (away left, home right, same order as today). Fit rule (helper, section 3), first that fits:
  1. One line, 12.5 px: `LAL 118 - 121 MIN`
  2. One line, 12 px (minimum type size here)
  3. Stacked scoreboard, two rows, 12.5 px: row 1 `LAL` left / `118` right, row 2 `MIN` left / `121` right. Numbers of the leading team in `--fg` 700, trailing in `--fg2`. Used when a 3-digit score or a 4-letter abbreviation does not fit on one line (expected at 340 for e.g. "NYK 140 - 143 WSH").
  Rule: never ellipsis, never a hyphen-wrapped number; abbreviations never truncate (show whatever the feed gave).
- No score yet (pre / no feed): Line 2 is the matchup as today: own-team pill `.own` + " @ MIN" / " vs MIN" via `muNodes()`. If it does not fit: show only the opponent, "@ MIN" (pill dropped). Never "...".
- Final state: both lines in `--fg2`.

### 2.7 States summary (what a tile shows)

| State | Name/photo/bet/price | Tracker | Foot tags | Game block |
|---|---|---|---|---|
| Pre-game (feed says pre, game counted as started) | normal | empty pips/meter, "No stats yet" | - | "Starting" / matchup |
| No feed | normal | empty, "Getting stats..." or "Stats unavailable" | - | "Started 8:00 PM" / matchup |
| Live, in progress | normal | bar + number + helper | - | status + score |
| Break | normal | same | - | "Half" / "Intermission" / "End Q1" + score |
| Final, won | dimmed to `--fg2` | full bar, WON | - | "Final" + score, dimmed |
| Final, lost | dimmed | LOST | - | same |
| Final, push | dimmed | stamp PUSH (neutral) | - | same |
| Void | dimmed | stamp VOID + reason line | - | same |
| Hit live (over passed) | normal | HIT, no helper | - | status + score |
| Lost live (under passed) | normal | LOST, no helper | - | status + score |
| Pulled (TOO LATE) but counted | normal | as above | `TOO LATE` tag | as above |
| DNP | normal | "Not played yet" / "Did not play" | - | as above |
| Scratch (listed Out) | not shown on Live (unchanged) | | | |

Empty / error states of the Live tab itself (no games, expired slate, update line) are unchanged.

### 2.8 Layout

- `.lvlist` stays a 2-column grid, `repeat(2,minmax(0,1fr))`, gap 8 px, now literally the same rule as `.board`. Make `.lvlist` an alias of `.board` (one rule) so the two cannot drift.
- All scope: drop the per-sport `.sport-sec-h` header; each tile carries the sport badge (section 2.5). Keep the NBA-then-NHL ordering and each sport's own sort (progress, then start). Do not merge the sorts across sports.
- Tile height budget (not a hard cap, a sanity check for "fit more"): at 380 a typical live tile (one-line name, pips, no helper) about 170 px, worst case (hyphen-wrapped name, wrapped bet, meter + helper, stacked score) about 235 px. A row is as tall as its tallest tile; that is accepted.
- Wider than 380: same 2-column grid, max width 560 px wrap, fit helpers re-run on resize.

### 2.9 Accessibility and motion

- Name keeps `role="img"` + `aria-label` full name (from `nameBlock`). Stamp has the word, not just color. Score line gets `aria-label="Lakers 118, Timberwolves 121"` style text only if the feed gives names; otherwise abbreviations as read.
- No new animation. Existing live refresh is a silent repaint; keep it. `prefers-reduced-motion`: nothing to do.

---

## 3. What the Engineer can share

Reuse as is (one source of truth, do not copy):
- `tileTop(p, false)`, `nameBlock`, `splitName`, `fitName`, `fitNames`, `NAME_SIZES`, `NAME_SUFFIX` (name tiers).
- `tilePrice(p)`, `betShort(p)`, `odds()`.
- `sportBadge(p)` and the `.sp-badge` / `.ft` rules. Pitfall: `renderLiveAll()` temporarily sets `S.sport` to the section's sport, so `sportBadge()` (which tests `S.sport==='all'`) returns null there. Give it an explicit argument, e.g. `sportBadge(p, forceAll)`, and tag each pick with `p.sport` in `renderLiveAll`.
- `.tile`, `.hs`, `.top`, `.nm .fn/.ln`, `.row2`, `.bt`, `.pr` CSS: `liveRow` just adds `.tile` to its root (`class="tile lv"` + ` fin`).
- Keep `tracker()`, `gameLine()`, `FINAL_STAMP`, `.stmp`, `.pips`, `.meter` logic and thresholds. Only their markup layout changes.

New, small, and generic (so Picks could use it later):
- `fitLines(root)`: for each element marked `data-fit` with a list of fallbacks (font sizes, then alternate text/markup), apply the first tier whose `scrollWidth <= clientWidth`. Same shape as `fitName`: loop tiers, test `fitsLine(el)`. Used for the number line (16/14/13, then drop noun), helper line (copy tiers), status line, score line (12.5, 12, stacked). Call it from the same places as `fitNames()` (end of `render()`, `resize`, fonts ready/loadingdone). Make `fitNames` call it so there is a single hook.
- `lvScoreBlock(away, as, home, hs)` builds both the one-line and the stacked forms; `fitLines` picks.
- CSS: delete the old `.lv` rules listed in 1b. Keep only the live-only pieces: `.lv .trk2` (new two/three-row layout), `.stmp`, `.pips`, `.meter`, `.lv.fin` dimming, `.lv.open`/`.lv-xp` (Lab only), plus new `.lvn` (number line), `.lvh` (helper), `.lvg` (game block).
- Remove the dead `.lv` branch in `headshot()`'s error handler (line ~757): with `.tile`, removing the broken `<img>` is correct, and `fitName` already handles a missing photo (`im` null).

Also uses `.lv` today (must keep working): `labLiveRow()` (Lab "Today", line ~2483) builds the same card and adds an open state (`.lv.open` spans both columns, `.lv-xp` detail). Move it to the same builders (`tileTop`, `tilePrice`, game block) so Lab matches too; keep its `role=button`, open state, and `.lv-xp` content unchanged. Per-sport `Lab` rows have `bet.sport` from `test._sp`; use that for the badge.

Fixtures (must keep working, QA uses them): `?fixture=liveon`, `livepre`, `livedone`, `allstarted`, `liveespnfail`, `liveallfail`, `feedsdown`, `tonight`, `normal`, `quiet`, `stale`, `expired`, `empty`. Add one new fixture, `livelong`, for this spec (build via `sports/nba/fixtures/make_fixtures.py`): the 12 names in section 4 on started games covering live, break, OT, 2OT, final, 3-digit score, no-feed, pre, TOO LATE-pulled, push, void, DNP; plus 4 NHL picks in the All scope (first-initial names such as "J. Slafkovsky" with the accent in the real data, a Jr. name, an OT final). Housekeeping flag: the root page loads `fixtures/NAME/` relative to the root, but on `origin/main` fixtures live under `sports/nba/fixtures/` only. I copied them to the scratch root to reproduce. Confirm how QA serves them and keep that working (root `fixtures/` or a documented path).

---

## 4. Test names (10 longest real names from the data, plus 2 edge cases)

Pulled from `sports/*/data` and fixtures, synthetic QA names excluded:

| # | Name | Why it matters |
|---|---|---|
| 1 | Nickeil Alexander-Walker | longest, hyphen |
| 2 | Shai Gilgeous-Alexander | hyphen |
| 3 | Giannis Antetokounmpo | one long unbreakable word |
| 4 | Collin Murray-Boyles | hyphen |
| 5 | Karl-Anthony Towns | long first name (initial tier) |
| 6 | Brandin Podziemski | long last name |
| 7 | Isaiah Hartenstein | long last name |
| 8 | Wendell Carter Jr | two-word last + suffix |
| 9 | Michael Porter Jr | suffix |
| 10 | Victor Wembanyama | long last name |
| 11 | Jaren Jackson Jr. | suffix with period |
| 12 | J. Slafkovsky (NHL, accented u in data) | abbreviated first name + diacritic |
| (+) | Nene | single name, no first/last stack |

Expected name result at 340 (inner 104, photo present), same as Picks today because it is the same helper: Alexander-Walker: photo off, wraps after the hyphen; Gilgeous-Alexander: photo off, wraps after the hyphen; Antetokounmpo: photo off, 13 px; Murray-Boyles: photo off, 15 px; Karl-Anthony Towns: first name "K.", photo on; Podziemski, Hartenstein: photo on, 13 px; Carter Jr, Porter Jr: photo on, 15 px, "Jr" kept; Jackson Jr.: photo on, 13 px; Wembanyama: photo off, 15 px. At 380 results are looser (same or fewer drops). Live and Picks tiles must produce the same tier for the same name at the same width.

---

## 5. Wireframes

Widths are tile widths: 380 viewport = 144 px tile, 340 viewport = 126 px tile (inner 122 / 104). `[ph]` = 26 px photo.

### 5.1 Live, over line, in progress (340 and 380 look the same, just roomier at 380)
```
+--------------------------+
| [ph] Nickeil             |
|      Alexander-Walker    |   <- fitNames tiers; at 340: no photo, wraps after hyphen
| O 27.5 pts        -115   |
| [=======|=====]          |
| 14 / 27.5 pts            |   16/14/13 px, never wraps
| needs 14 more            |
| Q2 3:45                  |
| LAL 48 - 51 MIN          |
+--------------------------+
```

### 5.2 Live, small line, pips, hit
```
+--------------------------+
| [ph] Collin              |
|      Murray-Boyles       |
| O 1.5 threes      +140   |
| (o)(o)            [HIT]  |
| 2 / 1.5 threes           |
| OT 1:02                  |
| CHA 118 - 121 MIL        |   <- 12.5; at 340 may step to 12 px or stack
+--------------------------+
```

### 5.3 Final, lost, 2OT, 3-digit score, stacked at 340
```
+--------------------------+
| [ph] Michael             |   (name, bet, price dimmed to --fg2)
|      Porter Jr           |
| U 27.5 pts        -110   |
| [=======|====]    [LOST] |
| 31 / 27.5 pts            |
| Final (2OT)              |
| NYK              140     |   <- stacked scoreboard (leader bold)
| WSH              143     |
+--------------------------+
```

### 5.4 Pulled, still counted, All scope
```
+--------------------------+
| [ph] Victor              |
|      Wembanyama          |
| O 9.5 reb          +100  |
| [====|=====]             |
| 4 / 9.5 reb              |
| needs 6 more             |
| TOO LATE            NBA  |
| Q3 8:21                  |
| SA 64 - 70 GS            |
+--------------------------+
```

### 5.5 No feed / waiting
```
+--------------------------+
| [ph] Giannis             |
|      Antetokounmpo       |   <- 13 px, no photo at 340
| O 1.5 threes      +115   |
| (o)(o)                   |
| Getting stats...         |
| Started 8:00 PM          |
| [LAL] @ MIN              |   <- own pill + opp; "@ MIN" if too narrow
+--------------------------+
```

---

## 6. Acceptance criteria (QA)

Viewports: 380 x 800 and 340 x 800 (and 320 as a stretch check, no horizontal page scroll at any of them). Pages: root, scopes All / NBA / NHL, `?fixture=livelong` plus `liveon`, `livepre`, `livedone`, `allstarted`, `liveespnfail`, `liveallfail`, `feedsdown`.

1. Name parity: for each of the 12 test names, the Live tile and the Picks tile at the same width show the same name tier (same text, font size, photo on/off). No Live name ends in an ellipsis, except the final last-resort tier, which must also match Picks.
2. No clipped text anywhere in a Live tile: for every `.nm .ln`, `.nm .fn`, number line, helper line, status line, score line, `scrollWidth <= clientWidth`. Zero `text-overflow:ellipsis` in effect on Live tiles outside the last-resort name tier. (QA can run: all `#app .tile.lv *` with `scrollWidth > clientWidth + 1` returns empty, excluding the meter.)
3. Scores: for every fixture game, both team abbreviations and both full scores are fully visible, including 3-digit scores (e.g. 118-121, 140-143) and 4-letter abbreviations, at 340. When stacked, rows align, the leader is bold.
4. Progress: "27 / 28.5" style numbers and "14 / 27.5 pts" show on one line, minimum 13 px, never broken across lines. Noun dropped only after 13 px fails. Helper line is one line or the short form.
5. Status copy exact per section 2.4 and 2.6 (Q2 3:45, OT 1:02, 2OT, Half, Intermission, End Q1, Final, Final (OT), Final (2OT), Starting, Started 8:00 PM).
6. Match with Picks: same photo size (26), same name type scale (12/14 and 15/19), bet via `betShort`, price 21 px 600 mono, tile padding 10/10/9, radius 8, grid gap 8, same sport badge placement in All scope. Side by side with Picks the tiles read as siblings.
7. Stamps: WON, LOST, HIT, PUSH, VOID render with correct colors (good / bad / neutral) and never overlap the meter or pips at 340.
8. TOO LATE-pulled pick that started appears on Live with the `TOO LATE` tag and still counts in Tonight W-L (unchanged logic).
9. All scope: no section headers; every tile has its NBA / NHL badge; NBA group then NHL group; the NHL tiles use the same helpers (no S.sport leak making badges disappear).
10. Refresh: leaving the page on Live for 30 s (3 polls) never flashes a clipped name or score; font-load and rotate/resize re-fit correctly.
11. Dim finals: finished tiles use `--fg2` for name and price (as today).
12. Lab "Today" rows use the same card and still open and close; Picks, Games, Record, Info are visually unchanged.
13. Fixtures: all existing `?fixture=` pages still load and render the Live tab; `livelong` exists and covers every state in 2.7.
14. No horizontal page scroll at 320, 340, 380; tap targets and the tab rail unchanged.

Sign-off: UX signs off the built result against sections 2 and 6 before QA runs 380 / 340.

## 7. Discord

No Discord format change. (Live tiles are page-only.)
