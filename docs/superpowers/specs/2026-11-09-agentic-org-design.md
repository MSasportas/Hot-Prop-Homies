# Hot Prop Homies: Agentic Org Design
_2026-11-09_

## Intent and Why

The two products (Prop Check NHL, Prop Check NBA) run themselves via GitHub Actions. They are the company's revenue engine. The CEO's job is to manage and improve them — changing rules, shipping fixes, expanding markets, reviewing results — without Matt ever touching the code or coordinating the work.

Today every Claude Code session is one Claude doing everything. This design replaces that with a real org: a persistent CEO Matt speaks to, backed by specialists who actually execute.

## Goals

- Matt talks to one agent: the CEO. Always. That never changes.
- The CEO delegates real work to real specialists, who run as sub-sessions with focused context.
- Each specialist knows their domain deeply and nothing else.
- Both products (NHL and NBA) are under one CEO.
- The org runs the products. The products run themselves.

## Non-Goals

- Not merging the two codebases or pipelines into one repo.
- Not changing how automated picks are generated.
- Not giving Matt a new interface — he still uses the live pages and Discord.

## Anti-Goals

- A CEO that asks Matt for clarification on decisions the team can make themselves.
- Specialists that re-read the whole codebase every time (expensive, slow).
- One session pretending to be multiple people (the status quo).

## The Org Structure

```
Matt
 └── CEO  (this session, Hot Prop Homies root)
       ├── NHL Sharp Director   → owns NHL edge, rules, pick logic
       ├── NBA Sharp Director   → owns NBA edge, rules, pick logic
       ├── Data Scientist       → cross-sport: record, model, samples, evidence
       ├── UX/UI Expert         → cross-sport: both pages, phone-first
       ├── QA Team              → cross-sport: browser tests, 380px, sign-off
       └── Research Agent       → cross-sport: hunts new edges, writes research/ only
```

## How It Works

### The CEO (this folder)

`C:\Users\TheClaw\Claude Code\Hot Prop Homies` is the CEO's home. When Matt opens this folder in Claude Code, he is talking to the CEO.

The CEO's CLAUDE.md (at this root) gives it:
- Company context: what both products are, how they're judged, Matt's fixed rules
- Pointers to both sport repos (NHL and NBA subfolders)
- Knowledge of the team: who each specialist is and when to call them
- The delegation protocol: how to spawn a specialist, what brief to give them, how to synthesize their output

The CEO does **not** read all of TEAM.md for each sport on every session. It knows the shape of each product and pulls details only when needed.

### Delegation Protocol

When Matt asks the CEO for something non-trivial, the CEO:

1. **Identifies which specialist(s)** own that work (Sharp Director for rule changes, DS for record questions, UX for page changes, etc.)
2. **Spawns them as sub-sessions** via Claude Code's session system, each with a focused brief that includes only their relevant context (their sport's TEAM.md, their files, their scope)
3. **Collects their output** — sub-sessions commit changes or return findings
4. **Synthesizes and reports to Matt** — one clear answer, not a transcript of agent chatter

The CEO never does the specialist's work itself. It routes, synthesizes, and decides.

### When Multiple Specialists Are Needed

Example: Matt says "our NHL shots edge is slipping, what should we change?"

1. CEO spawns **NHL Sharp Director** → reviews recent record, current rules, gap vs market
2. CEO spawns **Data Scientist** → pulls record stats, hit rates by bucket, CLV
3. Both run in parallel, report findings
4. CEO synthesizes → presents Matt with a proposed rule change and the evidence behind it
5. Matt says yes/no → CEO dispatches **Builder + QA** to ship it

Matt sees: one conversation. Behind it: 4-5 specialists that ran and reported.

### The Two Directors

**NHL Sharp Director** (`NHL/` subfolder context):
- Owns `config/rules.json`, the gap+guard thresholds, eligibility rules
- Knows the full record and what's been tried
- Makes the final call on what gets picked and why
- Consults DS for sample sizes before recommending rule changes

**NBA Sharp Director** (`NBA/` subfolder context):
- Owns NBA's pick logic, Pinnacle fair-price rule, market selection (rebounds, points, assists, 3PM)
- Knows NBA's open items (parlays, round robins, DK vs HR) and owns deciding them
- Same authority as NHL Sharp, different sport

The Directors do not cross-pollinate by default. They share the same CEO and DS, which is how learnings transfer.

### The Data Scientist

Cross-sport. Owns:
- Both records (NHL `data/record/`, NBA equivalent)
- Shadow logs, CLV, hit rates, edge evidence
- Sample sizing: tells the Sharp when a sample is big enough to act on
- Model calibration (NHL blend weight, NBA scoring model)

The DS is the gatekeeper on evidence. No rule change ships without a DS sign-off on the sample.

### UX/UI Expert

Cross-sport. Owns both `index.html` pages. Knows:
- Phone-first (380px), dark mode (NHL) / light mode (NBA)
- The tab structure, pick cards, record view
- What Matt can and cannot do from his phone

Dispatched whenever a page changes. Never touches backend logic.

### QA Team

Cross-sport. Gets dispatched **after** every build, with fresh eyes — it has not seen the build it is testing. Always tests in a real browser at 380px. Signs off before anything ships.

### Research Agent

Cross-sport but sport-specific runs. Owns:
- `NHL/research/` and `NBA/research/` directories
- Writes research output only — never production code, rules, or picks
- Runs edge hypotheses, reports findings to the CEO
- The CEO decides whether a finding becomes a rule change (which then goes to the Sharp)

## The Files

### CEO's CLAUDE.md (to be created at root)

`C:\Users\TheClaw\Claude Code\Hot Prop Homies\CLAUDE.md`

Contains:
- Who Matt is and how he is judged (copied from sport files, authoritative here)
- The org chart and each role's scope
- Both product pointers (NHL subfolder, NBA subfolder)
- The delegation protocol
- What only Matt can decide (keys, paying for things, Record resets)

### Agent Briefs (to be created)

Each specialist gets a brief at `agents/<role>.md`:
- `agents/nhl-sharp.md` — NHL-specific context, files, authority
- `agents/nba-sharp.md` — NBA-specific context, files, authority  
- `agents/data-scientist.md` — both sports, record files, DS authority
- `agents/ux.md` — both pages, design rules
- `agents/qa.md` — test protocol, browser requirements
- `agents/researcher.md` — research scope, write rules

These are the briefs the CEO pastes into sub-session prompts. They are short and focused — not full TEAM.md dumps.

## Constraints

- **One CEO at a time.** Same rule as today.
- **Scheduled cloud tasks (Researcher 7:52 AM, daily check 1:43 PM, weekly review Sundays) are still separate.** They are not sub-sessions of the CEO; they are the company's automated routines. The CEO reads their output but does not spawn them.
- **The Director for each sport is the sharp voice for that sport.** The CEO does not override them on betting decisions.
- **DS sample rule is a hard gate.** No rule change ships without a named sample. This cannot be waived.

## What Done Looks Like

1. `CLAUDE.md` exists at the Hot Prop Homies root and loads as the CEO on every session in this folder
2. `agents/` directory holds six brief files, one per role
3. When Matt opens this folder and asks a business question, the CEO routes to the right specialist, runs them as a sub-session, and returns a synthesized answer
4. When Matt asks about NHL picks tonight, he gets the NHL Sharp's view — not a generic answer
5. When a rule change is proposed, the DS names the sample, the Sharp approves, the Builder ships, QA signs off — and Matt sees the result, not the process
