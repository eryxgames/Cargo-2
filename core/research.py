# core/research.py
class Research:
    def __init__(self):
        self.unlocked_options = set()
        self.research_costs = {
            'xenoeconomy': 100,
            'telemetry': 150,
            'geophysics': 200,
            'chronopolitics': 250,
            'exogeology': 300,  # New research option
            'psychodynamics': 350  # New research option
        }
        self.research_benefits = {
            'xenoeconomy': {'tax_reduction': 0.02},
            'telemetry': {'scout_success': 0.2},
            'geophysics': {'exogeology': 0.15},
            'chronopolitics': {'revolution_success': 0.2},
            'exogeology': {'output_bonus': 0.25},
            'psychodynamics': {'price_control': 0.1}
        }
    
    def can_unlock(self, option, research_points):
        return research_points >= self.research_costs.get(option, float('inf'))

    def unlock(self, option):
        self.unlocked_options.add(option)