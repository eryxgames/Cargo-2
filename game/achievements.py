"""Achievements: things a captain did that the trilogy remembers.

Each is a storykit condition (the same words the story's scenes use), checked once a turn. An
achievement is announced when it is earned, listed in the journal, and written into the captain's
record ("achievements": [ids]), so Cargo 3 can read it. Cargo 1 drops the key when it reads a
Cargo 2 record, as it drops anything it does not know.
"""

ACHIEVEMENTS = {   # id: (title, what it took, condition)
    "no_more_deadheads": ("No more deadheads", "twenty-five trades", {"trades_completed": 25}),
    "milk_run": ("Milk run", "a hundred trades", {"trades_completed": 100}),
    "steel_rain": ("Steel rain", "twenty-five fights won", {"combat_victories": 25}),
    "far_and_wide": ("Far and wide", "fifteen places visited", {"discovered": 15}),
    "bondholder": ("Bondholder", "five Hansa bonds", {"hansa_bonds": 5}),
    "full_train": ("Full train", "every grip of a Farstrider filled", {"hull_class": 2, "modules_fitted": 7}),
    "shiny_side_up": ("Shiny-side up", "a million credits", {"money": 1000000}),
    "hansa_own": ("One of the Hansa's own", "the Hansa's standing at 60", {"standing.hansa": 60}),
    "mandate_own": ("One of the Mandate's own", "the Mandate's standing at 60", {"standing.mandate": 60}),
    "concord_own": ("One of the Concord's own", "the Concord's standing at 60", {"standing.concord": 60}),
    "keeps_things": ("A captain who keeps things", "the Binary Dawn's trust at 40", {"dawn_trust": 40}),
    "lot_1187": ("Lot 1187", "the heading file opened", {"done": ["heading.opened"]}),
    "eleven_years": ("Eleven years early", "a needle seen thrown into the past", {"done": ["ring.lost"]}),
    "the_pellet": ("The pellet", "a drink paid for forty years ago", {"flag": "paid_with_the_pellet"}),
}


class AchievementsMixin:
    """The Game's achievements. Game inherits it (game/world.py)."""

    def check_achievements(self):
        """Once a turn: announce what has been earned since the last look."""
        earned = self.__dict__.setdefault("achievements", {})
        snap = self.story.snapshot()
        for aid, (title, what, cond) in ACHIEVEMENTS.items():
            if aid not in earned and self.story.check(cond, snap):
                earned[aid] = self.turn
                self.display_simple_message("Achievement: %s (%s)." % (title, what), 2, color='32')

    def achievement_rows(self):
        earned = getattr(self, "achievements", {})
        return [["  %s: %s" % (ACHIEVEMENTS[a][0], ACHIEVEMENTS[a][1])] for a in ACHIEVEMENTS if a in earned]
