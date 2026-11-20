# Changelog

Cargo 2, the second part of the Cargo trilogy. Versions follow the game (`game/__init__.py`).

## 2.3.0

- **One captain, every part.** A game started as a recorded captain keeps the captain's id and
  log. The record now carries the captain's history: what they left in each part of the trilogy,
  their own time (the turns lived, whatever year the dock clock says), and the line of the
  timeline each game is. Nothing done in another part ever rewrites a save.
- **An errand from 2533, ready for Cargo 3** (still in development). There, Conte Ottavine wakes
  from a long stasis without the word that opens her family's vault: the chambers take the
  newest memories first. A Cargo 3 captain thrown back to 2460 can be at Delta when she first
  wakes, and be in the room when she chooses it (or suggest one). The word travels back in the
  record.
- Keys a newer game writes into a captain's record are kept and written out again.
- A record that went through an older game (Cargo 2 2.2.0, Cargo 1 1.2.1) is offered a join
  with the captain's newer record. An errand meant for a newer version is named when you start
  and when you export, and stays in the record until you update.
- The captain menu shows your own time, your line and your errands. New captains get a Cargo 2
  id (`C2-`); they used to get Cargo 1's prefix.
- Fixed: the port's price forecast (`prices`) was titled "{port_broker}" instead of words; a
  check now makes sure no name is ever shown as a raw {placeholder}, in the story or the code.

## 2.2.0

- **A side quest in every act.** Adit, an old loader agrobot on the cargo rings of Beta, Alpha
  and Gamma, is looking for its lost hand (from the start; Adit's patch routine: modules wear
  half as fast). Korai, a needle signaller who rides every needle, wants a verse she does not
  know (act 2; needle-talk: fewer fights on needles). The Stellar Institute sold its archive
  after the fire, and someone at Delta bought it (act 3; research and the Concord's thanks, or
  the Institute's survey charts: research goes further). Each can start from either end, some
  Cargo 1 captains have a shorter way, and none is needed for an ending.
- Astin Pfennig keeps the Kraal family's books at Delta. Small sights at Omega XIV, DSO-Gamma,
  DSO-Beta, Sigma VII and Nova Labs, some of them remembering what a Cargo 1 captain did.
- The captain's notes name a place only when the next step is there.
- Fixed: an equipment failure could take the founders' pass, Meza Voce's reader or another
  item a side quest needs, and the quest could not be finished.

## 2.1.0

- **Look and think.** `look` (lk) at a dock: what is going on (the next needle, people due),
  the people there, and things to examine. `think` (th): the captain's notes, from the leads
  they have picked up to what the story still needs.
- **People who travel on their own.** Pell Okafor flies Alpha, Beta and Gamma; Grab Allsa Targa
  never leaves Alpha; Meza Voce, Tylde Kren, Yzode van Rostrom and the other captain have
  routes of their own. Find them by reasoning, not by luck: the docks and your notes say where.
- **Two side quests and special equipment:** a sealed locker at Alpha that takes a pass nobody
  carries any more (the founders' transponder: cheaper needles), and a ship at Gamma that lies
  about what it is (a decoy code: Mandate patrols wave you through). Small finds at Delta,
  Epsilon, Beta and the segment itself. None of it is needed for an ending.
- The stats box shows CΔRGΩ][.

## 2.0.0

The whole game, rebuilt on Cargo 1.2's core with CLIo's screen and sound layer. About forty
years after the Hauler Hansa was founded.

- **The needles.** Between the stars a hauler books a place in a Hansa convoy: the front is
  safe and dear, the tail cheap and cold, and the Cargolytes work the tail. Inside a star system
  you fly on your own fuel. Needles leave planets every turn and other docks every third turn.
- **Standing** with the Hansa, the Mandate and the Concord, and a hidden trust kept by the
  machines. Fares, patrols, research and the roads of the story follow it.
- **Openings for every kind of captain:** a fresh hauler, each Cargo 1 ending (the Hansa
  founder, the legion veteran or Serac's colonel, the one who filed the heading, the tycoon),
  a career left unfinished, a Cargo 2 captain again, a Cargo 3 captain thrown back.
- **The story,** in three acts and four roads. The heading file comes up at auction; an
  expedition finds a segment of a ring around the Sun, and loses it when it throws a convoy
  eleven years into the past. Then the open road (the Hansa), the lighthouse (the Mandate), the
  door (House Rostrom), or a quiet fourth road for captains the machines trust. Each ending
  decides who holds the segments when Cargo 3 begins.
- **Cargo 1 remembered.** Every promise Cargo 1 made is kept, and every choice it carries over
  is read: Allsa Targa, Pell Okafor, Hanne Lauritz, Conte Ottavine, the other captain, CU-113,
  the colony at Sigma VII, Dharr Santor, Meza Voce, the Void Angels, and the bar where it began.
- **The ship's modules:** grips on the hull's spine for container modules, turret mounts,
  shields, radiation shielding, scanners, a repair bay, a robotic offloader, debris retrieval
  and a drone hangar. They wear, break and are mended at a yard.
- **Convoy fights,** round by round against bigger ships: focus fire, screen the haulers of
  your needle, countermeasures, drones, boarding, breaking off.
- **Research in two tiers:** branches whose twins close for good.
- **Achievements,** written into the captain's record with the standings, for Cargo 3.
- **Sound:** music composed as you play and effects, through CLIo's synthesizer; silent where
  nothing can play. `sound` turns it on or off.
- **Looks:** twelve styles (`style`), every screen from 36 columns up, in Termux too.
- Saves and captain records shared with Cargo 1 in `~/.cargo-saga`.
