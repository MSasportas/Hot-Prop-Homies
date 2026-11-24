# Lab cards redesign: spec for the Engineer

Author: UX Expert. Date: 2026-11-23. Scope: Lab tab on root `index.html` (renderLab, labPicks, Tonight expand in labLiveRow) plus new plain-language fields in `sports/nba/config/lab.json` and `sports/nhl/config/lab.json`. No change to what any number means, no change to test rules, thresholds, or retire logic.

Problem (Matt, 2026-11-23): an opened card is a wall of data-science text (base population, n=, CI, discovery, shadow-track, DS, Sharp, LVA2). He likes that the detail exists. He wants it readable by a consumer in seconds.

Fix in one line: every card answers four questions in plain words (What are we testing? How is it going? Is it real money? What happens next?) and the technical text moves into a closed "Show the math" drawer.

---

## 1. Design principles

1. Glance first: the closed card answers idea, status, progress, record in 3 lines.
2. Opened card is a template, never a paragraph. Every block has a label, an icon, and at most 2 lines.
3. Nothing is deleted. All Researcher text (`rule`, `discovery`, `gate`) stays, verbatim, in the drawer.
4. Honest by default: every paper test says so on the card, in plain words, in the same place every time.
5. Same visual language: dark theme, Orbitron headings (`--head`), IBM Plex Mono numbers (`--num`), cyan `--accent`, green `--good` and red `--bad` units, `--surface` card, `--line` borders.

---

## 2. New fields in lab.json (per test)

Engineer adds these to every test entry in both files. Copy for every current test is in section 9 and 10, ready to paste. Existing fields (`id, title, rule, summary, stats, need, discovery, gate, direction, no_auto_retire, status, base`) are unchanged.

| Field | Type | Limit | Used for |
|---|---|---|---|
| `name` | string | 28 chars | Card title. Replaces `title` on the page (title stays in file and in the drawer). |
| `plain` | string | 80 chars | One-line "what we're testing", shown under the title on the closed card. |
| `why` | string | 110 chars | "Why we think it works", expanded only. |
| `outcome` | enum `review` / `filter` / `matt` / `live` | | Picks the "If it passes" sentence (section 6). Default `review`. |
| `paper` | bool | | Default true. `false` only for `fast_checks` (its picks are real and on the Record). |

Fallbacks if a field is missing (a new Researcher test before the plain copy is written): title shows `title`; `plain` line hidden; The idea / Why block hidden; the exact `rule` text goes at the top of the Show the math drawer; status, meter, scorecard, paper banner all still render. Never show an empty labeled row.

Process note for CEO: the Researcher must add `name`, `plain`, `why`, `outcome` whenever they add a test. Plain copy is checked against section 8 rules.

No new stats are required for v1. Two optional upgrades, flagged to Data Scientist, not blockers:
- Summary files that already save `nights[]` (bets/flags with `date`, `units`) light up the trend chart and pick list. Tests without saved nights simply omit the chart.
- If the summary ever exposes break-even hit rate (`be`), the Wins chip adds "Needs 52.4%". Until then the chip shows only the win rate.

---

## 3. Status (computed on the page, display only)

Uses fields that exist: `k = w + l` (after the fade swap), `need`, `u` (units, after the fade sign flip), `t.status`.

| Order | Pill text | Rule | Color |
|---|---|---|---|
| 1 | Ready for review | `t.status === 'ready_for_sharp'` | `--good` fill-soft, `--good` text and border (existing `.lab-ready` look) |
| 2 | Check due | `k >= need`, not ready and `u >= 0` (`u < 0` stays Looking bad) | `--warn` text, `--warn-soft` bg |
| 3 | Looking good | `k >= min(need, max(20, 0.25*need))` and `u > 0` | `--good` |
| 3 | Looking bad | same sample floor and `u < 0` | `--bad` |
| 4 | Collecting | under the sample floor, or `u == 0` | `--accent` outline, transparent bg |
| 5 | Starting up | no stats yet | `--muted` outline |
| 6 | Retired | entries in the retired list only | `--muted` |

Pill: 11px `--num`, uppercase, letter-spacing .04em, padding 0 8px, height 20px, radius 10px, never wraps. The pill is always the same size so cards line up.

Status never claims a verdict: "Looking good" is a lean, not a pass. The only pass state is Ready for review.

---

