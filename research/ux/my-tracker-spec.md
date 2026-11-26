# My Tracker: UX spec

Author: UX Expert. Status: spec for Engineer. Scope: root `index.html` (NBA + NHL combined page). No code here, specs only.
Date: 2026-11-25. Matt's ask: pick any player, pick a stat, set a line, watch it track live, group up to 3 into a parlay.

---

## 1. Decision

**A section inside the Live tab, named "My Tracker". Not a new tab.**

Why, in four lines:
1. The rail already has 7 slots (Picks, Live, Games, Record, Lab, Info, HQ). An 8th breaks the rail at 320px.
2. The thing Matt wants is "watch scores live". That is what Live is. Same 10s poll, same tile look, same "Updated Xs ago" line. One place to look during games.
3. Live polling is already gated to "Live tab open + page visible". A tracker tab elsewhere would need its own gate. Inside Live it inherits it.
4. A segmented switch at the top of Live keeps the personal stuff walled off from our picks (see 2).

**Name: "My Tracker".** Plain, says it's his. Rejected: "Scratchpad" (cute, unclear), "Watchlist" (sounds like picks to watch), "My Bets" (implies real bets / the Record).

---

## 2. Where it lives and how it's walled off

At the top of the Live tab, above "Tonight 3-1" and above everything else, a two-option segmented control:

`[ Our Picks ]  [ My Tracker 3 ]`

- Full width, 44px tall, 2 equal segments, same pill look as `.sport-sw` but larger. Segment label 15px/600. Number is the count of tracked bets still in play (not finished); hidden at 0. Label and number are one no-break unit (`white-space:nowrap`; the segment grows, never clips).
- Default on open: **Our Picks** (the product). Remember last choice per device in `localStorage` (try/catch, falls back to Our Picks).
- Deep link: `#tracker` opens Live on My Tracker.
- The header sport switch (All / NBA / NHL) does **not** filter My Tracker. It always shows both sports, each tile carries an NBA or NHL badge. Show a one-line note under the segmented control only when the header is on a single sport: "My Tracker shows both sports." 13px, muted.
- When My Tracker is open, the Our Picks content (Tonight line, tiles) is not rendered. Never both on screen.

### Visual separation (never mistaken for picks)

Every My Tracker surface follows these rules, which no real pick surface uses:

| Rule | Spec |
|---|---|
| Persistent banner, top of view | "MY TRACKER. Your own notes. Not a Hot Prop Homies pick. Not on the Record." 13px, in a dashed-border strip, always visible (not dismissable) |
| Dashed borders | Tiles and parlay cards use `1.5px dashed var(--my-edge)`. Real picks are solid |
| "MINE" tag | Small tag on every tile and parlay: text `MINE`, 12px/700, letter-spacing .08em, no-break |
| Own accent | `--my-edge` / `--my-soft` (below). Not cyan (accent), not magenta (primary), not amber (warn) |
| No prices, no EV, no model, no units, no "agrees" | Nothing a real pick shows. Tracker shows stat, line, side, game status only |
| Never counted | Never in Tonight W-L, units, Record, Lab, Discord, status.json. Tracker W/L is never summed across nights |

Tokens (add alongside existing; exact values):

| Token | Night (default) | Day (Flame Day) |
|---|---|---|
| `--my-edge` | `#8B7CF0` | `#5B4BD1` |
| `--my-text` | `#B9AEFF` | `#4A3BB8` |
| `--my-soft` | `rgba(139,124,240,.14)` | `rgba(91,75,209,.10)` |

Hit/lost colors reuse `--good` and `--bad` (same meaning as everywhere). Under-line "used" uses `--warn` as on Live today.

---

## 3. What stats can be offered (checked against the live feed code)

Only what `index.html` already reads from the ESPN box score (labels PTS / REB / AST / 3PT-made; NHL S, G, A).

| Sport | Stats offered in v1 | Label in picker | Source column |
|---|---|---|---|
| NBA | Points | Points | PTS |
| NBA | Rebounds | Rebounds | REB |
| NBA | Assists | Assists | AST |
| NBA | Threes made | 3-pointers made | 3PT (made part) |
| NHL | Shots on goal | Shots on goal | S |
| NHL | Points (G + A) | Points | G + A |

Not offered in v1 (not parsed today): steals, blocks, turnovers, minutes, PRA combos, goals alone, assists alone (NHL G and A columns are in the same box, so goals and assists are an easy v2 add; Engineer should not ship them without UX copy). The picker must never show a stat the feed does not return.

