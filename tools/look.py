#!/usr/bin/env python3
"""Look and think (Cargo 2.1-2.2): people travel their routes, the docks have things to look at,
the captain's thoughts follow the leads, and the side quests work from first look to their reward:
the founders' locker at Alpha and the ship that lies at Gamma (2.1); Adit's hand, Korai's verse and
the Institute's archive (2.2), with the shorter ways some Cargo 1 captains have. Story items survive
equipment failures; nothing here is on the way to an ending, and a thought names a place only when
the next step is there.
Usage: python3 tools/look.py"""
import os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headless import quiet  # noqa: E402
from storytest import cargo, expect, flat, problems, record, start  # noqa: E402


def at(game, name):
    """Put the captain at a place, opening its kind of place first if the map does not show it yet."""
    if not any(loc.name == name for loc in game.locations):
        kind = next((k for k, places in game.hidden_locations.items() if any(p.name == name for p in places)), None)
        with quiet():
            game.unlock_location_type(kind)
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

# ---- 2.2, act 1 on: the loader's hand -----------------------------------------------------------------
game, io, _ = start(None)
states = game.story_manager.story_states
game.turn = 0
at(game, "Beta")
text = look(game, io, [])
expect("Talk to Adit" in text, "Adit works Beta's ring on turns 0-1")
text = look(game, io, [option(text, "Adit"), "1"])
expect("USE NO HOOKS" in text and "Geod's... Row" in text and states.get("adit_told_the_hand"), "Adit says where its hand went")
expect("Geod's Row, at Delta" in think(game, io), "the captain thinks of Geod's Row")
at(game, "Delta")
game.ship.money = 1500
text = look(game, io, [option(look(game, io, []), "Geod's Row")])
expect("Hansa registry stamp" in text and "Buy the loader's hand" not in text and "seed stock" not in text,
       "the hand is on a farm agrobot; 1,500 does not buy it")
game.ship.money = 5000
text = look(game, io, [option(look(game, io, []), "Geod's Row"), "1"])
expect(game.ship.items.get("loader_hand") and game.ship.money == 3000 and "never liked fruit" in text, "two thousand buys the hand")
at(game, "Beta")
for module in ("container", "turret"):
    game.ship.modules.append({"kind": module, "condition": 100})
with quiet():
    game.wear_modules(20)
expect(sorted(m["condition"] for m in game.ship.modules) == [80, 100], "modules wear as before without the patch")
text = look(game, io, [option(look(game, io, []), "Adit"), "1"])
expect(game.has_equipment("loader_patch") and not game.ship.items.get("loader_hand") and "Wear... less" in text,
       "Adit takes its hand back and patches the modules")
with quiet():
    game.wear_modules(20)
expect(sorted(m["condition"] for m in game.ship.modules) in ([70, 100], [80, 90]), "with the patch, modules wear half as fast")
expect("Adit's patch routine" in think(game, io) and "Geod's Row" not in think(game, io), "think lists the patch, and the lead is gone")
game, io, _ = start(record("cargo1", "trade", ["geod_fields"]))
game.ship.money = 0
at(game, "Delta")
text = look(game, io, [option(look(game, io, []), "Geod's Row"), "1"])
expect(game.ship.items.get("loader_hand") and "For the seed stock" in text, "a captain who brought Geod the seed stock gets the hand free")

# ---- 2.2, act 2 on: the singer's verse -------------------------------------------------------------------
game, io, _ = start(None)
states = game.story_manager.story_states
expect([game.story.where_is("warp_singer", t) for t in range(4)] == ["Epsilon", "Beta", "Delta", "Beta"],
       "Korai rides every needle: never two turns in one place")
game.turn = 1
at(game, "Beta")
expect("Korai" not in look(game, io, []), "in act 1 Korai is not at the docks yet")
game.story_manager.current_chapter = "ch2a"
text = look(game, io, [option(look(game, io, []), "Korai"), "1"])
expect("kettle being reasonable" in text and "eleven years" in text and states.get("korai_asked"), "Korai asks for a verse she does not know")
expect("Quantum Center" in think(game, io), "the captain thinks of the Quantum Center")
expect("Korai is due here next turn" in look(game, io, []) if game.story.where_is("warp_singer", 2) == "Beta" else True, "")
at(game, "Quantum Center")
rp = game.ship.research_points
text = look(game, io, [option(look(game, io, []), "ringing star"), "1"])
expect(game.ship.items.get("bell_trace") and game.ship.research_points == rp + 50, "the astronomers copy the trace")
expect("Quantum Center" not in think(game, io), "once the trace is aboard, the notes point at Korai, not the Center")
at(game, "Beta")
game.turn = 3
text = look(game, io, [option(look(game, io, []), "Korai"), "1"])
expect(game.has_equipment("needle_talk") and "Not yet" in text, "the trace is a needle calling; no needle is missing, yet")
here = game.current_location
there = next(loc for loc in game.locations if not game.same_system(loc, here))
io.queue.clear(); io.feed(["2"])
game.ship.money = 10 ** 6
with quiet():
    game.book_needle(there)
expect(abs(game.needle_risk - 0.7) < 1e-9, "needle-talk: fewer fights on the needle (%s)" % game.needle_risk)
game, io, _ = start(None)
game.story_manager.current_chapter = "ch2a"
game.story.done["ring.lost"] = 1
game.ship.items["bell_trace"] = 1
game.story_manager.story_states["korai_asked"] = True
game.turn = 1
at(game, "Beta")
text = look(game, io, [option(look(game, io, []), "Korai"), "1"])
expect("came out of the segment eleven years ago" in text and "began eleven years ago" in think(game, io),
       "after the segment turns, the trace has a needle, and the captain puts the two together")

