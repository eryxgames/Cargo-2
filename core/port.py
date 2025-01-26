# core/port.py
import random
import time

class PassengerModule:
    def __init__(self, name, capacity, comfort_level, cost):
        self.name = name
        self.capacity = capacity  # How many passengers it can hold
        self.comfort_level = comfort_level  # 1-5, affects passenger satisfaction and payment
        self.cost = cost
        self.passengers = []

class Passenger:
    def __init__(self, name, destination, wealth_level):
        self.name = name
        self.destination = destination
        self.wealth_level = wealth_level  # 1-5
        self.satisfaction = 100
        self.turns_waiting = 0
        # Add passenger classification
        self.classification = self.generate_classification()
        
    def generate_classification(self):
        classifications = [
            ("S", "Scientist", "science"),
            ("M", "Military", "military"),
            ("E", "Engineer", "engineering"),
            ("T", "Trader", "trade"),
            ("D", "Diplomat", "diplomacy"),
            ("R", "Researcher", "research")
        ]
        class_code, class_name, class_type = random.choice(classifications)
        return {
            "code": class_code,
            "name": class_name,
            "type": class_type
        }


class Port:
    def __init__(self, game):
        self.game = game
        self.available_modules = {
                "1": {
                    "name": "Basic Passenger",
                    "capacity": 4,
                    "comfort_level": 1,
                    "cost": 5000
                },
                "2": {
                    "name": "Standard Passenger",
                    "capacity": 8,
                    "comfort_level": 2,
                    "cost": 10000
                },
                "3": {
                    "name": "Luxury Passenger",
                    "capacity": 4,
                    "comfort_level": 4,
                    "cost": 20000
                },
                "4": {
                    "name": "Life Support Module",
                    "capacity": 4,
                    "comfort_level": 1,
                    "cost": 8000
                },
                "5": {
                    "name": "Business Class A",
                    "capacity": 2,
                    "comfort_level": 5,
                    "cost": 25000
                },
                "6": {
                    "name": "Research Lab Module",
                    "capacity": 2,
                    "comfort_level": 3,
                    "cost": 30000,
                    "special": "research_bonus"
                },
                "7": {
                    "name": "Colony Transport Mod.",
                    "capacity": 12,
                    "comfort_level": 2,
                    "cost": 35000,
                    "special": "colonist_bonus"
                },
                "8": {
                    "name": "Diplomatic Suite Mod.",
                    "capacity": 1,
                    "comfort_level": 6,
                    "cost": 40000,
                    "special": "diplomatic_bonus"
                }
            }
        
        # List of passengers waiting at each location
        self.waiting_passengers = {}
        
        # Passenger names for random generation
        self.first_names = ["John", "Emma", "Zara", "Chen", "Raj", "Ana", "Igor", "Yuki", "Omar", "Luna"]
        self.last_names = ["Smith", "Patel", "Wong", "Garcia", "Petrov", "Tanaka", "Mueller", "Kim", "Hassan", "Silva"]

    def get_special_characters(self):
        """Get special characters present at port"""
        return [char for char_id, char in 
                self.game.character_manager.active_characters.items()
                if char["location"] == self.game.current_location and
                "port" in char["character"].content['requirements'].get('spawn_locations', [])]

    def generate_passenger(self, current_location):
        """Generate a random passenger"""
        name = f"{random.choice(self.first_names)} {random.choice(self.last_names)}"
        # Choose destination from known locations except current
        possible_destinations = [loc for loc in self.game.known_locations if loc != current_location]
        if not possible_destinations:
            return None
        destination = random.choice(possible_destinations)
        wealth_level = random.randint(1, 5)
        return Passenger(name, destination, wealth_level)

    def add_special_passenger(self, character):
        """Add a special character to waiting passengers list"""
        current_location = self.game.current_location.name
        if current_location not in self.waiting_passengers:
            self.waiting_passengers[current_location] = []
            
        # Create passenger object from character
        passenger = Passenger(
            name=character.full_name,
            destination=random.choice(list(self.game.known_locations)),
            wealth_level=5  # VIPs and special characters are wealthy
        )
        
        # Add character-specific attributes
        passenger.is_special = True
        passenger.character = character
        passenger.classification = {"code": "V", "name": "VIP", "type": character.specialization}
        
        # Add to waiting list
        self.waiting_passengers[current_location].append(passenger)
        
        return passenger

    def update_passengers(self, location):
        """Update passenger list at a location"""
        if location not in self.waiting_passengers:
            self.waiting_passengers[location] = []
            
        # Remove passengers waiting too long
        self.waiting_passengers[location] = [p for p in self.waiting_passengers[location] 
                                           if p.turns_waiting < 10]

        # Check for special character spawning
        if random.random() < 0.2:  # 20% chance per turn
            self.game.reputation_manager.spawn_special_passenger()

        # Add new passengers (1-3 per turn)
        new_passengers = random.randint(1, 3)
        for _ in range(new_passengers):
            passenger = self.generate_passenger(location)
            if passenger:
                self.waiting_passengers[location].append(passenger)
                
        # Update waiting turns
        for passenger in self.waiting_passengers[location]:
            passenger.turns_waiting += 1

    def calculate_fare(self, passenger, module):
        """Calculate passenger fare based on distance, comfort, and wealth"""
        base_fare = 100 * passenger.wealth_level
        comfort_multiplier = 1 + (module.comfort_level * 0.2)
        distance_multiplier = 1
        
        # Add distance calculation if game has that mechanic
        # distance_multiplier = calculate_distance(current, destination)
        
        return int(base_fare * comfort_multiplier * distance_multiplier)

    def display_port_info(self):
        """Display port information and options"""
        content = []
        
        # Show installed modules
        content.append(["Installed Passenger Modules"])
        if hasattr(self.game.ship, 'passenger_modules'):
            for module in self.game.ship.passenger_modules:
                passengers = len(module.passengers)
                content.append([
                    f"{module.name}",
                    f"({passengers}/{module.capacity} passengers)",
                    f"Comfort Lvl.: {module.comfort_level}"
                ])
        else:
            content.append(["No passenger modules installed"])
            
        # Show current passengers
        content.append([""])
        content.append(["Current Passengers"])
        total_passengers = 0
        if hasattr(self.game.ship, 'passenger_modules'):
            for module in self.game.ship.passenger_modules:
                for passenger in module.passengers:
                    total_passengers += 1
                    content.append([
                        f"{passenger.name}",
                        f"→ {passenger.destination}",
                        f"Satisfaction: {passenger.satisfaction}%"
                    ])
        if total_passengers == 0:
            content.append(["No passengers currently aboard"])

        # Show waiting passengers at current location
        content.append([""])
        content.append(["Waiting Passengers"])
        location = self.game.current_location.name
        if location in self.waiting_passengers and self.waiting_passengers[location]:
            for passenger in self.waiting_passengers[location]:
                content.append([
                    f"{passenger.name}",
                    f"→ {passenger.destination}",
                    f"Class: {passenger.wealth_level}"
                ])
        else:
            content.append(["No passengers waiting"])
            
        return self.game.ui.create_box(content, 'double')

    def handle_port_menu(self):
        """Handle port menu options"""
        self.game.clear_screen()
        self.game.display_simple_message("Welcome to the Stardock Port!", 0)

        while True:
            options = {
                'view': ('v', "View Port Info"),
                'modules': ('m', "Purchase Modules"),
                'board': ('b', "Board Passengers"),
                'unload': ('u', "Unload Passengers"),
                'contracts': ('c', "Manage Contracts"),
                'travel': ('t', "Travel"),
                'back': ('', "Return to Main Menu")
            }
            
            # Show menu
            menu_content = [[f"Port Services {self.game.current_location.name} | PAX Checkout: {sum(len(module.passengers) for module in self.game.ship.passenger_modules)}/{sum(module.capacity for module in self.game.ship.passenger_modules)}"]]
            menu_content.append([f""])
            for cmd, (shortcut, desc) in options.items():
                menu_content.append([f"{cmd}/{shortcut if shortcut else ''}: {desc}"])
            print(self.game.ui.create_box(menu_content, 'single'))

            valid_inputs = [cmd for cmd in options.keys()] + [s[0] for s in options.values() if s[0]]
            action = self.game.validate_input("Choose action: ", valid_inputs)
            
            if action in ['back', None]:
                break
                
            elif action in ['view', 'v']:
                print(self.display_port_info())
                time.sleep(2)
                
            elif action in ['modules', 'm']:
                self.handle_module_purchase()
                
            elif action in ['board', 'b']:
                self.handle_passenger_boarding()
                
            elif action in ['unload', 'u']:
                self.handle_passenger_unloading()
                time.sleep(2)
            
            elif action in ['contracts', 'c']:
                self.game.contract_manager.handle_contract_menu()
            
            elif action in ['travel', 't']:
                if self.game.handle_travel():
                    break

            self.game.clear_screen()

    def handle_module_purchase(self):
        """Handle purchase of new modules with numbered selection"""
        while True:
