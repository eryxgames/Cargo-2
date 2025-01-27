# core/shop.py
import random
import csv
import os
import time

class Shop:
    def __init__(self, game):
         self.game = game
         self.item_data = self.load_item_data()
         # Track items for current turn
         self.current_turn_items = []
         self.sold_items = set()
         self.current_turn = 0
         self.current_offerings = []  # Keep this
        
         # Track discounts and special offers
         self.current_discounts = {}
         self.special_offers = {}

    def load_item_data(self):
        """Load item data from items.csv"""
        item_data = {}
        try:
            with open("data/items.csv", 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    item_data[row['item_id']] = row
            return item_data
        except FileNotFoundError:
            print("Error: items.csv not found. Using default items.")
            return {}
        except Exception as e:
            print(f"Error loading items from CSV: {e}")
            return {}

    def handle_shop_menu(self):
        """Enhanced shop interface with persistent sold items"""
        self.game.display_simple_message("Welcome to the Shop!", 1)

        # Display current money and location info
        status_content = [
            [f"Credits: {self.game.format_money(self.game.ship.money)}"],
            [f"Tech Level: {self.game.current_location.tech_level}"]
        ]
        print(self.game.create_box(status_content, 'single'))

        # Display current inventory
        inventory_content = [["Your Items"]]
        if self.game.ship.items:
            for item, count in self.game.ship.items.items():
                inventory_content.append([f"{item}: {count}"])
        else:
            inventory_content.append(["No items"])
        print(self.game.create_box(inventory_content, 'single'))

        # Get available items for this location
        if not hasattr(self, 'current_turn_items') or not self.current_turn_items:  # Changed condition
            # Only get new items if we haven't already for this turn
            self.current_turn_items = self.get_available_items(
                location=self.game.current_location,
                plot_points=self.game.story_manager.plot_points
            )

        # Get terminal width
        try:
            term_width = os.get_terminal_size().columns
        except OSError:
            term_width = 80

        # Adjust display based on terminal width
        if term_width < 80:  # Narrow display
            shop_content = [["Item", "Price", "Description/Status"]]
            
            for item_name, item_data in self.current_turn_items:
                if self.is_item_sold(item_name):
                    # Show SOLD in place of description
                    description = "SOLD"
                else:
                    description = item_data["description"]
                    if len(description) > 30:
                        description = description[:27] + "..."
                    
                shop_content.append([
                    item_name.title(),
                    self.game.format_money(self.get_item_price(item_name)),
                    description
                ])
        else:  # Wide display
            shop_content = [["Item", "¤", "Description", ""]]
            
            for item_name, item_data in self.current_turn_items:
                status = "Avail"
                description = self.get_item_description(item_name)
                
                if self.is_item_sold(item_name):
                    status = "SOLD"
                    
                if len(description) > 40:
                    description = description[:37] + "..."
                    
                shop_content.append([
                    item_name.title(),
                    self.game.format_money(self.get_item_price(item_name)),
                    description,
                    status
                ])
        
        print(self.game.create_box(shop_content, 'double'))

        # Only show unsold items in options
        available_items_names = [
            item[0] for item in self.current_turn_items 
            if not self.is_item_sold(item[0])
        ]

        if not available_items_names:
            self.game.display_simple_message("All items are sold out!")
            return

        item_choice = self.game.validate_input(
            "Choose item to buy (or 'none' to exit): ",
            available_items_names + ['none']
        )
        
        if item_choice == 'none':
            return

        for item_name, item_data in self.current_turn_items:
            if item_choice == item_name:
                price = self.get_item_price(item_name)
                if self.game.ship.money >= price:
                    self.game.ship.money -= price
                    self.game.ship.acquire_item(item_name)
                    self.mark_item_sold(item_name)
                    
                    self.game.display_simple_message([
                        f"You bought a {item_name}!",
                        f"Effect: {self.get_item_description(item_name)}",
                        f"Remaining credits: {self.game.format_money(self.game.ship.money)}"
                    ])
                else:
                    missing = price - self.game.ship.money
                    self.game.display_simple_message([
                        "Not enough money to buy this item.",
                        f"Price: {self.game.format_money(price)}",
                        f"Your credits: {self.game.format_money(self.game.ship.money)}",
                        f"Missing: {self.game.format_money(missing)}"
                    ])
                return

        time.sleep(1)

    def get_available_items(self, location, plot_points):
        """Get available items based on location and plot points"""
        available_pool = []
        
        # Start with base equipment pool, filtering by requirements
        for item_name, item_data in self.item_data.items():
              if (
                item_data.get('type') == 'equipment' and 
                location.tech_level >= int(item_data.get('tech_required', 0)) and
                plot_points >= int(item_data.get('plot_required', 0))
            ):
                available_pool.append((item_name, item_data))
            
        # Add location-specific items if applicable, also filtering
        location_type = location.location_type
        for item_name, item_data in self.item_data.items():
            if (
                location_type in item_data.get('location_type', '').split(',') and
                location.tech_level >= int(item_data.get('tech_required', 0)) and
                plot_points >= int(item_data.get('plot_required', 0))
            ):
                  available_pool.append((item_name, item_data))
            
        # Select random items from filtered pool
        if available_pool:
            selected_items = random.sample(available_pool, min(3, len(available_pool)))
            self.current_offerings = [item[0] for item in selected_items]
            return selected_items
        
        return []
    
    def get_item_requirements(self, item_name, location_type=None):
        """Get tech level and plot point requirements for an item"""
        item_data = self.item_data.get(item_name, {})
        
        if item_data:
            return {
                "tech_required": int(item_data.get("tech_required", 0)),
                "plot_required": int(item_data.get("plot_required", 0))
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
            item_data = self.item_data.get(item_name,{})
            if item_data:
                if (location.tech_level < int(item_data.get("tech_required", 0)) or
                    self.game.story_manager.plot_points < int(item_data.get("plot_required", 0))):
                    return False
                    
        return True

    def get_item_price(self, item_name):
        """Get the current price of an item, including any discounts"""
        item_data = self.item_data.get(item_name)
        if not item_data:
            return None
        
        base_price = int(item_data.get('price', 0))
            
        # Apply any active discounts
        discount = self.current_discounts.get(item_name, 0)
        final_price = base_price * (1 - discount)
        
        return int(final_price)

    def get_item_description(self, item_name):
        """Get the description of an item"""
        item_data = self.item_data.get(item_name, {})
        return item_data.get('description', "No description available")

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