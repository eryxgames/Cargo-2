#!/usr/bin/env python3
"""Look and think (Cargo 2.1): people travel their routes, the docks have things to look at, the
captain's thoughts follow the leads, and the two side quests (the founders' locker at Alpha, the
ship that lies at Gamma) work from first look to their special equipment. Nothing here is on the
way to an ending: the chapters never mention it.
Usage: python3 tools/look.py"""
import os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headless import quiet  # noqa: E402
from storytest import cargo, expect, flat, problems, start  # noqa: E402


def at(game, name):
    game.current_location = next(loc for loc in game.locations if loc.name == name)


def look(game, io, answers):
    io.queue.clear(); io.feed(answers + [""] * 8)
    with quiet() as buf:
        game.handle_look()
    return flat(buf.getvalue())


def think(game, io):
    io.queue.clear(); io.feed([""] * 4)
    with quiet() as buf:
        game.handle_think()
    return flat(buf.getvalue())


def option(text, words):
    """The number a look list gives to the entry with these words."""
    found = re.findall(r"(\d+)\. ([^0-9]+?)(?= \d+\. |Look at|$)", text)
    for number, label in found:
        if words.lower() in label.lower():
            return number
    return None


game, io, _ = start(None)
story = game.story
# ---- routes ---------------------------------------------------------------------------------------
expect([story.where_is("young_hauler", t) for t in range(7)] == ["Alpha", "Alpha", "Beta", "Beta", "Gamma", "Gamma", "Alpha"],
       "Pell flies Alpha, Beta, Gamma, two turns at each")
expect({story.where_is("convoy_captain", t) for t in range(30)} == {"Alpha"}, "Targa is always at Alpha")
expect(story.where_is("meza_voce", 0) == "Gamma" and story.where_is("meza_voce", 2) == "Delta", "Meza Voce starts a turn into her route")
game.turn = 0
at(game, "Alpha")
expect(set(game.people_here()) >= {"young_hauler", "convoy_captain"}, "at Alpha on turn 0: Pell and Targa")
game.turn = 2
expect("young_hauler" not in game.people_here(), "by turn 2 Pell has flown on")
expect(story.check({"here": "convoy_captain"}, story.snapshot()) and not story.check({"here": "young_hauler"}, story.snapshot()),
       "the here condition follows the routes")

# ---- the founders' locker ---------------------------------------------------------------------------
game, io, _ = start(None)
game.turn = 0
at(game, "Alpha")
text = look(game, io, [])
for words in ("Talk to Pell Okafor", "Talk to Grab Allsa Targa", "The founders' wall", "A sealed locker", "A needle forms"):
    expect(words in text, "looking around Alpha shows %r" % words)
text = look(game, io, [option(text, "sealed locker"), "1"])
expect("founders' pass" in text and game.story_manager.story_states.get("saw_the_locker"), "the locker wants a founders' pass")
expect("Open it" not in text, "without the pass the locker cannot be opened")
expect("Somebody who was there at the founding" in think(game, io), "the captain thinks about the locker")
text = look(game, io, [option(look(game, io, []), "Pell"), "1"])
expect("she is always at Alpha" in text, "Pell knows who keeps a founders' pass")
expect("keeps a founders' pass" in think(game, io), "the thought follows Pell's hint")
text = look(game, io, [option(look(game, io, []), "Targa"), "1"])
expect(game.ship.items.get("hansa_pass") and "Eleven were made" in text, "Targa gives the founders' pass")
expect("I have Allsa's founders' pass" in think(game, io) or "founders' pass, and Alpha" in think(game, io), "the captain remembers the pass")
fare = game.needle_fare("middle")
text = look(game, io, [option(look(game, io, []), "sealed locker"), "1"])
expect("a transponder, still charged" in text and game.has_equipment("founders_transponder"), "the pass opens the locker")
expect(game.needle_fare("middle") < fare, "the founders' transponder lowers the fares")
expect("Founders' transponder" in think(game, io), "the captain lists the special equipment")
text = look(game, io, [option(look(game, io, []), "sealed locker")])
expect("stands open and empty" in text, "an opened locker stays open")
text = look(game, io, [option(look(game, io, []), "Targa"), "1"])
expect(game.story_manager.story_states.get("told_targa") and game.standing_of("hansa") == 10, "Targa hears what was inside")

