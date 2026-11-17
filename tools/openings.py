#!/usr/bin/env python3
"""Every way into Cargo 2 starts right: a fresh captain, each Cargo 1 ending (and the flags that
change it), a Cargo 2 captain playing again and a Cargo 3 captain thrown back. For each record:
the right opening plays, standing starts where that opening puts it, nothing is left unfilled;
the act-1 scenes at the needle office show the variant and the choices the record calls for;
and the scenes come on their own in a few dozen turns at the docks.
Usage: python3 tools/openings.py"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headless import quiet  # noqa: E402
from storytest import cargo, expect, flat, options, play, problems, record, start, unfilled  # noqa: E402


# ---- the openings -------------------------------------------------------------------------
OPENINGS = [   # (what, record, opening, words it says, standing after it)
    ("a fresh captain", record(), "intro.fresh", "a place booked in the next needle", {}),
    ("Cargo 1, trade", record("cargo1", "trade", ["hansa_founder"]), "intro.founder", "founded by", {"hansa": 20}),
    ("Cargo 1, combat", record("cargo1", "combat"), "intro.veteran", "First Legion", {"mandate": 30}),
    ("Cargo 1, combat, Serac's colonel", record("cargo1", "combat", ["took_the_commission"]), "intro.colonel",
     "Serac's commission", {"mandate": 45, "hansa": -10}),
    ("Cargo 1, discovery", record("cargo1", "discovery"), "intro.heading", "course home", {"concord": 20}),
    ("Cargo 1, tycoon", record("cargo1", "tycoon"), "intro.tycoon", "richest hauler", {"hansa": 10, "concord": 10}),
    ("Cargo 1, tycoon who paid for the portal", record("cargo1", "tycoon", ["stellar_portal"]), "intro.tycoon",
     "paid for the portal", {"hansa": 10, "concord": 10}),
    ("Cargo 1, no ending", record("cargo1", ""), "intro.unfinished", "walked away from a career", {}),
    ("Cargo 2, again", record("cargo2", "trade"), "intro.again", "flown these years once already", {}),
    ("Cargo 3, thrown back", record("cargo3", "trade"), "intro.from_cargo3", "Gyrotron", {}),
]
for what, rec, opening, words, standing in OPENINGS:
    game, io, text = start(rec)
    played = [nid for nid in game.story.done if nid.startswith("intro.")]
    expect(played == [opening], "%s: opening %s, expected %s" % (what, played, opening))
    expect(words in flat(text), "%s: the opening does not say %r" % (what, words))
    expect(not unfilled(text), "%s: unfilled %s" % (what, unfilled(text)))
    if rec is not None:
        expect(rec["name"] in text, "%s: the opening does not name the captain" % what)
    for faction in cargo.FACTIONS:
        expect(game.standing_of(faction) == standing.get(faction, 0), "%s: standing with %s is %d, expected %d" % (
            what, faction, game.standing_of(faction), standing.get(faction, 0)))
    if opening == "intro.from_cargo3":
        expect(game.ship.items.get("old_navcomp"), "a Cargo 3 captain keeps the old navigation computer")
    # and the game goes on: a few turns of trips between docks, saved and loaded on the way
    io.default = "1"
    with quiet():
        for turn in range(6):
            game.turn += 1
            game.current_location = random.choice(game.locations[:5])
            game.story.tick()
    io.default = ""

# ---- a recorded captain is still that captain after a save and a load ---------------------------------
game, io, _ = start(record("cargo1", "combat", ["took_the_commission", "convoy_friend"]))
game.front_berths = 4
with quiet():
    game.save_game("openings")
    loaded = cargo.load_game("openings")
expect(loaded.story.origin and loaded.story.origin["story"]["ending"] == "combat"
       and "convoy_friend" in loaded.story.origin["story"]["flags"], "the captain record survives a save and a load")
expect(loaded.standing_of("mandate") == 45 and loaded.front_berths == 4, "standing and berths survive a save and a load")

# ---- the founders' wall --------------------------------------------------------------------
game, io, _ = start(record("cargo1", "trade", ["hansa_founder"]))
game.turn = 3
text = play(game, io, "hansa.first_mark", "1")
expect("Yours is the first" in flat(text), "a founder's name is first on the wall")
expect(game.standing_of("hansa") == 40 and game.hansa_bonds == 2, "the founders' share: standing 40 and two bonds (%d, %d)"
       % (game.standing_of("hansa"), game.hansa_bonds))
expect("hansa.first_mark:founders_share" in game.story.done, "the story remembers the founder's choice")
game, io, _ = start(record("cargo1", "trade", ["hansa_member"]))
game.turn = 3
text = play(game, io, "hansa.first_mark", "")
expect("the eleventh" in flat(text) and game.standing_of("hansa") == 30, "a member is eleventh and thanked")
game, io, _ = start(record("cargo1", "trade", ["hansa_outside"]))
game.ship.money = 9000
game.turn = 3
text = play(game, io, "hansa.first_mark", "1")
expect("None of them is yours" in flat(text), "a captain who stayed out is not on the wall")
expect(game.story_manager.story_states.get("joined_late") and game.ship.money == 4000 and game.standing_of("hansa") == 40,
       "joining forty years late costs 5,000 and is remembered")
game, io, _ = start(record("cargo1", "trade", ["hansa_outside"]))
game.ship.money = 1000
game.turn = 3
text = play(game, io, "hansa.first_mark", "1")
expect(game.ship.money == 1000 and game.standing_of("hansa") == 10, "without 5,000 the only answer is to stay out")
game, io, _ = start(None)
game.turn = 3
text = play(game, io, "hansa.first_mark", "")
expect("touch the glass for luck" in flat(text) and game.standing_of("hansa") == 0, "a fresh captain touches the glass")

# ---- Grab Targa ----------------------------------------------------------------------------
TARGA = [(["convoy_friend", "convoy_helped"], "I still owe you a berth"), (["convoy_helped"], "Two barges"),
         (["targa_remembers_the_raid"], "moves it to the tail"), (["convoy_refused"], "melons"), ([], "New captain")]
for flags, words in TARGA:
    game, io, _ = start(record("cargo1", "trade", flags) if flags else None)
    game.story.done["hansa.first_mark"] = 0
    game.turn = 5
    text = play(game, io, "hansa.targa", "1")
    expect(words in flat(text), "Targa with %s says %r" % (flags or "no history", words))
    expect(1 <= options(text) <= 2,
           "Targa with %s offers one pair of choices" % (flags or "no history"))
    if flags[:1] == ["convoy_friend"]:
        expect(game.front_berths == 10, "Targa's berth: ten jumps at the front")
        here = game.current_location
        there = next(loc for loc in game.locations if not game.same_system(loc, here))
        game.ship.money = 10 ** 6
        middle = game.needle_fare("middle")
        io.queue.clear(); io.feed(["1"])
        with quiet():
            booked = game.book_needle(there)
        expect(booked == "front" and game.ship.money == 10 ** 6 - middle and game.front_berths == 9,
               "a berth puts the front at the middle's fare and is used up")
    if flags == ["convoy_helped"]:
        expect(game.front_berths == 3, "a tow is worth three berths")

# ---- Pell at fifty-nine ------------------------------------------------------------------------
PELL = [(["pell_friend", "pell_lent"], "I'll take the place behind you"), (["pell_lent"], "pays back the ten thousand"),
        (["pell_redeemed"], "back from the raiders"), (["pell_turned_away"], "polite about it"),
        (["fought_pell"], "wrong side"), (["paid_pell"], "came back with a ship"), (["pell_advised"], "keep my receipts"),
        ([], "teaches new haulers")]
for flags, words in PELL:
    game, io, _ = start(record("cargo1", "trade", flags) if flags else None)
    game.story.done["hansa.first_mark"] = 0
    game.turn = 9
    money = game.ship.money
    text = play(game, io, "hansa.pell", "1")
    expect(words in flat(text), "Pell with %s says %r" % (flags or "no history", words))
    expect(options(text) <= 2, "Pell with %s offers at most two choices" % (flags or "no history"))
    if flags == ["pell_lent"]:
        expect(game.ship.money == money + 40000, "Pell pays back the loan with interest")

# ---- Lauritz's notebooks ---------------------------------------------------------------------
LAURITZ = [(["lauritz_bribed", "lauritz_trust"], "page nine"), (["lauritz_bribed", "fined_for_the_fee"], "fined in full"),
           (["lauritz_burned"], "opened her sealed case"), (["double_cross", "lauritz_trust"], "page seventy-two"),
           (["lauritz_trust"], "page forty-one"), (["lauritz_courier"], "never opened it"), ([], "The Manifests")]
for flags, words in LAURITZ:
    game, io, _ = start(record("cargo1", "trade", flags) if flags else None)
    game.story.done["hansa.first_mark"] = 0
    game.turn = 13
    game.ship.money = 100000
    text = play(game, io, "hansa.notebooks", "1")
    expect(words in flat(text), "Lauritz with %s: %r" % (flags or "no history", words))
    expect(options(text) <= 2, "Lauritz with %s offers at most two choices" % (flags or "no history"))
    if flags == ["lauritz_bribed", "lauritz_trust"]:
        expect(game.ship.money == 95000 and game.standing_of("mandate") == 5, "the old fine is paid with interest")

# ---- an old hand from Cargo 1, for a captain who imported one ------------------------------------
game, io, _ = start(None)
visitor = record("cargo1", "trade", ["hansa_founder"], name="Mor Halloway", rank="Hansa Founder")
game.visiting_captains.append(visitor)
text = play(game, io, "hansa.old_hand", "1")
expect("Mor Halloway, Hansa Founder" in flat(text), "an imported Cargo 1 captain sits under the founders' wall")

# ---- the scenes come on their own -------------------------------------------------------------
ACT1 = ("hansa.first_mark", "hansa.targa", "hansa.pell", "hansa.notebooks")
for seed in (1, 2, 3):
    rec = record("cargo1", "trade", ["hansa_founder", "convoy_friend", "pell_lent", "lauritz_trust"])
    game, io, _ = start(rec, seed)
    io.default = ""
    planets = [loc for loc in game.locations if type(loc).__name__ == "Planet"]
    with quiet() as buf:
        for turn in range(80):
            game.turn += 1
            game.current_location = random.choice(planets)
            game.story.tick()
    missing = [nid for nid in ACT1 if nid not in game.story.done]
    expect(not missing, "seed %d: in 80 turns at the docks these never played: %s" % (seed, missing))
    expect(not unfilled(buf.getvalue()), "seed %d: unfilled %s" % (seed, unfilled(buf.getvalue())))

print("openings: %d ways in, %d problems" % (len(OPENINGS), problems[0]))
sys.exit(1 if problems[0] else 0)
