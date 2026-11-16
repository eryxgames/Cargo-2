#!/bin/sh
# Run every check on Cargo 2. Usage: tools/check.sh [quick]
cd "$(dirname "$0")/.." || exit 1
T=tools
G=game/world.py
PY=${PYTHON:-python3}
if [ "$1" = "quick" ]; then SEEDS="1 2"; WIDTHS="80 40 36"; N=600; else SEEDS="1 2 3 4"; WIDTHS="100 80 60 50 44 40 36"; N=1500; fi
fail=0

echo "== CLIo's layer in kit/ is as copied"
$PY $T/sync_kit.py --check || fail=1

echo "== each module of the game imports on its own"
$PY $T/modules.py || fail=1

echo "== every style at every width, with and without colour and Unicode"
$PY $T/looks.py || fail=1

echo "== wrong-object references"
$PY $T/attrlint.py $G | tail -1

echo "== the game starts and exits as a program (UTF-8 and cp1252 output)"
$PY $T/smoke.py $PY cargo2.py || fail=1

echo "== damaged and hostile save / captain files"
$PY $T/test_files.py $G | tail -1 || fail=1

echo "== save / load round trips"
for s in $SEEDS; do $PY $T/roundtrip.py $G $s 1200 800 | $PY -c "
import json,sys
r=json.load(sys.stdin)
ok=r.get('identical') and r.get('captain_ok') and not r.get('stale_refs_to_old_game') and 'traceback' not in r
print('  seed', r['seed'], 'ok' if ok else 'FAIL', r.get('traceback','')[-300:])
sys.exit(0 if ok else 1)" || fail=1; done

echo "== random play at each width (crashes, lines wider than the screen)"
for w in $WIDTHS; do for s in $SEEDS; do $PY $T/infuzz.py $G $w $N $s | $PY -c "
import json,sys
r=json.load(sys.stdin)
ok=not r['traceback'] and not r['overflow_kinds']
print('  cols', r['cols'], 'seed', r['seed'], 'inputs', r['inputs'], 'ok' if ok else 'FAIL', (r['traceback'] or '')[-300:], r['overflow'][:2] if r['overflow_kinds'] else '')
sys.exit(0 if ok else 1)" || fail=1; done; done

echo "== long games through the real prompts at 36 columns, with saves and loads"
for goal in trade combat; do for s in $SEEDS; do $PY $T/bot.py $G $goal $s 400 --save-every=9 --cols=36 | $PY -c "
import json,sys
r=json.load(sys.stdin)
crash='traceback' in r
print('  %-7s seed %s: %s at turn %s, %s loads %s' % (r['goal'], r['seed'], r.get('ending') or r.get('end') or 'playing', r.get('turn'), r.get('loads'), 'CRASH '+r['traceback'][-300:] if crash else ''))
sys.exit(1 if crash else 0)" || fail=1; done; done

if [ $fail = 0 ]; then echo "ALL CHECKS PASSED"; else echo "SOME CHECKS FAILED"; exit 1; fi