NBA backup feed (NBA.com) returns the same four stats. If a game is only readable through the backup, the tile works the same.

---

## 4. Data the picker needs (Engineer notes)

The Live poll today only fetches box scores for games that have a pick. The tracker needs more. Requirements, in plain terms:

1. **Players list for the picker**, per game tonight, from the best available source, in this order:
   a. Players already in a game's ESPN box score (started or finished games). Every player listed, including bench. Key by ESPN athlete id.
   b. Players named on tonight's slate (`picks[].player`, `pid`, `team`, `game_id`), so pre-game picks' players are always findable.
   c. For games not started where a and b are thin: the ESPN team roster (simple GET, no headers, same rule as the other feeds). **Engineer must verify this works from the browser (CORS, simple GET) before relying on it.** If it does not, skip c and use the fallback copy in section 9 ("Players show once the box score opens").
2. **Poll scope.** A tracked bet adds its game to the poll "need" list even when that game has no pick. Tracker polling runs while the Live tab is open on either segment (`S.view === 'live'`), same 10s, same visible-page gate, same "never more than one poll in flight". The segment count may use the last known state.
3. **Not gated by picks.** Today polling is skipped when there are no started picks or when the slate is expired. Tracker must poll when it has any unfinished bet whose game is in progress, even if our slate is empty or expired. Both sports poll together regardless of the header toggle.
4. **Stat keying.** Tracker rows are keyed by tracker bet id (not pick id). Match player by ESPN athlete id first, then by normalized name within the team (existing `normName` / `nhlNameKey`). Unmatched = "No stats yet" state (section 8), never a wrong player.
5. **Prior-day results.** On open, any bet from a past slate day that never reached a final: one-shot fetch of that date's scoreboard + box (ESPN `?dates=YYYYMMDD`). See section 7.
6. **Fixtures.** Keep every `?fixture=NAME` page and the `?feed=espnfail / allfail` switches working. The tracker must work in fixture mode against the fixture feeds. Add a fixture-only seed `?trk=demo` that loads in-memory demo bets (never written to `localStorage`): 1 pending Over, 1 live-hitting Over, 1 lost Under, 1 final-hit, 1 parlay of 3 with one dead. This gives QA every state without live games.

---

## 5. The flow at 320 to 430px

### 5.1 My Tracker view, top to bottom

1. Segmented control (section 2).
2. Banner strip (dashed, `--my-soft` fill): "MY TRACKER. Your own notes. Not a Hot Prop Homies pick. Not on the Record." Wraps to 2-3 lines at 320. 13px.
3. `lvupd` line (existing): "Updated 4s ago". Same component, same copy rules.
4. Primary button, full width, 48px tall: **"+ Track a stat"**. Solid `--my-edge` fill, white text 16px/700. Always at the top so it is one thumb-tap from anywhere.
5. Parlays (if any), full width.
6. Singles still in play, then singles finished today. Sort: parlays first, then in-play by game progress (same `pickProgress` order Live uses), then finished.
7. "Yesterday" group, collapsed (section 7).
8. Footer line when 2+ ungrouped singles exist: button **"Make a parlay"** (secondary, 44px, dashed outline).

Layout width: one column (single-card rows) below 600px; two columns from 600px. This differs from Our Picks (2-up) on purpose: tiles here carry a longer player name, a bet line, a number, and a game line, and all of it must wrap, never clip. Max content width stays the page column.

### 5.2 "Track a stat" sheet (the create flow)

A bottom sheet that rises to 92% of the screen height (full width of the column, 16px top radius, grabber bar, dim scrim). Focus trapped; Escape and scrim-tap close; back button on phone closes the sheet, not the page. Reduced motion: no slide, fade 0.

**Step 1: Player**

