# core/gameplay.py
import os
import random
import time
import shutil
from core.utils import display_logo, logo_data, print_centered_text
from core.ship import Ship
from ui.text_ui import TextUI

# core/gameplay.py

def play_turn(game):
    # Check if beacon activated
    if hasattr(game, 'active_beacon') and game.active_beacon:
        # if game.handle_use_item(): # old code
        #    delattr(game, 'active_beacon')
        beacon_type = game.ship.item_data[game.active_beacon].get("beacon_type")
        if beacon_type:
            if beacon_type == "mcguffin":
               game.handle_use_item()
            else:
                # Trigger combat from beacon, but don't remove it, it is removed during travel
                enemy_id = game.game_events.handle_beacon_encounter(beacon_type)
                if enemy_id:
                    # Set the attribute for the game to handle in travel
                    setattr(game, 'active_beacon_encounter', enemy_id)

    game.display_turn_info()
    game.check_story_requirements()  # check if any new story beats, quests and chapters have been triggered
    game.check_location_events("turn_end")
    game.location_manager.check_location_unlocks()  # check for unlocks, moved from game to location manager
    game.story_manager.check_milestone_progress()  # re-added milestone checks here
    game.character_system.check_character_triggers()
    game.story_manager.check_chapter_progress()
    
    #check quests and contracts and update before turn is incremented
    game.quest_system.check_active_quests()
    game.contract_manager.update_contract_progress({
            "action": "",
            "commodity": "",
            "amount": 0,
            "location": game.current_location.name,
            "turn": game.turn
        })

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
    
    # Get location commands - IMPORTANT fix here
    location_commands = game.current_location.commands
    for cmd, shortcut in location_commands["available"]:
        if cmd == 'port' or shortcut == 'p':
            port_is_available = True
            game.port_system.update_passengers(game.current_location.name)

   
    # # Call random event before the player makes an action #Removed
    # game.random_event() #Removed

    valid_actions = []
    for cmd, shortcut in location_commands["available"]:
        valid_actions.extend([cmd, shortcut])
    
    # Add global commands
    valid_actions.extend(['quit', 'q', 'resign', 'rs', 'version', 'v'])
    valid_actions.extend(['log', 'l'])  # Add but don't show in command hints
    valid_actions.extend(['theme', '/'])  # Add theme switch
    valid_actions.extend(['use', 'us']) # Add use item command
    
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
                    game.ui.display_simple_message("Ship repaired.")
                else:
                    game.ui.display_simple_message(
                        f"Not enough money to repair. Cost: {game.format_money(cost)}"
                    )
            else:
                game.ui.display_simple_message("Ship doesn't need repairs.")
    elif action in ['mine', 'm']:
        game.display_mining_status()

    elif action in ['buy', 'b']:
        item = game.validate_input("Choose item (tech/agri/salt/fuel): ", 
                                ['tech', 'agri', 'salt', 'fuel'])
        if item is None:
            return

        if not game.current_location.can_trade(item):
            game.ui.display_simple_message(f"Trading of {item} is banned on this planet!")
            return

        if item in ['salt', 'fuel']:
            has_platform = any(p['type'] == item for p in game.current_location.mining_platforms)
            if not has_platform:
                game.ui.display_simple_message(f"No mining platform for {item} on this planet.")
                return

        quantity = game.validate_quantity_input("Enter quantity (max/m, half/h): ")
        if quantity is None:
            return

        price = game.current_location.market[item]
        if price <= 0:
            game.ui.display_simple_message(f"Cannot calculate amount: {item} has no valid price.")
            return
            
        #tax_rate = game.current_location.calculate_tax_rate(game.rank, price)
        tax_rate = game.current_location.calculate_tax_rate(game.rank, price, game)
        price_with_tax = price * (1 + tax_rate)
        max_quantity = int(game.ship.money / price_with_tax)

        if quantity == 'max':
            quantity = max_quantity
        elif quantity == 'half':
            quantity = (max_quantity + 1) // 2  # Round up division

        if game.ship.buy(item, quantity, game.current_location.market[item], 
                        game.current_location, game.rank):
            game.ui.display_simple_message(f"Bought {game.format_money(quantity)} {item}.")
            game.captain.record_activity("trades")
            game.handle_trade('buy', item, quantity, price)

    elif action in ['sell', 's']:
        item = game.validate_input("Choose item (tech/agri/salt/fuel): ", 
                                ['tech', 'agri', 'salt', 'fuel'])
        if item is None:
            return

        if not game.current_location.can_trade(item):
            game.ui.display_simple_message(f"Trading of {item} is banned on this planet!")
            return

        quantity = game.validate_quantity_input("Enter quantity to sell (max/m, half/h): ")
        if quantity is None:
            return
        
        # Get price *before* checking quantity and making sale
        price = game.current_location.market[item]
        if price <= 0:
            game.ui.display_simple_message(f"Cannot calculate amount: {item} has no valid price.")
            return

        if quantity == 'max':
            quantity = game.ship.cargo[item]
        if quantity == 'half':
            quantity = (game.ship.cargo[item]) // 2

        if game.ship.sell(item, quantity, game.current_location.market[item], 
                        game.current_location, game.rank):
            game.ui.display_simple_message(f"Sold {game.format_money(quantity)} {item}.")
            game.captain.record_activity("trades")
            game.handle_trade('sell', item, quantity, price)

    elif action in ['upgrade', 'u']:
        game.handle_upgrade()

    elif action in ['travel', 't']:
        game.handle_travel()

    elif action in ['info', 'i']:
        game.display_location_info()

    elif action in ['build', 'bl']:
        if not game.handle_building_construction():
           return #skip if canceled.

    elif action in ['cantina', 'c']:
         game.cantina.handle_cantina_menu()

    elif action in ['shop', 'sh']:
        game.shop.handle_shop_menu()

    elif action in ['action', 'a']:
        game.handle_actions()

    elif action in ['port', 'p']:
        if port_is_available:
            game.port_system.handle_port_menu()
            game.port_system.update_passenger_satisfaction()
        else:
            game.ui.display_simple_message("No port available at this location.")
            
        if port_is_available and hasattr(game.port_system, 'waiting_passengers'):
                location = game.current_location.name
                if location in game.port_system.waiting_passengers:
                     game.captain.record_activity("passengers", len(game.port_system.waiting_passengers[location]))

    elif action in ['log', 'l']:
        game.story_manager.display_story_progress()
        return    # Return after showing log to avoid counting it as a turn

    elif action in ['version', 'v']:
        display_logo(logo_data, centered=True)
        print_centered_text("")
        print_centered_text("Created by Dan Sandner")
        print_centered_text("v0.1.0-a, ©2025")

        time.sleep(3)
        return    
    
    elif action in ['theme', '/']:
        game.handle_theme_change()

    # Handle quit and resign commands
    elif action in ['quit', 'q']:
        if game.validate_input("Are you sure you want to quit? (yes/no): ", ['yes', 'no']) == 'yes':
            game.ui.display_simple_message("Thanks for playing!")
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

        # Call turn end methods from game.py
        game.end_turn_actions()
        # NEW CODE: run events AFTER turn ends
        game.random_event() #New Call

        return # Exit play_turn() and start new loop
    
    elif action in ['use', 'us']:
        game.handle_use_item()
    else:
        game.ui.display_simple_message("Invalid action.")
    
    # # Call random event here AFTER the player makes an action  #Old Commented
    # game.random_event() # Old Commented