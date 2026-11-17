# core/game_state.py
class GameState:
    def __init__(self):
        self.active_beacon = None
        self.active_beacon_encounter = None
        self.current_location = None
        self.is_game_over = False
        # Add other state properties here