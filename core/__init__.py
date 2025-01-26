# core/__init__.py
from core.game import Game
from core.location import Location
from core.character import SpecialCharacter, SpecialCharacterGenerator, SyntheticCharacterGenerator, AlienCharacterGenerator
from core.quest import Quest, QuestSystem # Removed Contract here
from core.contract import Contract # Added Contract here
from core.ship import Ship, PassengerModule, Passenger
from core.research import Research
from core.action import Action
from core.port import Port
from core.event import Event
from core.uprising import UprisingEffect, SyntheticEventManager, InfestationManager
from core.story import StoryManager, StoryChapter, StoryMilestone
from core.dynamic_character_system import DynamicCharacterSystem, SpecialCharacterEncounters
from core.gameplay import play_turn
from core.template import CharacterTemplate
from core.audio import AudioManager
from core.game_events import GameEvents
from core.location_data import LocationCommands, LocationCapabilities, LocationTerminology
from core.story_requirements import MilestoneRequirements
from core.shop import Shop