#            self.game.clear_screen()
            content = [["", f"¤: {self.game.format_money(self.game.ship.money)}"]]
    #        content.append([""])  # Empty line for spacing
            content.append(["#", "Module Types:", "Cap.", "Comf.", "Cost"])
#            content.append(["#", "Module Types:", "Cap.", "Comf.", "Cost", "Special"])
            
            for module_id, module in self.available_modules.items():
                special = module.get("special", "-")
                content.append([
                    module_id,
                    module["name"],
                    str(module["capacity"]),
                    str(module["comfort_level"]),
                    str(self.game.format_money(module["cost"])),
#                    special #yet uinimplemented module special
                ])
                    
            print(self.game.ui.create_box(content, 'double'))
            
            module_id = self.game.validate_input(
                "Enter module number to buy (or 'back'): ",
                list(self.available_modules.keys()) + ['back']
            )
            
            if module_id == 'back':
                self.game.clear_screen()
                return
                    
            if module_id in self.available_modules:
                module = self.available_modules[module_id]
                if self.game.ship.money >= module["cost"]:
                    self.game.ship.money -= module["cost"]
                    
                    if not hasattr(self.game.ship, 'passenger_modules'):
                        self.game.ship.passenger_modules = []
                        
                    new_module = PassengerModule(
                        module["name"],
                        module["capacity"],
                        module["comfort_level"],
                        module["cost"]
                    )
                    if "special" in module:
                        new_module.special = module["special"]
                    
                    self.game.ship.passenger_modules.append(new_module)
                    
                    self.game.display_simple_message(f"Purchased {module['name']}!")
