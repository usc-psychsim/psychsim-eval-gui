"""
Demo function class
"""

import pandas as pd

class DemoFunctions:
    def __init__(self):
        pass

    def demo_function(self, data=None, agent=None, action=None, *args, **kwargs):
        """
        This is a test function to illustrate how these functions work.
        If a param is present in the parameter list, it will enable the corresponding dropdown on the GUI
        *Note the params hve to be from the following: [agent, action, cycle, horizon, state]
        For example, 'agent' and 'action' are in the parameter list so these two should be enabled on the gui

        The 'data' comes from the 'select data/sample' dropdown. It is a PsychSimRun object.

        other arguments are passed in through the *args and **kwargs params

        This test function generates a dataframe with columns called 'agent' and 'action' and
        values from '<agent>_1-10 and <action>_11-20 where <agent> and <action> are the selected values on the gui

        *Note 'action' is actually an index of the action in the data, not the actual string itself

        These functions need to correspond to the output from the simulation file that was run.
        e.g. if that output is a dctionary with certain keys, then these functions must acces using the same keys

        """
        results = dict(agent=[f"{agent}_{i}" for i in range(1, 11)],
                       action=[f"{action}_{i}" for i in range(11, 21)])
        return pd.DataFrame(results)
