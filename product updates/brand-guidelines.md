# Hot Prop Homies — Brand Guidelines
**Version 1.1 · November 2026**

---

## 0. The One Sentence

> *Hot Prop Homies is the sharp friend in your group chat — a fully automated picks engine that runs itself so you just show up, see the edge, and bet.*

This is the decision filter. Every design and copy choice passes through it.

---

## 1. Name

### ⬜ MATT APPROVES THIS

**Recommendation: Keep "Hot Prop Homies"**

It's the most distinctive name in sports betting. No one else has it. It honors the gaming origin ("hot drop homies"), is specific to prop bets, and carries the friend-group energy. The in-product names ("Prop Check NHL", "Prop Check NBA") go away and become "HPH · NHL" and "HPH · NBA" or just the sport name under the brand.

**Two alternatives if Matt wants them:**

| Name | Vibe | Why it works | Why it doesn't |
|---|---|---|---|
| **Hot Drops** | Tight, punchy, gaming origin explicit | 2 words, punchier, universal | Loses "Prop" specificity and "Homies" warmth |
| **The Flame Homies** | Mascot-forward, crew energy | Names the mascot directly | Less prop-bet connection |

**Decision needed from Matt:** Keep "Hot Prop Homies" / try "Hot Drops" / other?

---

## 2. Brand Positioning

**Who:** Matt and his friend — casual bettors who want an edge without the work.  
**What:** A fully automated prop picks engine. No human involvement. Just open it and bet.  
**Different:** It runs itself. It looks like it was built by a pro. It's actually for friends.

**Tagline options (for Discord bot intro / Discord server header):**
- "Your edge, automated." 
- "The pick is already there."
- "Fire picks. No work."

---

## 3. Visual Identity

### 3a. Mascot — The Flame ✅ LOCKED

**Official mascot file:** `icons/Official logo.jpg`

**Character DNA:**
- Disembodied dark shadowy head, floating on pure black — no body, no shoulders
- Glowing **cyan eyes**: sharp rectangular brow bars + oval lower iris, angled angrily inward
- **Flame hood**: cyan at outer edges, hot magenta-pink in the middle, deep violet body — rises upward from the head
- Pure black background — neon colors sing against it

**Icon files generated from official logo:**

| File | Size | Used by |
|---|---|---|
| `icons/favicon-32.png` | 32×32 | Root + NBA browser tab |
| `icons/apple-touch-icon.png` | 180×180 | NHL home screen |
| `icons/apple-touch-icon-v2.png` | 180×180 | NBA home screen |
| `icons/apple-touch-icon-v3.png` | 180×180 | Root home screen |
| `icons/icon-192.png` | 192×192 | NHL PWA |
| `icons/icon-512.png` | 512×512 | PWA splash |

---

### 3b. Color Palette

The existing "Ballpark" colors are disconnected from the brand DNA. Colors extracted directly from the mascot icons.

**Three identity colors (non-negotiable):**
| Token | Hex | Name | Use |
|---|---|---|---|
| `--brand-pink` | `#E8187A` | Hot Magenta | Primary CTA, wins, HR button, fire |
| `--brand-violet` | `#5B1FA0` | Deep Violet | Background gradients, depth |
| `--brand-cyan` | `#17E9FF` | Electric Cyan | Live indicator, links, data, DK button, eyes |

**Light Mode — "Flame Day"**
```css
--bg: #F2EFFF;        /* light lavender — purple-tinted */
--surface: #FAFAFF;
--raise: #E8E3F8;
--line: #CBC3EC;
--line2: #A99FD0;
--fg: #0E0820;        /* deep purple-black */
--fg2: #261C52;
--muted: #695D94;

--accent: #1A5EC8;              /* data/DK blue */
--accent-soft: rgba(26,94,200,.10);
--accent-rgb: 26,94,200;
--on-accent: #FFFFFF;

--primary: #C8107A;             /* hot pink — HR button, wins */
--on-primary: #FFFFFF;
--selected-bg: rgba(200,16,122,.10);
--selected-text: #960A5A;

--good: #C8107A;
--good-soft: rgba(200,16,122,.08);
--good-rgb: 200,16,122;
--warn: #A05000;
--warn-soft: rgba(160,80,0,.08);
--bad: #695D94;
--bad-soft: rgba(105,93,148,.10);
--bad-rgb: 105,93,148;
```

