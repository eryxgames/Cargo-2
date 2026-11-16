#!/usr/bin/env python3
"""Cargo 2's own systems, checked one by one on a real game: standing with the factions (and
whatever later systems add here).

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
io.feed([""])
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

for problem in problems:
    print("FAIL", problem)
print("systems: %s" % ("ok" if not problems else "%d problems" % len(problems)))
sys.exit(1 if problems else 0)
