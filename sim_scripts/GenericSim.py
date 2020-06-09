"""
Test the gui structure for handling any type of simulation
The simulation must have the following members:

sim_steps (int): number of steps to run the simulation

the following methods:
run_sim: the code for executing a single step
        This must return a dictionary with the results


The test generates an array of data based on the current step

*SIM FILE MUST BE NAMED AS THE CLASS
"""


import numpy as np


class GenericSim:
    def __init__(self):
        self.sim_steps = 100
        self.current_step = 0
        # self.output_data = dict(ch1=dict(x=[], y=[]), ch2=dict(x=[], y=[]), ch3=dict(x=[], y=[]))
        self.output_data = dict(ch1=dict(), ch2=dict(), ch3=dict())

    def run_sim(self):
        output_data = dict(ch1=dict(), ch2=dict(), ch3=dict())
        #channel 1
        y = np.sin(0.5* self.current_step) + np.random.random_sample()
        output_data["ch1"]["y"] = y
        output_data["ch1"]["x"] = self.current_step

        #channel 2
        y = np.sin(0.25*self.current_step)
        output_data["ch2"]["y"] = y
        output_data["ch2"]["x"] = self.current_step

        #channel 3
        y = 3 * np.sin(0.125*self.current_step)
        output_data["ch3"]["y"] = y
        output_data["ch3"]["x"] = self.current_step

        self.current_step = self.current_step + 1

        return output_data


if __name__ == "__main__":
    sim = GenericSim()
    for step in range(sim.sim_steps):
        sim.run_sim()