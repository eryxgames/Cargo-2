#!/bin/sh
# Run every check on Cargo 2. Usage: tools/check.sh [quick]
cd "$(dirname "$0")/.." || exit 1
export CARGO_SOUND=0          # the checks never start an audio player
T=tools
G=game/world.py
PY=${PYTHON:-python3}
if [ "$1" = "quick" ]; then SEEDS="1 2"; WIDTHS="80 40 36"; N=600; FIGHTS=100; else SEEDS="1 2 3 4"; WIDTHS="100 80 60 50 44 40 36"; N=1500; FIGHTS=300; fi
fail=0

echo "== CLIo's layer in kit/ is as copied"
$PY $T/sync_kit.py --check || fail=1

echo "== the story: copied tools unchanged, built file current, no new findings, every scene plays,"
echo "   every way into the game (fresh, each Cargo 1 ending, Cargo 2 and 3 records) starts right,"
echo "   acts 1 to 3 turn where they should and pay what Cargo 1 promised"
$PY $T/sync_story.py --check || fail=1
$PY $T/build_story.py --check || fail=1
$PY storykit/validate.py story/saga.json --baseline story/findings-baseline.json > /tmp/cargo2-validate.txt; tail -2 /tmp/cargo2-validate.txt
grep -q "baseline: 0 new" /tmp/cargo2-validate.txt || fail=1
# Cargo 2 owes nothing: every promise due here paid, every flag Cargo 1 carries here read
grep -E "(promise-pending|carried-pending).*cargo2" /tmp/cargo2-validate.txt && fail=1
$PY $T/scenes.py $G > /tmp/cargo2-scenes.txt || fail=1
grep -E "CRASH|unfilled|FAIL" /tmp/cargo2-scenes.txt | head; tail -1 /tmp/cargo2-scenes.txt
$PY $T/openings.py || fail=1
$PY $T/acts.py || fail=1
$PY $T/look.py || fail=1
$PY $T/handoff.py --check || fail=1

echo "== Cargo 2's systems, one by one"
$PY $T/systems.py || fail=1

echo "== sound: songs composed and rendered, places, fights, act 3, effects, sound off (into a recorder)"
$PY $T/sound.py || fail=1

echo "== convoy fights against one-roll fights, every difficulty (win rate and damage)"
$PY $T/fights.py $FIGHTS > /tmp/cargo2-fights.txt || fail=1; grep OFF /tmp/cargo2-fights.txt; tail -1 /tmp/cargo2-fights.txt

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
echo "   (seed 2 plays a Cargo 1 captain with the same ending; seed 1 a fresh one)"
for goal in trade combat; do for s in $SEEDS; do
captain=""; [ $s = 2 ] && captain="--captain=$goal"
$PY $T/bot.py $G $goal $s 400 --save-every=9 --cols=36 $captain | $PY -c "
import json,sys
r=json.load(sys.stdin)
crash='traceback' in r
print('  %-7s seed %s%s: %s at turn %s, %s loads %s' % (r['goal'], r['seed'], ' (Cargo 1 captain)' if r.get('captain') else '', r.get('ending') or r.get('end') or 'playing', r.get('turn'), r.get('loads'), 'CRASH '+r['traceback'][-300:] if crash else ''))
sys.exit(1 if crash else 0)" || fail=1; done; done

if [ "$1" != "quick" ]; then
echo "== the door and the quiet node (36 columns, saves and loads)"
for goal in discovery dawn; do $PY $T/bot.py $G $goal 1 900 --save-every=9 --cols=36 | $PY -c "
import json,sys
r=json.load(sys.stdin)
crash='traceback' in r
ok=r.get('ending')==sys.argv[1].replace('discovery2','discovery') and not crash
print('  %-9s %s at turn %s %s' % (sys.argv[1], r.get('ending') or r.get('end'), r.get('turn'), 'CRASH '+r['traceback'][-300:] if crash else ''))
sys.exit(0 if ok else 1)" $goal || fail=1; done

echo "== a captain who looks around and follows the notes (36 columns, saves and loads): every road"
echo "   still ends, and the side quests get done"
for goal in trade combat discovery dawn; do $PY $T/bot.py $G $goal 3 900 --leads --save-every=9 --cols=36 | $PY -c "
import json,sys
r=json.load(sys.stdin)
crash='traceback' in r
done=[f for f in ('found_the_liar','locker_opened','loader_patch','needle_talk','returned_the_archive','institute_charts') if f in r['docks']['flags']]
ok=r.get('ending')==sys.argv[1] and not crash and len(done)>=3
print('  %-9s %s at turn %s; side quests done: %s %s' % (sys.argv[1], r.get('ending') or r.get('end'), r.get('turn'), ', '.join(done), 'CRASH '+r['traceback'][-300:] if crash else ''))
sys.exit(0 if ok else 1)" $goal || fail=1; done

echo "== the combat road on easy and expert (36 columns, saves and loads)"
for d in 1 3; do $PY $T/bot.py $G combat 1 700 --save-every=9 --cols=36 --difficulty=$d | $PY -c "
import json,sys
r=json.load(sys.stdin)
crash='traceback' in r
ok=r.get('ending')=='combat' and not crash
print('  difficulty %s: %s at turn %s, %s fights won, %s lost %s' % (sys.argv[1], r.get('ending') or r.get('end'), r.get('turn'), r.get('wins'), r.get('losses'), 'CRASH '+r['traceback'][-300:] if crash else ''))
sys.exit(0 if ok else 1)" $d || fail=1; done
fi

if [ $fail = 0 ]; then echo "ALL CHECKS PASSED"; else echo "SOME CHECKS FAILED"; exit 1; fi