# ---- 2.2, act 3: the Institute's archive ------------------------------------------------------------------
def archive_game(flags=(), money=10 ** 6):
    game, io, _ = start(record("cargo1", "discovery", flags) if flags else None)
    game.ship.money = money
    game.turn = 0
    return game, io, game.story_manager.story_states


game, io, states = archive_game()
at(game, "Stellar Institute")
game.story_manager.current_chapter = "ch2a"
expect("Ask the bursar" not in look(game, io, [option(look(game, io, []), "new roof")]), "before act 3 the roof is only a roof")
game.story_manager.current_chapter = "ch3a"
text = look(game, io, [option(look(game, io, []), "new roof"), "1"])
expect("Kraal paper" in text and states.get("asked_about_the_archive"), "the bursar says who bought the archive")
expect("Delta" in think(game, io), "the captain thinks of Delta")
at(game, "Delta")
text = look(game, io, [option(look(game, io, []), "Astin"), "1"])
expect(game.ship.items.get("institute_archive") and game.ship.money == 10 ** 6 - 50000 and "smelling of smoke" in text
       and "last box" not in text, "Astin sells the archive back; no invoice for a captain who never knew")
at(game, "Stellar Institute")
rp, concord = game.ship.research_points, game.standing_of("concord")
text = look(game, io, [option(look(game, io, []), "new roof"), "1"])
expect(states.get("returned_the_archive") and game.ship.research_points == rp + 400 and game.standing_of("concord") == concord + 10
       and not game.ship.items.get("institute_archive"), "the archive goes home: research and the Concord's thanks")
expect("spelled right" in look(game, io, [option(look(game, io, []), "new roof")]), "the brass plate has a second line")

game, io, states = archive_game(["found_the_chair", "neon_sleeper_carried"], money=1000)
game.story_manager.current_chapter = "ch3a"
states["asked_about_the_archive"] = True
game.story.done["sleeper.wakes"] = 1
at(game, "Delta")
text = look(game, io, [option(look(game, io, []), "Astin")])
expect("Buy the Institute's archive" not in text and "Ask Conte Ottavine" in text, "short of money, the Conte is the way")
text = look(game, io, [option(look(game, io, []), "Astin"), "1", "1"])
expect("The captain who carried me" in text and "You know whose firm it is" in text and states.get("kept_the_invoice"),
       "the Conte gives it; a captain who knew about the fire keeps the invoice")
at(game, "Stellar Institute")
text = look(game, io, [option(look(game, io, []), "new roof"), "2"])
expect(game.has_equipment("institute_charts") and not states.get("returned_the_archive"), "keeping the survey charts")
expect("The Institute's survey charts" in think(game, io), "think lists the charts")

# ---- 2.2: sights where there was nothing to look at --------------------------------------------------------
game, io, _ = start(record("cargo1", "discovery", ["asked_the_garrison", "nano_trusted"]))
for place, words in (("Omega XIV", "rock-bound"), ("DSO-Gamma", "Still not saying"), ("Nova Labs", "rule 15"),
                     ("Sigma VII", "KEPT THE SECRET"), ("DSO-Beta", "SEE LABEL")):
    at(game, place)
    text = look(game, io, ["1"])
    expect(words in text, "a sight at %s (%r)" % (place, words))
game.story.done["ring.lost"] = 1
at(game, "DSO-Gamma")
expect("hums every eleven minutes" in look(game, io, ["1"]), "after the segment turns, the ice at Scholz's Star hums")

# ---- keepsakes: an equipment failure breaks equipment, never the pass, the hand or the trace ------------------
game, io, _ = start(None)
game.ship.items.update({"hansa_pass": 1, "loader_hand": 1, "bell_trace": 1, "institute_archive": 1, "transponder_reader": 1})
random.seed(3)
for _ in range(60):
    game.ship.damage = 0
    with quiet():
        game.handle_disaster_event("Equipment malfunction!")
expect(all(game.ship.items.get(i) for i in ("hansa_pass", "loader_hand", "bell_trace", "institute_archive", "transponder_reader")),
       "sixty equipment failures leave the story's items aboard: %s" % sorted(game.ship.items))

# ---- off the critical path -------------------------------------------------------------------------
data = cargo.story_data()
docks = {nid for nid, n in data["nodes"].items() if n.get("arc") == "docks"}
used, gives = set(), set()
for nid in docks:
    node = data["nodes"][nid]
    for effects in [node.get("effects") or {}] + [c.get("effects") or {} for c in node.get("choices") or []]:
        gives |= set(effects.get("set") or []) | set((effects.get("give") or {}).get("items") or [])
for nid, node in data["nodes"].items():
    if node.get("kind") in ("chapter", "milestone", "ending"):
        used |= set(re.findall(r'"((?:sight|docks|thought)\.[a-z_.]+)"', str(node.get("requires")).replace("'", '"')))
        used |= {word for word in re.findall(r"[a-z_]+", str(node.get("requires"))) if word in gives}
expect(not used & (docks | gives), "no chapter or ending waits for anything at the docks: %s" % sorted(used & (docks | gives)))
# a thought names a place only where the next step is (players and tools/bot.py --leads fly there)
places = sorted((name for name in data["places"] if data["places"][name].get("type")), key=len, reverse=True)
for nid, node in data["nodes"].items():
    if node.get("kind") == "thought":
        named = [p for p in places if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(" ".join(p.split()[:2])), node["text"])]
        expect(len(named) <= 1, "%s points at one place at most: %s" % (nid, named))

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
