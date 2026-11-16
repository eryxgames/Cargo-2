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
- travel, trade, fights, quests, crew, the Hansa's dues, saves, autosave and continue;
- every screen from 36 columns up, in Termux too; standard library only.

The story of Cargo 2 is still to be written: for now there is one opening chapter, and the map
and the endings are still Cargo 1's. The plan (world in 2460, the convoy needles, factions and
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
  saves.py  captain.py      saves; the captain's record carried between the parts
  story.py  chapters.py     the storykit runtime; chapters, milestones, endings
  ship.py  travel.py  market.py  hansa.py  encounters.py  events.py  research.py
  actions.py  port.py  places.py  quests.py  contracts.py  people.py  passengers.py
  ranks.py  commands.py
kit/            CLIo's screen and sound layer, copied in by tools/sync_kit.py (Apache-2.0)
story/          the story (cargo2.story.json; storykit sources to come)
tools/          checks: smoke, bot, fuzzing, save round trips, hostile files, kit
legacy/         Cargo 2 0.1.0-a (2025), kept as a source of themes, research, items and texts
```

`kit/` is never edited here: change the files in CLIo and copy them again with
`python3 tools/sync_kit.py ../CLIo`. `tools/check.sh` (or `tools/check.sh quick`) runs every
check, including one that fails if a copied file was changed.

## Credits

Eryx Games. The `kit/` folder is from [CLIo](https://github.com/eryxgames/CLIo) by Daniel
Sandner, under the Apache License 2.0 (`kit/LICENSE`, `kit/NOTICE`).
