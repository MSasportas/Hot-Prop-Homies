#!/bin/sh
# Re-score the forward tests that have a Lab tile (Q24, LL, MM, NN, R28) and rewrite research/fwd/lab.json. Run from sports/nhl.
# cycle.sh runs it every cycle (the Lab summaries stay current); run_all.sh runs it as its Lab step.
PY="${PC_PYTHON:-python3}"
cd "$(dirname "$0")/../../.." || exit 1
set -e
"$PY" -I research/code/r24/score_q24.py "$PWD"          # Q24
"$PY" -I research/code/r24/score_ll.py "$PWD"           # LL1f, LL3a-b, LL4a-b, LL5, LL6
"$PY" -I research/code/r25/score_mm.py "$PWD"           # MM2a-b, MM3a-b, MM4, MM5a-b
"$PY" -I research/code/r26/score_nn.py "$PWD"           # NN2fa-b, NN4, NN5, NN6
# R28 runs last of the scorers and can fail or hang without stopping the others or the export (research only, like every scorer here)
timeout 300 "$PY" -I research/code/r28/score_r28.py "$PWD" >/dev/null || echo "R28 scorer failed; carrying on" >&2
"$PY" -I research/code/fwd/lab_export.py                # Lab tab totals for LL / MM / NN / R28