## 4. Collapsed card (380px)

Replaces `.lab-h`. Whole card is the tap target (min height 96px, well over 44px). One chevron.

```
+--------------------------------------------------+  width 352 (380 minus 14 gutters)
| [NBA]  Hot streak, bet under       [LOOKING GOOD] |  line 1: badge, name (Orbitron 14/19, 2 lines max), status pill
|                                                  |
| Bet UNDER on players who've been hot lately      |  line 2: plain (14/20, --fg2, 2 lines max)
|                                                  |
| 488 picks · goal was 300                 247-241 |  line 3: meter label (12 --muted) left, record right (14 --num 600)
| [==================================]    +24.36u  |  meter bar (6px) full width; units under record, green/red
| PAPER TEST - not in your picks                 v |  line 4: tag (11 --muted) left, chevron right
+--------------------------------------------------+
```

Details:
- Line 1: sport badge (existing `.sp-badge`) + name left; status pill right-aligned, flex:none. Name wraps to 2 lines before it ever pushes the pill off.
- Line 2: `plain`. Hidden if field missing.
- Line 3 meter label, plain words:
  - Under goal: `{k} of {need} picks` ("120 of 300 picks")
  - Goal reached: `{k} picks · goal was {need}` ("488 picks · goal was 300")
  - No stats: `Waiting for first picks`
- Meter: 6px tall (was 4), radius 3, `--line` track, fill `--accent`. When goal reached, fill is `--good` if Looking good or Ready, `--bad` if Looking bad, `--warn` if Check due. Fill animates on first paint (600ms ease-out). Tick mark at 25% (the sample floor, 1px `--line2`) so Matt can see "too early to read" territory. Role img, aria-label "{k} of {need} picks".
- Record `W-L` (after fade swap, as today) and units under it, right aligned, `--num`. Units 15px 600, green if >0, red if <0, `--muted` if 0.
- Line 4 tag, always present:
  - Paper tests: `PAPER TEST - not in your picks` in `--muted`, with a small dashed-circle glyph. (Use a hyphen, not an em dash.)
  - `fast_checks` (`paper:false`): `REAL PICKS - on your Record` in `--good`.
- Card border: paper tests get a dashed 1px `--line2` border ("pretend"); real picks solid `--line`. This is the whole-page cue: dashed means paper.
- Spacing 14px padding, 10px between lines, 12px between cards. Cards stay a stack (no grid) at all widths; max-width 560px centered at 768+.

Top of the tab (replaces the current muted sentence):

```
Lab
Paper tests. We pretend-bet ideas to see if they would make money.
None of these are in your picks unless the card says REAL PICKS.

[ 27 tests ]  [ 3 looking good ]  [ 9 looking bad ]  [ 15 collecting ]
```
- The summary chips double as filters (tap = filter, tap again = clear, `aria-pressed`). Chips scroll horizontally if needed; no page horizontal scroll. Counts come from the same status rule. "Check due" and "Ready for review" get their own chip only when count > 0.
- Sort within the list: Ready for review, Check due, Looking good (most units first), Collecting (most picks first), Looking bad (worst last), Starting up. Retired link stays at the bottom.
- The All/NBA/NHL toggle stays as is.

---

## 5. Expanded card

Tap anywhere on the closed part toggles. Opening animates height 180ms ease-out; opens below the collapsed block, which stays visible and unchanged (no jump). Order, top to bottom, 14px side padding, 16px between blocks:

```
(collapsed block, unchanged)
+--------------------------------------------------+
| THE IDEA                                         |  3 labeled rows, each: cyan icon + label + 1-2 lines
| (lightbulb) What we're testing                   |
|   Bet UNDER on players who've been hot lately.   |  plain
| (question)  Why we think it works                |
|   Hot streaks cool off, but books price the      |  why
|   streak in.                                     |
| (arrow)    If it passes                          |
|   Our betting expert reviews it. Nothing changes |  from outcome
|   in your picks until then.                      |
+--------------------------------------------------+
| SCORECARD                                        |  2 x 2 chips (see below)
| [Wins        ] [Profit      ]                    |
| [50.6%       ] [+24.36u     ]                    |
| [Picks       ] [Trend       ]                    |
| [488 of 300  ] [Up lately   ]                    |
+--------------------------------------------------+
| CUMULATIVE UNITS (sparkline, 56px tall)          |
|   ___/\__/---                                    |
| Nov 16                                   Nov 22  |
+--------------------------------------------------+
| WHAT HAPPENS NEXT                                |  two columns, equal width
| (check) If it passes   | (x) If it fails         |
| Moves to review.       | We retire it. Nothing   |
|                        | changes for you.        |
+--------------------------------------------------+
| (flask) We bet the opposite side                 |  fade tests only, single line pill
+--------------------------------------------------+
| > Show the math                                  |  closed drawer, 48px row
| > Recent picks (5)                               |  closed drawer, 48px row
+--------------------------------------------------+
```

