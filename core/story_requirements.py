# core/story_requirements.py
class MilestoneRequirements:
    """Enhanced requirements checking for story milestones"""
    
    @staticmethod
    def check_requirements(requirements, game):
        """Check if all requirements are met"""
        for req_type, req_value in requirements.items():
            if not MilestoneRequirements._check_single_requirement(req_type, req_value, game):
                return False
        return True

    @staticmethod
    def _check_single_requirement(req_type, req_value, game):
        """Check a single requirement"""
        check_methods = {
            "plot_points": lambda game, val: game.story_manager.plot_points >= val,
            "money": lambda game, val: game.ship.money >= val,
            "research_points": lambda game, val: game.ship.research_points >= val,
            "combat_victories": MilestoneRequirements._check_combat_victories,
            "combat_rating": lambda game, val: (game.ship.attack + game.ship.defense + game.ship.speed) >= val,
            "trades_completed": lambda game, val: game.trades_completed >= val,
            "trade_profit": lambda game, val: sum(game.ship.trade_profits.values()) >= val,
            "trade_specific": lambda game, val: game.ship.trade_profits.get(val[0], 0) >= val[1],
            "passengers_transported": lambda game, val: game.reputation_manager.total_passengers >= val,
            "passenger_reputation": lambda game, val: game.ship.passenger_reputation >= val,
            "passenger_class": lambda game, val: game.reputation_manager.class_transports.get(val[0], 0) >= val[1],
            "locations_discovered": MilestoneRequirements._check_locations_discovered,
            "buildings_built": MilestoneRequirements._check_buildings_built,
            "mining_platforms": MilestoneRequirements._check_mining_platforms,
            "quests_completed": MilestoneRequirements._check_quests_completed,
            "research_unlocked": lambda game, val: all(tech in game.research.unlocked_options for tech in val),
            "faction_reputation": lambda game, val: game.character_system.get_reputation(val[0]) >= val[1],
            "items": lambda game, val: all(item in game.ship.items for item in val),
            "chapters_completed": lambda game, val: all(chapter in game.story_manager.completed_chapters for chapter in val),
            "milestones_completed": lambda game, val: all(milestone in game.story_manager.completed_story_beats for milestone in val),
            "story_states": lambda game, val: all(game.story_manager.story_states.get(state, False) for state in val),
            "custom_condition": lambda game, val: val(game)
        }

        check_method = check_methods.get(req_type)
        if check_method:
            return check_method(game, req_value)
        else:
            print(f"Warning: Unknown requirement type {req_type}")
            return False

    @staticmethod
    def _check_combat_victories(game, req_value):
        """Check combat victories with specific type and total"""
        if isinstance(req_value, dict):
            # Check specific enemy types
            for enemy_type, amount in req_value.items():
                if game.ship.combat_victories.get(enemy_type, 0) < amount:
                    return False
            return True
        else:
            # Check total victories
            return game.ship.combat_victories['total'] >= req_value

    @staticmethod
    def _check_locations_discovered(game, req_value):
        """Check discovered locations with specific type and total"""
        if isinstance(req_value, dict):
            # Check specific location types
            for loc_type, amount in req_value.items():
                discovered = len([loc for loc in game.discovered_locations 
                                if loc.location_type == loc_type])
                if discovered < amount:
                    return False
            return True
        else:
            # Check total discoveries
            return len(game.discovered_locations) >= req_value

    @staticmethod
    def _check_buildings_built(game, req_value):
        """Check buildings built with specific type and total"""
        if isinstance(req_value, dict):
            # Check specific building types
            for building_type, amount in req_value.items():
                total_built = sum(1 for loc in game.locations 
                                for building in loc.buildings 
                                if building == building_type)
                if total_built < amount:
                    return False
            return True
        else:
            # Check total buildings
            return sum(len(loc.buildings) for loc in game.locations) >= req_value

    @staticmethod
    def _check_mining_platforms(game, req_value):
        """Check mining platforms with specific type and total"""
        if isinstance(req_value, dict):
            # Check specific resource types
            for resource_type, amount in req_value.items():
                total_platforms = sum(1 for loc in game.locations 
                                        for platform in loc.mining_platforms 
                                        if platform['type'] == resource_type)
                if total_platforms < amount:
                    return False
            return True
        else:
            # Check total platforms
            return sum(len(loc.mining_platforms) for loc in game.locations) >= req_value

    @staticmethod
    def _check_quests_completed(game, req_value):
        """Check completed quests with specific type and total"""
        if isinstance(req_value, dict):
            # Check specific quest types
            for quest_type, amount in req_value.items():
                completed = len([q for q in game.quest_system.completed_quests 
                                if q.quest_type == quest_type])
                if completed < amount:
                    return False
            return True
        else:
            # Check total completed quests
            return len(game.quest_system.completed_quests) >= req_value