**Dark Mode — "Flame Night" (the brand's true form)**
```css
--bg: #090812;        /* near-black, purple undertone */
--surface: #120F1E;
--raise: #1C1830;
--line: #2E2850;
--line2: #3D3666;
--fg: #F0EDF8;
--fg2: #C0B8E0;
--muted: #7A74A0;

--accent: #17E9FF;              /* electric cyan */
--accent-soft: rgba(23,233,255,.12);
--accent-rgb: 23,233,255;
--on-accent: #090812;

--primary: #E8187A;             /* hot magenta */
--on-primary: #FFFFFF;
--selected-bg: rgba(232,24,122,.15);
--selected-text: #F060A8;

--good: #E8187A;
--good-soft: rgba(232,24,122,.12);
--good-rgb: 232,24,122;
--warn: #FFB800;
--warn-soft: rgba(255,184,0,.12);
--bad: #7A74A0;
--bad-soft: rgba(122,116,160,.15);
--bad-rgb: 122,116,160;
```

**Emotional rationale:**  
Hot magenta = heat, fire, action, win. Electric cyan = data, precision, the eyes that see everything. Deep violet = depth, mystique, the shadow underneath. Together: a friend who's both dangerous and smart. Light mode = daytime, readable, clean. Dark mode = the real identity, the icons come alive, the brand is at home.

**Contrast check (WCAG AA required for phone in sunlight):**
- `--fg` (#0E0820) on `--bg` (#F2EFFF): ~18:1 ✓
- `--primary` (#C8107A) on white: ~4.8:1 ✓ (AA large text)
- `--fg` (#F0EDF8) on `--bg` (#090812) dark: ~18:1 ✓
- `--accent` (#17E9FF) on dark `--bg`: ~10:1 ✓

---

### 3c. Typography

**Recommendation:**

| Role | Font | Source | Rationale |
|---|---|---|---|
| Display / Logo / H1 | **Orbitron** | Google Fonts | Geometric, futuristic, HUD-style. Perfect for the wordmark and hero. The WOW factor in type. |
| Data / Numbers / Odds | **IBM Plex Mono** | Google Fonts | Keep. Tight, monospaced, reads odds/stats perfectly. |
| UI / Body / Everything else | **IBM Plex Sans** | Google Fonts | Keep. Proven, legible, data-smart, 8 weights. |

**Usage rules:**
- Orbitron: brand name only, section headers, stat callouts when making a hero moment. Never for body copy.
- IBM Plex Mono: all numbers, odds, record stats, percentages. Always tabular-nums.
- IBM Plex Sans: everything else. 400 and 600 weights do all the heavy lifting.

**CSS:**
```css
--head: "Orbitron", "Graduate", Georgia, serif;
--num: "IBM Plex Mono", ui-monospace, Menlo, monospace;
--body: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
--cond: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
```

---

### 3d. Logo / Wordmark

**Three variants:**

**1. Full Horizontal (primary)**  
`[Flame head icon — 32px] HOT PROP HOMIES` — Orbitron 700, all caps, spaced 0.08em tracking. Icon left-aligned to cap height. Used in the app header.

**2. Stacked (compact)**  
Flame head icon centered, 48px. Below: `HOT PROP` (line 1) / `HOMIES` (line 2), Orbitron 700, center-aligned. Used in Discord bot profile.

**3. Icon Only (minimum)**  
Just the flame head (hood + flame crown + cyan eyes). No text. Used for home screen icon (512px), small Discord avatar, favicon. This is the existing mascot — no changes needed if Direction A is chosen.

---

## 4. Voice & Tone

**The character speaking:** A sharp friend who already did the homework. Not an analyst, not a robot, not a warning label. The tone is "here's what I'd do" — confident, brief, specific.

### 7 Rules

1. **Talk like a friend tipping you off, not a finance dashboard.** "He's been a machine at home — take the over." Not "player shows elevated performance metrics in home environments."

2. **Be direct. Don't hedge.** If it's a pick, commit to it. "Take it." Not "this appears potentially worth considering."

3. **Short sentences. Never explain the model.** The picks are the product. Trust the work, don't document it.

4. **Numbers carry the story — let them.** Show the stat. Add one word of context if needed. That's it.

5. **Wins feel hot. Losses feel quiet.** Don't apologize for misses or over-celebrate wins. The record is the proof.

6. **Discord messages = text from a friend.** Casual, specific, actionable. Names, not positions. Hot take energy.

7. **On a phone, every word costs.** If you can cut it, cut it. Labels should be instantly understood or not exist.

### Before / After Rewrites

| Before (current) | After (brand voice) |
|---|---|
| "No picks available at this time. Check back later." | "Nothing tonight. Lines moved after I ran. Next game tomorrow." |
| "Pick posted: Nikola Jokić Over 24.5 Points (-115)" | "Jokić O24.5 · -115 · Take it" |
| "Player prop analysis indicates favorable over threshold conditions." | "He's hit this 7 of his last 9. Take the over." |

---

## 5. Design System Seed — Full CSS Token Set

This is the complete handoff to UX and Builder. Wire these variables into `index.html`.

```css
:root {
  /* ── BRAND IDENTITY ── */
  --brand-pink:   #E8187A;
  --brand-violet: #5B1FA0;
  --brand-cyan:   #17E9FF;
  --brand-black:  #090812;

  /* ── LIGHT MODE (Flame Day) ── */
  --bg:        #F2EFFF;
  --surface:   #FAFAFF;
  --raise:     #E8E3F8;
  --line:      #CBC3EC;
  --line2:     #A99FD0;
  --fg:        #0E0820;
  --fg2:       #261C52;
  --muted:     #695D94;

  --accent:       #1A5EC8;
  --accent-soft:  rgba(26,94,200,.10);
  --accent-rgb:   26,94,200;
  --on-accent:    #FFFFFF;

  --primary:      #C8107A;
  --primary-soft: rgba(200,16,122,.10);
  --primary-rgb:  200,16,122;
  --on-primary:   #FFFFFF;
  --selected-bg:  rgba(200,16,122,.10);
  --selected-text:#960A5A;

  --good:         #C8107A;
  --good-soft:    rgba(200,16,122,.08);
  --good-rgb:     200,16,122;
  --warn:         #A05000;
  --warn-soft:    rgba(160,80,0,.08);
  --bad:          #695D94;
  --bad-soft:     rgba(105,93,148,.10);
  --bad-rgb:      105,93,148;

  /* ── TYPOGRAPHY ── */
  --head: "Orbitron", "Graduate", Georgia, serif;
  --num:  "IBM Plex Mono", ui-monospace, Menlo, monospace;
  --body: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  --cond: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;

  /* ── RADII ── */
  --r-sm:   4px;
  --r-md:   8px;
  --r-lg:   12px;
  --r-xl:   20px;
  --r-pill: 9999px;

  /* ── SPACING ── */
  --sp-1: 4px;
  --sp-2: 8px;
  --sp-3: 12px;
  --sp-4: 16px;
  --sp-5: 24px;
  --sp-6: 32px;
  --sp-7: 48px;

  /* ── SHADOWS (light mode) ── */
  --shadow-sm:   0 1px 3px rgba(14,8,32,.08), 0 1px 2px rgba(14,8,32,.06);
  --shadow-md:   0 4px 12px rgba(14,8,32,.10), 0 2px 4px rgba(14,8,32,.06);
  --shadow-glow: 0 0 20px rgba(200,16,122,.20);  /* hot pick glow */
  --shadow-cyan: 0 0 20px rgba(23,233,255,.20);  /* data/live glow */

  /* ── FONT SIZES ── */
  --text-xs:   10.5px;
  --text-sm:   12px;
  --text-base: 14px;
  --text-md:   16px;
  --text-lg:   18px;
  --text-xl:   22px;
  --text-2xl:  28px;

  /* ── COMPONENT SIZING (preserve from current) ── */
  --w: clamp(52px,14.5vw,60px);
  --h: clamp(50px,7.2vh,58px);
  --sab: env(safe-area-inset-bottom,0px);
  --sat: env(safe-area-inset-top,0px);
  --sal: env(safe-area-inset-left,0px);

  color-scheme: light;
}

@media (prefers-color-scheme: dark) {
  :root {
    /* ── DARK MODE (Flame Night — the brand's true form) ── */
    --bg:        #090812;
    --surface:   #120F1E;
    --raise:     #1C1830;
    --line:      #2E2850;
    --line2:     #3D3666;
    --fg:        #F0EDF8;
    --fg2:       #C0B8E0;
    --muted:     #7A74A0;

    --accent:       #17E9FF;
    --accent-soft:  rgba(23,233,255,.12);
    --accent-rgb:   23,233,255;
    --on-accent:    #090812;

    --primary:      #E8187A;
    --primary-soft: rgba(232,24,122,.15);
    --primary-rgb:  232,24,122;
    --on-primary:   #FFFFFF;
    --selected-bg:  rgba(232,24,122,.15);
    --selected-text:#F060A8;

    --good:         #E8187A;
    --good-soft:    rgba(232,24,122,.12);
    --good-rgb:     232,24,122;
    --warn:         #FFB800;
    --warn-soft:    rgba(255,184,0,.12);
    --bad:          #7A74A0;
    --bad-soft:     rgba(122,116,160,.15);
    --bad-rgb:      122,116,160;

    --shadow-sm:   0 1px 3px rgba(0,0,0,.30), 0 1px 2px rgba(0,0,0,.20);
    --shadow-md:   0 4px 12px rgba(0,0,0,.40), 0 2px 4px rgba(0,0,0,.20);
    --shadow-glow: 0 0 24px rgba(232,24,122,.35);
    --shadow-cyan: 0 0 24px rgba(23,233,255,.30);

    color-scheme: dark;
  }
}
```

---

## 6. WOW Factor Spec

**The moment:** When Matt opens the page, the first thing he sees is the mascot icon — large, the flame actually subtly pulses (CSS animation, `@keyframes flame-pulse` on the `filter: drop-shadow`). Below it: the brand name in Orbitron. Below that: today's picks. The mascot is the hero, not a logo in a corner.

**Light mode hero:** Icon at ~72px with a hot magenta glow (`--shadow-glow`). Name in Orbitron 700, 22px.  
**Dark mode hero:** Same but the glow is brighter, the black background matches the icons exactly — the character looks like it's floating in space. This is the WOW.

**Animation (CSS only, no JS):**
```css
@keyframes flame-pulse {
  0%, 100% { filter: drop-shadow(0 0 8px rgba(232,24,122,.4)); }
  50%       { filter: drop-shadow(0 0 18px rgba(232,24,122,.8)) 
                       drop-shadow(0 0 32px rgba(23,233,255,.3)); }
}
.mascot-hero { animation: flame-pulse 2.4s ease-in-out infinite; }
```

---

## 7. Surface Rules

| Surface | Logo variant | Dark/Light | Font treatment |
|---|---|---|---|
| Web page header | Icon-only (32px) + wordmark | Follows device theme | Orbitron, 14px |
| Discord bot avatar | Icon-only | Always dark bg | n/a |
| iOS home screen | Icon-only (512px) | Dark bg on icon | n/a |
| Discord pick message | n/a | Dark context | IBM Plex Sans, brand voice |

---

## 8. What Replaces "Prop Check"

The page title `<h1>`, document title, and Discord bot name all currently use "Prop Check." Replace as follows:

| Was | Now |
|---|---|
| "Prop Check NHL" | "HPH · NHL" or just "NHL Picks" |
| "Prop Check NBA" | "HPH · NBA" or just "NBA Picks" |
| Discord bot name | "Hot Prop Homies" or "🔥 HPH Bot" |
| Page `<title>` | "Hot Prop Homies" |

---

## 9. Handoff Checklist

- [ ] **Matt approves:** Name choice (§1)
- [ ] **Matt approves:** Mascot direction A / B / C (§3a)
- [ ] **Matt approves:** Color palette (Flame Day + Flame Night) (§3b)
- [ ] UX Expert: implement tokens from §5, voice from §4
- [ ] Builder: wire CSS tokens, update `<title>` and h1 strings, add Orbitron font import
- [ ] Builder: add `flame-pulse` animation to mascot icon on page
- [ ] QA: audit all UI strings against voice guide §4

---

*Brand Strategist agent — Hot Prop Homies — Nov 2026*