### 5.1 The idea block
- Three rows, label 12px `--muted` uppercase `--num`, body 14/20 `--fg`. Icons are inline SVG 18px, stroke `--accent`, 1.5px: lightbulb, question mark in circle, arrow-right in circle. No emoji.
- Caps: each body at most 2 lines at 380px.
- "If it passes" body is chosen by `outcome` (section 6). A reality-check line is added under it, only while the test is under goal and Looking good: `Early results can be luck. It has to hold up.` 12px `--muted` italic-free.

### 5.2 Scorecard (2 x 2 chips)
Chip: `--raise` bg, 1px `--line`, radius 8px, padding 10px 12px, min-height 64px. Label 11px `--muted` uppercase `--num`; value 18px `--num` 600; sub line 11px `--muted`.

| Chip | Value | Sub line | Color |
|---|---|---|---|
| Wins | `w/(w+l)` as `50.6%` (after fade swap) | `247 won, 241 lost` | `--fg` |
| Profit | `+24.36u` (after fade swap) | NBA only: `about +$243 at $10 a pick`. NHL: none. | green/red/muted |
| Picks | `{k} of {need}` or `{k}` if over | `{pending} still to play` if pending > 0 | `--fg` |
| Trend | `Up lately` / `Down lately` / `Flat` | `last 7 nights: +3.1u` | green/red/muted |

Trend source: last 7 nights of `nights[]` units (fade-flipped). If fewer than 3 nights are saved, drop the Trend chip and render the 3 remaining chips (Wins, Profit, Picks) in one row of 3 with the same sizing. Never show an empty chip.

Dollar line is NBA only because the fixed stake is $10 a unit for NBA. NHL shows units only.

### 5.3 Sparkline
- Data: cumulative units by night from `nights[]`, fade-flipped. Needs 3+ nights; otherwise the block is omitted (no placeholder).
- 56px tall, full width, stroke 2px `--accent`; area under line `--accent-soft`; zero line 1px dashed `--line2`; end dot 5px, green if above zero, red if below. Start and end dates 11px `--muted` below. No axes, no gridlines.
- Draws left to right over 500ms ease-out on first open. Respect reduced motion (render final state).
- Accessible: `role="img"`, aria-label "Cumulative units, from {start} to {end}: {first} to {last}".

### 5.4 What happens next row
Two equal columns, each with an icon, label (12px `--muted`), and 1-2 lines of 13/18 text.
- Passes (check-circle icon, `--good`): text from `outcome` (short form, section 6).
- Fails (x-circle icon, `--muted`): `We retire it. Nothing changes for you.` (all paper tests). `fast_checks`: `We turn the extra checks off.`
- Stacks to one column under 340px width.

### 5.5 Fade line (only when `direction === 'fade'`)
One full-width pill, `--accent-soft` bg, `--accent` text 13px: `We bet the opposite side.` and a second muted line: `The record above is what betting against it would have done.` This replaces the old "fade: shown as betting against the tracked side".

### 5.6 Show the math drawer (closed by default)
Row: 48px tall, label `Show the math`, chevron right. Open state kept in `S.labMath[id]`, independent from the card state. Inside, each item is a labeled block, 12/17 `--muted` labels, 12/18 `--fg2` text, 10px between blocks, nothing over 3 lines without a scroll-free wrap. Order and mapping to existing fields:

| Label | Source | Notes |
|---|---|---|
| Exact rule | `t.rule` | verbatim |
| What the history showed | `t.discovery` | verbatim; omit if missing |
| Pass mark | `t.gate` | verbatim; omit if missing |
| Counts | `{k} graded, {pending} pending, {void} void` | pending/void omitted when 0 |
| Beat the closing price | `st.clv` (fade-flipped) as `+1.2%` | label in plain words; omit if missing |
| Updated | `fStamp(sm.updated_at)` | `Updated 5:00 AM` |

