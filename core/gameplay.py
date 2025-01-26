# core/gameplay.py
import os
import random
import time
import shutil
from core.utils import display_logo, print_centered_text
from core.ship import Ship
from ui.text_ui import TextUI

def play_turn(game):
    game.display_turn_info()
    game.check_location_unlocks()
    game.check_milestone_triggers()
    game.character_system.check_character_triggers()
    game.story_manager.check_milestone_progress()
    game.story_manager.check_chapter_progress()
    game.force_check_chapter_progression()
    game.quest_system.check_active_quests()
    # Get location commands
    location_commands = game.current_location.commands

    game.character_manager.update()

    game.infestation_manager.check_global_infestations()
    if hasattr(game.ship, 'active_infestations'):
        game.infestation_manager.update_ship_infestations()

    # Update synthetic events (if they exist)
    if hasattr(game, 'synthetic_events'):
        game.synthetic_events.update()
    
    # For each location, check building counts
    for location in game.locations:
        neuroguild_count = location.buildings.count("Neuroengineering Guild")
        agrobot_count = location.buildings.count("Agrobot Assembly Line")
        
        if neuroguild_count >= 4 and random.random() < 0.2:
            game.synthetic_events.start_uprising("Neurodroid", location)
        if agrobot_count >= 4 and random.random() < 0.2:
            game.synthetic_events.start_uprising("Agrobot", location)
    
    # Update port system if port command is available
    port_is_available = False
    for cmd, shortcut in location_commands["available"]:
        if cmd == 'port' or shortcut == 'p':
            port_is_available = True
            game.port_system.update_passengers(game.current_location.name)
    
    # Create list of valid actions
    valid_actions = []
    for cmd, shortcut in location_commands["available"]:
        valid_actions.extend([cmd, shortcut])
    
    # Add global commands
    valid_actions.extend(['quit', 'q', 'resign', 'rs', 'version', 'v'])
    valid_actions.extend(['log', 'l'])  # Add but don't show in command hints

    action = game.validate_input("Choose action: ", valid_actions)

    # Handle cancelled command
    if action is None:
        return
                    
    # Handle research/repair based on location type
    elif action in ['research', 'r']:
        if game.current_location.location_type == "ResearchColony":
            game.handle_research_options()
        elif action == 'r':  # Only handle repair if 'r' and not at Research Colony
            if game.ship.damage > 0:
                cost = game.ship.damage * 10
                if game.ship.repair(cost):
                    game.display_simple_message("Ship repaired.")
                else:
                    game.display_simple_message(
                        f"Not enough money to repair. Cost: {game.format_money(cost)}"
                    )
            else:
                game.display_simple_message("Ship doesn't need repairs.")            

    elif action in ['buy', 'b']:
        item = game.validate_input("Choose item (tech/agri/salt/fuel): ", 
                                ['tech', 'agri', 'salt', 'fuel'])
        if item is None:
            return

        if not game.current_location.can_trade(item):
            game.display_simple_message(f"Trading of {item} is banned on this planet!")
            return

        if item in ['salt', 'fuel']:
            has_platform = any(p['type'] == item for p in game.current_location.mining_platforms)
            if not has_platform:
                game.display_simple_message(f"No mining platform for {item} on this planet.")
                return

        quantity = game.validate_quantity_input("Enter quantity (max/m, half/h): ")
        if quantity is None:
            return

        price = game.current_location.market[item]
        if price <= 0:
            game.display_simple_message(f"Cannot calculate amount: {item} has no valid price.")
            return
            
        tax_rate = game.current_location.calculate_tax_rate(game.rank, price)
        price_with_tax = price * (1 + tax_rate)
        max_quantity = int(game.ship.money / price_with_tax)

        if quantity == 'max':
            quantity = max_quantity
        elif quantity == 'half':
            quantity = (max_quantity + 1) // 2  # Round up division

        if game.ship.buy(item, quantity, game.current_location.market[item], 
                        game.current_location, game.rank):
            game.display_simple_message(f"Bought {game.format_money(quantity)} {item}.")
            game.handle_trade('buy', item, quantity, price)

    elif action in ['sell', 's']:
        item = game.validate_input("Choose item (tech/agri/salt/fuel): ", 
                                ['tech', 'agri', 'salt', 'fuel'])
        if item is None:
            return

        if not game.current_location.can_trade(item):
            game.display_simple_message(f"Trading of {item} is banned on this planet!")
            return

        quantity = game.validate_quantity_input("Enter quantity to sell (max/m, half/h): ")
        if quantity is None:
            return

        if quantity == 'max':
            quantity = game.ship.cargo[item]
        if quantity == 'half':
            quantity = (game.ship.cargo[item]) // 2

        if game.ship.sell(item, quantity, game.current_location.market[item], 
                        game.current_location, game.rank):
            game.display_simple_message(f"Sold {game.format_money(quantity)} {item}.")
            game.handle_trade('sell', item, quantity, price)

    elif action in ['upgrade', 'u']:
        property_name = game.validate_input(
            "Choose property to upgrade (attack/defense/speed): ", 
            ['attack', 'defense', 'speed']
        )
        if property_name is None:
            return

        cost = game.ship.upgrade_costs[property_name]
        if game.ship.upgrade(property_name, cost):
            game.display_simple_message(f"Upgraded {property_name}.")
            game.ship.upgrade_costs[property_name] = int(cost * 1.5)

    elif action in ['travel', 't']:
        game.handle_travel()

    elif action in ['info', 'i']:
        game.display_location_info()

    elif action in ['build', 'bl']:
        building_costs = {
            'stockmarket': 5000,
            'permaculture': 3000,
            'organic': 4000,
            'agrobot': 5000,
            'nanotech': 6000,
            'neuroengineering': 7000,
            'mining': 10000,
            'salt_refinery': 15000,
            'fuel_refinery': 15000,
            'combined_refinery': 25000
        }

        valid_options = [
            'stockmarket', 'sm',
            'permaculture', 'pc',
            'organic', 'oc',
            'agrobot', 'ab',
            'nanotech', 'nt',
            'neuroengineering', 'ne',
            'mining', 'm',
            'salt refinery', 'sr',
            'fuel refinery', 'fr',
            'combined refinery', 'cr'
        ]

        building_name = game.validate_input(
            "Choose building type: ",
            valid_options
        )
        
        if building_name is None:
            return

        game.handle_building_construction(building_name, building_costs)

    elif action in ['cantina', 'c']:
        game.visit_cantina()

    elif action in ['shop', 'sh']:
        game.visit_shop()

    elif action in ['action', 'a']:
        game.handle_actions()

    elif action in ['mine', 'm']:
        game.handle_mining()
        
    elif action in ['port', 'p']:
        if port_is_available:
            game.port_system.handle_port_menu()
            game.port_system.update_passenger_satisfaction()
        else:
            game.display_simple_message("No port available at this location.")

    elif action in ['log', 'l']:
        game.story_manager.display_story_progress()
        return    # Return after showing log to avoid counting it as a turn

    elif action in ['version', 'v']:
        display_logo(game.settings.get("logo_data", []), centered=True)
        print_centered_text("")
        print_centered_text("Created by Dan Sandner")
        print_centered_text("v1.0.2, ©2025")

        time.sleep(3)
        return    

    # Handle quit and resign commands
    elif action in ['quit', 'q']:
        if game.validate_input("Are you sure you want to quit? (yes/no): ", ['yes', 'no']) == 'yes':
            game.display_simple_message("Thanks for playing!")
            exit()
        return

    elif action in ['resign', 'rs']:
        if game.validate_input("Are you sure you want to resign? (yes/no): ", ['yes', 'no']) == 'yes':
            game.display_score()
            exit()
        return    

    elif action in ['end', 'e']:
        # Update passenger satisfaction at end of turn if port is available
        if port_is_available:
            game.port_system.update_passenger_satisfaction()
        game.turn += 1
        game.random_event()
        game.shop.reset_turn()  # Reset shop state at end of each turn 
        return

    else:
        game.display_simple_message("Invalid action.")