#                    time.sleep(1)
                    self.game.clear_screen()
                    return
                else:
                    self.game.display_simple_message("Not enough money!")
#                    time.sleep(1)
                    self.game.clear_screen()
                    return

    def handle_passenger_boarding(self):
        """Handle passenger boarding with removal from waiting list"""
        while True:
            location = self.game.current_location.name
            
            if not hasattr(self.game.ship, 'passenger_modules'):
                self.game.display_simple_message("No passenger modules installed!")
                self.game.clear_screen()
                return
                        
            if location not in self.waiting_passengers or not self.waiting_passengers[location]:
                self.game.display_simple_message("No passengers waiting!")
                self.game.clear_screen()
                return
                        
            available_modules = [m for m in self.game.ship.passenger_modules 
                            if len(m.passengers) < m.capacity]
            
            if not available_modules:
                self.game.display_simple_message("No room for more passengers!")
                self.game.clear_screen()
                return

            # Show module status
            self.display_module_status()

            # Show waiting passengers
            self.display_waiting_passengers()

            # Get command
            self.game.display_simple_message(
                "Enter numbers to select passengers, 'refresh/r' to refresh list, 'autoboard/a' for auto boarding, or Enter to cancel:", 0
            )
            
            selection = input(">>> ").strip().lower()
            
            if not selection:  # Empty Enter
                return
                
            if selection in ['refresh', 'r']:
                # Regenerate waiting passengers
                self.update_passengers(location)
                continue
                
            if selection in ['autoboard', 'a']:
                self.handle_autoboard(available_modules)
                continue
                
            try:
                # Parse space-separated numbers
                passenger_nums = [int(num) - 1 for num in selection.split()]
                waiting_passengers = self.waiting_passengers[location]
                
                # Validate numbers and get passengers
                selected_passengers = []
                if all(0 <= num < len(waiting_passengers) for num in passenger_nums):
                    # Get passengers and remove them from waiting list
                    selected_passengers = [waiting_passengers[num] for num in sorted(passenger_nums, reverse=True)]
                    for num in sorted(passenger_nums, reverse=True):
                        del waiting_passengers[num]
                    
                    if selected_passengers:
                        self.handle_module_assignment(selected_passengers, available_modules)
                else:
                    self.game.display_simple_message("Invalid passenger number(s)")
                    
            except ValueError:
                self.game.display_simple_message("Invalid input. Please enter numbers separated by spaces.")

    def handle_passenger_unloading(self):
            """Handle passenger unloading with reputation effects and bonuses"""
            if not hasattr(self.game.ship, 'passenger_modules'):
                self.game.display_simple_message("No passenger modules installed!")
                return
                    
            current_location = self.game.current_location.name
            passengers_to_unload = []
            total_earnings = 0
            
            # Find passengers that have reached their destination
            for module in self.game.ship.passenger_modules:
                for passenger in module.passengers[:]:
                    if passenger.destination == current_location:
                        # Calculate fare with reputation multiplier
                        base_fare = self.calculate_fare(passenger, module)
                        reputation_multiplier = self.game.reputation_manager.get_fare_multiplier()
                        satisfaction_multiplier = passenger.satisfaction / 100
                        bonus_multiplier = 1.0  # Default multiplier

                        # Apply organization bonus if applicable
                        org_bonus = self.get_bonus_type(passenger)
                        bonus_message = None
                        if org_bonus:
                            org_name, multiplier, message = org_bonus
                            bonus_multiplier = multiplier
                            bonus_message = f"{org_name} doubles the revenue! {message} Plot points +1"
                            self.game.story_manager.plot_points += 1

                        # Calculate final payment with all multipliers
                        final_payment = int(base_fare * satisfaction_multiplier * reputation_multiplier * bonus_multiplier)

                        # Update reputation based on passenger satisfaction
                        reputation_change = self.game.reputation_manager.update_reputation(passenger.satisfaction, passenger)

                        # Handle special passengers
                        if hasattr(passenger, 'is_vip'):
                            self.game.reputation_manager.handle_vip_delivery(passenger)
                        elif hasattr(passenger, 'is_story_character'):
                            self.game.reputation_manager.handle_story_character_delivery(passenger)

                        # Update contract progress if available
                        if hasattr(self.game, 'contract_manager'):
                            passenger_data = {
                                "class": passenger.classification["code"],
                                "satisfaction": passenger.satisfaction
                            }
                            event_data = {
                                "location": current_location,
                                "passenger_data": passenger_data,
                                "action": "unload"
                            }
                            for contract in self.game.contract_manager.active_contracts:
                                contract.update_progress(event_data)

                        # Increment total passengers delivered
                        self.game.reputation_manager.total_passengers += 1

                        # Record unloading result
                        passengers_to_unload.append({
                            'passenger': passenger,
                            'payment': final_payment,
                            'satisfaction': passenger.satisfaction,
                            'reputation_change': reputation_change,
                            'bonus_message': bonus_message
                        })

                        # Apply payment and remove passenger
                        self.game.ship.money += final_payment
                        module.passengers.remove(passenger)
                        total_earnings += final_payment

            # Display unloading results
            if passengers_to_unload:
                content = [["Passengers Disembarked"]]
                
                for result in passengers_to_unload:
                    passenger = result['passenger']
                    content.append([
                        passenger.name,
                        f"Fare: {self.game.format_money(result['payment'])}",
                        f"Satisfied: {result['satisfaction']}%"
                    ])
                    
                    # Add reputation change if significant
                    if abs(result['reputation_change']) >= 0.1:
                        content.append([
                            f"└─ Reputation Change: {'+' if result['reputation_change'] > 0 else ''}{result['reputation_change']:.1f}"
                        ])
                    
                    # Add bonus message if any
                    if result['bonus_message']:
                        content.append([f"└─ {result['bonus_message']}"])
                
                content.append([""])
                content.append([f"Total Earnings: {self.game.format_money(total_earnings)}"])
                
                print(self.game.ui.create_box(content, 'double'))
            else:
                self.game.display_simple_message("No passengers to unload here!")
