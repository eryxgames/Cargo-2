# core/story.py
import yaml
import os
import random
from core.utils import display_logo
from core.template import CharacterTemplate
from core.location_data import LocationTerminology
from core.quest import Quest
from core.utils import format_money
from core.story_requirements import MilestoneRequirements

class StoryMilestone:
    def __init__(self, milestone_id, title, description, requirements, rewards=None, unlocks=None, story_text=None, alternate_text=None):
        self.id = milestone_id
        self.title = title
        self.description = description
        self.requirements = requirements
        self.rewards = rewards or {}
        self.unlocks = unlocks or []  # List of unlock dictionaries
        self.story_text = story_text
        self.alternate_text = alternate_text
        self.completed = False
        self.completion_turn = None

    def check_completion(self, game):
        """Check if milestone requirements are met"""
        if self.completed:
            return True
        return MilestoneRequirements.check_requirements(self.requirements, game)

    def complete(self, game):
        """Complete milestone and handle unlocks"""
        if not self.completed:
            self.completed = True
            self.completion_turn = game.turn
            
            # Handle rewards
            if self.rewards:
                if "money" in self.rewards:
                    game.ship.money += self.rewards["money"]
                if "research_points" in self.rewards:
                    game.ship.research_points += self.rewards["research_points"]
                if "plot_points" in self.rewards:
                    game.story_manager.plot_points += self.rewards["plot_points"]
                if "items" in self.rewards:
                    for item in self.rewards["items"]:
                        game.ship.acquire_item(item)

            # Handle unlocks
            unlock_messages = []
            for unlock in self.unlocks:
                unlock_type = unlock.get("type")
                unlock_id = unlock.get("id")
                
                if unlock_type == "item":
                    game.ship.acquire_item(unlock_id)
                    unlock_messages.append(f"Unlocked item: {unlock_id}")
                    
                elif unlock_type == "location_type":
                    game.unlocked_location_types.add(unlock_id)
                    # Add hidden locations of this type to available locations
                    if unlock_id in game.hidden_locations:
                        game.locations.extend(game.hidden_locations[unlock_id])
                        unlock_messages.append(f"Unlocked new location type: {unlock_id}")
                        
                elif unlock_type == "specific_location":
                    # Search in hidden_locations
                    for loc_type, locations in game.hidden_locations.items():
                        for location in locations:
                            if location.name == unlock_id:
                                game.locations.append(location)
                                game.known_locations.append(location.name)
                                unlock_messages.append(f"Discovered location: {location.name}")
                                break
                    
                    # Search in chapter_locations
                    for chapter_num, chapter_locs in game.chapter_locations.items():
                        for loc_type, locations in chapter_locs.items():
                            for location in locations:
                                if location.name == unlock_id:
                                    game.locations.append(location)
                                    game.known_locations.append(location.name)
                                    unlock_messages.append(f"Discovered location: {location.name}")
                                    break

                elif unlock_type == "chapter_locations":
                    chapter_num = unlock.get("chapter")
                    if chapter_num in game.chapter_locations:
                        for loc_type, locations in game.chapter_locations[chapter_num].items():
                            game.locations.extend(locations)
                            for loc in locations:
                                game.known_locations.append(loc.name)
                        unlock_messages.append(f"Unlocked Chapter {chapter_num} locations!")

            # Display completion message with unlocks
            completion_message = [
                f"Milestone Completed: {self.title}!",
                self.description,
                "",
                "Rewards:"
            ]
            
            # Add rewards to message
            for reward_type, value in self.rewards.items():
                if reward_type == "money":
                    completion_message.append(f"• {game.format_money(value)} credits")
                elif reward_type == "plot_points":
                    completion_message.append(f"• {value} plot points")
                elif reward_type == "research_points":
                    completion_message.append(f"• {value} research points")
                elif reward_type == "items":
                    completion_message.append(f"• Items: {', '.join(value)}")

            # Add unlock messages
            if unlock_messages:
                completion_message.append("")
                completion_message.append("Unlocked:")
                for msg in unlock_messages:
                    completion_message.append(f"• {msg}")

            game.display_story_message(completion_message)

            # Display story text (if available)
            if self.story_text:
                game.display_story_message(game.word_wrap(self.story_text))
            elif self.alternate_text:
                game.display_story_message(game.word_wrap(self.alternate_text))