Each block's text is at 12px so even long Researcher text reads as a short footnote after the card is already clear. Long text stays; it just never competes with the answer. Researcher text may still contain jargon: that is acceptable only inside this drawer.

### 5.7 Recent picks drawer (closed by default)
Wraps the existing `labPicks`. Row label `Recent picks` with count of nights. Opening shows the 3 newest nights; a `Show all nights` text button (44px tall) reveals the rest. Each night header unchanged (date, W-L, units). Pick rows unchanged except result words (Won / Lost / Push / Void / Pending / Pulled), fade picks show "Under" etc. as the bet we make.

When no pick list is saved, the drawer row is replaced by one muted line: `Pick-by-pick list is coming. The totals above are live.` (replaces "This test's pick list isn't saved yet, only its totals.") Not a drawer.

---

## 6. "If it passes" copy by `outcome`

| outcome | Long form (The idea block) | Short form (Next row) |
|---|---|---|
| `review` | Our betting expert looks it over. Nothing changes in your picks until then. | Goes to review. |
| `filter` | We could change which of our real picks you see. Nothing changes until it is reviewed. | We review it. |
| `matt` | It goes to you. Nothing changes in your picks until you say go. | You get the call. |
| `live` | These are already real picks on your Record. We keep the faster checks. | Kept. |

---

## 7. States

| State | Behavior |
|---|---|
| Loading page | Existing skeletons. |
| Test with no summary yet | Pill `Starting up`, meter label `Waiting for first picks`, no record on the right (`...`), expanded shows idea block plus `No results logged yet.`; missing-summary error shows `Its numbers couldn't be read.` (existing strings). |
| Stale | Drawer `Updated` line is the only place; if `updated_at` is over 36 hours old the line turns `--warn` and reads `Updated {time} - older than usual`. |
| Ready for review | Pill green, meter full green, passes column highlighted with a 2px `--good` left border. Still the tag `PAPER TEST - not in your picks` until Matt or the Sharp makes it live. |
| Retired list | Link line `{n} retired` unchanged. Each line uses `name` (fallback title): `{name} · 120-140 -9.2u · failed its test · Nov 20`. Existing RETIRED_WHY wording is already plain; keep. |
| Error | Existing "Can't load the Lab right now." |
| Reduced motion | No fill/line draw, no height animation; instant states. |

Tonight section (labLiveRow expanded area): replace the `rule` / `discovery` / `gate` dump with: bold `name`, then `plain`, then the one tag line `PAPER TEST - not in your picks`, then a `See this test` text link that opens the test card in the Lab list (scroll + open). No technical text on the live card.

---

## 8. Copy rules

- Reading level about 8th grade. Short, common words.
- Limits: `name` 28 chars; `plain` 80 chars (2 lines); `why` 110 chars (2 lines); any label 24 chars; any value 14 chars; status pill 16 chars.
- One idea per sentence, active voice, present tense. Start `plain` with the action ("Bet...", "Skip...", "Follow...", "Check...").
- Banned on the card face (allowed only in the Show the math drawer): n=, ROI, CI, bucket, discovery, shadow-track, base population, DS, Sharp, LVA, CLV, EV, de-vig, fade, hit rate, forward test, gate, sample. Use: wins, profit, picks, "the opposite side", "our betting expert", "the closing price", "books".
- Units: show `u` with sign and two decimals as today. NBA may add dollars at $10.
- "Sharp books" is allowed only to mean the sharp-bookmaker concept where the test is about them, written as "sharp books (the ones pros use)" in `why` once. Prefer "sharp books" in the `name`/`plain` only when no simpler word fits (NP1, MM2a/b, NP2, NN6 use "sharp"/"casual").
- Never promise results. No "will", "guaranteed", "free money". Use "may", "could", "looks".
- No em dashes anywhere. No emoji.

---

## 9. Plain copy, NBA (`sports/nba/config/lab.json`), 27 tests

`outcome` default is `review`; only exceptions are listed in the last column.

