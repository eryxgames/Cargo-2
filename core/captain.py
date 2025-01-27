# core/captain.py
import json

class Captain:
    def __init__(self, game, name="Explorer"):
        self.game = game
        self.name = name
        self.rank = "Explorer"
        self.perks = []
        self.traits = []
        self.total_trades = 0
        self.total_combat_victories = 0
        self.total_research_points = 0
        self.total_passengers_transported = 0
        self.total_contracts_completed = 0
        self.total_quests_completed = 0
        self.rank_data = self.load_rank_data()
        self.activity_log = []
        self.rank_check_interval = 12
        self.category_ranks = {} # Track separate category ranks
        
    def load_rank_data(self):
        """Load rank data from data/ranks.json"""
        try:
            with open("data/ranks.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: ranks.json not found. Using default settings.")
            return {}
        except json.JSONDecodeError:
            print("Error: Could not parse ranks.json. Using default settings.")
            return {}

    def update_rank(self):
        """Update the player's rank based on various achievements"""
        
        if not hasattr(self, 'rank_data'):
            print("Warning: Rank data not loaded. Using default rank.")
            return

        # Tracked parameters
        achievements = {
            "trades": self.total_trades,
            "combat": self.total_combat_victories,
            "research": self.total_research_points,
            "passengers": self.total_passengers_transported,
            "contracts": self.total_contracts_completed,
            "quests": self.total_quests_completed
        }
        
        # Default "Explorer" rank, if no rank is found
        new_rank = "Explorer"
        
        # Track activity proportions for the last 12 turns
        recent_activity = self.get_recent_activity()
        if recent_activity:
             total_activity = sum(recent_activity.values())
             proportions = {key: value / total_activity for key, value in recent_activity.items()}
        else:
             proportions = {}
        # Check categories
        for cat, data in self.rank_data.items():
            if cat == "general":
                # Handle general ranks which require a mix of things
                for rank_info in data.get("ranks", []):
                    if all(achievements.get(key,0) >= value for key, value in rank_info.items() if key != 'rank') and all(proportions.get(key, 0) >= value for key, value in rank_info.items() if key not in ['rank', "trades", "combat", "research", "passengers", "contracts", "quests"] ):
                        new_rank = rank_info['rank']
            elif cat in achievements:
                # Handle single-type ranks
                best_rank = "Explorer"
                for rank_info in data.get("ranks", []):
                   achivement_name = cat
                   if achievements.get(achivement_name, 0) >= rank_info.get(cat, 0):
                       if not proportions or cat not in proportions or proportions[cat] >= rank_info.get("proportion", 0):
                            best_rank = rank_info.get("rank", "Explorer")
                self.category_ranks[cat] = best_rank
                        
        self.rank = new_rank
        
    def rank_multiplier(self, type="multiplier"):
         """Returns rank multiplier for calculations"""
         for rank_info in self.rank_data.get("final", {}).get("ranks", []):
            if rank_info.get("rank") == self.rank:
              return rank_info.get(type, 1.0)
         return 1.0
    
    def get_rank_for_type(self, category):
        """Get rank for a specific category"""
        return self.category_ranks.get(category, "None")

    def record_activity(self, activity_type, amount=1):
        """Record player activity for calculating rank."""
        self.activity_log.append({"turn": self.game.turn, "type": activity_type, "amount": amount})

    def get_recent_activity(self):
        """Get a summary of player activities for the last few turns."""
        recent_activities = {}
        for activity in self.activity_log:
            if self.game.turn - activity["turn"] < self.rank_check_interval:
                activity_type = activity["type"]
                recent_activities[activity_type] = recent_activities.get(activity_type, 0) + activity["amount"]
                
        return recent_activities
    
    def format_rank_display(self):
        """Formats the rank display string"""
        category_rank = ""
        if "quest" in self.category_ranks:
            category_rank = f"{self.category_ranks['quest']} "
        
        if "combat" in self.category_ranks and "trade" not in self.category_ranks and "research" not in self.category_ranks and "passenger" not in self.category_ranks and "contract" not in self.category_ranks:
            category_rank = f"{self.category_ranks['combat']} "
        elif "trade" in self.category_ranks and "combat" not in self.category_ranks and "research" not in self.category_ranks and "passenger" not in self.category_ranks and "contract" not in self.category_ranks:
            category_rank = f"{self.category_ranks['trade']} "
        elif "research" in self.category_ranks and "combat" not in self.category_ranks and "trade" not in self.category_ranks and "passenger" not in self.category_ranks and "contract" not in self.category_ranks:
            category_rank = f"{self.category_ranks['research']} "
        elif "passenger" in self.category_ranks and "combat" not in self.category_ranks and "trade" not in self.category_ranks and "research" not in self.category_ranks and "contract" not in self.category_ranks:
            category_rank = f"{self.category_ranks['passenger']} "
        elif "contract" in self.category_ranks and "combat" not in self.category_ranks and "trade" not in self.category_ranks and "research" not in self.category_ranks and "passenger" not in self.category_ranks:
             category_rank = f"{self.category_ranks['contract']} "
        
        return f"{category_rank}{self.name}, {self.rank}"

    def generate_ending_report(self):
        """Generate a text based ending report based on achieved rank and game progress"""
        report = f"Captain {self.name}, of rank {self.rank}, has completed their journey.\n"
        report += f"Trades Completed: {self.total_trades}\n"
        report += f"Combat Victories: {self.total_combat_victories}\n"
        report += f"Research Points Acquired: {self.total_research_points}\n"
        report += f"Passengers Transported: {self.total_passengers_transported}\n"
        report += f"Contracts Completed: {self.total_contracts_completed}\n"
        report += f"Quests Completed: {self.total_quests_completed}\n"

        # TODO: add more stats and game-ending story parts

        return report