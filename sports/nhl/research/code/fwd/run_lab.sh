#!/bin/sh
# Re-score the forward tests that have a Lab tile (Q24, LL, MM, NN) and rewrite research/fwd/lab.json. Run from sports/nhl.
# cycle.sh runs it every cycle (the Lab summaries stay current); run_all.sh runs it as its Lab step.
PY="${PC_PYTHON:-python3}"
cd "$(dirname "$0")/../../.." || exit 1
set -e
"$PY" -I research/code/r24/score_q24.py "$PWD"          # Q24
"$PY" -I research/code/r24/score_ll.py "$PWD"           # LL1f, LL3a-b, LL4a-b, LL5, LL6
"$PY" -I research/code/r25/score_mm.py "$PWD"           # MM2a-b, MM3a-b, MM4, MM5a-b
"$PY" -I research/code/r26/score_nn.py "$PWD"           # NN2fa-b, NN4, NN5, NN6
"$PY" -I research/code/fwd/lab_export.py                # Lab tab totals for LL / MM / NN
