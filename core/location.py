# core/location.py
import random
import os
import shutil
import csv
from core.utils import format_money
from core.template import CharacterTemplate
from core.location_data import LocationCommands, LocationCapabilities, LocationTerminology


class Location:
    def __init__(self, name, location_type, tech_level, agri_level, research_points, economy, affiliation, relation_to_player):
        self.name = name
        self.location_type = location_type
        self.tech_level = int(tech_level)  # Ensure type conversion
        self.agri_level = int(agri_level)
        self.research_points = int(research_points)
        self.economy = economy
        self.affiliation = affiliation
        self.relation_to_player = relation_to_player
        self.stockmarket_base = False
        self.stockmarket_cost = 5000
        self.buildings = []
        self.exogeology = self.get_base_exogeology()
        self.banned_commodities = []
        self.ban_duration = {}
        self.mineral_deposits = {}
        self.mining_platforms = []
        self.production_cooldown = {}
        # Generate market after initializing attributes
        self.market = self.generate_market()
        self.security_level = 5  # Initialize with medium security level

    @property
    def commands(self):
        """Get all commands for this location"""
        return LocationCommands.get_commands_for_location(self)

    def calculate_mining_output(self, platform_type):
        """Calculate mining output based on efficiency and random factors"""
        base_output = random.randint(10, 20)
        efficiency_bonus = self.exogeology / 100
        return int(base_output * efficiency_bonus)

    def produce_resources(self):
        """Handle resource production from mining platforms"""
        for platform in self.mining_platforms:
            resource_type = platform['type']
            if resource_type not in self.production_cooldown or self.production_cooldown[resource_type] <= 0:
                output = self.calculate_mining_output(resource_type)
                if resource_type == 'salt':
                    self.market['salt'] = random.randint(80, 120)
                elif resource_type == 'fuel':
                    self.market['fuel'] = random.randint(150, 200)
                self.production_cooldown[resource_type] = 3  # 3 turns cooldown
            else:
                self.production_cooldown[resource_type] -= 1

    def build_mining_platform(self, deposit_type, cost):
        """Build a new mining platform for specified deposit"""
        if deposit_type in self.mineral_deposits:
            if self.mineral_deposits[deposit_type] > 0:
                self.mining_platforms.append({
                    'type': deposit_type,
                    'efficiency': self.exogeology,
                    'capacity': random.randint(100, 200)
                })
                self.mineral_deposits[deposit_type] -= 1
                return True
        return False

    def generate_market(self):
        # Generate base market prices based on tech and agri levels
        market = {
            'tech': 100 - (self.tech_level * 10),
            'agri': 50 + (self.agri_level * 5),
            'salt': 0,
            'fuel': 0
        }
        
        # Apply refinery effects
        if "Halide Extraction Refinery" in self.buildings:
            # Salt refinery lowers agri prices, sets salt price
            market['salt'] = random.randint(100, 150)
            market['agri'] = max(1, int(market['agri'] * 0.8))
        
        if "Plasma Catalysis Refinery" in self.buildings:
            # Fuel refinery lowers tech prices, sets fuel price
            market['fuel'] = random.randint(150, 200)
            market['tech'] = max(1, int(market['tech'] * 0.8))
        
        if "Elemental Fusion Refinery" in self.buildings:
            # Combined refinery raises tech and agri prices
            market['tech'] = int(market['tech'] * 1.3)
            market['agri'] = int(market['agri'] * 1.3)
        
        return market
    
    def display_market_info(self):
        """Display market information with mining details"""
        market_content = [["Commodity", "Price", "Status"]]
        
        # Regular commodities
        market_content.append(["Tech", str(self.market['tech']), ""])
        market_content.append(["Agri", str(self.market['agri']), ""])
        
        # Mining commodities
        for resource in ['salt', 'fuel']:
            price = self.market[resource]
            status = ""
            
            # Check for mining platform
            platform = next((p for p in self.mining_platforms 
                            if p.resource_type == resource), None)
            if platform:
                status = f"M: {platform.current_amount}/{platform.max_capacity}"
            elif any(b == "Refinery" for b in self.buildings):
                status = "R"  # Show refinery indicator
                
            if price > 0 or status:  # Only show if tradeable
                market_content.append([
                    resource.capitalize(),
                    str(price),
                    status
                ])
        
        return self.game.ui.create_box(market_content, 'single')    

    def update_market(self, difficulty):
        """Update market prices with location-specific logic"""
        capabilities = self.get_capabilities()
        tradeable = capabilities.get("can_trade", [])
        
        for commodity in self.market:
            if commodity not in tradeable:
                continue
                
            # Base price changes with randomization and difficulty scaling
            base_change = random.randint(-5, 5) * (1 + difficulty)
            
            # Apply economic effects
            if self.economy == "Booming":
                base_change += 5
            elif self.economy == "Declining":
                base_change -= 5
            elif self.economy == "Formative":
                base_change = int(base_change * 1.2)  # More volatile prices
            
            # Apply stockmarket effects if present
            if self.stockmarket_base:
                base_change = max(1, base_change - 10)
            
            # Handle building effects
            for building in self.buildings:
                if building == "Permaculture Paradise" and commodity == 'agri':
                    base_change = max(1, base_change * 0.8)
                elif building == "The Nanotech Nexus":
                    base_change = max(1, base_change * 0.85)

            # Calculate new price
            new_price = max(1, self.market[commodity] + base_change)
            
            # Apply commodity-specific limits
            if commodity == 'salt':
                new_price = min(new_price, 150)
            elif commodity == 'fuel':
                new_price = min(new_price, 250)
            else:
                new_price = min(new_price, 200)
                
            self.market[commodity] = new_price

            # Handle zero prices and bans
            if new_price == 0 and commodity not in self.banned_commodities:
                self.add_temporary_ban(commodity, random.randint(2, 4))

        # Update ban durations and remove expired bans
        for commodity in list(self.ban_duration.keys()):
            self.ban_duration[commodity] -= 1
            if self.ban_duration[commodity] <= 0:
                self.banned_commodities.remove(commodity)
                del self.ban_duration[commodity]
                # Reset price for previously banned commodity
                if commodity == 'tech':
                    self.market['tech'] = 100 - (self.tech_level * 10)
                elif commodity == 'agri':
                    self.market['agri'] = 50 + (self.agri_level * 5)

        # Update production cooldowns
        for resource_type in list(self.production_cooldown.keys()):
            if self.production_cooldown[resource_type] > 0:
                self.production_cooldown[resource_type] -= 1

    def calculate_tax_rate(self, player_rank, profit):
        """Calculate tax rate based on player rank and location type"""
        base_tax = 0.05  # 5% base tax
        rank_multiplier = {
            "Explorer": 1,
            "Pilot": 1.2,
            "Captain": 1.4,
            "Commander": 1.6,
            "Star Commander": 1.8,
            "Space Admiral": 2.0,
            "Stellar Hero": 2.2,
            "Galactic Legend": 2.5
        }
        
        # Reduce tax based on number of buildings
        building_discount = len(self.buildings) * 0.02  # 2% reduction per building
        
        # Location-specific tax adjustments
        location_tax_modifier = {
            "Planet": 1.0,
            "AsteroidBase": 0.8,  # Lower taxes to encourage mining
            "DeepSpaceOutpost": 1.2,  # Higher taxes for premium services
            "ResearchColony": 1.5   # Highest taxes due to research benefits
        }
        
        location_modifier = location_tax_modifier.get(self.location_type, 1.0)
        final_tax_rate = (base_tax * rank_multiplier.get(player_rank, 1) * location_modifier) - building_discount
        return max(0.01, min(0.25, final_tax_rate))  # Keep between 1% and 25%

    def add_temporary_ban(self, commodity, duration):
        """Add a temporary trade ban for a commodity"""
        if commodity not in self.banned_commodities:
            self.banned_commodities.append(commodity)
            self.ban_duration[commodity] = duration

    def build_building(self, building_name):
        """Build a building and apply its effects.
        Returns: cost_multiplier for the building"""
        if not self.can_build(building_name.lower()):
            return 0  # Return 0 to indicate building not allowed
            
        cost_multiplier = self.buildings.count(building_name) + 1
        
        # Apply building effects
        building_data = self.game.building_data.get(building_name, {})
        
        for effect_str in building_data.get("effects", "").split(','):
            if not effect_str:
                continue
            effect_name, effect_value = effect_str.split(":")
            
            if effect_name == 'mining_efficiency':
                self.exogeology = min(100, self.exogeology + int(float(effect_value)))
            elif effect_name == 'agri_price':
                self.market['agri'] = max(1, int(self.market['agri'] * float(effect_value)))
            elif effect_name == 'tech_price':
                self.market['tech'] = max(1, int(self.market['tech'] * float(effect_value)))
            elif effect_name == 'stockmarket':
                self.stockmarket_base = True
                self.market['tech'] = max(1, self.market['tech'] - 10)
                self.market['agri'] = max(1, self.market['agri'] - 5)
            elif effect_name == "Halide Extraction Refinery":
                self.market['agri'] = max(1, self.market['agri'] * 0.8)
                self.market['salt'] = random.randint(100,150)
            elif effect_name == "Plasma Catalysis Refinery":
                self.market['tech'] = max(1, self.market['tech'] * 0.8)
                self.market['fuel'] = random.randint(150, 200)
            elif effect_name == "Elemental Fusion Refinery":
                self.market['tech'] = int(self.market['tech'] * 1.3)
                self.market['agri'] = int(self.market['agri'] * 1.3)
        
        # Add building to location's buildings list
        self.buildings.append(building_name)
        
        return cost_multiplier

    def get_capabilities(self):
        """Get capabilities for this location type"""
        return LocationCapabilities.CAPABILITIES.get(self.location_type, {})

    def get_term(self, term_type, use_variant=False):
        """Get contextual terminology for this location"""
        return LocationTerminology.get_term(self.location_type, term_type, use_variant)

    def can_trade(self, commodity):
        """Check if this location can trade a specific commodity"""
        # First, check if commodity is banned - this should be the first check
        if commodity in self.banned_commodities:
            return False

        # Always allow standard commodities
        if commodity in self.get_capabilities().get("can_trade", []):
            return True

        # Allow salt/fuel if corresponding refinery exists
        if commodity == 'salt' and any(b == "Halide Extraction Refinery" for b in self.buildings):
            return True
        
        if commodity == 'fuel' and any(b == "Plasma Catalysis Refinery" for b in self.buildings):
            return True
        
        # Allow trading all commodities if Combined Refinery exists
        if any(b == "Elemental Fusion Refinery" for b in self.buildings):
            return True

        return False

    def can_build(self, building_type):
        """Check if this location can build a specific building with debug info"""
        capabilities = self.get_capabilities()
        can_build_list = capabilities.get("can_build", [])
        
        # Convert building type to match capability format
        building_type = building_type.lower()
        
        # Remove any facility/paradise/authority suffix for comparison
        building_base = building_type.split()[0]
        
        # Return whether the base building type is in capabilities
        return building_base in can_build_list

    def can_mine(self, resource_type):
        """Check if this location can mine a specific resource"""
        return resource_type in self.get_capabilities().get("can_mine", [])

    def get_base_exogeology(self):
        """Get base mining efficiency with randomized ranges per location type"""
        ranges = {
            "Planet": (35, 65),
            "AsteroidBase": (68, 78),
            "DeepSpaceOutpost": (42, 52),
            "ResearchColony": (16, 36)
        }
        base_range = ranges.get(self.location_type, (50, 60))
        return random.randint(*base_range)

    def get_research_multiplier(self):
        """Get research point multiplier for this location type"""
        return self.get_capabilities().get("research_multiplier", 1.0) 