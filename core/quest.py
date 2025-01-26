# core/quest.py
import random

class Quest:
    def __init__(self, name, description, reward_money, reward_rp, quest_type="generic", 
                 requirements=None, on_complete=None, milestone=None, destination=None, rewards=None):
        self.name = name
        self.description = description
        self.destination = destination
        self.reward_money = reward_money
        self.reward_rp = reward_rp  # Research Points reward
        self.quest_type = quest_type
        self.requirements = requirements or {}
        self.on_complete = on_complete
        self.milestone = milestone
        self.progress = 0
        self.completed = False
        self.target_progress = self.requirements.get('target_progress', 1)
        self.location_requirement = self.requirements.get('location_type', None)
        # Add additional rewards handling
        self.rewards = rewards or {}  # Store extra rewards like items

    def __eq__(self, other):
        """Define equality to help prevent duplicates"""
        if not isinstance(other, Quest):
            return False
        return (self.name == other.name and 
                self.quest_type == other.quest_type)

    # Cantina quests from listen to gossip, added to Quest class
    def update_cantina_progress(self, event_data):
        """Update cantina quests based on trade actions"""
        if self.quest_type == "cantina":
            action = event_data.get("action", "")
            
            if action in ["buy", "sell"]:
                commodity = event_data.get("commodity")
                amount = event_data.get("amount", 0)
                
                if "Deliver" in self.name and commodity:
                    target_commodity = self.name.split()[2].lower()
                    if commodity == target_commodity:
                        self.progress += amount
                        return self.progress >= self.requirements.get("amount", 0)
                    
            elif action == "passenger_delivered":
                self.progress += 1
                return self.progress >= self.requirements.get("count", 0)
            
        return False

    def update_research_progress(self, activity_type):
        """Update progress for research activities"""
        if not hasattr(self, 'tracked_progress'):
            self.tracked_progress = {}
        
        if activity_type in self.tracked_progress:
            self.tracked_progress[activity_type] += 1
            return self.check_research_completion(self.game)
        return False

    def check_completion(self, game):
        """Check if quest requirements are met"""
        if self.completed:
            return False

        # Map quest types to their completion check methods
        completion_checks = {
            "mining": self.check_mining_completion,
            "combat": self.check_combat_completion,
            "trade": self.check_trade_completion,
            "exploration": self.check_exploration_completion,
            "research": self.check_research_completion,
            "cantina": self.check_cantina_completion,
            "item_delivery": self.check_item_delivery_completion,
            "character_delivery": self.check_character_delivery_completion,
            "delivery": self.check_delivery_completion
        }

        check_method = completion_checks.get(self.quest_type)
        if check_method:
            return check_method(game)
        
        # Generic quest completion check
        return self.progress >= self.target_progress

    def check_mining_completion(self, game):
        """Check mining quest requirements"""
        if 'resource_type' in self.requirements:
            resource = self.requirements['resource_type']
            target_amount = self.requirements.get('amount', 0)
            return game.ship.cargo[resource] >= target_amount
        return False

    def check_trade_completion(self, game):
        """Check trading quest requirements"""
        if 'commodity' in self.requirements:
            target_profit = self.requirements.get('profit', 0)
            return game.ship.trade_profits.get(
                self.requirements['commodity'], 0) >= target_profit
        return False

    def check_delivery_completion(self, game):
        """Check cargo delivery quest requirements"""
        return (game.current_location.name == self.destination and
                game.ship.cargo[self.requirements['commodity']] >= self.requirements['amount'])

    def check_item_delivery_completion(self, game):
        """Check item delivery quest requirements"""
        return (game.current_location.name == self.destination and
                self.requirements["item"] in game.ship.items)

    def check_character_delivery_completion(self, game):
        """Check character delivery quest requirements"""
        if hasattr(game.ship, 'passenger_modules'):
            for module in game.ship.passenger_modules:
                for passenger in module.passengers:
                    if (passenger.name == self.requirements["character"] and
                        game.current_location.name == self.destination):
                        return True
        return False

    def check_research_completion(self, game):
        """Check research quest requirements"""
        if not hasattr(self, 'tracked_progress'):
            self.tracked_progress = {
                'research_points_gained': 0,
                'analysis_completed': 0,
                'experiments_conducted': 0
            }
        
        # Check if required criteria are met
        criteria = self.requirements.get('completion_criteria', {})
        for key, target in criteria.items():
            # Use game parameter to track research progress if needed
            current_value = self.tracked_progress.get(key, 0)
            
            # If the key is research-related, you might want to pull from game state
            if key == 'research_points_gained':
                current_value = game.ship.research_points
            
            if current_value < target:
                return False
        return True
    
    def check_combat_completion(self, game):
        """Check combat quest requirements"""
        if 'enemy_type' in self.requirements:
            enemy_type = self.requirements['enemy_type']
            required_amount = self.requirements.get('amount', 1)
            return game.ship.combat_victories.get(enemy_type, 0) >= required_amount
        # If no specific enemy type, check total victories
        return game.ship.combat_victories['total'] >= self.requirements.get('amount', 1)

    def check_exploration_completion(self, game):
        """Check exploration quest requirements"""
        if 'location_type' in self.requirements:
            discovered = len([loc for loc in game.discovered_locations 
                            if isinstance(loc, self.requirements['location_type'])])
            return discovered >= self.requirements.get('amount', 1)
        
        if 'specific_location' in self.requirements:
            return self.requirements['specific_location'] in game.discovered_locations

        # For generic exploration goals
        return self.progress >= self.target_progress

    def check_cantina_completion(self, game):
        """Check if cantina quest requirements are met"""
        if "Deliver" in self.name:
            # Check trade profits
            commodity = self.name.split()[2].lower()
            return game.ship.trade_profits.get(commodity, 0) >= self.requirements.get('amount', 0)
        
        elif "Transport" in self.name:
            # Check passenger transport
            return game.reputation_manager.total_passengers >= self.requirements.get('count', 0)
        
        elif "Eliminate" in self.name:
            # Check combat victories
            enemy_type = self.name.split()[2].lower()
            return game.ship.combat_victories.get(enemy_type, 0) >= self.requirements.get('victories', 0)

        return False

    def update_progress(self, event_data):
        """Update quest progress based on game events"""
        if self.completed:
            return False

        progress_made = False
        
        # Update based on event type
        if event_data.get("type") == "combat" and self.quest_type == "combat":
            if event_data.get("outcome") == "victory":
                self.progress += 1
                progress_made = True
                
        elif event_data.get("action") in ["buy", "sell"] and self.quest_type == "trade":
            commodity = event_data.get("commodity")
            if commodity == self.requirements.get("commodity"):
                self.progress += event_data.get("amount", 0)
                progress_made = True

        return progress_made and self.check_completion(self.game)
    
    def complete(self, game):
        """Complete the quest and award all rewards"""
        if not self.completed:
            self.completed = True
            
            # Award base rewards
            game.ship.money += self.reward_money
            game.ship.research_points += self.reward_rp
            
            # Award additional rewards if present
            if hasattr(self, 'rewards'):
                if "reputation" in self.rewards:
                    game.ship.passenger_reputation += self.rewards["reputation"]
                if "plot_points" in self.rewards:
                    game.story_manager.plot_points += self.rewards["plot_points"]
                if "bonus_item" in self.rewards:
                    game.ship.acquire_item(self.rewards["bonus_item"])

            # Execute completion callback if exists
            if self.on_complete:
                self.on_complete()

            # Display completion message with all rewards
            completion_message = [
                f"Quest Completed: {self.name}",
                f"Rewards:",
                f"• {game.format_money(self.reward_money)} credits",
                f"• {self.reward_rp} research points"
            ]

            if hasattr(self, 'rewards'):
                if self.rewards.get("reputation"):
                    completion_message.append(f"• +{self.rewards['reputation']} reputation")
                if self.rewards.get("plot_points"):
                    completion_message.append(f"• +{self.rewards['plot_points']} plot points")
                if self.rewards.get("bonus_item"):
                    completion_message.append(f"• Bonus item: {self.rewards['bonus_item']}")

            game.display_story_message(completion_message)

