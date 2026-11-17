#!/usr/bin/env python3
"""Acts 1 to 3 of Cargo 2: the frame and its turning points, and Cargo 1's promises paid.
- the chapters, milestones and endings take their titles and conditions from story/cargo2/;
- act 1 does not end before the heading file is opened, act 3 does not open before the first
  segment is lost; every way through the auction, the expedition and the loss;
- the sleeper wakes, the other captain books your needle, the Binary Dawn speaks, the colony at
  Sigma VII hears the ring: each with the variant and the choices its Cargo 1 flags call for;
- the four roads of act 3, each to the holder of the segments its climax decides; the fourth
  stays secret until it opens.
Usage: python3 tools/acts.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headless import quiet  # noqa: E402
from storytest import cargo, expect, flat, options, play, problems, record, start  # noqa: E402


def standing(game):
    return {f: game.standing_of(f) for f in cargo.FACTIONS}


def progress(game):
    with quiet():
        game.story_manager.check_milestone_progress()
        game.story_manager.check_chapter_progress()


# ---- the frame -----------------------------------------------------------------------------------
game, io, _ = start(None)
sm = game.story_manager
TITLES = {"ch1": "Forty Years On", "ch2a": "Instruments and Cargo", "ch2b": "Escort Duty", "ch3a": "The Open Road",
          "ch3b": "The Lighthouse", "ch3c": "The Door", "ending_trade": "A Road Anyone Can Book"}
for cid, title in TITLES.items():
    expect(sm.chapters[cid].title == title, "chapter %s is called %r, not %r" % (cid, sm.chapters[cid].title, title))
expect(sm.chapters["ch1"].milestones["basic_license"].title == "A slot of your own", "milestones take the story's titles")
data = cargo.story_data()
for nid in ("ch1", "ch2a", "ch3a", "ch1.first_trade", "ch2b.defeat_pirates", "ending_trade.trade_ending"):
    expect(nid in data["repaired"], "%s: the story's condition is the one the game uses" % nid)

# act 1 waits for the heading
game.trades_completed = 6
game.ship.money = 50000
game.ship.combat_victories["total"] = 1
progress(game)
expect(all(m.completed for m in sm.chapters["ch1"].milestones.values()), "act 1's milestones complete from the story's conditions")
expect(not sm.chapters["ch1"].completed, "act 1 does not end before the heading file is opened")
needs = [words for _, words in sm.chapter_needs(sm.chapters["ch1"])]
expect(any("Lot 1187" in w for w in needs), "the progress screen names the turning point: %s" % needs)
game.turn = 9
text = play(game, io, "heading.opened", "1")
expect("Lot 1187" in flat(text) and "heading.read" in game.story.done, "the auction plays and the heading is read")
io.queue.clear(); io.feed([""] * 10)
progress(game)
expect(sm.chapters["ch1"].completed, "act 1 ends once the heading is opened")

# a milestone's condition is the story's, research included
ms = sm.chapters["ch3c"].milestones["alien_artifacts"]
expect(not ms.check_completion(game), "the year on the other side waits for research and colonies")
game.research.unlocked_options.update(["xenoeconomy", "telemetry"])
colonies = [loc for loc in game.locations if type(loc).__name__ == "ResearchColony"][:2]
game.discovered_locations.update(loc.name for loc in colonies)
expect(len(colonies) < 2 or ms.check_completion(game), "the year on the other side: two colonies and two researches")

# act 3 waits for the segment's loss
sm.completed_chapters.add("ch2a")
sm.plot_points = 500
game.ship.trade_profits["contracts"] = 10 ** 6
expect(not cargo.chapter_requirements_met(sm.chapters["ch3a"], game), "act 3 does not open before the segment is lost")
game.story.done["ring.lost"] = game.turn
expect(not cargo.chapter_requirements_met(sm.chapters["ch3a"], game), "the open road needs the Hansa's trust")
game.change_standing("hansa", 25)
expect(cargo.chapter_requirements_met(sm.chapters["ch3a"], game), "act 3 opens after the segment is lost, with the Hansa's trust")

# an old save: milestones learn their chapter again
for chapter in sm.chapters.values():
    for m in chapter.milestones.values():
        del m.chapter_id
with quiet():
    game.bring_up_to_date()
expect(sm.chapters["ch2b"].milestones["defeat_pirates"].chapter_id == "ch2b", "an old save's milestones read the story again")

# endings are named by the part they come from
expect(cargo.ending_title(record("cargo2", "trade")) == "the Open Road", "a Cargo 2 trade ending is the Open Road")
expect(cargo.ending_title(record("cargo1", "trade")) == "the Hauler Hansa", "a Cargo 1 trade ending is still the Hauler Hansa")

# ---- the auction: Lot 1187 -----------------------------------------------------------------------
AUCTION = [   # (record flags / ending, money, answer, words, flag set, words in the reading)
    (("discovery", []), 1000, "1", "The handwriting on the cover is yours", "heading_bought", "You read it in the auction room"),
    (("trade", ["rostrom_creditor"]), 30000, "1", "orders to let you outbid him", "heading_bought", "You read it"),
    ((None, []), 30000, "2", "It's a course to home", "heading_kren", "reads it aloud"),
    ((None, []), 1000, "1", "It's a course to home", "heading_rostrom", "over his shoulder"),
]
for (ending, flags), money, answer, words, flag, reading in AUCTION:
    game, io, _ = start(record("cargo1", ending, flags) if ending else None)
    game.turn, game.trades_completed, game.ship.money = 9, 3, money
    text = play(game, io, "heading.opened", answer)
    what = "auction (%s %s, %d credits, answer %s)" % (ending, flags, money, answer)
    expect(words in flat(text), "%s says %r" % (what, words))
    expect(game.story_manager.story_states.get(flag), "%s sets %s" % (what, flag))
    expect(reading in flat(text) and "Stator Field" in flat(text), "%s reads the course: %r" % (what, reading))
    expect(options(text) <= 2 or money >= 20000, "%s offers only what the captain can afford" % what)

# ---- the expedition, the segment, the loss -----------------------------------------------------------
game, io, _ = start(None)
game.story_manager.current_chapter = "ch2a"
game.story.done["heading.opened"] = 1
game.story_manager.story_states["heading_bought"] = True
before = game.ship.money
text = play(game, io, "ring.expedition", "4")
expect("finder's fee" in flat(text) and game.ship.money == before + 25000, "the file's owner may take a finder's fee")
expect(any(loc.name == "Stator Field Megastructure" for loc in game.locations), "the expedition puts the segment on the map")
game, io, _ = start(None)
game.story_manager.current_chapter = "ch2b"
game.story.done["heading.opened"] = 1
text = play(game, io, "ring.expedition", "2")
expect(options(text) == 3 and standing(game)["mandate"] == 10, "without the file: three ways to go, the escort is the Mandate's")
text = play(game, io, "ring.segment", "1", where="Stator Field Megastructure")
expect("eleven minutes" in flat(text) and standing(game)["concord"] == 5, "at the segment: readings for the survey")
game.turn += 6
text = play(game, io, "ring.lost", "3")
expect("eleven years ago" in flat(text) and game.story_manager.story_states.get("saw_the_segment_turn")
       and standing(game)["concord"] == 20, "the segment turns under a needle; the logs go to House Rostrom")

# ---- the sleeper wakes ---------------------------------------------------------------------------
SLEEPER = [(["neon_sleeper_carried"], "then for you, by name", 30000), (["neon_land"], "next to Geod's Row", 30000),
           ([], "the captain who carried me", 10000)]
for flags, words, paid in SLEEPER:
    game, io, _ = start(record("cargo1", "trade", flags) if flags else None)
    game.turn = 13
    before = game.ship.money
    text = play(game, io, "sleeper.wakes", "1", where="Delta")
    expect(words in flat(text) and "Astin Pfennig" in flat(text), "the sleeper with %s: %r" % (flags or "no history", words))
    expect(game.ship.money == before + paid and game.story_manager.story_states.get("ottavine_patron"),
           "the sleeper with %s pays %d" % (flags or "no history", paid))

# ---- the other captain ---------------------------------------------------------------------------
CLONE = [(["clone_partner"], "Split them again", "1", 20000), (["clone_reported"], "Not my face", "2", 0),
         (["clone_let_go", "clone_reported"], "copy you reported", "1", 0), (["clone_let_go"], "Serac sends his regards", "1", 0),
         (["rescanned"], "yours at twenty-five", "1", 0), ([], "nobody ever grew a copy of you", "2", 0)]
for flags, words, answer, paid in CLONE:
    game, io, _ = start(record("cargo1", "trade", flags) if flags else None)
    game.turn = 19
    game.story.done["hansa.first_mark"] = 1
    before = game.ship.money
    text = play(game, io, "clone.name_twice", answer)
    expect(words.lower() in flat(text).lower(), "the other captain with %s: %r" % (flags or "no history", words))
    expect(options(text) <= 2 and game.ship.money == before + paid, "the other captain with %s: two choices" % (flags or "no history"))

# ---- order 4471 ----------------------------------------------------------------------------------
SEED = [(["first_node"], "ELEVEN THOUSAND", 20), (["cu113_contract"], "AN HOUR THAT WAS MINE", 20),
        (["cu113_refused"], "SAID NO", 10), (["cu113_sold"], "RESEARCH HOUSE", 5), (["cu113_wiped"], "YOU WIPED", 5),
        (["relay_cut"], "GREW AROUND THE CUT", 5), ([], "A CAPTAIN WHO KEEPS THINGS", 10)]
for flags, words, trust in SEED:
    game, io, _ = start(record("cargo1", "trade", flags) if flags else None)
    game.story_manager.current_chapter = "ch2a"
    text = play(game, io, "dawn.seed", "1")
    expect(words in flat(text), "the seed with %s: %r" % (flags or "no history", words))
    expect(game.dawn_trust == trust and options(text) <= 2, "the seed with %s: answering is worth %d (%d)" % (
        flags or "no history", trust, game.dawn_trust))
game, io, _ = start(None)
game.story_manager.current_chapter = "ch2b"
play(game, io, "dawn.seed", "2")
expect(game.dawn_trust == -20 and standing(game)["mandate"] == 10, "reporting the broker robot pleases the Mandate, not the Dawn")

# ---- the hollow rock -------------------------------------------------------------------------------
ROCK = [(["nano_trusted"], "ASKING YOU FIRST"), (["nano_supplier"], "THIRD GALLERY"), (["nano_sold_out"], "WE MOVED"),
        (["nano_sampled"], "NOT LEARNED TO HEAR"), ([], "WHO SHOULD WE TELL")]
for flags, words in ROCK:
    game, io, _ = start(record("cargo1", "trade", flags) if flags else None)
    game.story_manager.current_chapter = "ch2a"
    game.story.done["ring.expedition"] = 1
    text = play(game, io, "rock.receiver", "3")
    expect(words in flat(text) and "ONCE EVERY ELEVEN MINUTES" in flat(text), "the rock with %s: %r" % (flags or "no history", words))
    expect(game.story_manager.story_states.get("rock_listening") and game.dawn_trust == 5, "keeping the colony's news")

# ---- act 3: the four roads --------------------------------------------------------------------------
ROADS = [   # chapter, crisis, low point, climax, answers, the segments' holder it leads to
    ("ch3a", "road.hansa.blockade", "road.hansa.licence", "road.hansa.vote", ["1", "1", "1"], "segments_common"),
    ("ch3b", "road.mandate.decoys", "road.mandate.list", "road.mandate.taking", ["2", "1", "1"], "segments_mandate"),
    ("ch3c", "road.door.second_turn", "road.door.clocks", "road.door.through", ["1", "1", "1"], "segments_rostrom"),
    ("ch3d", "road.dawn.census", "road.dawn.price", "road.dawn.quiet", ["1", "1", "1"], "segments_dawn"),
]
ENDING = {"ch3a": "ending_trade", "ch3b": "ending_combat", "ch3c": "ending_discovery", "ch3d": "ending_dawn"}
for cid, crisis, low, climax, answers, holder in ROADS:
    game, io, _ = start(None)
    sm = game.story_manager
    sm.current_chapter = cid
    sm.completed_chapters.update(["ch1", "ch2a", "ch2b", cid])
    sm.plot_points = 500
    game.ship.money = 200000
    for nid, answer in zip((crisis, low, climax), answers):
        game.turn += 10
        play(game, io, nid, answer)
    expect(game.story_manager.story_states.get(holder), "%s: the climax leaves the segments with %s" % (cid, holder))
    cond = game.story.condition_for(ENDING[cid])
    expect(cond and climax in cond.get("done", []), "%s's ending waits for %s" % (cid, climax))
game, io, _ = start(record("cargo1", "trade", ["kept_the_pellet", "met_the_stranger"]))
game.story_manager.current_chapter = "ch3c"
game.story_manager.plot_points = 500
game.story.done.update({"road.door.clocks": 1})
game.turn = 20
text = play(game, io, "road.door.through", "1")
expect("worn smooth" in flat(text) and game.story_manager.story_states.get("paid_with_the_pellet"),
       "the captain who kept the pellet closes the loop at the bar")

# the fourth road is secret until it opens; old saves learn of it
game, io, _ = start(None)
sm = game.story_manager
sm.current_chapter = "ch2a"
sm.chapters["ch2a"].completed = True
io.queue.clear(); io.feed([""] * 4)
with quiet() as buf:
    sm.present_chapter_choice([sm.chapters["ch3c"]])
expect("Quiet Node" not in buf.getvalue() and "Open Road" in buf.getvalue(), "the quiet node is not listed while it is shut")
del sm.chapters["ch3d"]
sm.chapters["ch2a"].next_chapters.remove("ch3d")
with quiet():
    game.bring_up_to_date()
expect("ch3d" in sm.chapters and "ch3d" in sm.chapters["ch2a"].next_chapters, "an old save learns the fourth road")
expect(cargo.ending_title(record("cargo2", "dawn")) == "the Quiet Node", "a Cargo 2 dawn ending is the Quiet Node")

# ---- the last promises, and old acquaintances ---------------------------------------------------------
ECHOES = [   # scene, record flags, words, answer, where
    ("santor.returns", ["fourth_test_copy"], "kept for forty years in a locker", "3", None),
    ("santor.returns", ["fourth_test_to_rostrom"], "He wants it back", "1", None),
    ("santor.returns", [], "eleven minutes", "4", None),
    ("lyra.expedition", ["logged_the_lyra_signal"], "copy of the old signal log", "1", None),
    ("lyra.expedition", ["heard_the_lyra_story"], "Maud Kettle", "1", None),
    ("lyra.expedition", [], "no signal, no wreck, no answer", "1", None),
    ("rootstock.voce", ["rootstock_family"], "We kept your place at the table", "2", None),
    ("rootstock.voce", ["sold_the_exoparts"], "Our loaders still wear them", "1", None),
    ("rootstock.voce", ["met_rootstock"], "feeds three systems", "3", None),
    ("mraz.angels", ["mraz_spared"], "Same hauler", "1", None),
    ("mraz.angels", ["mraz_hired"], "The rate has gone up", "2", None),
    ("mraz.angels", ["mraz_handed"], "remembers who put her there", "3", None),
    ("cargolytes.sect", ["met_cargolytes"], "apparent good order", "3", None),
]
for nid, flags, words, answer, where in ECHOES:
    game, io, _ = start(record("cargo1", "trade", flags) if flags else None)
    game.story_manager.current_chapter = "ch2a"
    game.story.done.update({"ring.lost": 1, "ring.expedition": 1})
    game.turn, game.ship.money = 30, 100000
    text = play(game, io, nid, answer, where)
    expect(words.lower() in flat(text).lower(), "%s with %s: %r" % (nid, flags or "no history", words))

print("acts: frame, turning points and promises, %d problems" % problems[0])
sys.exit(1 if problems[0] else 0)
