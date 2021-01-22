"""
This file is hacked together to get the output from the trajectories generated in benchmark.py (benchmark_copy.py) into the GUI
"""

import pickle
from appraisal import appraisal_dimensions as ad


class RunBenchmarkTrajectories():
    def __init__(self):
        file = open("sim_scripts/output/benchmark/trajectories_pickle20210122-122352", 'rb')
        # file = open("output/benchmark/trajectories_pickle20210122-122352", 'rb')
        self.trajectories = pickle.load(file)
        file.close()
        self.agent_name = 'Player'
        self.sim_steps = len(self.trajectories[0])
        self.current_step = 0

    def run_step(self):
        traj_world = self.trajectories[0][self.current_step][0]
        traj_observer = traj_world.agents["ATOMIC"]
        traj_debug = self.trajectories[0][self.current_step][2]

        return_result = {"WORLD_STATE": traj_world.state,
                         "AGENT_STATE": traj_debug,
                         "TRAJECTORY": self.trajectories[0][self.current_step],
                         "OBSERVER": traj_observer}
        self.current_step = self.current_step + 1
        return return_result

if __name__ == "__main__":
    sim = RunBenchmarkTrajectories()
    for step in range(sim.sim_steps):
        res = sim.run_step()
    pass