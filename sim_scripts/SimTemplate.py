"""
Template class for simulations to be used with psychsim-gui-qt
"""

class SimTemplate:
    def __init__(self):
        self.sim_steps = 20

    def run_step(self):
        """
        overwrite this function
        returns dictionary e.g. self.result0 = {'TriageAg1': {}}; return self.result0
        """
        pass

if __name__ == "__main__":
    sim = SimTemplate()
    sim.run_step()