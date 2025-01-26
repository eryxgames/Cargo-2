# core/action.py
import random

class Action:
    def __init__(self):
        # Base costs for actions
        self.action_costs = {
            'research': 100,
            'scout': 50,
            'geoscan': 75,
            'revolution': 100,
            'psychodynamics': 60
        }
        
        # Success chances for various actions
        self.base_success_rates = {
            'scout': 0.65,
            'geoscan': 0.70,
            'revolution': 0.50,
            'psychodynamics': 0.60
        }

    def research(self, planet, option, research_system):
        """
        Attempt to research a new technology
        Returns: (bool success, str message)
        """
        if option in research_system.unlocked_options:
            return False, "This research has already been completed."
            
        # Apply immediate benefits based on research type
        if option == 'exogeology':
            planet.exogeology = min(100, 
                int(planet.exogeology * (1 + research_system.research_benefits['exogeology']['output_bonus'])))
        
        return True, f"Successfully researched {option}!"

    def scout_area(self, planet, research_system):
        """
        Scout the area for resources or items
        Returns: (bool success, str type, any value, str message)
        """
        # Calculate success chance
        success_chance = self.base_success_rates['scout']
        if 'telemetry' in research_system.unlocked_options:
            success_chance += research_system.research_benefits['telemetry']['scout_success']
            
        if random.random() < success_chance:
            discovery_type = random.choice(['tech', 'agri', 'item'])
            
            if discovery_type == 'item':
                item = random.choice(['scanner', 'probe', 'turrets', 'shield'])
                return True, 'item', item, f"Found a {item}!"
            else:
                amount = random.randint(10, 30)
                return True, discovery_type, amount, f"Found {amount} units of {discovery_type}!"
        
        return False, None, None, "Scouting attempt failed!"

    def geoscan(self, planet, research_system):
        """
        Scan for mineral deposits
        Returns: (bool success, str deposit_type, int amount, str message)
        """
        # Calculate success chance
        success_chance = self.base_success_rates['geoscan']
        if 'geophysics' in research_system.unlocked_options:
            success_chance += research_system.research_benefits['geophysics']['exogeology']
            
        if random.random() < success_chance:
            deposit_type = random.choice(['salt', 'fuel'])
            amount = random.randint(1000, 5000)
            
            if deposit_type not in planet.mineral_deposits:
                planet.mineral_deposits[deposit_type] = amount
                return True, deposit_type, amount, f"Found {amount} units of {deposit_type} deposits!"
            else:
                bonus = random.randint(500, 1000)
                planet.mineral_deposits[deposit_type] += bonus
                return True, deposit_type, bonus, f"Found additional {bonus} units of {deposit_type} deposits!"
                
        return False, None, None, "Geoscan failed to find any deposits!"

    def incite_revolution(self, planet, research_system):
        """
        Attempt to change planet's economy
        Returns: (bool success, str new_economy, str message)
        """
        # Calculate success chance
        success_chance = self.base_success_rates['revolution']
        if 'chronopolitics' in research_system.unlocked_options:
            success_chance += research_system.research_benefits['chronopolitics']['revolution_success']
            
        if random.random() < success_chance:
            current_economy = planet.economy
            possible_economies = ['Booming', 'Stable', 'Declining', 'Formative']
            possible_economies.remove(current_economy)
            new_economy = random.choice(possible_economies)
            planet.economy = new_economy
            return True, new_economy, f"Revolution successful! Economy changed to {new_economy}!"
            
        return False, None, "Revolution attempt failed!"

    def manipulate_market(self, planet, commodity, research_system):
        """
        Attempt to manipulate market prices
        Returns: (bool success, float price_change, str message)
        """
        if random.random() < self.base_success_rates['psychodynamics']:
            manipulation_power = research_system.research_benefits['psychodynamics']['price_control']
            current_price = planet.market[commodity]
            
            # Determine direction of manipulation (increase/decrease)
            direction = random.choice([-1, 1])
            change = direction * random.uniform(0.1, manipulation_power) * current_price
            
            # Apply change with bounds checking
            new_price = max(1, current_price + change)
            if commodity == 'salt':
                new_price = min(new_price, 150)
            elif commodity == 'fuel':
                new_price = min(new_price, 250)
            else:
                new_price = min(new_price, 200)
                
            planet.market[commodity] = new_price
            price_change = new_price - current_price
            return True, price_change, f"Successfully manipulated {commodity} price by {abs(price_change):.1f}!"
            
        return False, 0, "Market manipulation attempt failed!"