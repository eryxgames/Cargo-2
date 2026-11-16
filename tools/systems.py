#!/usr/bin/env python3
"""Cargo 2's own systems, checked one by one on a real game: standing with the factions, the
needles between the stars and the hops inside a system (and whatever later systems add here).

    python3 tools/systems.py
"""
import os, random, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ["CARGO_SAGA_HOME"] = tempfile.mkdtemp(prefix="cargo-systems-")
import headless  # noqa: E402

cargo = headless.load(os.path.join(os.path.dirname(HERE), "game", "world.py"))
problems = []


def expect(ok, what):
    if not ok:
        problems.append(what)


# ---- standing ------------------------------------------------------------------------
game, io = headless.new_game(cargo)
expect(game.standing == {"hansa": 0, "mandate": 0, "concord": 0}, "a new game starts at standing 0: %s" % game.standing)
game.story.apply({"standing.hansa": 30, "standing.mandate": -250, "dawn_trust": 15})
expect(game.standing_of("hansa") == 30, "an effect moves the Hansa standing")
expect(game.standing_of("mandate") == -100, "standing stops at -100")
expect(game.dawn_trust == 15, "the dawn's trust moves")
snap = game.story_snapshot()["stats"]
expect(snap.get("standing.hansa") == 30 and snap.get("standing.mandate") == -100 and snap.get("dawn_trust") == 15,
       "the story sees the standings: %s" % {k: v for k, v in snap.items() if "standing" in k or "dawn" in k})
expect(game.story.check({"standing.hansa": 25}, game.story.snapshot()), "a condition reads a standing")
expect(not game.story.check({"standing.concord": 1}, game.story.snapshot()), "a condition fails on a low standing")
expect(abs(game.hansa_fare_factor() - 0.88) < 1e-9, "the Hansa's fares follow its standing")
game.standing["mandate"] = 100
random.seed(1)
expect(all(game.waved_through("militia") for _ in range(20)), "a trusted captain is waved through by cutters")
expect(not any(game.waved_through("pirate") for _ in range(20)), "pirates wave nobody through")
game.standing["mandate"] = 10
expect(not any(game.waved_through("militia") for _ in range(50)), "a captain the Mandate barely knows is stopped")
game.standing["concord"] = 100
expect(abs(game.concord_research_factor() - 1.5) < 1e-9, "the Concord shares more with a trusted captain")
io.queue.clear(); io.feed([""])
with headless.quiet() as out:
    game.story.journal()
expect("The Hansa: +30, trusted" in out.getvalue(), "the journal shows standing")

# a save from before standing existed loads with every standing at 0
game, io = headless.new_game(cargo)
del game.standing, game.dawn_trust
with headless.quiet():
    game.save_game("old")
    loaded = cargo.load_game("old")
expect(loaded.standing == {"hansa": 0, "mandate": 0, "concord": 0} and loaded.dawn_trust == 0,
       "an older save gets standing 0")

# ---- the needles -----------------------------------------------------------------------
game, io = headless.new_game(cargo)
game.turn = 50
here = game.current_location
by_name = {loc.name: loc for loc in game.locations + [l for g in game.hidden_locations.values() for l in g]
           + [l for c in game.chapter_locations.values() for g in c.values() for l in g]}
expect(game.same_system("Omega XIV", "Ancient Ruins Alpha") and not game.same_system("Alpha", "Beta"),
       "places in the same star system are told from the rest")
middle = game.needle_fare("middle")
expect(game.needle_fare("front") in (2 * middle, 2 * middle + 1) and abs(game.needle_fare("tail") - middle / 2) <= 1,
       "front costs twice the middle, the tail half: %s" % [game.needle_fare(p) for p in ("front", "middle", "tail")])
game.hansa_bonds = 2
expect(game.needle_fare("middle") < middle, "bonds lower the fare")
game.hansa_bonds = 0
game.standing["hansa"] = -100
expect(game.needle_fare("middle") > middle, "a Hansa that distrusts the captain charges more")
game.standing["hansa"] = 0
other = next(loc for loc in game.locations if not game.same_system(loc, here))
money, turn = game.ship.money, game.turn
io.queue.clear(); io.feed([""])                                     # Enter at the needle office: stay
with headless.quiet():
    went = game.travel_to_location(other.name)
expect(not went and game.current_location is here and game.turn == turn and game.ship.money == money,
       "Enter at the needle office: no needle, no turn, no fare")
game.ship.money = 100000
io.queue.clear(); io.feed(["2"] + [""] * 30)
random.seed(3)
with headless.quiet():
    went = game.travel_to_location(other.name)
expect(went and game.current_location is other and game.turn == turn + 1, "a booked needle takes the ship there")
expect(game.ship.money <= 100000 - middle, "the middle place is paid: %s" % (100000 - game.ship.money))
# riding on account, and past the limit
game.ship.money = 0
fare = game.needle_fare("middle")
io.queue.clear(); io.feed(["2"])
with headless.quiet():
    booked = game.book_needle(here)
expect(booked == "middle" and getattr(game, "dues_arrears", 0) == fare, "a captain without money rides on account")
game.dues_arrears = 10 * fare
game.ship.cargo["salt"] = 40
io.queue.clear(); io.feed(["2"])
with headless.quiet():
    booked = game.book_needle(here)
expect(booked is None and game.ship.cargo["salt"] < 40, "past the limit the office refuses and the convoy master takes cargo")
# a hop inside a system burns fuel, or buys it
game, io = headless.new_game(cargo)
omega, ruins = by_name["Omega XIV"], by_name["Ancient Ruins Alpha"]
game.locations += [omega, ruins]
game.current_location = omega
game.ship.cargo["fuel"], game.ship.money = 10, 1000
io.queue.clear(); io.feed([""] * 30)
with headless.quiet():
    went = game.travel_to_location(ruins.name)
expect(went and game.ship.cargo["fuel"] == 7, "a hop inside the system burns 3 fuel")
game.ship.cargo["fuel"], money = 1, game.ship.money
game.current_location = omega
io.queue.clear(); io.feed([""] * 30)
with headless.quiet():
    game.travel_to_location(ruins.name)
expect(game.ship.cargo["fuel"] == 0 and money - game.ship.money >= 60, "fuel the hold lacks is bought from the yard")
# the tail: the Cargolytes sometimes cut containers off
game, io = headless.new_game(cargo)
game.ship.cargo["tech"] = 100
losses = 0
for seed in range(200):
    random.seed(seed)
    game.needle_position = "tail"
    before = game.ship.cargo["tech"]
    with headless.quiet():
        game.after_needle()
    losses += game.ship.cargo["tech"] < before
    game.ship.cargo["tech"] = 100
expect(5 < losses < 50, "the tail loses containers now and then: %d in 200" % losses)
game.needle_position = "front"
with headless.quiet():
    game.after_needle()
expect(game.ship.cargo["tech"] == 100, "the front loses nothing")

for problem in problems:
    print("FAIL", problem)
print("systems: %s" % ("ok" if not problems else "%d problems" % len(problems)))
sys.exit(1 if problems else 0)