class QuestSystem:
    def __init__(self, game):
        self.game = game
        self.active_quests = []  # For Quest objects
        self.available_quests = []  # For tuple-based quests (legacy support)
        self.completed_quests = []
        self.story_progress = 0
        self.quest_ids = set()  # Track unique quest IDs
        self.quest_message_shown = set()  # Track shown quest messages

        # Quest line progression tracking
        self.quest_lines = {
            "mining": ["basic_mining", "advanced_mining", "expert_mining"],
            "combat": ["patrol_duty", "pirate_hunting", "fleet_command"],
            "research": ["data_collection", "experiment_assistance", "breakthrough"]
        }
        self.quest_line_progress = {
            "mining": 0,
            "combat": 0,
            "research": 0
        }

    def check_active_quests(self):
        for quest in self.active_quests:
            if quest.check_completion(self.game):
                self.complete_quest(quest)

    def display_quests(self):
        """Display all active quests"""
        active_quests = [q for q in self.active_quests if isinstance(q, Quest)]
        if active_quests:
            quest_content = [["Active Quests"]]
            quest_content.append([""])
            for quest in active_quests:
                quest_content.append([quest.name])
                quest_content.append([f"└─ {quest.description}"])
                quest_content.append([f"└─ Rewards: {self.game.format_money(quest.reward_money)} credits, {quest.reward_rp} RP"])
                if hasattr(quest, 'requirements'):
                    progress = ""
                    if 'target_progress' in quest.requirements:
                        progress = f" ({quest.progress}/{quest.requirements['target_progress']})"
                    quest_content.append([f"└─ Progress{progress}"])
                quest_content.append([""])
            
            print(self.game.ui.create_box(quest_content, 'double'))
        else:
            self.game.display_simple_message("No active quests.")
        
        input("Press Enter to continue...")        

    def update_from_trade(self, trade_data):
        """Update quests based on trade actions"""
        for quest in self.active_quests:
            if quest.quest_type == "trade":
                # Check if trade matches quest requirements
                if trade_data.get('action') == 'buy' or trade_data.get('action') == 'sell':
                    commodity = trade_data.get("commodity")
                    if commodity == quest.requirements.get("commodity"):
                        quest.progress += trade_data.get("amount", 0)
                        
                        # Display quest progress
                        self.display_quest_progress(quest)
                        
                        # Check if quest is completed
                        if quest.check_completion(self.game):
                            self.complete_quest(quest)

        # Update cantina-type quests if they exist
        for quest in self.active_quests:
            if hasattr(quest, 'update_cantina_progress'):
                quest.update_cantina_progress(trade_data)

        

    def update_discovery_quests(self, location):
        """Update quests that involve location discovery"""
        for quest in self.active_quests:
            if quest.quest_type == "exploration":
                if "location_type" in quest.requirements:
                    if location.location_type == quest.requirements["location_type"]:
                        quest.progress += 1
                        self.display_quest_progress(quest)
                        
                        if quest.check_completion(self.game):
                            self.complete_quest(quest)
                            
                elif "specific_location" in quest.requirements:
                    if location.name == quest.requirements["specific_location"]:
                        quest.progress += 1
                        self.display_quest_progress(quest)
                        
                        if quest.check_completion(self.game):
                            self.complete_quest(quest)

            elif quest.quest_type == "location_unlock":
                if "location_type" in quest.requirements:
                    if location.location_type == quest.requirements["location_type"]:
                        quest.progress += 1
                        self.display_quest_progress(quest)
                        
                        if quest.check_completion(self.game):
                            self.complete_quest(quest)

    def update_cargo_quests(self, cargo_lost):
        """Update quests that involve cargo requirements"""
        for quest in self.active_quests:
            if quest.quest_type == "cargo" or quest.quest_type == "trade":
                # Check if quest requires specific cargo type that was lost
                if "cargo_type" in quest.requirements:
                    cargo_type = quest.requirements["cargo_type"]
                    if cargo_type in cargo_lost:
                        # Update progress based on remaining cargo
                        remaining_cargo = self.game.ship.cargo[cargo_type]
                        if "target_amount" in quest.requirements:
                            quest.progress = remaining_cargo / quest.requirements["target_amount"]
                        self.display_quest_progress(quest)

    def update_money_quests(self, money_lost):
        """Update quests that involve money requirements"""
        if money_lost > 0:  # Only process if money was actually lost
            for quest in self.active_quests:
                # Check trade profit quests
                if quest.quest_type == "profit" or quest.quest_type == "trade":
                    if "target_money" in quest.requirements:
                        current_money = self.game.ship.money
                        target_money = quest.requirements["target_money"]
                        quest.progress = max(0, min(1.0, current_money / target_money))
                        self.display_quest_progress(quest)
                        
                # Check money protection quests
                if quest.quest_type == "protect" and "max_money_loss" in quest.requirements:
                    if money_lost > quest.requirements["max_money_loss"]:
                        quest.failed = True
                        self.game.display_simple_message(f"Quest failed: Lost too much money!")
                        self.active_quests.remove(quest)
                        
                # Update trade margin quests
                if quest.quest_type == "margin" and "min_balance" in quest.requirements:
                    if self.game.ship.money < quest.requirements["min_balance"]:
                        quest.progress = max(0.0, quest.progress - 0.2)  # Lose 20% progress
                        self.display_quest_progress(quest)

    def update_combat_quests(self, damage_taken):
        """Update quests that involve combat requirements"""
        for quest in self.active_quests:
            if quest.quest_type == "combat":
                # Update survival quests
                if "max_damage" in quest.requirements:
                    if damage_taken > quest.requirements["max_damage"]:
                        quest.failed = True
                        self.display_quest_progress(quest)
                
                # Update combat victory quests that require minimal damage
                if "damage_threshold" in quest.requirements:
                    if damage_taken <= quest.requirements["damage_threshold"]:
                        quest.progress += 1
                        self.display_quest_progress(quest)

    def add_quest_type(self, quest_type):
        """Add a new type of quest to the available pool"""
        if not hasattr(self, 'available_quest_types'):
            self.available_quest_types = set()
        self.available_quest_types.add(quest_type)

    def generate_station_missions(self):
        """Generate station defense missions"""
        quest = Quest(
            name="Station Defense",
            description="Defend the station from incoming threats",
            reward_money=5000,
            reward_rp=50,
            quest_type="combat",
            requirements={"victories": 3, "damage_threshold": 20}
        )
        self.add_quest(quest)

    def generate_research_missions(self):
        """Generate research-related missions"""
        quest = Quest(
            name="Scientific Discovery",
            description="Collect research data from various phenomena",
            reward_money=4000,
            reward_rp=100,
            quest_type="research",
            requirements={"research_points": 50}
        )
        self.add_quest(quest)

    def generate_emergency_missions(self):
        """Generate emergency response missions"""
        quest = Quest(
            name="Emergency Response",
            description="Help ships in distress while avoiding damage",
            reward_money=6000,
            reward_rp=75,
            quest_type="combat",
            requirements={"rescues": 2, "max_damage": 30}
        )
        self.add_quest(quest)

    def check_event_requirements(self, event_result):
        """Check if an event satisfies any quest requirements"""
        event_type = event_result.get("type", "")
        for quest in self.active_quests:
            if quest.quest_type == event_type:
                quest.progress += 1
                self.display_quest_progress(quest)
                if quest.check_completion(self.game):
                    self.complete_quest(quest)

    def generate_quest(self, quest_type, difficulty):
        """Generate a quest based on type and difficulty"""
        base_reward = 1000 * (difficulty + 1)
        research_reward = 50 * (difficulty + 1)
        
        quest_templates = {
            "mining": [
                {
                    "name": f"Mine {50 * (difficulty + 1)} units of salt",
                    "description": "Extract valuable minerals from the asteroid field",
                    "type": "mining",
                    "requirements": {
                        "resource_type": "salt",
                        "amount": 50 * (difficulty + 1)
                    },
                    "reward_money": base_reward,
                    "reward_rp": research_reward
                },
                {
                    "name": f"Extract {40 * (difficulty + 1)} units of fuel",
                    "description": "Extract fuel from deep space deposits",
                    "type": "mining",
                    "requirements": {
                        "resource_type": "fuel",
                        "amount": 40 * (difficulty + 1)
                    },
                    "reward_money": int(base_reward * 1.2),
                    "reward_rp": int(research_reward * 1.2)
                }
            ],
            "combat": [
                {
                    "name": f"Eliminate {2 * (difficulty + 1)} pirate ships",
                    "description": "Clear the sector of pirate activity",
                    "type": "combat",
                    "requirements": {
                        "enemy_type": "pirate",
                        "amount": 2 * (difficulty + 1)
                    },
                    "reward_money": int(base_reward * 1.5),
                    "reward_rp": int(research_reward * 1.5)
                },
                {
                    "name": f"Defend trade route for {3 * (difficulty + 1)} turns",
                    "description": "Maintain security in a trade route",
                    "type": "patrol",
                    "requirements": {
                        "turns": 3 * (difficulty + 1)
                    },
                    "reward_money": int(base_reward * 1.3),
                    "reward_rp": int(research_reward * 1.3)
                }
            ],
            "research": [
                {
                    "name": f"Collect {30 * (difficulty + 1)} research data",
                    "description": "Gather scientific data from space phenomena",
                    "type": "research",
                    "requirements": {
                        "research_type": "data",
                        "target_points": 30 * (difficulty + 1)
                    },
                    "reward_money": int(base_reward * 1.2),
                    "reward_rp": int(research_reward * 2)
                }
            ],
            "story": [
                {
                    "name": "Investigate mysterious signals",
                    "description": "Track down the source of unusual transmissions",
                    "type": "story",
                    "requirements": {
                        "story_progression": 1
                    },
                    "reward_money": int(base_reward * 2),
                    "reward_rp": int(research_reward * 3)
                }
            ]
        }
        
        # Select a random quest template
        if quest_type in quest_templates:
            template = random.choice(quest_templates[quest_type])
            quest = Quest(
                name=template["name"],
                description=template["description"],
                reward_money=template["reward_money"],
                reward_rp=template["reward_rp"],
                quest_type=template["type"],
                requirements=template["requirements"]
            )
            return quest
        return None

    def display_quest_progress(self, quest):
        """Display quest progress update"""
        if isinstance(quest, Quest):
            progress_text = f"Quest Progress: {quest.name}"
            if quest.target_progress > 1:
                progress_text += f" ({quest.progress}/{quest.target_progress})"
            self.game.display_simple_message(progress_text)

    def get_available_quest_types(self):
        """Get available quest types based on game progress"""
        available_types = ["mining", "combat", "trade"]  # Basic types
        
        # Add research quests if conditions met
        if self.game.ship.research_points >= 50:
            available_types.append("research")
            
        # Add story quests if conditions met
        if self.story_progress >= 5:
            available_types.append("story")
            
        return available_types

    def add_quest(self, quest):
        """Add a new quest with duplication check"""
        # Create unique identifier for the quest
        quest_id = f"{quest.name}_{quest.quest_type}"
        
        # Check if quest is already active
        existing_quest = any(q.name == quest.name and q.quest_type == quest.quest_type 
                           for q in self.active_quests)
        if existing_quest:
            return False  # Don't add duplicate quest
        
        # Check if we've already shown this quest message
        if quest_id not in self.quest_message_shown:
            self.game.display_story_message([
                "New Quest Available!",
                quest.name,
                quest.description,
                f"Rewards: {self.game.format_money(quest.reward_money)} credits, {quest.reward_rp} RP"
            ])
            self.quest_message_shown.add(quest_id)
        
        # Add quest to active quests
        self.active_quests.append(quest)
        return True