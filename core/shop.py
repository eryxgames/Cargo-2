# core/shop.py
import random
import json
import os
class Shop:
    def __init__(self):
        self.base_equipment = {
            "navcomp": {
                "price": 500,
                "description": "Navigation computer reveals all destinations",
                "tech_required": 1,
                "plot_required": 0
            },
            "scanner": {
                "price": 700,
                "description": "Basic scanner improves resource detection",
                "tech_required": 2,
                "plot_required": 0
            },
            "probe": {
                "price": 900,
                "description": "Deep space probe increases exploration success",
                "tech_required": 3,
                "plot_required": 10
            },
            "turrets": {
                "price": 1200,
                "description": "Defense turrets to automatically repel pirates",
                "tech_required": 4,
                "plot_required": 15
            },
            "shield": {
                "price": 1500,
                "description": "Energy shield reduces damage taken in combat",
                "tech_required": 5,
                "plot_required": 20
            },
            "patcher": {
                "price": 300,
                "description": "Hull patcher repairs minor combat damage",
                "tech_required": 1,
                "plot_required": 0
            },
            # Transport Equipment
            "cargo_extender": {
                "price": 5000,
                "description": "Increases cargo capacity by 20%",
                "tech_required": 3,
                "plot_required": 25
            },
            "containment_field": {
                "price": 8000,
                "description": "Specialized storage for salt/fuel (+30% capacity)",
                "tech_required": 4,
                "plot_required": 30
            },
            "auto_loader": {
                "price": 12000,
                "description": "Reduces loading/unloading time (-1 turn per trade)",
                "tech_required": 5,
                "plot_required": 35
            },
            # Advanced Transport Equipment
            "quantum_compressor": {
                "price": 20000,
                "description": "Advanced compression (+50% capacity for all cargo)",
                "tech_required": 6,
                "plot_required": 50
            },
            "stasis_vault": {
                "price": 25000,
                "description": "Perfect resource preservation (+75% capacity for special resources)",
                "tech_required": 7,
                "plot_required": 60
            },
            "temporal_accelerator": {
                "price": 30000,
                "description": "Time dilation for faster delivery (-2 turns per trade)",
                "tech_required": 8,
                "plot_required": 75
            }
        }

        # Location-specific items with requirements
        self.location_equipment = {
            "AsteroidBase": {
                "mining_laser": {
                    "price": 2000,
                    "description": "Improves mining efficiency and defense",
                    "tech_required": 3,
                    "plot_required": 15
                },  
                "cargo_scanner": {
                    "price": 1800,
                    "description": "Detects valuable mineral deposits",
                    "tech_required": 4,
                    "plot_required": 20
                },
                "shield_booster": {
                    "price": 2500,
                    "description": "Offers extra protection in asteroid fields",
                    "tech_required": 5,
                    "plot_required": 25
                },
                "mining_compressor": {
                    "price": 15000,
                    "description": "Specialized for asteroid mining (+40% capacity for mined resources)",
                    "tech_required": 6,
                    "plot_required": 40
                }
            },
            "DeepSpaceOutpost": {
                "advanced_radar": {
                    "price": 2200,
                    "description": "Early warning system for threats",
                    "tech_required": 4,
                    "plot_required": 30
                },
                "combat_drone": {
                    "price": 3000,
                    "description": "Assists in space battles",
                    "tech_required": 5,
                    "plot_required": 35
                },
                "repair_bot": {
                    "price": 2800,
                    "description": "Automatic repairs during travel",
                    "tech_required": 6,
                    "plot_required": 40
                },
                "emergency_warp": {
                    "price": 18000,
                    "description": "Emergency escape system (50% chance to avoid combat)",
                    "tech_required": 7,
                    "plot_required": 50
                }
            },
            "ResearchColony": {
                "research_module": {
                    "price": 2500,
                    "description": "Improves research point gains",
                    "tech_required": 5,
                    "plot_required": 40
                },
                "data_analyzer": {
                    "price": 2800,
                    "description": "Better research success rates",
                    "tech_required": 6,
                    "plot_required": 45
                },
                "quantum_scanner": {
                    "price": 3500,
                    "description": "Reveals anomalies and secrets",
                    "tech_required": 7,
                    "plot_required": 50
                },
                "containment_optimizer": {
                    "price": 22000,
                    "description": "Smart cargo optimization (+25% capacity and -1 turn per trade)",
                    "tech_required": 8,
                    "plot_required": 60
                }
            }
        }

        # Add specialized location-specific transport equipment
        self.location_equipment["AsteroidBase"]["mining_compressor"] = {
            "price": 15000,
            "description": "Specialized for asteroid mining (+40% capacity for mined resources)"
        }
        
        self.location_equipment["DeepSpaceOutpost"]["emergency_warp"] = {
            "price": 18000,
            "description": "Emergency escape system (50% chance to avoid combat during transport)"
        }
        
        self.location_equipment["ResearchColony"]["containment_optimizer"] = {
            "price": 22000,
            "description": "Smart cargo optimization (+25% capacity and -1 turn per trade)"
        }
        
        # Track sold items per turn
        # Track items for current turn
        self.current_turn_items = []
        self.sold_items = set()
        self.current_turn = 0
        self.current_offerings = []  # Keep this
        
        # Track discounts and special offers
        self.current_discounts = {}
        self.special_offers = {}

    def get_available_items(self, location, plot_points):
        """Get available items based on location and plot points"""
        available_pool = []
        
        # Start with base equipment pool, filtering by requirements
        for name, data in self.base_equipment.items():
            if (location.tech_level >= data["tech_required"] and 
                plot_points >= data["plot_required"]):
                available_pool.append((name, data))
        
        # Add location-specific items if applicable, also filtering
        location_type = location.location_type
        if location_type in self.location_equipment:
            for name, data in self.location_equipment[location_type].items():
                if (location.tech_level >= data["tech_required"] and 
                    plot_points >= data["plot_required"]):
                    available_pool.append((name, data))
            
        # Select random items from filtered pool
        if available_pool:
            selected_items = random.sample(available_pool, min(2, len(available_pool)))
            self.current_offerings = [item[0] for item in selected_items]
            return selected_items
        
        return []
    
    def get_item_requirements(self, item_name, location_type=None):
        """Get tech level and plot point requirements for an item"""
        if item_name in self.base_equipment:
            data = self.base_equipment[item_name]
            return {
                "tech_required": data["tech_required"],
                "plot_required": data["plot_required"]
            }
        elif location_type and location_type in self.location_equipment:
            if item_name in self.location_equipment[location_type]:
                data = self.location_equipment[location_type][item_name]
                return {
                    "tech_required": data["tech_required"],
                    "plot_required": data["plot_required"]
                }
        return None    

    def mark_item_sold(self, item_name):
        """Mark an item as sold for this turn"""
        self.sold_items.add(item_name)
        if item_name in self.current_offerings:
            self.current_offerings.remove(item_name)

    def is_item_available(self, item_name, location=None):
        """Check if an item is available for purchase"""
        # First check if item is sold
        if item_name in self.sold_items:
            return False
            
        # Then check if it's in current offerings
        if item_name not in self.current_offerings:
            return False
            
        # If location provided, check tech and plot requirements
        if location:
            item_data = None
            if item_name in self.base_equipment:
                item_data = self.base_equipment[item_name]
            elif location.location_type in self.location_equipment:
                if item_name in self.location_equipment[location.location_type]:
                    item_data = self.location_equipment[location.location_type][item_name]
            
            if item_data:
                if (location.tech_level < item_data["tech_required"] or
                    location.story_manager.plot_points < item_data["plot_required"]):
                    return False
                    
        return True

    def get_item_price(self, item_name, location_type=None):
        """Get the current price of an item, including any discounts"""
        base_price = None
        
        # Check base equipment
        if item_name in self.base_equipment:
            base_price = self.base_equipment[item_name]["price"]
        
        # Check location-specific equipment
        elif location_type and location_type in self.location_equipment:
            if item_name in self.location_equipment[location_type]:
                base_price = self.location_equipment[location_type][item_name]["price"]
        
        if base_price is None:
            return None
            
        # Apply any active discounts
        discount = self.current_discounts.get(item_name, 0)
        final_price = base_price * (1 - discount)
        
        return int(final_price)

    def get_item_description(self, item_name, location_type=None):
        """Get the description of an item"""
        # Check base equipment
        if item_name in self.base_equipment:
            return self.base_equipment[item_name]["description"]
        
        # Check location-specific equipment
        if location_type and location_type in self.location_equipment:
            if item_name in self.location_equipment[location_type]:
                return self.location_equipment[location_type][item_name]["description"]
        
        return "No description available"

    def add_special_offer(self, item_name, discount):
        """Add a special offer with a discount percentage (0-1)"""
        self.current_discounts[item_name] = min(1, max(0, discount))

    def remove_special_offer(self, item_name):
        """Remove a special offer"""
        if item_name in self.current_discounts:
            del self.current_discounts[item_name]

    def clear_special_offers(self):
        """Clear all special offers"""
        self.current_discounts.clear()

    def is_item_sold(self, item_name):
        """Check if an item has been sold this turn"""
        return item_name in self.sold_items

    def reset_turn(self):
        """Reset shop state for new turn"""
        self.sold_items.clear()
        self.current_offerings.clear()
        self.clear_special_offers()
        self.current_turn_items = []