"""
Test the gui structure for handling any type of simulation
All simulation scripts must meet the following criteria:

1) A member named 'sim_steps' (int): number of steps to run the simulation

2) A method named 'run_sim': the code for executing a single step
        This must return a dictionary with the results

3) The class name must be the same as the file name
"""

import numpy as np


class DemoSim:
    def __init__(self):
        self.sim_steps = 101
        self.current_step = 0
        self.output_data = dict(ch1=dict(), ch2=dict(), ch3=dict())

    def run_step(self):
        sin_data = dict(ch1=dict(), ch2=dict(), ch3=dict())
        random_data = dict(ch4=dict(), ch5=dict())

        # Populate all the sinusoid channels
        # channel 1
        y = np.sin(0.5* self.current_step) + np.random.random_sample()
        sin_data["ch1"]["y"] = y
        sin_data["ch1"]["x"] = self.current_step

        # channel 2
        y = np.sin(0.25*self.current_step)
        sin_data["ch2"]["y"] = y
        sin_data["ch2"]["x"] = self.current_step

        # channel 3
        y = 3 * np.sin(0.125*self.current_step)
        sin_data["ch3"]["y"] = y
        sin_data["ch3"]["x"] = self.current_step

        # Populate the random channels
        y = np.random.random_sample()
        random_data["ch4"]["y"] = y
        random_data["ch4"]["x"] = self.current_step

        # channel 2
        y = np.random.random_sample() * 2
        random_data["ch5"]["y"] = y
        random_data["ch5"]["x"] = self.current_step

        output_data = {"sin": sin_data,
                       "random": random_data}

        self.current_step = self.current_step + 1

        return output_data


if __name__ == "__main__":
    sim = DemoSim()
    for step in range(sim.sim_steps):
        sim.run_step()
    pass