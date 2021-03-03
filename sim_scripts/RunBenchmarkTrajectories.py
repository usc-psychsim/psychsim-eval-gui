"""
This file is hacked together to get the output from the trajectories generated in benchmark.py (benchmark_copy.py) into the GUI
"""

import pickle
from appraisal import appraisal_dimensions as ad


class RunBenchmarkTrajectories():
    def __init__(self):
        # file = open("sim_scripts/output/benchmark/trajectories_pickle20210203-104402", 'rb')
        # file = open("sim_scripts/output/benchmark/trajectories_pickle20210122-122352", 'rb') # - 25 steps, action selection = 'distribution'
        #file = open("sim_scripts/output/benchmark/trajectories_pickle20210221-172542", 'rb') # - 50 steps, action selection = 'distribution', pedro weights
        # file = open("sim_scripts/output/benchmark/trajectories_pickle20210221-161257", 'rb') # - 50 steps, action selection = random, pedro weights
        # file = open("sim_scripts/output/benchmark/trajectories_pickle20210228-121328", 'rb') # - 20 steps, action selection = 'distribution, pedro weights
        # file = open("sim_scripts/output/benchmark/trajectories_pickle20210302-122811", 'rb') # 20 steps, action seleciton=distribution, changed weights, no obs
        file = open("sim_scripts/output/benchmark/trajectories_pickle20210303-181549", 'rb') # 7 steps, action selection = distribution, no obs
        self.trajectories = pickle.load(file)
        file.close()
        self.agent_name = 'Player'
        self.sim_steps = len(self.trajectories[0])
        self.current_step = 0

    def run_step(self):
        traj_world = self.trajectories[0][self.current_step][0]

        return_result = {"WORLD_STATE": traj_world.state,
                         "AGENT_STATE": traj_world,
                         "TRAJECTORY": self.trajectories[0][self.current_step]}#,
                         # "OBSERVER": traj_observer}
        self.current_step = self.current_step + 1
        return return_result

if __name__ == "__main__":
    sim = RunBenchmarkTrajectories()
    for step in range(sim.sim_steps):
        res = sim.run_step()
    pass