| id | name | plain | why | outcome |
|---|---|---|---|---|
| fast_checks | Faster price checks | Check prices every 15 minutes near tip-off | Hard Rock copies Pinnacle in 20 to 30 minutes, so wider checks missed most moves. | live (`paper:false`) |
| pin_judge | Pinnacle price check | Bet when Hard Rock pays 2%+ more than Pinnacle's fair price | Pinnacle is the sharpest book. If Hard Rock pays more, that is a bargain. | matt |
| threes_judge | 3-pointer bargains | Bet 3-pointer props when Hard Rock beats Pinnacle by 1%+ | Same idea as the Pinnacle check, with a lower bar, only for 3s. | matt |
| AH1 | Big move, unders only | Of our real picks, unders after a big line move (4+ pts) | A big move can mean real news. We check if the under side does best. | filter |
| AH2 | Late and big | Of our real picks, late ones after a 3+ pt move | Late moves are fresh news, and Hard Rock has less time to fix its price. | filter |
| AH3 | Late, only Pinnacle moved | Of our real picks, late ones where only Pinnacle moved | One sharp book moving alone may know something others do not. | filter |
| AH4 | Hard Rock has not moved | Of our real picks, ones where Hard Rock's price is unchanged and fair | A price that sat still while the market moved can be a bargain. | filter |
| AH5 | Big move, only Pinnacle | Of our real picks, a 4+ pt move that only Pinnacle made | A big move nobody copied may be early news. Or it may be noise. | filter |
| AH6 | 90 to 45 min before tip | Of our real picks, the ones made 90 to 45 minutes before tip | We check if picks do better at certain times before the game. | filter |
| AH7 | 45 to 20 min before tip | Of our real picks, the ones made 45 to 20 minutes before tip | We check if picks do better at certain times before the game. | filter |
| AH8 | Late unders | Of our real picks, unders made in the last 90 minutes | Late news may make unders hit more. We are checking. | filter |
| AH9 | A few books follow | Of our real picks, ones where 2 to 4 other books moved the same way | Some agreement may mean the move is real, before the price is gone. | filter |
| AH10 | Big-move unders by size | Unders after a 3 to 4 pt move, compared with 4+ pts | We check if a bigger move means a better under. | filter |
| AH11 | Morning overs vs unders | Picks made before the last 90 minutes, overs and unders compared | We check which side does better early in the day. | filter |
| AH12 | Medium-big, only Pinnacle | Of our real picks, a 3+ pt move that only Pinnacle made | A smaller version of the big-move test, so we get more picks to judge. | filter |
| AH13 | Hard Rock stuck, unders | Of our real picks, unders where Hard Rock's price has not changed | A stuck price on the under side may be a bargain. | filter |
| AH14 | Small moves, fair price | Of our real picks, small moves (2 to 3 pts) at a fair price | Small moves are common. We check if the fairly priced ones pay. | filter |
| AH15 | Late, fair price | Of our real picks, late ones (last 90 min) at a fair price | Late and fairly priced may be the sweet spot. | filter |
| NP1 | Sharp vs casual books | Bet the way the sharp books lean when casual books disagree | Sharp books (the ones pros use) are usually right. | review |
| NP2 | Against casual-book moves | Bet against a move that only casual books made | If casual books move and sharp books stay put, the move may be wrong. | review |
| NP3 | Whole market moved | Follow a move that most books made but Hard Rock has not | If everyone else moved, Hard Rock's price is probably out of date. | review |
| LVA1 | Skip unders, low line | Skip Under picks when the line is well below his average | A line far below his usual may already be too low. Early results were poor. | filter |
| LVA2 | Overs, high line | Flag Over picks when the line is well above his average | Early results: these overs won 8 of 8. That is too few to trust yet. | filter |
| NP4 | Exchanges moved first | Follow the betting exchanges when they move and Hard Rock has not | Exchanges like Novig are sharp. Hard Rock may be slow to catch up. | review |
| DM1 | Fewer minutes, bet Under | Bet UNDER on players getting fewer minutes lately | Less court time means fewer points and rebounds. Books may be slow to adjust. | review |
| DM2 | Hot streak, bet under | Bet UNDER on players who've been hot lately | Hot streaks cool off, but books price the streak in. We bet the opposite side. | review |
| DM3 | Pinnacle far from pack | Bet OVER instead when the Under looks like a trap | When Pinnacle is far from the other books, the under tends to lose. | review |

