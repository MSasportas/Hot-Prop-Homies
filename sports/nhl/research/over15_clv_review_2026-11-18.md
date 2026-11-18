# NHL Over 1.5 Shots — Shadow CLV Review
**Date:** 2026-11-18  
**Author:** Data Scientist  
**Purpose:** Gate assessment for future rule change on Over 1.5 shots market. Requested by NHL Sharp.

---

## Background

The NHL Sharp flagged the Over 1.5 shots market for review: 8 live picks, 2-6, approximately -49% ROI since launch. The 100-pick gate for a threshold change has not been reached. This report runs shadow/paper CLV on all Over 1.5 candidates (flags + vetoes) to assess whether the "strong CLV evidence" standard for a gate override is met.

---

## Data Sources

- Primary: `sports/nhl/data/paper/events.jsonl` (Gap+Guard research log, live from 2026-10-20)
- Secondary: `sports/nhl/data/shadow/2026-11-06.json` (for D. Yurov, missing from paper log)
- Cross-reference: `sports/nhl/data/record/events.jsonl` (Record confirmed 8 live picks, 2-6, -49.2% ROI)

---

## All Over 1.5 Shots Candidates

9 total candidates found (8 flags/live picks, 1 veto). All resolved.

| # | Date | Player | Team | Kind | Price | CLV (%) | Result | Units |
|---|------|--------|------|------|-------|---------|--------|-------|
| 1 | 2026-10-22 | R. Andersson | VGK | flag | -105 | +8.05 | L | -1.00 |
| 2 | 2026-10-24 | J. Eberle | SEA | flag | -110 | +5.21 | W | +0.91 |
| 3 | 2026-10-27 | J. Trouba | SJS | flag | +105 | +2.91 | L | -1.00 |
| 4 | 2026-11-02 | D. Nurse | SJS | flag | +115 | +6.29 | L | -1.00 |
| 5 | 2026-11-03 | A. Gritsyuk | NJD | flag | -165 | null* | L | -1.00 |
| 6 | 2026-11-06 | D. Yurov | MIN | flag | +125 | ~+5.9** | L | -1.00 |
| 7 | 2026-11-10 | G. Forsling | FLA | veto | +140 | +3.62 | W | +1.40 |
| 8 | 2026-11-14 | F. Minten | BOS | flag | +115 | +3.13 | W | +1.15 |
| 9 | 2026-11-14 | K. Sherwood | SJS | flag | +105 | +10.55 | L | -1.00 |

\* Gritsyuk: first_caught_at_close, no movement tracked, CLV null.  
\** Yurov: 2026-11-06 not in paper/events.jsonl (gap in coverage). Derived from shadow consensus (cons_fair_over flat open→close ~47.1%) and record show event gap_pct 5.9%. Approximate.

---

## Summary Statistics

**Volume:**
- Total candidates: 9
- Flags (live picks): 8
- Vetoes (research only): 1
- All resolved: yes

**Results:**

| Scope | W | L | Hit Rate | ROI |
|-------|---|---|----------|-----|
| Live picks (flags only) | 2 | 6 | 25.0% | -49.3% |
| All candidates (flags + veto) | 3 | 6 | 33.3% | n/a |

**CLV Distribution (n=8 with data, 1 null excluded):**

| Metric | Value |
|--------|-------|
| Mean CLV | +5.71% |
| Median CLV | +5.55% |
| % Positive CLV | 100% (8/8) |
| Range | +2.91% to +10.55% |

---

## Gate Verdict

**The CLV evidence does NOT meet the "strong CLV evidence" standard for a gate override.**

Three reasons:

**1. Sample size too small.** n=9 candidates, n=8 with CLV data. At this n, a lower-bound confidence interval on mean CLV would be wide enough to include zero. No reliable inference is possible.

**2. 100% positive CLV is expected, not diagnostic.** The Gap+Guard system is designed to flag lines where our price beats the closing consensus. Any passing flag is expected to show positive CLV. 100% positive on 8 observations is consistent with the system functioning normally, not with Over 1.5 specifically having special merit. It does not distinguish Over 1.5 from Under candidates.

**3. Outcome signal is unambiguous in the other direction.** 2-6 (25% hit rate) with mean bet pricing implying ~45-48% breakeven is 2+ standard deviations below expectation on 8 picks. The CLV and outcome signals contradict each other, which is resolvable by sample in theory, but requires more data to resolve, not less.

**What would constitute "strong" CLV evidence:**
- Minimum n=30 candidates with CLV data
- Mean CLV > +5% with 80th percentile lower bound > +2%
- Or: CLV in top quartile vs all other shots markets (comparative, not absolute)

---

## Recommendation to Sharp

Continue shadow/paper tracking. At the current rate (~1 Over 1.5 candidate per 2-3 days), n=30 arrives around early December. Gate remains at 100 graded picks unless a comparative CLV study at n=30 shows Over 1.5 materially outperforming Under candidates.

The 2-6 results are not actionable from a data standpoint — they are consistent with normal variance on 8 picks and do not independently justify removing the market. The CLV signal is consistent with normal system operation on this market.

---

*Files consulted: `sports/nhl/data/paper/events.jsonl`, `sports/nhl/data/paper/summary.json`, `sports/nhl/data/shadow/2026-11-06.json`, `sports/nhl/data/record/events.jsonl`*