- Title: "Pick a player". X to close (44px target).
- Search field, 48px tall, autofocus off on first open (so the keyboard does not cover the list); placeholder "Search a player or team". `inputmode="search"`, `autocomplete="off"`, `autocapitalize="words"`. Matching: case-insensitive, accent-insensitive (use `normName`), matches name, team code, or team name. 
- Sport chips under it, 40px tall: `All` `NBA` `NHL`. Default All.
- Result list, grouped by game. Group header (sticky, 13px/700, muted): game line + badge, e.g. "NBA  LAL at DEN. Live, Q3 4:12" or "NHL  BOS at TOR. Starts 7:00 PM". Group order: live games first, then upcoming by start time, then finished (finished games are listed dimmed and marked "Final", and cannot be added; see 5.4).
- Player row: 56px tall, full-width tap target. Left: headshot 32px (reuse `headshot()`, initials fallback). Name 16px/600, wraps to a 2nd line if long, never ellipsis. Under it, 13px muted: team code and position if known, and "On the court" / "Bench" is NOT shown (not in feed). Right: a chevron.
- Players already tracked: still listed; no special treatment (Matt may track two stats on one player).
- Loading: skeleton rows ("Loading tonight's players...").
- No match: "No player named that tonight. Check the spelling, or try a team." and a text link "Clear search".
- List cap: renders at most 60 rows at a time; if more, "Keep typing to narrow it." (13px) at the bottom. Without a search, shows live games' players first.

**Step 2: Stat, side, line** (same sheet, slides in; header has a back arrow "Players")