Note on the AH group: these are filters on the real picks, so "Paper test" is still true (the filter is not applied to your picks) but the card tag for `outcome: filter` reads `PAPER TEST - picks unchanged`. Same dashed border.

## 10. Plain copy, NHL (`sports/nhl/config/lab.json`), 21 tests

All NHL tests are paper and `outcome: review` unless noted. `outcome: matt` for q24 (its gate says 1 PM picks stay off until Matt says go). Tests are shots on goal unless noted (the `why` says so where it is not).

| id | name | plain | why |
|---|---|---|---|
| q24 | 1 PM price | Bet shots at the 1 PM price when Hard Rock beats other books by 1%+ | Hard Rock's early price is sometimes better than the market's. We grade at that price. (outcome: matt) |
| fwd_LL1f-fade | Hard Rock moved: go against | After Hard Rock changes a price since 1 PM, bet the other way | Hard Rock may overshoot, and the old price was right. We bet the opposite side. |
| fwd_LL1f-follow | Hard Rock moved: follow | After Hard Rock changes a price since 1 PM, bet the same way | Hard Rock may have news, and the move is right. |
| fwd_LL3a_tight | Bargain, books agree | Bet when Hard Rock pays 1%+ more and the other books all agree | If every other book agrees, the bargain is more likely real. |
| fwd_LL3b_loose | Bargain, books split | Bet when Hard Rock pays 1%+ more and the other books disagree | When books disagree, a good price may just be noise. We check. |
| fwd_LL4a_fade | Hard Rock alone: go against | When only Hard Rock moves a price, bet the other way | A move nobody else made may be a mistake. We bet the opposite side. |
| fwd_LL4b_follow | Hard Rock alone: follow | When only Hard Rock moves a price, bet the same way | A move nobody else made may be news only Hard Rock saw. |
| fwd_LL5_exch | Exchange prices | Use betting exchange prices to find bargains | Exchanges have almost no markup, so their price is a good guide to the real odds. |
| fwd_LL6_line | Different line at Hard Rock | Bet when Hard Rock's line is different from the other books | A different line can hide a better chance to win. |
| fwd_MM2a_split | Sharp vs casual books | Follow the sharp books when casual books disagree | Sharp books (the ones pros use) are usually right. |
| fwd_MM2b_split_2pct | Sharp vs casual, big gap | Same as above, only when the gap is 2%+ | A bigger gap should be a clearer signal, with fewer picks. |
| fwd_MM3a_persist | Gap lasts 90 to 45 min | Bet when a price gap stays from 90 to 45 minutes before the game | A gap that lasts is likelier to be real than one that flashes. |
| fwd_MM3b_confirm | Gap still there at 45 min | Bet when a price gap is still there 45 minutes before the game | Checking again later filters out gaps that close fast. |
| fwd_MM4_total | Game total moved | Bet shots when the game total moved but player prices did not | If the game's expected scoring changed, a player's price may be behind. |
| fwd_MM5a_follow | Hard Rock line shift: follow | When Hard Rock shifts its line, bet the way it moved | Hard Rock may know something. |
| fwd_MM5b_fade | Hard Rock line shift: go against | When Hard Rock shifts its line, bet the other way | A line shift may be an overreaction. We bet the opposite side. |
| fwd_NN2fa_follow_market | Winner: follow the market | Pick the game winner the other books favor when Hard Rock disagrees | The books together are usually more right than one book. Research only, game winners are not picks. |
| fwd_NN2fb_follow_HR | Winner: follow Hard Rock | Pick the game winner Hard Rock favors when it disagrees with others | Hard Rock may see something the others miss. Research only, game winners are not picks. |
| fwd_NN4_exch_steam | Exchanges moved first | Follow the betting exchanges when they move and Hard Rock has not | Exchanges are sharp. Hard Rock may be slow to catch up. |
| fwd_NN5_market_moves | Market moved, Hard Rock not | Follow the market when most books moved and Hard Rock has not | If everyone else moved, Hard Rock's price is probably out of date. |
| fwd_NN6_fade_soft | Against casual-book moves | Bet against a move that only casual books made | If casual books move and sharp books stay put, the move may be wrong. |

NHL `plain` rows over 80 chars (check at build; trim words, do not change meaning): "Pick the game winner the other books favor when Hard Rock disagrees" and "Bet shots at the 1 PM price when Hard Rock beats other books by 1%+" are the longest; if over 80 the Engineer lets it wrap to 2 lines (it fits).