# ---- the ship that lies -----------------------------------------------------------------------------
game, io, _ = start(None)
game.turn = 0
at(game, "Gamma")
text = look(game, io, [option(look(game, io, []), "traffic console"), "1"])
expect("Most of them tell the truth" in text and "reader down the list" not in text, "the console, without a reader")
expect("Meza Voce reads manifests" in think(game, io), "the captain thinks of Meza Voce")
game.turn = 1                                               # Meza Voce is at Gamma on turns 0-1
text = look(game, io, [option(look(game, io, []), "Meza Voce"), "1"])
expect(game.ship.items.get("transponder_reader") and "A ship that lies" in text, "Meza Voce lends a reader")
text = look(game, io, [option(look(game, io, []), "traffic console"), "1", "1"])
expect("Mandate decoy hull" in text and game.has_equipment("decoy_code"), "the reader finds the lying ship, and its code")
random.seed(1)
waves = sum(game.waved_through("militia") for _ in range(400))
expect(150 < waves < 250, "the decoy code waves the ship through about half the time: %d of 400" % waves)

# ---- the segment's scratches, the asteroid in the harbour ------------------------------------------------
game, io, _ = start(None)
game.story.done["ring.expedition"] = 1
game.turn = 0
at(game, "Epsilon")
text = look(game, io, [option(look(game, io, []), "Kren"), "1"])
expect("Eleven. Nobody has counted them twice" in text, "Kren tells of the scratches")
expect("Stator Field" in think(game, io), "the captain thinks of the scratches")
with quiet():
    game.reveal_place("Stator Field Megastructure") if hasattr(game, "reveal_place") else None
rp = game.ship.research_points
loc = next((l for l in game.locations if l.name == "Stator Field Megastructure"), None)
if loc is not None:
    game.current_location = loc
    text = look(game, io, [option(look(game, io, []), "inner face"), "1"])
    expect("there are twelve" in text and game.ship.research_points == rp + 150, "counting twice finds a twelfth")
at(game, "Beta")
expect("asteroid in the harbour" not in look(game, io, []), "the asteroid is not in Beta's harbour before the segment turns")
game.story.done["ring.lost"] = 1
expect("asteroid in the harbour" in look(game, io, []), "after it turns, the asteroid is")

# ---- off the critical path -------------------------------------------------------------------------
data = cargo.story_data()
docks = {nid for nid, n in data["nodes"].items() if n.get("arc") == "docks"}
used = set()
for nid, node in data["nodes"].items():
    if node.get("kind") in ("chapter", "milestone", "ending"):
        used |= set(re.findall(r'"((?:sight|docks|thought)\.[a-z_.]+)"', str(node.get("requires")).replace("'", '"')))
expect(not used & docks, "no chapter or ending waits for anything at the docks")

# ---- think: the way on, in the captain's words; people met, with their routes --------------------------------
game, io, _ = start(None)
game.turn = 0
at(game, "Alpha")
look(game, io, [option(look(game, io, []), "Pell"), "2"])
text = think(game, io)
expect("To go on (Forty Years On), I still need" in text, "think says what the chapter still needs")
expect("Pell Okafor flies Alpha, Beta, Gamma, 2 turns at each" in text, "think remembers where Pell flies")
game.turn = 1
at(game, "Beta")
expect("Pell Okafor is due here next turn" in look(game, io, []), "the dock says when a known face is due")

print("look: people, sights, thoughts and the side quests, %d problems" % problems[0])
sys.exit(1 if problems[0] else 0)
