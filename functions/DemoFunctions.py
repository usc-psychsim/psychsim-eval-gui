"""
This file defines functions to be used with sims_scripts/DemoSim.py

Both files serve as an example of how to write a sim script and corresponding functions

Functions must meet the following mandatory criteria:
1) return a pandas dataframe in the format: TODO: define this format

2) Return in the format (returnType, return_data)
    where returnType is from the folloinwg (tree|table).
        tree: display data on the gui as a tree
        table: display data on the gui as a table

Functions can be connected together in the following way:
TODO: add this part
"""

import pandas as pd


TREE_TYPE = 'tree'
TABLE_TYPE = 'table'

class DemoFunctions:
    def __init__(self):
        pass

    def get_info(self, data):
        """
        Extract the info of the whole data including:
            Data Types
            Number of channels in data
        :return:
        """
        output_data = {}
        for step_data in data.data.values():
            type_info = []
            channel_info = []
            for type, type_data in step_data.items():
                type_info.append(type)
                channel_info.append(len(type_data))
            output_data["data_type"] = type_info
            output_data["number_channels"] = channel_info
        return TABLE_TYPE, pd.DataFrame(output_data).T

    def get_type_info(self, data, type):
        """
        Extract the info of a particular data type including:
            channel names
            channel lengths
            channel means
            channel medians
            channel stds
        :return:
        """
        pass

    def get_all_data(self, data):
        """
        Extract all data
        :return:
        """
        all_steps = []
        for step, step_data in data.data.items():
            individual_step = {}
            for type, type_data in step_data.items():
                for channel, channel_data in type_data.items():
                    individual_step["step"] = [step]
                    individual_step["type"] = [type]
                    individual_step["channel"] = [channel]
                    individual_step["x"] = [channel_data["x"]]
                    individual_step["y"] = [channel_data["y"]]
                    df = pd.DataFrame(individual_step)
                    df = df.set_index("step")
                    all_steps.append(df.T)


        output_data = pd.concat(all_steps, axis=1)
        return TABLE_TYPE, pd.DataFrame(output_data)

    def get_type_data(self, data, data_type: (get_info, "data_type")):
        # TODO: fix this - it would only really work if we don't pass params (except data) to the function - otherwise it gets really complicated...
        """
        Extract data for a particular data type
        :return:
        """
        pass