class StoryChapter:
    def __init__(self, chapter_id, title, description, requirements, milestones, next_chapters=None):
        self.id = chapter_id
        self.title = title
        self.description = description
        self.requirements = requirements
        self.milestones = {}  # Dictionary of milestone_id: StoryMilestone
        self.next_chapters = next_chapters or []  # List of possible next chapter IDs
        self.completed = False
        self.completion_turn = None
        
        # Initialize milestones
        for milestone_data in milestones:
            milestone = StoryMilestone(**milestone_data)
            self.milestones[milestone.id] = milestone

    def check_completion(self, game):
        """Check if chapter can be completed"""
        if self.completed:
            return True

        # First check chapter requirements
        for req_type, req_value in self.requirements.items():
            if not MilestoneRequirements._check_single_requirement(req_type, req_value, game):
                return False

        # Then check if all required milestones are completed
        return all(milestone.completed for milestone in self.milestones.values())

    def get_available_milestones(self, game):
        """Get list of currently available milestones"""
        return [m for m in self.milestones.values() 
                if not m.completed and m.check_completion(game)]

    def get_next_chapters(self, game):
        """Get list of possible next chapters based on current game state"""
        available_chapters = []
        for chapter_id in self.next_chapters:
            chapter = game.story_manager.chapters[chapter_id]
            if all(MilestoneRequirements._check_single_requirement(req_type, req_value, game) 
                for req_type, req_value in chapter.requirements.items()):
                available_chapters.append(chapter)
        return available_chapters
    
    def handle_chapter_unlocks(self, game):
        """Handle any unlocks when chapter completes"""
        if hasattr(self, 'unlocks') and self.unlocks:
            for unlock in self.unlocks:
                unlock_type = unlock.get("type")
                unlock_id = unlock.get("id")
                
                if unlock_type == "location_type":
                    game.unlock_location_type(unlock_id)
                elif unlock_type == "chapter_locations":
                    chapter_num = unlock.get("chapter")
                    if chapter_num in game.chapter_locations:
                        for locations in game.chapter_locations[chapter_num].values():
                            game.locations.extend(locations)
                            
