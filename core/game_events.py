# core/game_events.py
import random
from core.utils import format_money
#from core.combat import Combat, CombatResult
from core.template import CharacterTemplate


class GameEvents:
    def __init__(self, game):
        self.game = game
        self.event_data = self.load_event_data()
        #self.combat = Combat(game)
        self.templates = CharacterTemplate.load_character_templates("data/characters.yml")
        self.event_cooldowns = {}  # Track cooldowns per event id

    def load_event_data(self):
        """Load event data from data/events.yml"""
        try:
            with open("data/events.yml", 'r') as f:
                import yaml
                return yaml.safe_load(f)
        except FileNotFoundError:
            print("Error: events.yml not found. Using default event data.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error loading events from YAML: {e}")
            return {}

    def check_event_conditions(self, event):
            """Check if an event's conditions are met"""
            conditions = event.get("conditions", {})

            if "location_type" in conditions:
                location_types = conditions["location_type"]
                print(f"Location_types: {location_types} and location_type: {self.game.current_location.location_type}")#DEBUG here!
                if isinstance(location_types, list):
                    if self.game.current_location.location_type not in location_types:
                        return False
                elif self.game.current_location.location_type != location_types:
                    return False
            if "min_turn" in conditions and self.game.turn < conditions["min_turn"]:
                print(f"Min_turn: {conditions['min_turn']} and turn: {self.game.turn}")#DEBUG here!
                return False
            if "max_turn" in conditions and self.game.turn > conditions["max_turn"]:
                print(f"Max_turn: {conditions['max_turn']} and turn: {self.game.turn}")#DEBUG here!
                return False
            if "min_reputation" in conditions and self.game.ship.passenger_reputation < conditions["min_reputation"]:
                print(f"min_reputation: {conditions['min_reputation']} and reputation: {self.game.ship.passenger_reputation}")#DEBUG here!
                return False
            if "max_reputation" in conditions and self.game.ship.passenger_reputation > conditions["max_reputation"]:
                print(f"max_reputation: {conditions['max_reputation']} and reputation: {self.game.ship.passenger_reputation}")#DEBUG here!
                return False
            if "min_combat_victories" in conditions and self.game.ship.combat_victories['total'] < conditions["min_combat_victories"]:
                print(f"min_combat_victories: {conditions['min_combat_victories']} and combat victories: {self.game.ship.combat_victories['total']}")#DEBUG here!
                return False
            if "min_trades_completed" in conditions and self.game.trades_completed < conditions["min_trades_completed"]:
                print(f"min_trades_completed: {conditions['min_trades_completed']} and trades completed: {self.game.trades_completed}")#DEBUG here!
                return False
            if "max_trades_completed" in conditions and self.game.trades_completed > conditions["max_trades_completed"]:
                print(f"max_trades_completed: {conditions['max_trades_completed']} and trades completed: {self.game.trades_completed}")#DEBUG here!
                return False
            if "min_plot_points" in conditions and self.game.story_manager.plot_points < conditions["min_plot_points"]:
                print(f"min_plot_points: {conditions['min_plot_points']} and plot points: {self.game.story_manager.plot_points}")#DEBUG here!
                return False
            if "max_plot_points" in conditions and self.game.story_manager.plot_points > conditions["max_plot_points"]:
                print(f"max_plot_points: {conditions['max_plot_points']} and plot points: {self.game.story_manager.plot_points}")#DEBUG here!
                return False
            if "min_ship_speed" in conditions and self.game.ship.speed < conditions["min_ship_speed"]:
                print(f"min_ship_speed: {conditions['min_ship_speed']} and ship speed: {self.game.ship.speed}")#DEBUG here!
                return False
            if "min_trade_profit" in conditions:
                total_profit = sum(self.game.ship.trade_profits.values())
                if total_profit < conditions["min_trade_profit"]:
                    print(f"min_trade_profit: {conditions['min_trade_profit']} and trade profit: {total_profit}")#DEBUG here!
                    return False
            if "min_cargo_amount" in conditions:
                if not hasattr(self.game.ship, 'cargo'):
                    return False
                for cargo, amount in conditions["min_cargo_amount"].items():
                    if self.game.ship.cargo.get(cargo, 0) < amount:
                        print(f"min_cargo_amount: {amount} and cargo: {self.game.ship.cargo.get(cargo, 0)}")#DEBUG here!
                        return False
            if "min_passengers_transported" in conditions:
                if self.game.reputation_manager.total_passengers < conditions["min_passengers_transported"]:
                    print(f"min_passengers_transported: {conditions['min_passengers_transported']} and passengers transported: {self.game.reputation_manager.total_passengers}")#DEBUG here!
                    return False
            if "items_required" in conditions:
                for required_item in conditions["items_required"]:
                    if required_item not in self.game.ship.items:
                        print(f"Missing required item: {required_item}")
                        return False
            return True

    def get_weighted_event(self, is_beacon=False):
            """Selects a weighted random event"""
            eligible_events = []
            print ("Starting get_weighted_event")#debug
            for event_id, event_data in self.event_data.items():
                print (f"Checking event {event_id}")#debug
                #Skip check beacon events
                if is_beacon:
                    print ("Skipped " + event_id + " because is beacon call")
                if (self.check_event_conditions(event_data) and 
                    self.check_event_cooldown(event_id) and
                    not is_beacon #Skip the check, for manual calls.
                    ):
                    eligible_events.append((event_id, event_data.get("weight", 1)))
                    print (f"Event {event_id} is eligible")#debug
                else:
                    print (f"Event {event_id} is not eligible")#debug
            if not eligible_events:
                print ("No eligible events at all!")#debug
                return None
            else:
                print ("Eligible events:" + str(eligible_events))#add
            
            # Accumulate weights
            weighted_events = []
            total_weight = 0
            for event_id, weight in eligible_events:
                total_weight += weight
                weighted_events.append((event_id, total_weight))
            
            # Select a weighted random event
            random_value = random.uniform(0, total_weight)
            for event_id, weight in weighted_events:
                if random_value <= weight:
                    print (f"Returning event: {event_id}")#debug
                    return event_id
            return None  # Shouldn't happen

    def check_event_cooldown(self, event_id):
        """Check if an event is on cooldown"""
        if event_id in self.event_cooldowns:
            if self.game.turn - self.event_cooldowns[event_id] < self.event_data[event_id].get("cooldown", 0):
                return False
        return True

    def trigger_event(self, event_id, is_beacon=False):
        """Trigger specific event with its consequences"""
        if not event_id:
            return False
        
        return self.handle_event(event_id, is_beacon=is_beacon)

    def trigger_beacon_event(self, event_id):
        """Trigger beacon-specific event without conditions check"""
        
        if not event_id:
          print(f"Error: No event ID is present!")
          return False
        
        success = self.handle_event(event_id, is_beacon=True)
        return success

    def apply_plot_points(self, event_data):
        """Apply plot points based on the event"""
        plot_points = event_data.get("plot_points")

        if plot_points is None:
            return False

        if isinstance(plot_points, int):
            self.game.story_manager.plot_points += plot_points
        elif isinstance(plot_points, dict):
            base_points = plot_points.get("base", 0)
            multiplier = plot_points.get("multiplier", 1)
            self.game.story_manager.plot_points += int(base_points * multiplier)

    def random_event(self):
            """Handles random game events"""
            print(f"Running random event, probability {self.game.event_probability}")#debug
            if random.random() < self.game.event_probability:
                print("Event roll succeeded")#debug
                # Select a weighted random event
                event_id = self.get_weighted_event()
                if not event_id:
                    print("No eligible events")#debug
                    return  # if not event, do not run anything further
                
                print (f"We are now on {event_id}")#debug
                self.handle_event(event_id) #here!
                print(f"Triggered event based on random chance {self.game.event_probability} from pool of {len([ev for ev, data in self.event_data.items() if self.check_event_conditions(data) and not data.get('beacon_type') ])} events")

    def handle_combat_event(self, event_id, is_beacon=False):
        """Handle combat event using CombatSystem class"""
        event = self.event_data.get(event_id)
        if not event:
            print(f"Error: No event data found for event ID: {event_id}!")
            return False

        if not is_beacon:
            if not self.check_event_conditions(event):
                print(f"Error: Event conditions not met for event {event_id}!")
                return False

        enemy_pool = event.get("enemy_pool", ["pirate_scout"])
        enemy_id = random.choice(enemy_pool)

        if not enemy_id:
            print(f"Error: No enemy_id defined for event {event_id} inside enemy_pool")
            return False

        # Use combat system for resolve_combat
        combat_data = {"enemy_id": enemy_id}
        result = self.game.combat_system.resolve_combat(self.game.ship, self.game.ship, combat_data)

        # Process outcome of combat
        if result.is_victory():
            self.game.ui.display_simple_message(self.get_event_message(event, "successful_defense"), 3, color='32')
            if result.get_rewards():
                rewards = result.get_rewards()
                self.game.handle_research_gain(rewards.get("research", 0))
        elif result.is_defeat():
            self.game.ui.display_simple_message(self.get_event_message(event, "damage_taken"), 3, color='31')

        # Apply plot point logic
        self.apply_plot_points(event)

        # Check for story events
        self.game.story_manager.check_event_trigger(event_id, self.game)
        return True
    
    def get_event_message(self, event, message_type):
        """Get message for event based on type"""
        if event and "messages" in event:
            if message_type in event["messages"]:
                return event["messages"][message_type]
            else:
                return event["messages"].get("default")
        return event.get("message")  # Fallback to old message if not defined in new

    def handle_beacon_encounter(self, beacon_type):
        """Handle a beacon-triggered combat event"""
        if beacon_type == "distress_a":
            return "distress_beacon_a_event"  # Set the event id
        elif beacon_type == "distress_b":
            return "distress_beacon_b_event"
        elif beacon_type == "distress_c":
            return "distress_beacon_c_event"
        elif beacon_type == "nav_a":
            return "nav_beacon_a_event"
        elif beacon_type == "mcguffin":
            return "mcguffin_beacon_event"
        else:
            self.game.ui.display_simple_message(f"Unknown beacon type: {beacon_type}", 3, color='31')
            return None

    def trigger_boss_battle(self):
        """Trigger boss battle using CharacterTemplate with ship, instead of defined stats"""
        boss_id = 'grand_commander_voxx'  # using a template id, for test, later we can randomize
        boss_template = self.templates.get(boss_id)
        if not boss_template:
            print(f"Warning: Boss {boss_id} not defined. Using default boss data.")
            return False

        # Get ship stats from character data, and if it has not, just a default stats
        ship_stats = boss_template.content.get('ship',
            {'attack': 3, 'defense': 3, 'speed': 2}
        )

        # Create a temporary enemy object using the boss template data
        # so we can pass it to the combat system
        class BossEnemy:
            def __init__(self, data):
                self.attack = data.get('attack', 1)
                self.defense = data.get('defense', 1)
                self.speed = data.get('speed', 1)
                # Add any other relevant stats from the template
                self.get = lambda key, default=None: data.get(key, default)  #mock get

        boss = BossEnemy(ship_stats) #now we generate boss on the fly
        # Start combat using Combat class and pass boss stats directly
        combat_data = {"enemy_id": boss_id}  # Provide boss_id as combat data
        result = self.game.combat_system.resolve_combat(self.game.ship, boss, combat_data)

        if result.is_victory():
            self.game.ui.display_simple_message(result.get_message(), 3, color='32')
            if result.get_rewards():
                rewards = result.get_rewards()
                self.game.handle_research_gain(rewards.get("research", 0))
        elif result.is_defeat():
            self.game.ui.display_simple_message(result.get_message(), 3, color='31')
        # Check for unlock based on victory
        return result.is_victory()

    def handle_exploration_event(self, event_name):
        """Handle exploration events with full outcome processing"""
        event = self.event_data.get(event_name.lower().replace(" ", "_"))
        if not self.check_event_conditions(event):
            return False

        success_chance = event.get("success_chance", 0.7)

        # Modify success chance based on equipment
        if "scanner" in self.game.ship.items:
            success_chance += 0.1
        if "probe" in self.game.ship.items:
            success_chance += 0.1

        # Location type modifiers
        location_modifiers = {
            "Planet": 0,
            "AsteroidBase": 0.05,
            "DeepSpaceOutpost": 0.1,
            "ResearchColony": 0.15
        }
        success_chance += location_modifiers.get(self.game.current_location.location_type, 0)

        if random.random() < success_chance:
            # Determine discovery type and rewards
            discovery_types = event.get("reward_type",
                "valuable minerals,ancient artifacts,scientific data,advanced technology"
            ).split(',')

            discovery = random.choice(discovery_types)

            # Calculate rewards with location and rank bonuses
            rank_multiplier = {
                "Explorer": 1.0,
                "Pilot": 1.2,
                "Captain": 1.5,
                "Commander": 1.8,
                "Star Commander": 2.2,
                "Space Admiral": 2.5,
                "Stellar Hero": 3.0,
                "Galactic Legend": 3.5
            }.get(self.game.rank, 1.0)

            location_bonus = 1.0
            if self.game.current_location.location_type == "ResearchColony":
                location_bonus = 1.5

            # Apply rewards
            money_reward = random.randint(1000, 3000)
            money_reward = int(money_reward * rank_multiplier * location_bonus)
            self.game.ship.money += money_reward

            rp_reward = random.randint(10, 30)
            rp_reward = int(rp_reward * rank_multiplier * location_bonus)
            self.game.ship.research_points += rp_reward

            # Special discovery effects
            if discovery == "ancient artifacts":
                self.game.story_manager.plot_points += 2
                if random.random() < 0.3:  # 30% chance
                    self.game.quest_system.generate_quest("exploration", 1.5)

            elif discovery == "advanced technology":
                if random.random() < 0.4:  # 40% chance
                    tech_bonus = random.choice(["attack", "defense", "speed"])
                    self.game.ship.upgrade_property(tech_bonus, 1)
                    self.game.ui.display_simple_message(f"The technology improved your ship's {tech_bonus}!")

            self.game.ui.display_simple_message([
                f"Exploration Success! Found {discovery}!",
                f"Earned {self.game.format_money(money_reward)} credits",
                f"Gained {rp_reward} research points"
            ], color='32')

        else:
            # Handle exploration failure
            damage = random.randint(5, 15)
            self.game.ship.damage = min(99, self.game.ship.damage + damage)

            self.game.ui.display_simple_message([
                "Exploration failed!",
                f"Ship took {damage}% damage from hazardous conditions."
            ], color='31')
            return True

    def handle_trade_event(self, event_name):
        """Handle trade disruption events with full market impact"""
        event = self.event_data.get(event_name.lower().replace(" ", "_"))
        if not self.check_event_conditions(event):
            return False

        # Use event data directly
        price_impact = event.get("price_impact")
        duration = event.get("duration")
        severity = event.get("severity", "minor")

        # Select affected commodities
        commodities = ["tech", "agri", "salt", "fuel"]
        num_affected = random.randint(1, len(commodities))
        affected_commodities = random.sample(commodities, num_affected)

        # Apply market effects
        for commodity in affected_commodities:
            impact = random.uniform(*price_impact)
            current_price = self.game.current_location.market[commodity]

            # Calculate new price
            new_price = current_price * (1 + impact)

            # Apply commodity-specific limits
            if commodity == "salt":
                new_price = max(60, min(150, new_price))
            elif commodity == "fuel":
                new_price = max(120, min(250, new_price))
            else:
                new_price = max(1, min(200, new_price))

            self.game.current_location.market[commodity] = new_price

            # Add temporary trade ban if price would be too low
            if new_price < 10:
                duration = random.randint(*duration)
                self.current_location.add_temporary_ban(commodity, duration)

        # Generate message based on severity
        messages = {
            "major": f"Major market disruption! {event['message']}",
            "moderate": f"Market instability detected. {event['message']}",
            "minor": f"Minor market fluctuation. {event['message']}"
        }

        # Handle custom message for the event.
        message_type = "default"
        if any(self.game.current_location.market[commodity] < 10 for commodity in affected_commodities):
            message_type = "affected_commodities"

        self.game.ui.display_simple_message([
            self.get_event_message(event, message_type).format(commodities=", ".join(affected_commodities)),
            "Check market prices for details."
            ])

        # Possible quest generation
        if severity == "major" and random.random() < 0.3:
            self.game.quest_system.generate_quest("trade", 1.5)
        return True

    def handle_disaster_event(self, event_name):
        """Complete disaster event handler"""
        event = self.event_data.get(event_name.lower().replace(" ", "_"), self.event_data["equipment_malfunction"])
        if not self.check_event_conditions(event):
            return False

        # Calculate base damage
        min_damage, max_damage = event.get("base_damage", (10, 20))
        damage = random.randint(min_damage, max_damage)

        # Apply shield protection if available
        if "shield" in self.game.ship.items and event.get("shield_protection", 0) > 0:
            if random.random() < event.get("shield_protection", 0):
                damage = int(damage * 0.4)  # 60% reduction when shields work
                self.game.ui.display_simple_message("Shields partially mitigated the disaster!", 2, color='32')

        # Apply final damage
        self.game.ship.damage = min(99, self.game.ship.damage + damage)

        # Handle cargo loss if applicable
        if event.get("cargo_loss", False):
            cargo_lost = False
            for cargo_type in ['tech', 'agri', 'salt', 'fuel']:
                if self.game.ship.cargo[cargo_type] > 0:
                    lost = random.randint(1, max(1, int(self.game.ship.cargo[cargo_type] // 2)))
                    self.game.ship.cargo[cargo_type] = max(0, self.game.ship.cargo[cargo_type] - lost)
                    if lost > 0:
                        cargo_lost = True
                        self.game.ui.display_simple_message(
                            f"Lost {self.game.format_money(lost)} units of {cargo_type}!",
                            2, color='31'
                        )

        # Handle equipment failure
        if event.get("equipment_failure", False):
            if self.game.ship.items and random.random() < 0.3:
                item = random.choice(list(self.game.ship.items.keys()))
                self.game.ship.items[item] -= 1
                if self.game.ship.items[item] <= 0:
                    del self.game.ship.items[item]
                self.game.ui.display_simple_message(f"Equipment failure! Lost {item}!", 2, color='31')

        # Display final disaster results
        self.game.ui.display_simple_message(
            f"Event! {event['message']} caused {damage}% damage to the ship!",
            3, color='31'
        )

        # Check for repair opportunity
        if "repair_bot" in self.game.ship.items and random.random() < 0.4:
            repair = random.randint(5, 15)
            self.game.ship.damage = max(0, self.game.ship.damage - repair)
            self.game.ui.display_simple_message(
                f"Repair bot automatically fixed {repair}% damage!",
                2, color='32'
            )
        return True
    
    def handle_event(self, event_id, is_beacon=False):
            """Central event dispatcher"""
            event_data = self.event_data.get(event_id)
            if not event_data:
                print(f"Error: No event data found for event ID: {event_id}!")
                return False

            event_type = event_data.get("type")
            
            # Set cooldown for event that was just triggered
            self.event_cooldowns[event_id] = self.game.turn

            match event_type:
                case "combat":
                    success = self.handle_combat_event(event_id, is_beacon) #added here, and fixed
                    if success:
                    # Apply plot point logic
                        self.apply_plot_points(event_data)
                        return True
                    else:
                        return False
                case "trade":
                    self.handle_trade_event(event_id)
                case "exploration":
                    self.handle_exploration_event(event_id)
                case "disaster":
                    self.handle_disaster_event(event_id)
                case "passenger":
                    self.handle_passenger_event(event_id)
                case _:
                    print(f"Warning: Unknown event type {event_type}")
                    return False

            # Apply plot point logic
            self.apply_plot_points(event_data)

            # Check for story events
            self.game.story_manager.check_event_trigger(event_id, self.game)
            return True   