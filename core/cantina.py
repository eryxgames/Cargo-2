# core/cantina.py
import random
import time

class Cantina:
    def __init__(self, game):
        self.game = game

    def handle_cantina_menu(self):
        self.game.clear_screen()
        self.game.display_simple_message("Welcome to the Cantina!", 0)

        # Check for present characters and announce them first
        present_characters = [char for char_id, char in 
                            self.game.character_manager.active_characters.items()
                            if (char["location"] == self.game.current_location and
                                "cantina" in char["character"].content['requirements'].get('spawn_locations', []))]
        
        if present_characters:
            for char in present_characters:
                self.game.character_manager.announce_character(char['character'].character_id)
                time.sleep(1)  # Brief pause between character announcements

        # Check and complete cantina quests
        cantina_quests = [q for q in self.game.quest_system.active_quests if q.quest_type == "cantina"]
        
        for quest in cantina_quests:
            if quest.check_completion(self.game):
                quest.complete(self.game)

        while True:
            options = {
                'map': ('bm', "Buy Map"),
                'update': ('um', "Update Map"),
                'gossip': ('lg', "Listen to Gossip"),
                'quests': ('q', "View Quests"),
                'contracts': ('c', "Manage Contracts"),
                'story': ('s', "View Story Progress"),
                'back': ('', "Return to Main Menu")
            }

            menu_content = [[f"Cantina Services - {self.game.current_location.name}"]]
            menu_content.append([f""])
            for cmd, (shortcut, desc) in options.items():
                menu_content.append([f"{cmd}/{shortcut if shortcut else ''}: {desc}"])
            print(self.game.create_box(menu_content, 'single'))

            valid_inputs = [cmd for cmd in options.keys()] + [s[0] for s in options.values() if s[0]]
            action = self.game.validate_input("Choose action: ", valid_inputs)

            if action in ['back', None]:
                break
                
            elif action in ['map', 'bm']:
                self.handle_buy_map()
                
            elif action in ['update', 'um']:
                self.handle_update_map()
                
            elif action in ['gossip', 'lg']:
                self.handle_gossip()
                
            elif action in ['quests', 'q']:
                self.game.quest_system.display_quests()
                
            elif action in ['contracts', 'c']:
                self.game.contract_manager.handle_contract_menu()
                
            elif action in ['story', 's']:
                self.display_story_status()

            time.sleep(1)
            self.game.clear_screen()

    def handle_buy_map(self):
        if self.game.ship.money >= 200:
            self.game.ship.money -= 200
            new_locations = []
            for location in self.game.locations:
                if location.name not in self.game.known_locations and location.location_type in self.game.unlocked_location_types:
                    new_locations.append(location)
                    self.game.known_locations.append(location.name)
                
            if new_locations:
                map_content = []
                # Header
                map_content.append(["New Locations!"])
                map_content.append([""])
                map_content.append(["Location", "Type", "Tech", "Agri", "Economy"])
                
                # Location data
                for location in new_locations:
                    features = []
                    if location.mining_platforms:
                        features.append("Mining")
                    if location.buildings:
                        features.append("Buildings")
                    if location.stockmarket_base:
                        features.append("Stock Market")
                    
                    map_content.append([
                        location.name,
                        location.location_type,
                        str(location.tech_level),
                        str(location.agri_level),
                        location.economy
                    ])
                    
                    # Add features as separate rows with proper indentation
                    if features:
                        map_content.append(["└─ Features: " + ", ".join(features), "", "", "", ""])
                
                print(self.game.create_box(map_content, 'double'))
                input("Press Enter to continue...")
            else:
                self.game.ship.money += 200  # Refund if no new locations
                self.game.display_simple_message("No new locations to discover!")
        else:
            self.game.display_simple_message("Not enough money to buy a map.")

    def handle_update_map(self):
        if self.game.ship.money >= 350:
            self.game.ship.money -= 350
            
            market_content = []
            # Header
            market_content.append(["Map Update"])
            market_content.append([""])
            market_content.append(["Location", "Tech", "Agri", "Salt", "Fuel"])
            
            # Show detailed info for known locations
            has_data = False
            for location_name in self.game.known_locations:
                location = next((loc for loc in self.game.locations if loc.name == location_name), None)
                if location:
                    has_data = True
                    tech_price = "BANNED" if 'tech' in location.banned_commodities else self.game.format_money(location.market['tech'])
                    agri_price = "BANNED" if 'agri' in location.banned_commodities else self.game.format_money(location.market['agri'])
                    salt_price = "BANNED" if 'salt' in location.banned_commodities else self.game.format_money(location.market['salt'])
                    fuel_price = "BANNED" if 'fuel' in location.banned_commodities else self.game.format_money(location.market['fuel'])
                    
                    market_content.append([
                        location.name,
                        tech_price,
                        agri_price,
                        salt_price if any(p['type'] == 'salt' for p in location.mining_platforms) else "No Mine",
                        fuel_price if any(p['type'] == 'fuel' for p in location.mining_platforms) else "No Mine"
                    ])
                    
                    # Add special features as separate rows
                    features = []
                    if location.stockmarket_base:
                        features.append("Stock Market")
                    if location.buildings:
                        features.append(f"Buildings: {', '.join(location.buildings)}")
                    if location.mining_platforms:
                        features.append(f"Mining Platforms: {len(location.mining_platforms)}")
                        
                    if features:
                        for feature in features:
                            market_content.append(["└─ " + feature, "", "", "", ""])
            
            if has_data:
                print(self.game.create_box(market_content, 'double'))
                input("Press Enter to continue...")
            else:
                self.game.ship.money += 350  # Refund if no data to show
                self.game.display_simple_message("No new information available!")
        else:
            self.game.display_simple_message("Not enough money to update the map.")

    def handle_gossip(self):
        """Handle gossip and quest generation in cantina"""
        if self.game.ship.money >= 150:
            self.game.ship.money -= 150
            gossip_content = [["Latest Market Gossip"]]
            gossip_content.append([""])
            
            # Generate market information
            found_gossip = False
            for location in self.game.locations:
                if location.name in self.game.known_locations:
                    location_gossip = []
                    if location.market['tech'] < 50:
                        location_gossip.append(f"Cheap tech goods available")
                    if location.market['agri'] < 30:
                        location_gossip.append(f"Cheap agri goods available")
                    if location.market['tech'] > 100:
                        location_gossip.append(f"High tech prices")
                    if location.market['agri'] > 80:
                        location_gossip.append(f"High agri prices")
                            
                    if location_gossip:
                        found_gossip = True
                        gossip_content.append([location.name])
                        for gossip in location_gossip:
                            gossip_content.append([f"└─ {gossip}"])
                
            if found_gossip:
                print(self.game.create_box(gossip_content, 'double'))
                
                # 30% chance to get a quest
                if random.random() < 0.3:
                    quest = self.game.quest_system.generate_quest(quest_type="cantina", difficulty=1)
                    if quest:
                        self.game.quest_system.add_quest(quest)
                        self.game.display_story_message([
                            "New Quest Available!",
                            quest.name,
                            quest.description,
                            f"Rewards: {self.game.format_money(quest.reward_money)} credits, {quest.reward_rp} RP"
                        ])
            else:
                self.game.display_simple_message("No interesting gossip today!")
        else:
            self.game.display_simple_message("Not enough money to listen to gossip.")

    def display_story_status(self):
        """Display story progress and achievements"""
        story_content = [["Story Progress & Achievements"]]
        story_content.append([""])
        
        # Current chapter info
        current_chapter_obj = self.game.story_manager.chapters[self.game.story_manager.current_chapter]
        story_content.append([f"Current Chapter {self.game.story_manager.get_chapter_number_roman()} : {current_chapter_obj.title}"])
        story_content.append([f"Plot Points: {self.game.story_manager.plot_points}"])
        
        # Completed story beats
        if self.game.story_manager.completed_story_beats:
            story_content.append([""])
            story_content.append(["Completed Story Elements"])
            for beat in self.game.story_manager.completed_story_beats:
                story_content.append([f"• {beat.replace('_', ' ').title()}"])
        
        # Achievements
        if hasattr(self.game.story_manager, 'unlocked_achievements') and self.game.story_manager.unlocked_achievements:
            story_content.append([""])
            story_content.append(["Achievements Unlocked"])
            for achievement in self.game.story_manager.unlocked_achievements:
                story_content.append([f"• {achievement.replace('_', ' ').title()}"])
        
        # Location discoveries
        if hasattr(self.game.story_manager, 'discovered_locations_by_type'):
            story_content.append([""])
            story_content.append(["Location Discoveries"])
            for loc_type, count in self.game.story_manager.discovered_locations_by_type.items():
                story_content.append([f"• {loc_type}: {count} discovered"])
        
        print(self.game.create_box(story_content, 'double'))
        input("Press Enter to continue...")