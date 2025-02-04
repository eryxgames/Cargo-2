# core/new_combat_system.py
import random
import math
import yaml
from core.combat_system import CombatSystem, CombatResult
from core.utils import format_money


class NewCombatSystem(CombatSystem):
    def __init__(self, game):
        super().__init__(game)
        self.enemy_data = self.load_enemy_data()

    def load_enemy_data(self):
        """Load enemy data from data/enemies.yml"""
        try:
            with open("data/enemies.yml", 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print("Error: enemies.yml not found. Using default enemy data.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error loading enemies from YAML: {e}")
            return {}

    def resolve_combat(self, attacker, defender, combat_data=None):
        """Resolves a combat encounter using the new system."""

        enemy_id = combat_data.get("enemy_id")
        enemy = self.enemy_data.get(enemy_id)

        if not enemy:
            print(f"Error: Enemy data not found for {enemy_id}")
            return CombatResult("defeat", "Unknown enemy encountered.")

        enemy_type = enemy.get("type", "pirate")

        # Check for automatic defense
        if "turrets" in attacker.items and random.random() < 0.4:
            self.game.ui.display_simple_message(f"Event! {enemy.get('name', 'Unknown')} repelled by defense systems!", 3, color='32')
            attacker.record_combat_victory(enemy_type)  # Update combat statistics
            if enemy_type == "pirate":
                rep_gain = random.randint(1, 3)
                self.game.reputation += rep_gain
                attacker.passenger_reputation += rep_gain
                self.game.ui.display_simple_message(f"Gained {rep_gain} reputation for automated pirate defense!")
            attacker.research_points += int(5 * enemy.get("reward_mult", 1))
            return CombatResult("victory", message="Encounter repelled by defense systems")

        # Calculate damage
        damage = self.calculate_damage(attacker, enemy)

        # Apply status effects (if any)
        self.apply_status_effects(attacker, enemy, combat_data)

        # Apply shield mechanics
        shield_capacity = attacker.defense * 15
        damage_reduction = min(shield_capacity, damage * 0.3)
        damage -= damage_reduction

        # Ensure damage doesn't exceed 99%
        final_damage = min(99, int(attacker.damage + damage))
        damage_dealt = final_damage - attacker.damage
        attacker.damage = final_damage

        # Handle cargo/money loss
        losses = []
        if attacker.money > 0:
            stolen = random.randint(1, max(1, int(attacker.money // 2)))
            attacker.money -= stolen
            losses.append(f"{self.game.format_money(stolen)} credits")

        for cargo_type in ['tech', 'agri', 'salt', 'fuel']:
            if attacker.cargo[cargo_type] > 0:
                stolen_cargo = random.randint(1, max(1, int(attacker.cargo[cargo_type] // 3)))
                attacker.cargo[cargo_type] -= stolen_cargo
                if stolen_cargo > 0:
                    losses.append(f"{stolen_cargo} {cargo_type}")

        # Check for critical hits
        crit_chance = self.calculate_crit_chance(attacker, enemy)
        is_critical = random.random() < crit_chance
        if is_critical:
            damage *= (1.5 + (attacker.attack * 0.1))
            self.game.ui.display_simple_message("Critical Hit!", 2, color='33')

        # Check evasion
        evasion_chance = self.calculate_evasion_chance(attacker, enemy)
        is_evaded = random.random() < evasion_chance
        if is_evaded:
            self.game.ui.display_simple_message("Attack Evaded!", 2, color='32')
            return CombatResult("evade", message="Attack evaded.")

        if attacker.attack > enemy.get("defense", 1):  # check basic stats for win
            # Counter-attack successful - record victory
            attacker.record_combat_victory(enemy_type)

            reward_mult = enemy.get("reward_mult", 1)
            rewards = {
                "money": int(random.randint(100, 500) * reward_mult),
                "research": int(random.randint(10, 25) * reward_mult)
            }

            attacker.money += rewards["money"]
            attacker.research_points += rewards["research"]

            # Add reputation gains for pirate victories
            if enemy_type == "pirate":
                rep_gain = random.randint(2, 5)
                self.game.reputation += rep_gain
                attacker.passenger_reputation += rep_gain
                rep_message = f"\nReputation increased by {rep_gain} reputation for defeating pirates!"
            else:
                rep_message = ""

            if losses:
                loss_text = ", ".join(losses)
                message = f"Event! {enemy.get('message', 'Unknown enemy')} caused {damage_dealt}% damage and stole {loss_text}!\n" + \
                          f"Counter-attack successful! Gained {self.game.format_money(rewards['money'])} credits and {rewards['research']} research points!" + \
                          rep_message
            else:
                message = f"Event! {enemy.get('message', 'Unknown enemy')} caused {damage_dealt}% damage!\n" + \
                          f"Counter-attack successful! Gained {self.game.format_money(rewards['money'])} credits and {rewards['research']} research points!" + \
                          rep_message

            return CombatResult("victory", message=message, rewards=rewards)
        else:
            # Combat defeat - record defeat with enemy type
            attacker.record_combat_defeat(enemy_type)

            # Lose reputation on pirate defeats
            if enemy_type == "pirate":
                rep_loss = random.randint(1, 3)
                self.game.reputation = max(0, self.game.reputation - rep_loss)
                attacker.passenger_reputation = max(0, attacker.passenger_reputation - rep_loss)
                rep_message = f"\nLost {rep_loss} reputation from pirate defeat!"
            else:
                rep_message = ""

            if losses:
                loss_text = ", ".join(losses)
                message = f"Event! {enemy.get('message', 'Unknown enemy')} caused {damage_dealt}% damage and stole {loss_text}!" + rep_message
            else:
                message = f"Event! {enemy.get('message', 'Unknown enemy')} caused {damage_dealt}% damage!" + rep_message

            return CombatResult("defeat", message=message)

    def calculate_damage(self, attacker, enemy):
        """Calculates damage using the new formula."""
        atk = attacker.attack
        def_ = enemy.get("defense", 1)
        base_impact = (atk * 2) - def_
        scaled_damage = (math.log(max(base_impact, 1), 3) * 15) + base_impact
        damage = scaled_damage * random.uniform(0.85, 1.15)
        return damage
    
    def apply_status_effects(self, attacker, defender, combat_data=None):
        """
        Apply different status effects on attacker or defender.
        """
        # TODO later.
        pass

    def calculate_crit_chance(self, attacker, defender):
        """Calculates critical hit chance."""
        stat_difference = attacker.attack - defender.get("defense", 1)
        crit_bonus = max(0, stat_difference * 0.03)
        final_crit_chance = min(0.05 + crit_bonus, 0.25)  # Base 5%, max 25%
        return final_crit_chance

    def calculate_evasion_chance(self, attacker, defender):
        """Calculates evasion chance."""
        speed_difference = max(0, attacker.speed - defender.get("speed", 1))
        bonus_evasion = speed_difference * 0.03
        final_evasion = min((attacker.speed * 0.02) + bonus_evasion, 0.35)  # Base speed * 2%, max 35%
        return final_evasion

    def handle_boss_battle(self, boss_id):
        """Handle special boss battle encounter"""
        enemy = self.enemy_data.get(boss_id)

        # Set special properties for boss fight
        if not enemy:
            return CombatResult("defeat", "Boss not defined correctly.")

        boss_type = enemy.get("type", "boss")

        # Display special message for this boss battle
        self.game.ui.display_simple_message([
            "WARNING! Encountering a significant enemy presence:",
            f"Battle against: {enemy.get('name', 'Unknown')}"
        ], 3, color='31')

        # Use core resolve_combat and add special rewards
        combat_data = {"enemy_id": boss_id}
        combat_result = self.resolve_combat(self.game.ship, enemy, combat_data)
        if combat_result.is_victory():
            rewards = combat_result.get_rewards()
            if rewards:
                rewards['money'] = int(rewards['money'] * 3)  # triple
                rewards['research'] = int(rewards['research'] * 2)  # double

            # Give special message for boss victory
            self.game.ui.display_simple_message([
                "Victory! Defeated the Boss: " + enemy.get("name"),
                f"Credits: {self.game.format_money(rewards['money'])}",
                f"Research Points: {rewards['research']}"
            ], 3, color='32')
            return CombatResult("victory", combat_result.get_message(), rewards=rewards)
        elif combat_result.is_defeat():
            self.game.ui.display_simple_message("Defeated by the boss: " + enemy.get("name"), 3, color='31')
            return CombatResult("defeat", combat_result.get_message())
        return combat_result

    def get_combat_message(self, message_id, data=None):
         """
         Return message for combat
         """
         return "generic_message"

# Remove any code that is not part of combat system, for example messages etc.
# messages should come from game ui