---

## 11. Interaction

- Card tap toggles open; `aria-expanded` on the card button. Only the closed block is the button, so text selection inside the opened card works.
- Drawers: independent toggles, 48px rows, `aria-expanded`, state kept in `S.labMath[id]` and `S.labPicksOpen[id]`; they stay open across redraws.
- Opening a card does not close others. Opening a card scrolls it so its title is at the top only if its title is off-screen.
- Status summary chips filter; the filter resets on tab switch.
- Focus: visible 2px `--accent` outline on card, chips, drawers (matches `.lab-h:focus-visible`).

## 12. Motion

| What | Duration | Easing | Reduced motion |
|---|---|---|---|
| Progress fill, first paint | 600ms | ease-out | none |
| Card expand/collapse | 180ms | ease-out | none |
| Sparkline draw | 500ms | ease-out | none |
| Drawer open | 160ms | ease-out | none |

No looping animation. Nothing moves after settling.

## 13. Do not break

- `?fixture=NAME` pages keep working. Add one Lab fixture covering every state in section 7 (Collecting, Looking good, Looking bad, Check due, Ready for review, Starting up, a fade test, a paper:false test, a test with no nights, a test with nights) for QA at 380px. Existing fixtures must keep loading with the old lab.json shape: all new fields are optional (section 2 fallbacks).
- Summary-file shapes (`nights[].bets` NBA, `nights[].flags` NHL), `labPicks` logic, fade swap, and the retired list loader are unchanged.
- `LAB_REDRAW`, Tonight section, All/NBA/NHL toggle unchanged except the Tonight expanded text (section 7).
- No Discord change.

---

## 14. Acceptance criteria (QA at 380px; also check 340 and 768)

1. Closed card shows, without scrolling inside the card: sport badge, name, status pill, plain line, meter with words, record and units, paper tag. Name never pushes the pill off screen; 2-line max.
2. DM2 (Hot streak, bet under) closed reads: `Bet UNDER on players who've been hot lately`, pill the pill from section 3 (a test at goal that is not ready is `CHECK DUE` when units are 0 or up, `LOOKING BAD` when down), `488 picks · goal was 300`, its record and units, `PAPER TEST - not in your picks`.
3. Opened card shows The idea (3 rows), scorecard, trend chart (if 3+ nights saved), What happens next, fade line (fade tests), and two closed drawers. No paragraph over 2 lines outside the drawers. Total opened height of DM2 with drawers closed is at most 1.5 screens at 380x800.
4. None of these words appear outside Show the math: n=, ROI, CI, bucket, discovery, shadow-track, base population, DS, Sharp (as a person), LVA, CLV, EV, gate, fade (as a word), hit rate.
5. Every string in Show the math equals the existing lab.json text (rule, discovery, gate) exactly; counts, closing-price and Updated lines are present when the data exists.
6. Fade tests: record, units, and Wins chip use the swapped numbers (DM2 shows 247-241 +24.36u as today), and the fade line is visible.
7. Paper tests have dashed border and the paper tag; `fast_checks` has solid border and `REAL PICKS - on your Record`. `filter` outcome tests show the `picks unchanged` tag text.
8. Status pill matches section 3 for each fixture state; no state claims a pass except Ready for review.
9. Tests with no nights saved: no chart, no empty chips, one line `Pick-by-pick list is coming. The totals above are live.`
10. Missing `name/plain/why/outcome` falls back cleanly (title shown, rule inside the drawer), no blank rows, no console errors.
11. Summary chips filter correctly and counts add up to the visible tests; works with the All/NBA/NHL toggle.
12. Tap targets at least 44px; no horizontal page scroll at 340; contrast of 11px labels on `--raise` is at least 4.5:1 (`--muted` #9490B8 on #221E42 passes; verify).
13. Reduced-motion on: no animation at all.
14. Tonight cards: expanded shows name, plain line, paper tag, `See this test` link; no technical text.
15. Both sports' plain copy matches sections 9 and 10 exactly and respects the length limits in section 8.

## 15. Open item for CEO / Data Scientist (not blocking)

Most tests have no saved pick list (summaries carry totals only). Saving `nights[]` for every test in the summary generators would light up the sparkline, trend chip, and recent picks everywhere. UX asks the Data Scientist to scope that; the page works without it.