class StoryManager:
    def __init__(self, game):
        self.game = game
        self.current_chapter = None
        self.completed_chapters = set()
        self.completed_story_beats = set()
        self.plot_points = 0
        self.story_states = {
            "pirate_threat": False,
            "alien_discovery": False,
            "trade_empire": False,
            "resource_empire": False,
            "ancient_mystery": False,
            "galactic_crisis": False
        }
        self.chapters = self.load_chapters()
        self.event_cooldowns = {}
        self.enabled_events = set()

    def load_chapters(self):
        """Load all chapters and milestones from data/story.yml"""
        try:
            with open("data/story.yml", 'r') as f:
                data = yaml.safe_load(f)
                chapters = {}
                for chapter_id, chapter_data in data.items():
                    chapters[chapter_id] = StoryChapter(chapter_id, **chapter_data)
                return chapters
        except FileNotFoundError:
            print("Error: story.yml not found. Using default story.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error loading story from YAML: {e}")
            return {}

    def get_chapter_number(self, chapter_string=None):
        """
        Extract numeric chapter number from chapter string.
        If no chapter string provided, uses current chapter.
        Returns: int chapter number
        """
        if chapter_string is None:
            chapter_string = self.current_chapter
        try:
            return int(''.join(filter(str.isdigit, chapter_string)))
        except (ValueError, TypeError):
            return 1  # Default to chapter 1 if conversion fails

    def number_to_roman(self, num):
        """Convert integer to Roman numeral with dot"""
        roman_map = {
            1: 'I.', 2: 'II.', 3: 'III.', 4: 'IV.', 5: 'V.', 
            6: 'VI.', 7: 'VII.', 8: 'VIII.', 9: 'IX.', 10: 'X.',
            11: 'XI.', 12: 'XII.', 13: 'XIII.', 14: 'XIV.', 15: 'XV.',
            16: 'XVI.', 17: 'XVII.', 18: 'XVIII.', 19: 'XIX.', 20: 'XX.',
            21: 'XXI.', 22: 'XXII.', 23: 'XXIII.', 24: 'XXIV.', 25: 'XXV.',
            26: 'XXVI.', 27: 'XXVII.', 28: 'XXVIII.', 29: 'XXIX.', 30: 'XXX.'
        }
        
        return roman_map.get(num, str(num))

    def get_chapter_number_roman(self, chapter_string=None):
        """Get chapter number as Roman numeral"""
        number = self.get_chapter_number(chapter_string)
        return self.number_to_roman(number)

    def start_game(self):
        """Initialize story at game start"""
        self.current_chapter = "ch1"  # Store the ID string instead of the chapter object
        first_chapter = self.chapters["ch1"]
        
        self.game.display_story_message([
            f"Chapter I.: {first_chapter.title}",
            first_chapter.description,
            "",
            "Your journey begins..."
        ])

    def is_story_completed(self):
        """Check if the story has reached an ending"""
        if not self.current_chapter:
            return False
        current_chapter_obj = self.chapters[self.current_chapter]
        return (not current_chapter_obj.next_chapters and 
                current_chapter_obj.completed)

    def check_milestone_progress(self):
        """Check for milestone completions in current chapter"""
        if self.current_chapter:
            current_chapter_obj = self.chapters[self.current_chapter]
            available_milestones = current_chapter_obj.get_available_milestones(self.game)
            for milestone in available_milestones:
                if milestone.check_completion(self.game):
                    milestone.complete(self.game)
                    self.completed_story_beats.add(milestone.id)

    def get_current_objectives(self):
        """Get current chapter objectives"""
        if self.current_chapter:
            chapter_obj = self.chapters[self.current_chapter]
            return [(m.title, m.completed) for m in chapter_obj.milestones.values()]
        return []

    def check_chapter_progress(self):
        """Enhanced chapter progression checking"""
        if not self.current_chapter:
            return

        current_chapter_obj = self.chapters[self.current_chapter]
        
        # Check current chapter's requirements
        current_chapter_requirements_met = True
        if current_chapter_obj.requirements:
            for req_type, req_value in current_chapter_obj.requirements.items():
                if not MilestoneRequirements._check_single_requirement(req_type, req_value, self.game):
                    current_chapter_requirements_met = False
                    print(f"Current Chapter Requirement Not Met: {req_type}")

        # Check milestone completions
        milestones_completed = all(milestone.completed for milestone in current_chapter_obj.milestones.values())
        
        # Complete current chapter if requirements are met
        if current_chapter_requirements_met and milestones_completed and not current_chapter_obj.completed:
            self.complete_current_chapter()
            
            # Find potential next chapters
            next_chapters = current_chapter_obj.get_next_chapters(self.game)
            
            if next_chapters:
                # Multiple possible next chapters
                if len(next_chapters) > 1:
                    self.present_chapter_choice(next_chapters)
                # Single next chapter
                elif len(next_chapters) == 1:
                    # Double-check requirements for the single next chapter
                    next_chapter = next_chapters[0]
                    next_chapter_requirements_met = True
                    
                    if next_chapter.requirements:
                        for req_type, req_value in next_chapter.requirements.items():
                            if not MilestoneRequirements._check_single_requirement(req_type, req_value, self.game):
                                next_chapter_requirements_met = False
                                print(f"Next Chapter Requirement Not Met: {req_type}")
                    
                    if next_chapter_requirements_met:
                        self.start_chapter(next_chapter.id)
                    else:
                        print(f"Cannot start chapter {next_chapter.id} - requirements not met")
            
            # No next chapters (potentially an ending)
            elif not current_chapter_obj.next_chapters:
                self.handle_game_ending()

    def handle_game_ending(self):
        """Handle reaching a game ending"""
        ending_messages = {
            "ending_trade": [
                "Congratulations! You've become a legendary trade mogul!",
                "Your economic empire spans the galaxy.",
                f"Final wealth: {self.game.format_money(self.game.ship.money)}",
                f"Total trades: {self.game.trades_completed}"
            ],
            "ending_combat": [
                "Congratulations! You're now a legendary fleet admiral!",
                "Your military prowess is unmatched.",
                f"Combat victories: {self.game.ship.combat_victories['total']}",
                f"Final rank: {self.game.rank}"
            ],
            "ending_discovery": [
                "Congratulations! You've solved the sector's ancient mysteries!",
                "Your discoveries will change history forever.",
                f"Research points: {self.game.ship.research_points}",
                f"Discoveries: {len(self.game.discovered_locations)}"
            ]
        }

        messages = ending_messages.get(self.current_chapter, 
            ["Congratulations! You've completed your journey!"])
        
        self.game.display_story_message(messages)
        self.game.display_score()

    def complete_current_chapter(self):
        """Handle chapter completion with unlocks"""
        current_chapter_obj = self.chapters[self.current_chapter]
        if not current_chapter_obj.completed:
            current_chapter_obj.completed = True
            current_chapter_obj.completion_turn = self.game.turn
            self.completed_chapters.add(self.current_chapter)
            
            # Handle any chapter unlocks
            current_chapter_obj.handle_chapter_unlocks(self.game)
            
            # Get next chapter options
            next_chapters = current_chapter_obj.get_next_chapters(self.game)
            
            self.game.display_story_message([
                f"Chapter Complete: {current_chapter_obj.title}",
                "Your journey continues to evolve..."
            ])
            
            # Present chapter choice or transition to next chapter
            if next_chapters:
                if len(next_chapters) > 1:
                    self.present_chapter_choice(next_chapters)
                else:
                    self._chapter_just_announced = True  # Prevent duplicate announcement
                    self.start_chapter(next_chapters[0].id)
                    self.game.display_story_message([
                        f"Chapter {self.current_chapter}: {next_chapters[0].title}",
                        next_chapters[0].description
                    ])

    def present_chapter_choice(self, available_chapters):
        """Present chapter choices to player"""
        content = [["Choose Your Path"]]
        for i, chapter in enumerate(available_chapters, 1):
            content.extend([
                [""],
                [f"{i}. {chapter.title}"],
                [chapter.description]
            ])
        print(self.game.ui.create_box(content, 'double'))
        
        choice = self.game.validate_input(
            f"Choose your path (1-{len(available_chapters)}): ",
            [str(i) for i in range(1, len(available_chapters) + 1)]
        )
        
        if choice:
            chosen_chapter = available_chapters[int(choice) - 1]
            self.start_chapter(chosen_chapter.id)  # Use the ID

    def start_chapter(self, chapter):
        """Start a new chapter"""
        if isinstance(chapter, str):
            self.current_chapter = chapter
            chapter_obj = self.chapters[chapter]
        else:
            self.current_chapter = chapter.id
            chapter_obj = chapter
        
        # Only announce chapter if it wasn't just announced by complete_current_chapter
        if not getattr(self, '_chapter_just_announced', False):
            self.game.display_story_message([
                f"Chapter {self.get_chapter_number_roman()}: {chapter_obj.title}",
                chapter_obj.description,
                "",
                "New milestones await..."
            ])
        self._chapter_just_announced = False

    def get_current_objectives(self):
        """Get current chapter objectives"""
        if self.current_chapter:
            return [(m.title, m.completed) for m in self.current_chapter.milestones.values()]
        return []

    def save_progress(self):
        """Return story progress data for saving"""
        return {
            "current_chapter": self.current_chapter,
            "completed_chapters": list(self.completed_chapters),
            "completed_story_beats": list(self.completed_story_beats),
            "plot_points": self.plot_points,
            "story_states": dict(self.story_states)
        }

    def load_progress(self, data):
        """Load story progress from saved data"""
        if data["current_chapter"]:
            self.current_chapter = data["current_chapter"]
        self.completed_chapters = set(data["completed_chapters"])
        self.completed_story_beats = set(data["completed_story_beats"])
        self.plot_points = data["plot_points"]
        self.story_states.update(data["story_states"])

    def complete_milestone(self, milestone_id):
        """Complete a specific milestone in the current chapter"""
        if self.current_chapter:
            current_chapter_obj = self.chapters[self.current_chapter]
            
            # Check if milestone exists in current chapter
            if milestone_id in current_chapter_obj.milestones:
                milestone = current_chapter_obj.milestones[milestone_id]
                
                # Complete the milestone if not already completed
                if not milestone.completed:
                    milestone.complete(self.game)
                    self.completed_story_beats.add(milestone_id)
                    return True
        
        return False
    
    def process_event(self, event_type, details):
        """Process events and award plot points"""
        if self.check_cooldown(event_type):
            return

        points = self.calculate_points(event_type, details)
        
        # Extract numeric part of chapter string and use that for multiplier
        chapter_num = int(''.join(filter(str.isdigit, self.current_chapter)))
        points *= (1 + chapter_num * 0.2)
        
        self.plot_points += int(points)
        
        self.update_story_states(event_type, details)
        self.check_chapter_progress()

    def trigger_story_event(self, event_id, details=None):
        """Legacy support for story events"""
        if event_id in self.enabled_events:
            self.process_event("story", {
                "event_id": event_id,
                "details": details
            })
            return True
        return False

    def check_event_trigger(self, event, game):
        """Check if an event triggers any story progression"""
        if isinstance(event, str):
            if "Pirate" in event:
                self.process_event("combat", {"enemy_type": "pirate"})
            elif "artifact" in event.lower():
                self.process_event("exploration", {"discovery_type": "artifact"})
            elif "trade" in event.lower():
                self.process_event("trade", {})
            elif "research" in event.lower():
                self.process_event("research", {})

    def handle_quest_completion(self, quest):
        """Update story progress when quests complete"""
        plot_points = {
            "story": 10,
            "combat": 5,
            "trade": 5,
            "exploration": 8,
            "research": 8
        }.get(quest.quest_type, 3)
        
        self.plot_points += plot_points
        
        # Handle milestone completion if this was a story quest
        if quest.milestone and self.current_chapter:
            chapter_obj = self.chapters[self.current_chapter]
            if quest.milestone in chapter_obj.milestones:
                milestone = chapter_obj.milestones[quest.milestone]
                milestone.complete(self.game)
        
        # Update story states based on quest completion
        if quest.quest_type == "trade" and self.game.trades_completed >= 50:
            self.story_states["trade_empire"] = True
        elif quest.quest_type == "combat" and self.game.ship.combat_victories['total'] >= 25:
            self.story_states["pirate_threat"] = True
        elif quest.quest_type == "research" and len(self.game.research.unlocked_options) >= 3:
            self.story_states["tech_breakthrough"] = True
        elif quest.quest_type == "exploration" and len(self.game.discovered_locations) >= 5:
            self.story_states["ancient_mystery"] = True
            
        # Check for chapter progression
        self.check_chapter_progress()
        
        # Generate new quests if appropriate
        if random.random() < 0.3:  # 30% chance for follow-up quest
            self.game.quest_system.generate_quest(quest.quest_type, 1.5)

    def check_cooldown(self, event_type):
        """Check event cooldown to prevent spam"""
        current_turn = self.game.turn
        if event_type in self.event_cooldowns:
            if current_turn - self.event_cooldowns[event_type] < 5:
                return True
        self.event_cooldowns[event_type] = current_turn
        return False

    def check_discovery_milestone(self, location):
        """
        Check if a discovered location triggers any story milestones
        
        Args:
            location: The location object that was discovered
        """
        if not self.current_chapter:
            return False

        current_chapter_obj = self.chapters[self.current_chapter]
        
        # Check each milestone in the current chapter
        for milestone_id, milestone in current_chapter_obj.milestones.items():
            if not milestone.completed and 'locations_discovered' in milestone.requirements:
                required_locations = milestone.requirements['locations_discovered']
                
                # Check if specific location type requirements are met
                if isinstance(required_locations, dict):
                    for loc_type, count in required_locations.items():
                        discovered = len([loc for loc in self.game.discovered_locations 
                                        if loc.location_type == loc_type])
                        if discovered < count:
                            return False
                
                # Check total location type discovery
                elif isinstance(required_locations, int):
                    if len(self.game.discovered_locations) < required_locations:
                        return False
        
        return True

    def calculate_points(self, event_type, details):
        """Calculate points based on event type and details"""
        base_points = {
            "combat": 5,
            "trade": 3,
            "exploration": 8,
            "research": 6,
            "story": 10
        }.get(event_type, 2)
        
        if details.get("enemy_type") == "pirate":
            base_points *= 1.5
        elif details.get("discovery_type") == "artifact":
            base_points *= 2
            
        return base_points

    def update_story_states(self, event_type, details):
        """Update story state flags based on events"""
        if event_type == "combat" and details.get("enemy_type") == "pirate":
            self.story_states["pirate_threat"] = True
        elif event_type == "exploration" and details.get("discovery_type") == "artifact":
            self.story_states["alien_discovery"] = True

    def display_story_progress(self):
        """Display story progress and achievements"""
        story_content = [["Story Progress & Achievements"]]
        story_content.append([""])
        
        # Current chapter info
        current_chapter_obj = self.chapters[self.current_chapter]
        story_content.append([f"Current Chapter {self.get_chapter_number_roman()} : {current_chapter_obj.title}"])
        story_content.append([f"Plot Points: {self.plot_points}"])
        
        # Completed story beats
        if self.completed_story_beats:
            story_content.append([""])
            story_content.append(["Completed Story Elements"])
            for beat in self.completed_story_beats:
                story_content.append([f"• {beat.replace('_', ' ').title()}"])
        
        # Achievements
        if hasattr(self, 'unlocked_achievements') and self.unlocked_achievements:
            story_content.append([""])
            story_content.append(["Achievements Unlocked"])
            for achievement in self.unlocked_achievements:
                story_content.append([f"• {achievement.replace('_', ' ').title()}"])
        
        # Location discoveries
        if hasattr(self, 'discovered_locations_by_type'):
            story_content.append([""])
            story_content.append(["Location Discoveries"])
            for loc_type, count in self.discovered_locations_by_type.items():
                story_content.append([f"• {loc_type}: {count} discovered"])
        
        print(self.game.ui.create_box(story_content, 'double'))
        input("Press Enter to continue...")