- Player summary card at top: headshot 40px, name 17px/700 (wraps), game line (status, score) 13px. **Live preview:** if the game is on, a line "Right now: 14 points" / "Right now: 3 shots on goal" in mono 16px. If not started: "Game starts 7:00 PM."
- **Stat**: chips in a wrapping row, each 44px tall, min 88px wide, label 15px/600: NBA `Points` `Rebounds` `Assists` `3-pointers made`; NHL `Shots on goal` `Points`. Single select, none preselected (forces a choice; the Add button stays disabled until stat, side, and line are all set).
- **Side**: two big segments, 48px tall: `Over` `Under`. None preselected.
- **Line**: number field, 52px tall, mono 20px/700, `inputmode="decimal"`, with a `-` and `+` stepper (48px square) either side. Step 0.5. Min 0.5, max 199.5, whole and half numbers both allowed (a whole number line can push). Placeholder "e.g. 24.5". Under it, 13px muted helper: "Use the line from your own bet. It can be any number." When the live stat is known, show a one-tap chip "Start at 14.5" (right now + 0.5) to speed a live add; never suggest a line otherwise (we don't want this to look like a pick or a model line).
- **Preview tile**: below the form, a live preview of the exact tile Matt is about to create (meter, tick, "0 / 24.5 points, needs 25 more"). It updates as he types. This is the confirmation, so no extra confirm dialog.
- **Add button**, sticky at the sheet bottom, 52px, safe-area padded: **"Add to My Tracker"** (disabled until valid; disabled text color meets contrast; helper line above when disabled names what's missing: "Pick a stat, Over or Under, and a line.").
- After Add: the sheet closes, the new tile scrolls into view and pulses its border once (400ms ease-out; reduced motion: no pulse, 2s highlighted border instead). A toast: "Added. Tracking Jokic points." with **Undo** (5s).
- If Matt backs out at step 2, nothing is saved.

Validation errors (inline, under the field, 13px, `--bad`):
- Empty line: "Enter a line."
- Not a number / more than one decimal: "Use a number like 24.5."
- Below 0.5 or above 199.5: "Pick a line from 0.5 to 199.5."
- Quarter lines (e.g. 24.25): rounded input is rejected with "Use .0 or .5 lines."
- Duplicate (same player, stat, side, line, still in play): "You're already tracking that." (Add stays disabled; Matt can change one value.)

### 5.3 Tracked-bet tile (single)

Full-width card, `--surface`, `1.5px dashed var(--my-edge)`, 8px radius, 12px padding, 8px gap between cards.

```
[headshot 28]  Player Name (wraps)             [NBA] [MINE]
Over 24.5 points                              (15px mono, 600)
[meter ===========|----]   [HIT]                 (meter flex, stamp right)
18 / 24.5 points, needs 7 more                (15px mono, 600)
Q3 4:12 · LAL 71-68 DEN                       (13px, wraps)
```

- Name 16px/600 (`--cond`), up to 2 lines, no ellipsis. NBA/NHL badge + MINE tag: both 12px, no-break each, sit top right; if the row is too narrow they drop to a line under the name (flex-wrap), never overlap or clip.
- Bet line: "Over 24.5 points" / "Under 2.5 shots on goal" / "Over 1.5 points" etc. Text in mono 15px, wraps.
- Bar: reuse existing `tracker()` logic and look exactly (pips when line is under 6, otherwise the meter with a tick at the line). Same HIT/LOST rules as Our Picks Live: Over HITs the moment stat > line; Under is LOST the moment stat > line and only HITs at the final. Whole-number lines: stat equal to line at the final = PUSH.
- Number line "18 / 24.5 points, needs 7 more" (existing copy pattern). Under: "2 / 3.5 shots on goal, 1 to spare".
- Stamp: `HIT`, `LOST`, `PUSH`, `VOID` (reuse `.stmp`, 13px min). Pending has no stamp.
- Game line: reuse `gameLine()` output (status, score). Wraps; no ellipsis (this overrides the Live tile's single-line clip for tracker tiles, per the no-cut-off rule).
- Tap anywhere on the tile (not on the select box) = expand to show Edit and Delete (5.5). Min tap area 44px tall.
- In parlay-select mode (5.6) a 28px checkbox appears at the left of the card; tap the whole card to toggle it.
- Finished tile: whole card dims slightly (opacity .85, text stays at AA contrast), border stays dashed (always personal). Result stamp stays.

### 5.4 Adding a bet for a game that already started or ended

- Game in progress: allowed. Current number is used as the starting point. Over HITs immediately if the line is already below the number; show HIT and a note "Already past the line when added." (13px, muted).
- Game starts later: allowed. Tile shows "Starts 7:00 PM" in the game line and "Not started yet" in the number line.
- Game finished: **not allowed** in the picker list for that game (group is dimmed, rows non-tappable, header says "Final"). Reason: tracking a settled number is not tracking. Row tap shows a 13px note "That game is over."
- Player did not dress: allowed to add (we can't know pre-game); shows "Has not played yet", then DNP at final (section 8).

### 5.5 Edit and delete

Tap a tile to expand it in place (full width, `--my-soft` fill, border becomes solid `--my-edge` while open, same pattern as `.lv.open`). Shows:

- **Edit line**: stepper + field (same control as create). **Flip to Over/Under**: segmented. Save button "Save" 44px. A changed bet keeps its tile position and parlay. Editing is blocked once the game is final ("Game is over. Delete it or leave it.").
- Player and stat can't be edited. Helper: "To change the player or the stat, delete this and add a new one."
- **Delete** button, 44px, text `--bad`. No confirm dialog. Instead a toast "Deleted. Undo" (5s). Undo restores to the same slot and parlay.
- If the deleted bet was a parlay leg: see 6.4.

Tap the tile again, or tap Save, to collapse. Only one tile expands at a time.

### 5.6 Parlay

**Make a parlay (select mode)**

1. Tap **Make a parlay** (shown only when 2 or more ungrouped, not-finished-settled singles exist).
2. The view enters select mode: banner swaps to "Pick 2 or 3 bets for your parlay." Each eligible tile shows a checkbox. Tiles already in a parlay are hidden or greyed with "In a parlay" (not selectable).
3. Sticky bar at the bottom above the nav (56px, safe-area padded): left "2 picked", right button **"Make parlay"**. Disabled until 2 are picked. At 3 selected, the remaining unselected tiles dim and tapping one shows the toast "Parlays max out at 3 legs."
4. Tap **Cancel** (sticky bar, left of count) or Escape to leave select mode.
5. Make parlay: the tiles collapse into one parlay card at the position of the topmost leg (animation: tiles slide into the card, 300ms ease-out; reduced motion: instant). Toast: "Parlay made. 2 legs." with Undo (5s).

Rules:
- 2 or 3 legs, no more (Matt's rule). A bet belongs to at most one parlay.
- Legs may be different games and different sports. Two legs on the same player and same stat are not allowed (toast: "That's the same stat twice.").
- Eligible legs: any not-yet-final bet. Final bets can't be added to a parlay; Make parlay hides them.

**Parlay card**

Full-width card, `2px dashed var(--my-edge)` with a `--my-soft` fill, 10px radius, 12px padding.

```
MY PARLAY · 3 legs                       [MINE]
ALIVE   2 of 3 hit                              <- status line (big)
-------------------------------------------------
Jokic  Over 24.5 points      [meter] 18 / 24.5  HIT
Tatum  Over 6.5 rebounds     [meter] 4 / 6.5       
Matthews Over 3.5 shots on goal  [meter] 2 / 3.5
Q3 4:12 · LAL 71-68 DEN       (per leg, 13px)
-------------------------------------------------
[ Ungroup ]
```

- Header: "MY PARLAY · 3 legs" 13px/700 caps, letter-spacing .08em, with the MINE tag. 
- **Overall status** (the big thing; 22px/700 `--head` for the word, 15px mono for the count):
  - `ALIVE` (`--my-text`): no leg has lost, not all legs are done. Count "2 of 3 hit".
  - `ALL HIT` (`--good`): every non-push leg is HIT.
  - `DEAD` (`--bad`): any leg LOST. Count line becomes "Leg 2 lost. Parlay is dead." Dead parlays stay on screen, dimmed, so the remaining legs can still be watched; the card header shows a strike-through-free dimmed treatment (opacity .8, `--bad` left bar 4px). No strike-through text (readability).
  - `PUSH` (muted): every leg pushed or void.
- A leg that pushes or is VOID/DNP at the final is dropped from the parlay (standard sportsbook handling). Status line says "Leg 2 void. Now a 2-leg parlay." Parlay legs count in the header updates ("2 legs, 1 dropped").
- Each leg is its own row (not a 2-up). Row: name 15px/600 wraps; bet text 14px mono wraps; meter; number; per-leg stamp. Leg game line 13px, wraps. Rows are separated by a 1px `--line` rule. Whole leg row tappable to expand Edit/Delete exactly like a single (5.5), inside the card.
- Over legs that already HIT show a green check (and the word HIT, never color alone). Under legs that haven't lost yet show "Holding" until final, then HIT.
- No price, no payout, no odds, no stake. Plainly: "No price. Just tracking."
- **Ungroup** button, 44px, dashed outline: breaks the parlay back into singles in place (no confirm; toast "Ungrouped. Undo").
- Removing a leg (Delete on a leg): if 2 legs remain it stays a parlay; if only 1 would remain, the parlay auto-ungroups with the toast "Parlay needs 2 legs. Ungrouped."

---

## 6. State rules in one table

| State | Single tile | Parlay |
|---|---|---|
| Not started | "Not started yet", game line "Starts 7:00 PM", empty meter | Header status ALIVE "0 of 2 hit" |
| In play, pending | Meter + "14 / 24.5 points, needs 11 more" | ALIVE, "n of N hit" |
| Over passes line | HIT stamp, green meter (locks) | Leg HIT; parlay stays ALIVE until all legs done |
| Under passes line | LOST stamp (locks) | Parlay DEAD immediately |
| Final, Over short | LOST at the final | Parlay DEAD |
| Final, Under held | HIT at the final | Leg HIT |
| Whole line, equal at final | PUSH | Leg dropped |
| DNP at final | VOID "Did not play" | Leg dropped |
| Game final, result saved | Tile settles, stays on view until next slate day | `ALL HIT`, `DEAD`, or `PUSH` |

The "locks" detail: once an Over has HIT it stays HIT; once an Under has LOST it stays LOST, even if the feed later glitches to a lower number. Store the settled result on the bet when first seen (see section 10).

---

## 7. After the game ends, and the next day

- **Same night:** a finished bet stays in the list with its stamp. Finished bets sort below in-play bets. A parlay whose last leg ends settles to ALL HIT / DEAD / PUSH and stays.
- **No running record.** There is deliberately no W-L total, no units, no streak. A small line above the list, only when something finished tonight: "Tonight's tracker: 2 hit, 1 missed." 14px, muted, never in `--head` font and never next to the Our Picks "Tonight" line. Don't show it on the next day. Reason: a personal W-L next to our Record invites exactly the mixup we are avoiding.
- **Slate rollover (the next slate day, same cutoff `slateDay()` uses):** all finished bets and parlays move into a collapsed group **"Yesterday (4)"**, 44px header row, chevron. Tapping expands them (same tiles, read-only, dimmed). Anything older than 2 days is deleted automatically at open. Unfinished bets whose game never reached a final (e.g. postponed) go to Yesterday as `VOID` with note "Game did not finish."
- **Clear finished** button (44px, text button, `--muted`) at the bottom of the list, shown when any finished bet exists. One tap removes all finished singles and parlays; toast "Cleared. Undo" (5s).
- **Closed the app before the game ended:** on next open, any bet whose game was not final is re-checked once using that date's scoreboard + box score (section 4.5). If found final: stamped normally. If the feed can't confirm: stamp `?` (a muted outline stamp, not a result), message "Final not saved. Mark it yourself." with two small buttons **"Hit"** and **"Missed"**. Matt's choice is saved and the stamp changes to HIT / LOST. Never guess.

---

## 8. Empty and error states (exact copy)

| Situation | Where | Copy |
|---|---|---|
| Nothing tracked yet | My Tracker body | Title: "Nothing tracked yet." Body: "Pick a player, a stat, and a line. We'll watch it for you." Button: "+ Track a stat" (same primary button). 13px note: "Stays on this phone only." |
| No games tonight | Sheet step 1 | "No games tonight. Come back on a game day." |
| Players list loading | Sheet | "Loading tonight's players..." (skeleton rows) |
| Players list failed | Sheet | "Couldn't load the players list. Try again." Button "Try again". |
| Pre-game player data thin | Sheet group | "Players show once the box score opens (usually at tip)." |
| Live scores unavailable | Above list | Reuse: "Live scores unavailable. Trying again every 10 seconds." (amber `lvupd.bad`) |
| Stats unavailable for one bet | Tile number line | "Live stats unavailable" (feed is down); previous number stays visible with "Last seen 14 / 24.5" in muted if known |
| Not started | Tile number line | "Not started yet" |
| Game on, player not in box yet | Tile number line | "No stats yet" |
| Player did not play, game live | Tile number line | "Has not played yet" |
| Player did not play, game final | Tile + stamp | Stamp VOID, line "Did not play" |
| Player not found in feed after the game starts (no match) | Tile number line | "Can't find him in the live numbers." and under it, 13px: "Delete this and add him again." |
| Game moved / not on today's scoreboard | Tile | "This game isn't on tonight's schedule." with a Delete button inline |
| Storage unavailable (private window, blocked) | Banner above list, amber | "Can't save on this browser. Your tracker will be gone when you close this tab." (shown once per open; bets still work in memory) |
| Storage full | Toast | "Phone storage is full. That one wasn't saved." |
| Corrupt storage | Silent reset + toast | "Your saved tracker couldn't be read, so it was cleared." Only after a try/catch parse failure; never throws |
| Tracker at 20 bets | Add attempt | "20 is the max. Delete one to add another." (limit: 20 singles total) |
| Parlay select with <2 eligible | Make a parlay hidden | n/a |

All error copy is 13px minimum, in-flow, wraps, never truncated.

---

## 9. Layout and no-cut-off rules (carry-over from the shipped rule)

At 320, 340, 380, and 430 px wide, and in both Night and Day themes:

- No ellipsis anywhere in My Tracker, the sheet, the toasts. Nothing clipped, nothing horizontally scrolling. Long names ("Shai Gilgeous-Alexander", "Giannis Antetokounmpo", "Nikita Kucherov") wrap to two lines.
- Smallest text anywhere: 13px. Names 15 to 17px. Numbers 15 to 20px mono.
- Pills (stamps, badges, MINE tag, count, "2 of 3 hit") each stay one no-break unit with their number: `white-space:nowrap`, never split "2 of 3 hit" or "HIT" from its box. If the row is too narrow the pill drops to the next line whole.
- Tap targets 44px minimum height and width, with 8px minimum gap between neighbors (sheet chips, steppers, checkboxes).
- Text contrast AA (4.5:1) against its fill in both themes, including the dimmed (finished / dead) states and the `--my-text` on `--my-soft`.
- Sheet and sticky bars respect `env(safe-area-inset-bottom)`. The on-screen keyboard must not hide the Add button or the field being typed in (scroll the focused field into view; `visualViewport` aware).
- Wider than 430: the page column stays centered as today; the sheet is max 480px wide, centered. Two-column tiles from 600px; parlay cards stay full width.

---

## 10. Storage (plain)

There is no backend. My Tracker is saved **on this phone, in this browser, only**.

What that means for Matt:
- It stays when he closes the page and comes back, as long as he uses the same phone and the same browser.
- It does **not** follow him to another phone, another browser (Safari vs Chrome), or a computer.
- Clearing site data, "private/incognito" browsing, or iOS clearing storage after weeks of not opening the site will erase it.
- It cannot be backed up or seen by the team. It never goes to GitHub, Discord, or the Record.

Spec:
- Key: `hph.tracker.v1`. One JSON object: `{ v: 1, bets: [...], parlays: [...], day: "YYYY-MM-DD" }`. Per bet: `id` (random, short), `sport`, `gameDay`, `gameKey` (sport + ESPN event id), `pid` (ESPN athlete id, if known), `name`, `team`, `stat` (one of `points`, `rebounds`, `assists`, `threes`, `shots`), `side` (`over` / `under`), `line` (number, half steps), `createdAt`, `settled` (null, or `{result: 'W'|'L'|'PUSH'|'VOID', actual: number, at}`), `manual` (true when Matt marked it), `parlayId` (null or string). Per parlay: `id`, `legIds` (2 or 3), `createdAt`.
- Every read and write in try/catch. If `localStorage` throws, keep everything in memory and show the storage banner (section 8). Page never breaks.
- Write on every change, debounced 250ms; also on `visibilitychange` hidden.
- Cap: 20 singles and 6 parlays total live in storage. Anything older than 2 days is purged at open (section 7).
- Last-open segment choice stored separately: `hph.live.seg` = `picks` | `tracker`.
- Never store: odds, prices, anything about a real pick, any personal data. Never send tracker contents anywhere (no analytics, no network calls beyond the existing public score feeds).
- Reset lives in My Tracker only (not Info): footer text button "Delete everything in My Tracker" (44px, `--bad`), requires one confirm tap ("Delete all 7? This can't be undone." [Delete all] [Cancel]). This is the one place a confirm is used, because it is destructive and large.

---

## 11. Motion

| What | Duration / easing | Reduced motion |
|---|---|---|
| Sheet rise / dismiss | 260ms `cubic-bezier(.2,.8,.2,1)` | Instant, no slide |
| Step 1 to step 2 slide | 200ms ease-out | Instant |
| New tile border pulse | 400ms ease-out, once | 2s static highlighted border |
| Tiles gather into parlay | 300ms ease-out | Instant |
| Meter fill on poll updates | 400ms width ease | Instant |
| HIT stamp lands | 180ms scale from 1.15 to 1 | No scale |
| Toast in / out | 200ms fade + 8px rise | Fade only, 0 rise |

No sound, no haptic requirement. Optional: `navigator.vibrate(15)` when a tracked Over flips to HIT while the tab is open (ignored if unsupported). Not required.

---

## 12. Accessibility

- Segmented control is a `role="tablist"`-style pair of buttons with `aria-pressed`/`aria-selected`; sheet is `role="dialog" aria-modal="true"` with a labelled title and a focus trap; stamps and status have visible text, never color alone; `lvupd` stays `role="status"`.
- Meters are `aria-hidden` as today, with the text line carrying the meaning ("18 of 24.5 points, needs 7 more"). Parlay status word has `aria-live="polite"` so a flip to DEAD / ALL HIT is announced.
- Select-mode checkboxes are real `<input type="checkbox">` with 28px visible box inside a 44px target and an accessible name "Select Jokic over 24.5 points".

---

## 13. Discord

**No Discord change.** My Tracker never touches Discord, the Record, `status.json`, or any workflow. Do not add a share-to-Discord button.

---

## 14. Acceptance criteria and QA test cases

QA checks each at 320, 340, 380, 430 px, Night and Day, and with Reduce Motion on/off.

**Placement and separation**
1. Live tab shows `Our Picks | My Tracker` segmented control; default Our Picks; remembers last choice; `#tracker` opens My Tracker.
2. My Tracker never renders any Our Picks tiles or Tonight line; Our Picks never renders tracker tiles.
3. Banner "MY TRACKER. Your own notes. Not a Hot Prop Homies pick. Not on the Record." is always visible on My Tracker and wraps with no clip.
4. Every tile/parlay has dashed `--my-edge` border and a MINE tag. No price, EV, model%, or units anywhere in the tracker.
5. Header sport switch set to NBA, NHL, or All: My Tracker content unchanged; one-line note shown on single-sport only.

**Creating**
6. "+ Track a stat" opens the sheet; search filters by name, accent-insensitive ("Jokic" finds "Jokić"; "bos" finds Celtics/Bruins players), and by team.
7. Sport chips All/NBA/NHL filter the list; groups sorted live, then upcoming, then final (final rows non-tappable).
8. NBA shows only Points, Rebounds, Assists, 3-pointers made; NHL shows only Shots on goal, Points. No other stat appears.
9. Add is disabled until stat, side, and line are set; helper names what's missing.
10. Line validation: empty, "abc", 24.25, 0, 200, "24.5.5" all show the specified message; 24.5, 25, 0.5, 199.5 accepted; stepper moves 0.5, clamps at both ends.
11. Preview tile matches the tile created. Add creates exactly one tile, scrolls to it, shows toast with Undo; Undo removes it.
12. Duplicate (same player, stat, side, line, in play) is blocked with "You're already tracking that."
13. Add on a game in progress with the line already passed shows HIT and the "Already past the line when added." note.
14. 21st bet blocked with the max message.

**Tracking (use fixtures + `?trk=demo`; also a live game night)**
15. Number, meter, and game line update within one poll (10s) without a full re-render flash; "Updated Xs ago" ticks.
16. Over hits the moment stat exceeds the line and never reverts; Under is LOST the moment stat exceeds the line and never reverts; Under only HITs at the final.
17. Whole-number line, stat equals line at the final: PUSH. DNP at final: VOID "Did not play".
18. Over at a final below the line: LOST.
19. `?feed=espnfail`: falls back to NBA.com and tiles still work (NBA). `?feed=allfail`: "Live scores unavailable. Trying again every 10 seconds." amber; tiles keep last numbers with "Last seen ..." and recover on the next good poll.
20. Player not matched in box: "Can't find him in the live numbers." Not a wrong player's number.
21. A tracked bet in a game with no pick still polls and updates; poll runs when slate is empty/expired.
22. Polling only while Live is open and page visible; none while on other tabs or when hidden.

**Edit / delete**
23. Tap tile expands in place; only one open at a time; Edit line and Flip side save and keep position and parlay; blocked when final.
24. Delete shows toast with Undo for 5s and restores the same slot (and parlay membership). No confirm dialog on a single delete.

**Parlay**
25. "Make a parlay" appears only with 2+ eligible singles. Select mode: checkboxes, count in the sticky bar, Make parlay disabled until 2, at 3 others dim with "Parlays max out at 3 legs."
26. Parlay of 2 and of 3 legs displays each leg full width with its own meter, number, game line, stamp, plus one overall status word and count.
27. Status truth table: all pending = ALIVE "0 of N hit"; some HIT, none lost = ALIVE "k of N hit"; any LOST (including an Under that passes the line mid-game) = DEAD immediately with "Leg k lost. Parlay is dead."; all legs HIT = ALL HIT; one leg void/push at the final is dropped and the count updates; all void/push = PUSH.
28. Mixed-sport parlay (one NBA leg, one NHL leg) works. Same player + same stat twice is refused.
29. Ungroup returns singles in place, with Undo. Deleting a leg from a 3-leg parlay leaves a 2-leg parlay; deleting from a 2-leg parlay auto-ungroups with the specified toast.
30. A bet can only be in one parlay; grouped bets are not selectable for a second parlay.

**After the game / next day**
31. Finished bets stay with stamps the same night, sorted below in-play. "Tonight's tracker: 2 hit, 1 missed." appears only when something finished, and is not styled like or placed next to the Our Picks Tonight line. No lifetime W-L anywhere.
32. After the next slate rollover finished bets appear under collapsed "Yesterday (n)"; bets older than 2 days are gone on open; "Clear finished" works with Undo.
33. Close the page mid-game, reopen next day: unresolved bets are re-checked once; found = stamped; not found = `?` stamp with "Final not saved. Mark it yourself." and Hit / Missed buttons that persist.

**Storage**
34. Reload: all bets, parlays, and the last segment persist. Open the same URL in another browser/profile: tracker is empty (expected, per-device). Copy in the empty state says "Stays on this phone only."
35. With localStorage blocked (private mode / throwing accessor): page doesn't break, tracker works in memory, amber banner shown. With corrupt JSON in the key: silent reset + toast, no console error that blocks render. With storage full: toast, bet not saved.
36. "Delete everything in My Tracker" needs one confirm; Cancel keeps all.

**Isolation (hard)**
37. Nothing in the tracker appears in Record, Lab, Our Picks "Tonight", status, or any network call to our own data/ files; no write to anything except `hph.tracker.v1` and `hph.live.seg`. No change to Discord, workflows, or `data/`.
38. All existing `?fixture=NAME` pages render exactly as before; Our Picks Live unchanged except the new segmented control above it.

**Readability**
39. At 320/340/380/430: no ellipsis, no horizontal scroll, no clipped text anywhere in My Tracker or the sheet; names wrap; every pill is a single no-break unit; minimum 13px; 44px tap targets; AA contrast in both themes (including dimmed finished/dead states).
40. Keyboard open on a 380px phone: Add button and the active field remain visible.

---

## 15. Open items for CEO (not blocking the spec)

- Engineer to verify the ESPN team-roster fetch (section 4.1c). If it is not browser-safe, upcoming-game players come from the slate only, with the fallback copy; the spec still works.
- Optional v2 (not in this spec): goals-only and assists-only (NHL), PRA combo (NBA), tracker odds/payout field. None are offered until UX writes copy for them.
- UX sign-off required on the built result at 380px before QA.
