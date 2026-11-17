# Cargo 2

The Cargo saga continues, about forty years after the Hauler Hansa was founded. The second part
of the Cargo trilogy, set in the [Eryxian universe](https://github.com/eryxgames/eryxian/wiki).

```console
>>>
        ╔═══════ C Δ R G Ω ][ ══════╗
        ║     Space Trading Saga    ║
        ╚═══════════════════════════╝
                Version 2.0.0-dev
```

## Status

Being rebuilt (November 2026). The first milestone is the skeleton: Cargo 1.2's game running as
Cargo 2, split into modules, with CLIo's screen and sound layer alongside, ready to be given its
own world and story. What works now:

- a new game, or one started as any captain whose record is in the shared folder; a captain from
  Cargo 1 comes in with their name, ranks and choices;
- the opening fits the captain: a fresh hauler; Cargo 1's Hansa founder, legion veteran (or
  Serac's colonel), the one who filed the heading, the tycoon, or a career left unfinished; a
  captain from Cargo 2 again, or from Cargo 3, thrown back. Each starts with its own standing;
- act 1 at the needle office: the founders' wall, Grab Allsa Targa, Pell Okafor at fifty-nine and
  Hanne Lauritz's notebooks remember what a Cargo 1 captain did, and greet a fresh one; the
  cantinas talk about 2460;
- acts 1 and 2: the heading file comes up at auction and is read; an expedition finds the first
  segment of the ring past Sedna's orbit, and loses it when it throws a needle eleven years into
  the past. On the way Conte Ottavine wakes, the other captain books your needle, the Binary Dawn
  speaks and the colony at Sigma VII hears the ring turning: each as your Cargo 1 captain left it;
- act 3, four roads, each with a crisis, a low point and a climax that decides who holds the
  segments when Cargo 3 begins: the open road (the Hansa: the closed buoys, the licence, the vote
  on the drive), the lighthouse (the Mandate: decoys, Serac's list, the taking), the door (House
  Rostrom: the second turn, two clocks, and through the door to an outpost bar forty years ago),
  and a quiet fourth road for captains the machines trust, which nobody mentions until it opens;
- Dharr Santor comes back for the name on the drive; an expedition to Lyra goes quiet; Meza Voce,
  the Void Angels, the Cargolytes and some thirty rumours remember what a Cargo 1 captain did;
- travel, trade, fights, quests, crew, saves, autosave and continue;
- every screen from 36 columns up, in Termux too; standard library only;
- the needles: between the stars you book a place in a Hansa convoy (front: safe and dear; tail:
  cheap and cold, and the Cargolytes work the tail); inside a star system you fly on your own fuel;
- the ship's modules, after the hauler manuals: the hull's spine has grips (three on the old
  hauler, five on an Ironback, seven on a Farstrider) and yards at planets and asteroid bases fit
  container modules, turret mounts, shields, radiation shielding, scanners, a repair bay, a robotic
  offloader, debris retrieval and a drone hangar (upgrade/u, modules); modules wear in fights and
  on rough lanes, and a broken one does nothing until it is mended;
- convoy fights: a ship of threat 3 or more is fought round by round (focus fire, screen the
  haulers of your needle, countermeasures, drones, boarding, breaking off); the haulers in the
  file behind you can be hit, and the Hansa hears how you looked after them. Focused fire wins as
  often as Cargo 1's one-roll fight did (tools/fights.py checks every difficulty);
- needles leave planets every turn and other docks every third turn: from an outpost you may
  wait at the buoy;
- standing with the Hansa, the Mandate and the Concord, in the journal: the Hansa's fares follow
  it, Mandate cutters wave a trusted captain through, the Concord's houses share more research;
- styles: `style` picks one of twelve (CLIo's seven, and five from Cargo 2's first version:
  cargo, hercules, dark, blue, green); frames and colours follow it, and it is kept for later
  games. `CARGO_STYLE=name` picks one for a single run; `NO_COLOR=1` turns colour off and
  `CARGO_ASCII=1` draws in plain ASCII.

The story is written through to its four endings, and every promise Cargo 1 made to Cargo 2 is
kept. Still to come: research trees, achievements, the map of 2460, sound, and balance. The plan (world in 2460, the convoy needles, factions and
the ring, the modular ship, tactical convoy combat, research trees) is in the project's design
document.

## Playing

```bash
git clone https://github.com/eryxgames/Cargo-2.git
cd Cargo-2
python3 cargo2.py
```

Python 3.8 or newer, nothing to install. Saves and captain records are shared with Cargo 1
(1.2.1 and later) in `~/.cargo-saga`; set `CARGO_SAGA_HOME` to keep them elsewhere.

## Layout

```
cargo2.py       launcher
game/           the game, Cargo 1.2's core split by what each part does:
  world.py        Game: its state and the turn loop; inherits the mixins of the modules below
  start.py        continue a save, or a new game (fresh or as a recorded captain)
  terminal.py     width, narrow layouts, wrapping, boxes;  screens.py: the Game's screens
  look.py         CLIo's terminal detection and themes, applied to the boxes
  saves.py  captain.py      saves; the captain's record carried between the parts
  story.py  chapters.py     the storykit runtime; chapters, milestones, endings
  ship.py  travel.py  market.py  hansa.py  encounters.py  events.py  research.py
  actions.py  port.py  places.py  quests.py  contracts.py  people.py  passengers.py
  ranks.py  commands.py  factions.py  needles.py  modules.py  tactics.py
kit/            CLIo's screen and sound layer, copied in by tools/sync_kit.py (Apache-2.0)
story/          the story: cargo2.story.json and the files in story/cargo2/, built into
                cargo2.game.json for the game; saga.json and Cargo 1's story, copied
storykit/       the trilogy's story tools (format, validator, map), copied
themes/         Cargo 2's own styles (CLIo theme files), beside CLIo's in kit/style/
tools/          checks: smoke, bot, fuzzing, save round trips, hostile files, kit
legacy/         Cargo 2 0.1.0-a (2025), kept as a source of themes, research, items and texts
```

`kit/` is never edited here: change the files in CLIo and copy them again with
`python3 tools/sync_kit.py ../CLIo`. `tools/check.sh` (or `tools/check.sh quick`) runs every
check, including one that fails if a copied file was changed.

## Writing the story

The story is data in the storykit format (`storykit/FORMAT.md`): scenes, choices, conditions and
effects in `story/cargo2/*.json`, listed in `story/cargo2.story.json`. The chapters, their
milestones and the endings are there too (`story/cargo2/main.json`): their conditions are the ones
the game uses. Characters who span the
trilogy are named once, in `story/saga.json`. After a change:

```bash
python3 tools/build_story.py                     # builds story/cargo2.game.json
python3 storykit/validate.py story/saga.json     # unknown names, broken links, unpaid promises
python3 tools/scenes.py                          # plays every scene with every choice
python3 tools/openings.py                        # every kind of captain starts right
python3 tools/acts.py                            # the turning points, and the promises paid
```

`storykit/`, `story/saga.json` and Cargo 1's story are copies from the Cargo repository
(`python3 tools/sync_story.py ../Cargo`); change them there.

## Credits

Eryx Games. The `kit/` folder is from [CLIo](https://github.com/eryxgames/CLIo) by Daniel
Sandner, under the Apache License 2.0 (`kit/LICENSE`, `kit/NOTICE`).