#                self.game.clear_screen()

    def get_bonus_type(self, passenger):
        """Get bonus type based on passenger classification"""
        bonus_types = {
            "S": ("Scientific Institute", 2.0, "Scientific research strengthened!"),
            "M": ("Planetary Defense Council", 3.0, "Military recruitment enhanced!"),
            "E": ("Engineering Corps", 2.5, "Engineering capacity expanded!"),
            "T": ("Trade Federation", 2.0, "Commercial networks expanded!"),
            "D": ("Diplomatic Service", 3.0, "Diplomatic relations improved!"),
            "R": ("Research Foundation", 2.5, "Research capabilities enhanced!")
        }
        passenger_class = passenger.classification["code"]
        if random.random() < 0.3:  # 30% chance for bonus
            return bonus_types.get(passenger_class)
        return None

    def handle_autoboard(self, available_modules):
        """Handle automatic passenger boarding based on destination"""
        location = self.game.current_location.name
        waiting_passengers = self.waiting_passengers[location]
        
        # Get unique destinations
        destinations = sorted(set(p.destination for p in waiting_passengers))
        
        # Show destinations
        content = [["Available Destinations"]]
        for i, dest in enumerate(destinations, 1):
            matching = sum(1 for p in waiting_passengers if p.destination == dest)
            content.append([f"{i}. {dest}", f"{matching} passengers waiting"])
        print(self.game.ui.create_box(content, 'single'))
        
        # Get destination choice
        self.game.display_simple_message("Choose destination number:", 0)
        try:
            choice = int(input(">>> "))
            if 1 <= choice <= len(destinations):
                target_dest = destinations[choice-1]
                
                # Get matching passengers
                matching_passengers = [p for p in waiting_passengers if p.destination == target_dest]
                
                # Board as many as possible
                modules_space = sum(m.capacity - len(m.passengers) for m in available_modules)
                to_board = matching_passengers[:modules_space]
                
                if to_board:
                    self.handle_module_assignment(to_board, available_modules)
                else:
                    self.game.display_simple_message("No matching passengers to board!")
                    
        except (ValueError, IndexError):
            self.game.display_simple_message("Invalid choice!")

    def display_module_status(self):
        """Display current module status"""
        module_status = [["Current Module Status"]]
        for module in self.game.ship.passenger_modules:
            passengers_info = []
            for p in module.passengers:
                passengers_info.append(f"{p.name} [{p.classification['code']}] → {p.destination}")
            module_status.append([
                f"{module.name}",
                f"({len(module.passengers)}/{module.capacity})",
                f"Comfort: {module.comfort_level}"
            ])
            for p_info in passengers_info:
                module_status.append([f"└─ {p_info}"])
        print(self.game.ui.create_box(module_status, 'single'))

    def display_waiting_passengers(self):
        """Display waiting passengers"""
        location = self.game.current_location.name
        content = [[""]]
        content.append(["#", f"Waiting on {location}", "Dest.", "Cls.", "≈Fare"])
        
        waiting_passengers = self.waiting_passengers[location]
        for i, passenger in enumerate(waiting_passengers, 1):
            best_module = max(
                (m for m in self.game.ship.passenger_modules if len(m.passengers) < m.capacity), 
                key=lambda m: m.comfort_level
            )
            est_fare = self.calculate_fare(passenger, best_module)
            content.append([
                str(i),
                f"{passenger.name} [{passenger.classification['code']}]",
                passenger.destination,
                f"L{passenger.wealth_level}",
                self.game.format_money(est_fare)
            ])
        
        print(self.game.ui.create_box(content, 'double'))            

    def handle_module_assignment(self, selected_passengers, available_modules):
        """Handle assigning selected passengers to modules"""
        passengers_left = selected_passengers.copy()
        
        while passengers_left and available_modules:
            # Show remaining passengers
            content = [["Remaining Passengers"]]
            for i, passenger in enumerate(passengers_left, 1):
                content.append([
                    f"{i}. {passenger.name} [{passenger.classification['code']}]",
                    passenger.destination
                ])
            print(self.game.ui.create_box(content, 'single'))
            
            # Show available modules
            module_content = [["Available Modules"]]
            for i, module in enumerate(available_modules, 1):
                module_content.append([
                    f"{i}. {module.name}",
                    f"({len(module.passengers)}/{module.capacity})",
                    f"Comfort: {module.comfort_level}"
                ])
            print(self.game.ui.create_box(module_content, 'single'))
            
            # Get module choice with auto option
            self.game.display_simple_message(
                "Choose module number, 'auto/a' for automatic assignment, or 'back':", 0
            )
            choice = input(">>> ").strip().lower()
            
            if choice == 'back':
                break
                
            if choice in ['auto', 'a']:
                self.auto_assign_modules(passengers_left, available_modules)
                break
                
            try:
                module_num = int(choice)
                if 1 <= module_num <= len(available_modules):
                    chosen_module = available_modules[module_num - 1]
                    if len(chosen_module.passengers) >= chosen_module.capacity:
                        self.game.display_simple_message("Module is full!")
                        continue
                        
                    # Add first remaining passenger
                    passenger = passengers_left.pop(0)
                    chosen_module.passengers.append(passenger)
                    self.game.display_simple_message(f"Assigned {passenger.name} to {chosen_module.name}")
                    
                    # Remove full modules from available list
                    if len(chosen_module.passengers) >= chosen_module.capacity:
                        available_modules.remove(chosen_module)
                else:
                    self.game.display_simple_message("Invalid module number")
            except ValueError:
                self.game.display_simple_message("Invalid input")

    def auto_assign_modules(self, passengers, modules):
        """Automatically assign passengers to modules"""
        # Sort modules by comfort level (highest first)
        sorted_modules = sorted(modules, key=lambda m: m.comfort_level, reverse=True)
        
        # Sort passengers by wealth level (highest first)
        sorted_passengers = sorted(passengers, key=lambda p: p.wealth_level, reverse=True)
        
        assigned = 0
        location = self.game.current_location.name
        
        for passenger in sorted_passengers[:]:  # Use slice to create copy for iteration
            for module in sorted_modules:
                if len(module.passengers) < module.capacity:
                    module.passengers.append(passenger)
                    if passenger in self.waiting_passengers[location]:  # Remove from waiting list
                        self.waiting_passengers[location].remove(passenger)
                    assigned += 1
                    self.game.display_simple_message(
                        f"Auto-assigned {passenger.name} to {module.name}"
                    )
                    break
        
        remaining = len(passengers) - assigned
        if remaining > 0:
            self.game.display_simple_message(f"Could not assign {remaining} passengers - no space left")
            
    def update_passenger_satisfaction(self):
        """Update passenger satisfaction during travel"""
        if not hasattr(self.game.ship, 'passenger_modules'):
            return
            
        for module in self.game.ship.passenger_modules:
            for passenger in module.passengers:
                # Base satisfaction change
                change = 0
                
                # Comfort level effect
                if module.comfort_level >= passenger.wealth_level:
                    change += 2  # Satisfied with comfort
                else:
                    change -= 3  # Dissatisfied with comfort
                    
                # Ship damage effect
                if self.game.ship.damage > 50:
                    change -= 5
                elif self.game.ship.damage > 25:
                    change -= 2
                    
                # Update satisfaction
                passenger.satisfaction = max(0, min(100, passenger.satisfaction + change))
    
    def get_fare_multiplier(self):
        """Get fare multiplier based on reputation"""
        reputation = self.game.ship.passenger_reputation
        if reputation >= 80:
            return 2.0
        elif reputation >= 60:
            return 1.5
        elif reputation >= 40:
            return 1.3
        elif reputation >= 20:
            return 1.1
        return 1.0

    def handle_vip_delivery(self, passenger):
        """Handle delivery of VIP passenger"""
        if hasattr(passenger, 'is_vip') and passenger.is_vip:
            # Award rewards
            self.game.ship.money += passenger.rewards["base_money"]
            self.game.ship.passenger_reputation += passenger.rewards["reputation"]
            self.game.story_manager.plot_points += passenger.plot_points
            
            self.game.display_simple_message([
                f"VIP Passenger Successfully Delivered!",
                f"Earned {self.game.format_money(passenger.rewards['base_money'])} credits",
                f"Reputation +{passenger.rewards['reputation']}",
                f"Plot Points +{passenger.rewards['plot_points']}"
            ])
    def handle_story_character_delivery(self, passenger):
        """Handle delivery of story character"""
        if hasattr(passenger, 'is_story_character') and passenger.is_story_character:
            # Advance event chain
            event_chain = passenger.event_chain
            stage = event_chain.advance()
            
            if stage:
                self.game.character_system.handle_event_stage(stage, passenger)
            
            if event_chain.is_complete():
                char_type = next(k for k, v in self.active_story_chains.items() 
                               if v == event_chain)
                del self.active_story_chains[char_type]
                
                self.game.display_story_message([
                    f"Story Arc Complete: {char_type}",
                    "A new chapter in your journey unfolds..."
                ])