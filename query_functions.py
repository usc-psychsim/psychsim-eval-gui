"""
Query function definitions used by psychsim gui
"""
import pandas as pd
import numpy as np
import traceback

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
        get list of agents in the data
        :return:
        """
        agent_list = dict()
        for key, value in kwargs.items():
            if key == "data":
                for sim_data in value.values():
                    for step_data in sim_data.values():
                        for agent_data in step_data.values():
                            if type(agent_data) == dict:
                                for agent in list(agent_data.keys()):
                                    agent_list[agent] = agent

        return agent_list



    def get_actions(self, *args, **kwargs):
        """
        return a list of actions taken, and their corresponding steps
        :param agent:
        :return:
        """
        actions_dict = dict(step=[], action=[])
        try:
            data = kwargs['data']
            for sim_data in data.values():
                for step, step_data in sim_data.items():
                    for agent_data in step_data['step_data'].values():
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
        pass

