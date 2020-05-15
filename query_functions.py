"""
Query function definitions used by psychsim gui
"""
#TODO: make the doc strings appear in the dialog?

import pandas as pd
import numpy as np
import traceback

import psychsim_gui_helpers as pgh

class PsychSimQuery:
    def __init__(self):
        pass

    def query_all(self, *args, **kwargs):
        """
        A general query that given a planning agent, one of its action, a cycle number and a certain planning horizon
        it prints out projected actions of different agents and projected resulting states for all agents.
        :param planning_agent:
        :param action:
        :param cycle:
        :param planning_horizon:
        :return:
        """
        print("query_all")
        pass

    def query_action(self, *args, **kwargs):
        """
         action specific query, which I can use to look at overall reasoning of a planning agent.
        :param planning_agent:
        :param action:
        :param cycle:
        :param planning_horizon:
        :return:
        """
        return "query_action"
        pass

    def query_state(self, *args, **kwargs):
        """
        A state specific query which gives access to a certain state. Using this one I can plot some of values during
        reasoning in one cycle and get insight from it
        :param planning_agent:
        :param action:
        :param cycle:
        :param planning_horizon:
        :param state:
        :return:
        """
        print("query_state")
        pass

    def diff_checker(self, *args, **kwargs):
        """
        Ideally having a diff checker that gets two queries would help, however having the other queries there exist
        a lot of diff checker tools that can be used to see the difference between two queries.
        :param query1:
        :param query2:
        :return:
        """
        print("diff_checker")
        pass

#-------own--------------

    def get_agents(self, *args, **kwargs):
        """
        get list of agents in the data. Data must be a PsychSimRun class
        :return:
        """
        #TODO: return a dataframe
        agent_dict = dict(agent=[])
        for key, value in kwargs.items():
            if key == "data":
                for step_data in value.data.values():
                    if type(step_data) == dict:
                        for agent in list(step_data.keys()):
                            if agent not in agent_dict['agent']:
                                agent_dict['agent'].append(agent)

        output_data = pd.DataFrame.from_dict(agent_dict)
        return output_data



    def get_actions(self, *args, **kwargs):
        """
        return a list of actions taken, and their corresponding steps
        :param agent:
        :return:
        """
        actions_dict = dict(step=[], action=[])
        try:
            data = kwargs['data']
            data_id = kwargs['data_id']
            agent_id = kwargs['agent']
            for step, step_data in data.data.items():
                for agent, agent_data in step_data.items():
                    if agent == agent_id:
                        for d in agent_data['__decision__'].values():
                            if type(d) == dict:
                                for k, v in d.items():
                                    if k == 'action':
                                        actions_dict['action'].append(str(v))
                                        actions_dict['step'].append(step)
        except:
            tb = traceback.format_exc()
            print(tb)

        output_data = pd.DataFrame.from_dict(actions_dict)
        return output_data

    def get_beliefs(self, *args, **kwargs):
        """
        return a dataframe of beliefs for the agent at each step
        :param agent:
        :return:
        """
        try:
            data = kwargs['data']
            data_id = kwargs['data_id']
            agent_id = kwargs['agent']
            output_data = pd.DataFrame()
            for step, step_data in data.data.items():
                output_data = output_data.append(self.__get_debug_data(debug=step_data, step=step))
            return output_data
        except:
            tb = traceback.format_exc()
            print(tb)

    def __get_debug_data(self, debug, step, level=0):
        # TODO: make this output some sort of dataframe
        # THIS ASSUMES THE STRUCTURE WON'T CHANGE
        sim_info = pd.DataFrame(columns=["step", "agent", "action"])
        step_info = []

        for k, v in debug.items():
            agent_info = dict(step=[step],agent=None, action=None, possible_actions=None, beliefs=None)
            agent_info["agent"] = k
            for k1, v1 in v.items():
                for k2, v2 in v1.items():
                    if type(v2) == dict:
                        for k3, v3 in v2.items():
                            # if type(v3) == self.psychsim_module.ActionSet:
                            if v3.__class__.__name__ == "ActionSet":
                                agent_info["action"] = v3
                            if type(v3) == dict:
                                agent_info["possible_actions"] = v3
            if agent_info["possible_actions"] is not None:
                agent_info["beliefs"] = [agent_info["possible_actions"][agent_info["action"]]["__beliefs__"]]
            step_info.append(agent_info)

        # TODO: turn ste_info rows into a dataframe here PROPERLY
        step_dataframes = []
        for info in step_info:
            info["action"] = [str(info["action"])]
            info.pop("possible_actions", None)
            # agent_info.pop("beliefs", None)
            agent_df = pd.DataFrame.from_dict(info) #TODO: FIX THIS
            if info['beliefs']:
                vds_vals = self.__extract_values_fromVectorDistributionSet(info['beliefs'][0])
                agent_df = pd.concat([agent_df, vds_vals], axis=1)
            agent_df = agent_df.drop('beliefs', axis=1)
            step_dataframes.append(agent_df)
        output_df = pd.concat(step_dataframes)
        return output_df

    def __extract_values_fromVectorDistributionSet(self, vds):
        vds_values = pd.DataFrame()
        clean_header = []
        actor_values = []
        for key in vds.keyMap:
            # print(actor_distribution_set.marginal(key))
            actor_values.append(str(vds.marginal(key)).split()[-1])
            if "Actor" in key:
                key = key.split(' ')[-1]
            clean_header.append(key)
        data = pd.DataFrame(actor_values).T
        data.columns = clean_header
        # TODO: create the region column
        vds_values = vds_values.append(data)
        return vds_values
