#!/usr/bin/env python3
"""The captain's history across the parts (game/record.py, copied from the Cargo repository):
the id, log, line and the captain's own time carried on; the ledger of eras; errands, and Cargo
2's own errand (the word for the Kraal vault); keys from newer games kept; a record from an
older game joined back up; notes for versions too old; hostile histories cleaned; old saves.

    python3 tools/history.py
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headless import IO, patch, quiet  # noqa: E402
from storytest import captains, cargo, expect, flat, play, problems, record, start  # noqa: E402
from game import record as history  # noqa: E402
from game import start as starting  # noqa: E402


def sealed(rec):
    rec["check"] = captains._captain_check(rec)
    return rec


def from_cargo3(state="open", needs="2.3.0", extra=None):
    """A record as Cargo 3 writes it: history, an errand for 2460, keys Cargo 2 does not know."""
    rec = dict(record("cargo3", "", ["the_pod"], name="Vega Orl", rank="Able Hand"))
    rec.update({"origin": {"game": "cargo3", "version": "3.0.0"}, "id": "C1-0000BEEF", "line": "L-00000003", "parent": "L-00000001", "own_time": 300,
                "ledger": {"cargo1": {"flags": ["thirteenth_name"], "ending": "trade", "version": "1.3.0",
                                      "line": "L-00000001", "turns": 160}},
                "errands": [{"id": "vault_word", "from": "cargo3", "to": "cargo2", "state": state, "needs": needs,
                             "title": "the word that opens the Kraal vault", "line": "L-00000003"},
                            {"id": "thirteenth_line", "from": "cargo3", "to": "cargo1", "state": "done",
                             "needs": "1.3.0", "title": "a name for the thirteenth line", "line": "L-00000003"}],
                "devices": {"procrustes_analyzer": {"from": "nowhere yet"}}})
    rec.update(extra or {})
    return captains.clean_captain(sealed(rec))


def at(game, place):
    game.current_location = next(loc for loc in game.locations if loc.name == place)


# ---- the record a new game writes ----------------------------------------------------------------
game, io, _ = start(None)
game.turn = 25
rec = game.captain_record()
expect(rec["id"].startswith("C2-") and rec["line"].startswith("L-") and rec["parent"] == "" and rec["own_time"] == 25,
       "a fresh captain: a Cargo 2 id, a line of its own, its own time: %s" % {k: rec[k] for k in ("id", "line", "own_time")})
expect(set(rec["ledger"]) == {"cargo2"} and rec["ledger"]["cargo2"]["version"] == cargo.VERSION, "the ledger holds this part")

# ---- a captain from 2533 on an errand ------------------------------------------------------------
came = from_cargo3()
expect(came["devices"] == {"procrustes_analyzer": {"from": "nowhere yet"}}, "keys Cargo 2 does not know are kept")
game, io, text = start(came)
expect(game.captain_id == "C1-0000BEEF" and game.captain_start["parent"] == "L-00000003"
       and game.captain_start["line"] != "L-00000003", "the same captain, on a new line from the record's")
expect([n for n in game.story.done if n.startswith("intro.")] == ["intro.errand"] and "lost the word" not in flat(text)
       and "without the word that opens her family's vault" in flat(text), "the errand's opening plays")
expect(game.ship.items.get("old_navcomp"), "and the captain keeps the old navigation computer")
snap = game.story.snapshot()
expect(game.story.check({"past": {"era": "cargo1", "flag": "thirteenth_name"}}, snap)
       and game.story.check({"past": {"era": "cargo3", "flag": "the_pod"}}, snap)
       and not game.story.check({"past": {"era": "cargo1", "flag": "thirteenth_blank"}}, snap)
       and game.story.check({"errand": {"vault_word": "open", "thirteenth_line": "done"}}, snap), "past and errand conditions")
thought = cargo.story_data()["nodes"]["thought.vault_word"]
expect(game.story.check(thought["requires"], snap), "a thought reminds the captain of the errand")
# Delta: she wakes, then the vault
at(game, "Delta")
game.turn = 14
play(game, io, "sleeper.wakes", "2", where="Delta")
vault = cargo.story_data()["nodes"]["sleeper.vault"]
expect(not game.story.check(game.story.requires_of(vault), game.story.snapshot()), "the vault waits a little after she wakes")
game.turn = 17
for answer, word in (("1", "patience"), ("2", "coffee"), ("3", "tuesday")):
    trial, tio, _ = start(from_cargo3())
    trial.story.done["sleeper.wakes"] = 1
    trial.turn = 5
    out = play(trial, tio, "sleeper.vault", answer, where="Delta")
    flags = trial.story_manager.story_states
    expect(flags.get("vault_word_known") and flags.get("vault_word_" + word), "choice %s: the word is %s" % (answer, word))
    expect(history.errand_state(trial.errands, "vault_word") == "done", "choice %s finishes the errand" % answer)
    expect(word in flat(out).lower(), "choice %s: the word is said aloud" % answer)
    expect(not trial.story.check(thought["requires"], trial.story.snapshot()), "and the thought goes quiet")
    if answer == "1":
        done = trial
done.turn = 60
rec = done.captain_record()
expect(rec["id"] == "C1-0000BEEF" and rec["own_time"] == 360 and rec["parent"] == "L-00000003", "the record goes on")
expect(set(rec["ledger"]) == {"cargo1", "cargo2", "cargo3"} and "vault_word_patience" in rec["ledger"]["cargo2"]["flags"]
       and "thirteenth_name" in rec["ledger"]["cargo1"]["flags"], "the ledger now has 2460 with the word, and 2420 as it was")
expect([e["state"] for e in rec["errands"] if e["id"] == "vault_word"] == ["done"], "the errand travels on done")
expect(rec["devices"] == {"procrustes_analyzer": {"from": "nowhere yet"}}, "keys from newer games are written out again")
expect(captains.clean_captain(json.loads(json.dumps(rec))) == rec, "the record reads back as it was written")
# without the errand: the plain opening, and no vault scene
game, io, text = start(from_cargo3(state="done"))
expect([n for n in game.story.done if n.startswith("intro.")] == ["intro.from_cargo3"], "no errand open: the plain opening")
game.story.done["sleeper.wakes"] = 0
game.turn = 9
at(game, "Delta")
expect(not game.story.check(game.story.requires_of(vault), game.story.snapshot()), "and no vault scene")

# ---- versions ----------------------------------------------------------------------------------
notes = history.import_notes(from_cargo3(needs="2.4.0"), "cargo2", cargo.VERSION, cargo.story_data()["features"])
expect(len(notes) == 1 and "2.4.0 or newer" in notes[0], "an errand for a newer Cargo 2 is named at import: %s" % notes)
game, io, _ = start(from_cargo3(needs="2.4.0"))
expect(any("2.4.0" in n for n in history.export_notes(game.errands, "cargo2", cargo.VERSION)), "and again at export")
notes = history.import_notes(from_cargo3(), "cargo2", cargo.VERSION, cargo.story_data()["features"])
expect(notes == ["An errand from 2533 waits here: the word that opens the Kraal vault."], "a doable errand is named: %s" % notes)

# ---- a record that went through an older Cargo 2 (2.2.0 keeps no history) ------------------------------
older = dict(record("cargo2", "trade", ["ottavine_patron"], name="Vega Orl", rank="Commodore"))
older["origin"] = {"game": "cargo2", "version": "2.2.0"}
older = captains.clean_captain(sealed(older))
newer = from_cargo3()
expect(history.join_candidates(older, [older, newer], cargo.story_data()["features"]) == [newer], "the newer record is found")
for answer, joined in (("yes", True), ("no", False)):
    for name in os.listdir(cargo.captain_folder()) if os.path.isdir(cargo.captain_folder()) else []:
        os.remove(os.path.join(cargo.captain_folder(), name))
    cargo.write_json(os.path.join(cargo.captain_folder(), "vega-cargo3.captain"), newer)
    io = IO()
    patch(cargo, io)
    io.feed([answer])
    with quiet() as out:
        got = starting.join_and_tell(older)
    expect((got["id"] == newer["id"]) == joined and ("joined" in out.getvalue()) == joined,
           "answering %s to the join: %s" % (answer, "joined" if joined else "kept apart"))
    if joined:
        game, io, _ = start(got)
        expect(set(game.captain_start["ledger"]) == {"cargo1", "cargo2", "cargo3"}
               and "ottavine_patron" in game.captain_start["ledger"]["cargo2"]["flags"], "the joined record has every era")

# ---- other lines of the same captain may visit ----------------------------------------------------------
game, io, _ = start(from_cargo3())
mine = game.captain_record()
expect("own record" in game.receive_captain(mine), "a captain cannot take in this very record")
other = dict(mine)
other["line"] = "L-0000FFFF"
expect("crossed" in game.receive_captain(sealed(other)), "the same captain from another line can cross over")

# ---- hostile histories ------------------------------------------------------------------------------------
junk = dict(record("cargo3", "", name="Junk"))
junk.update({"own_time": -5, "ledger": {"cargo1": "nope", "cargo9": {}, "cargo2": {"flags": ["a"] * 5000}},
             "errands": [{"id": "", "to": "cargo2"}, {"id": "e", "to": "mars"}, 7] * 10,
             "big": "x" * 20000, "bad key!": 1, **{"k%d" % i: i for i in range(40)}})
clean = captains.clean_captain(sealed(junk))
expect(clean["own_time"] == 0 and set(clean["ledger"]) == {"cargo2"} and clean["errands"] == []
       and "big" not in clean and "bad key!" not in clean and len([k for k in clean if k.startswith("k")]) <= history.KEPT_MOST,
       "a hostile history is cut down")
game, io, _ = start(clean)
expect(game.captain_record()["format"] == "cargo-captain", "and a game still starts and writes its record")

# ---- saves from 2.2, and damaged history in a save ----------------------------------------------------------
game, io, _ = start(from_cargo3())
del game.captain_start
del game.errands
with quiet():
    game.save_game("old")
    loaded = cargo.load_game("old")
expect(isinstance(loaded.captain_start, dict) and set(loaded.captain_start["ledger"]) == {"cargo1", "cargo3"},
       "a save from before 2.3 gets a history, from the record it began as: %s" % list(loaded.captain_start["ledger"]))
loaded.captain_start = "rubbish"
loaded.errands = [{"id": "x"}, 5]
loaded.bring_up_to_date()
expect(isinstance(loaded.captain_start, dict) and loaded.errands == [], "a damaged history in a save is mended")
random.seed(3)

print("history: %s" % ("ok" if not problems[0] else "%d problems" % problems[0]))
sys.exit(1 if problems[0] else 0)
