# Cargo 2 0.1.0-a (legacy)

The first attempt at Cargo 2 (January to February 2025): Cargo 1 as it was then, split into
`core/` and `ui/`, with its data in `data/` tables. It needs pygame and PyYAML and does not
save. It is kept here, unchanged, as a source: its colour themes, research tree, actions,
items and beacons, buildings, ranks, enemy table, uprisings and texts are being carried into
the new Cargo 2 (see the design in the project, section 2). Nothing outside this folder
imports it.

Run it as before, from this folder: `pip install pyyaml pygame`, then `python cargo.py`.
