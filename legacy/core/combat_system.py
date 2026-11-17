# core/combat_system.py
from abc import ABC, abstractmethod

class CombatResult:
    def __init__(self, result_type, message="", rewards=None):
        self.result_type = result_type
        self.message = message
        self.rewards = rewards or {}

    def is_victory(self):
        return self.result_type == "victory"
    
    def is_defeat(self):
        return self.result_type == "defeat"
    
    def is_escape(self):
        return self.result_type == "escape"
    
    def get_message(self):
        return self.message
    
    def get_rewards(self):
         return self.rewards

class CombatSystem(ABC):
    """
    Abstract base class for combat systems.
    """

    def __init__(self, game):
        """
        Initializes the combat system with a reference to the game object.
        """
        self.game = game

    @abstractmethod
    def resolve_combat(self, attacker, defender, combat_data=None):
        """
        Resolves a combat encounter between an attacker and a defender.

        Args:
            attacker: The attacking entity (e.g., ship, character).
            defender: The defending entity (e.g., ship, character).
            combat_data: (Optional) Additional data relevant to the combat encounter
                         (e.g., enemy ID, location, special conditions).

        Returns:
            A CombatResult object representing the outcome of the combat.
        """
        pass

    @abstractmethod
    def calculate_damage(self, attacker, defender, combat_data=None):
         """
         Calculates damage dealt by attacker, based on different combat conditions.
         """
         pass

    @abstractmethod
    def apply_status_effects(self, attacker, defender, combat_data=None):
         """
         Apply different status effects on attacker or defender.
         """
         pass

    def get_combat_message(self, message_id, data=None):
         """
         Return message for combat
         """
         pass