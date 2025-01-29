# core/research.py
import yaml
import os

class Research:
    def __init__(self):
        self.unlocked_options = set()
        self.research_data = self.load_research_data() #data driven now

    def load_research_data(self):
         """Load research data from data/research.yml"""
         try:
            with open("data/research.yml", 'r') as f:
                data = yaml.safe_load(f)
                return data.get("research_options", {})
         except FileNotFoundError:
             print("Error: research.yml not found. Using default research data.")
             return {}
         except yaml.YAMLError as e:
             print(f"Error loading research from YAML: {e}")
             return {}

    @property
    def research_costs(self):
        """Dynamically retrieve research costs"""
        return {
            key: item['cost']
            for key, item in self.research_data.items()
        }
    
    @property
    def research_benefits(self):
        """Dynamically retrieve research benefits"""
        return {
            key: item.get('effects', {})
            for key, item in self.research_data.items()
        }
    
    def get_research_requirements(self, option):
         """Get tech level and plot point requirements for a research option"""
         research = self.research_data.get(option, {})
         return {
             "tech_level": int(research.get("tech_level", 0)),
             "plot_points": int(research.get("plot_points", 0))
         }

    def get_research_type(self, option):
        """Get type of research"""
        research = self.research_data.get(option, {})
        return research.get('type')

    def can_unlock(self, option, research_points):
        """Check if a research option can be unlocked given available research points"""
        return research_points >= self.research_costs.get(option, float('inf'))

    def unlock(self, option):
        """Unlock a research option"""
        self.unlocked_options.add(option)