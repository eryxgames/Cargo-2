#!/usr/bin/env python3
"""What Cargo 2 hands to Cargo 3, written out from the built story: how each ending leaves the
segments, the promises still owed, the flags a captain record carries to Cargo 3 (by arc), the
achievements and standings in the record, and the characters whose timelines continue.

    python3 tools/handoff.py            # writes story/CARGO2-HANDOFF.md
    python3 tools/handoff.py --check    # fails if that file is out of date
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from headless import load  # noqa: E402

OUT = os.path.join(ROOT, "story", "CARGO2-HANDOFF.md")
HOLDERS = ("segments_common", "segments_hansa", "segments_mandate", "segments_rostrom", "segments_dawn")


def setters(nodes, order):
    """flag -> (arc, node) of the first node, in story order, that sets it."""
    rank = {nid: i for i, nid in enumerate(order)}
    found = {}
    for nid, node in sorted(nodes.items(), key=lambda item: rank.get(item[0], len(rank))):
        for eff in [node.get("effects") or {}] + [(c.get("effects") or {}) for c in node.get("choices", [])]:
            for flag in eff.get("set", []):
                found.setdefault(flag, (node.get("arc") or nid.split(".")[0], nid))
    return found


def fill(data, text):
    chars = data["characters"]

    def swap(m):
        person = chars.get(m.group(1)) or {}
        if m.group(2) == "short":
            return person.get("short") or person.get("name") or m.group(0)
        return person.get("name") or m.group(0)
    return re.sub(r"\{([a-z_][a-z0-9_]*)(?:\.([a-z_]+))?\}", swap, text)


def build():
    game = load(os.path.join(ROOT, "game", "world.py"))
    data = game.story_data()
    saga = json.load(open(os.path.join(ROOT, "story", "saga.json"), encoding="utf-8"))
    flags, nodes = data["flags"], data["nodes"]
    found = setters(nodes, data.get("order", []))
    carried = {f: i for f, i in flags.items() if "cargo3" in (i.get("carries_to") or [])}
    lines = ["# Cargo 2: what Cargo 3 inherits", "",
             "Written by `tools/handoff.py` from the built story; do not edit by hand.", "",
             "Cargo 2 has %d story nodes, %d characters and %d flags; %d flags are meant for Cargo 3. A captain"
             " record carries every flag that is set (up to 160, the carried ones first), the endings below,"
             " the achievements and the standings with the Hansa, the Mandate and the Concord."
             % (len(nodes), len(data["characters"]), len(flags), len(carried)), "",
             "## Endings and the segments", "",
             "Each road's climax decides who holds the ring's segments when Cargo 3 begins (a flag in the record).", "",
             "| Ending (record) | Road | Possible holders |", "| --- | --- | --- |"]
    roads = {"trade": ("ending_trade", "road_hansa"), "combat": ("ending_combat", "road_mandate"),
             "discovery": ("ending_discovery", "road_door"), "dawn": ("ending_dawn", "road_dawn")}
    for ending, (eid, arc) in roads.items():
        holders = sorted({f for f in HOLDERS if found.get(f, ("", ""))[0] == arc} |
                         {f for f in HOLDERS for nid, n in nodes.items() if n.get("arc") == arc
                          for c in n.get("choices", []) if f in (c.get("effects") or {}).get("set", [])})
        title = (nodes.get(eid) or {}).get("title", eid)
        lines.append("| %s (`%s`) | %s | %s |" % (title, ending, arc.replace("road_", ""), ", ".join("`%s`" % h for h in holders)))
    lines += ["", "| Holder flag | Means |", "| --- | --- |"]
    for f in HOLDERS:
        lines.append("| `%s` | %s |" % (f, fill(data, flags[f]["about"])))
    lines += ["", "## Promises owed to Cargo 3", "", "| Promise | What |", "| --- | --- |"]
    for pid, prom in saga.get("promises", {}).items():
        if prom.get("pay_by") == "cargo3":
            lines.append("| `%s` | %s |" % (pid, prom.get("about", "")))
    lines += ["", "## Flags carried to Cargo 3, by arc", ""]
    by_arc = {}
    for f, info in sorted(carried.items()):
        by_arc.setdefault(found.get(f, ("game", ""))[0], []).append((f, info))
    for arc in sorted(by_arc):
        lines += ["### %s" % arc, "", "| Flag | Means |", "| --- | --- |"]
        for f, info in by_arc[arc]:
            lines.append("| `%s` | %s |" % (f, fill(data, info.get("about", ""))))
        lines.append("")
    lines += ["## Achievements in the record", "", "| Id | Title | What it took |", "| --- | --- | --- |"]
    for aid, (title, what, _cond) in game.ACHIEVEMENTS.items():
        lines.append("| `%s` | %s | %s |" % (aid, title, what))
    lines += ["", "## Characters who go on", "", "| Character | In Cargo 3 |", "| --- | --- |"]
    for cid, char in saga.get("characters", {}).items():
        later = [t.get("as", "") for t in char.get("timeline", []) if t.get("game") == "cargo3"]
        if later:
            lines.append("| %s | %s |" % (char.get("name", cid), "; ".join(later).replace("|", "/")))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    text = build()
    if "--check" in sys.argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != text:
            print("story/CARGO2-HANDOFF.md is out of date: run python3 tools/handoff.py")
            sys.exit(1)
        print("hand-off up to date")
    else:
        open(OUT, "w", encoding="utf-8").write(text)
        print("wrote", OUT)
