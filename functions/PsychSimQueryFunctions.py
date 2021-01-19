"""
Query function definitions used by psychsim gui

"""

import pandas as pd
import numpy as np
import traceback
from random import randint

import psychsim_gui_helpers as pgh


class PsychSimQueryFunctions:
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

        NOTE: the index must be a string.
        NOTE: it is better to have 'step' on the x axis
        """
        results = dict(agent=[f"{agent}_{i}" for i in range(1, 11)],
                       action=[f"{action}_{randint(0, 3)}" for i in range(1, 11)])
        output = pd.DataFrame(results)
        output = output.set_index('agent')
        return pd.DataFrame(output)



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

    def query_action(self, data=None, agent=None, action=None, *args, **kwargs):
        """
         action specific query, which I can use to look at overall reasoning of a planning agent.

         This function answers the question "what was the agent's reasoning for taking the eventual action.
         It shows the hypothetical actions and rewards that were used to decide on the current action.
        :param planning_agent: agent to query
        :param action: action to query. This is actually the step value of the action
        :param cycle:
        :param planning_horizon:
        :return:
        """
        try:
            action_of_interest = data.data[action]["AGENT_STATE"][agent]
            output_data = pd.DataFrame()
            for la_key, legal_action in action_of_interest["__decision__"]["TriageAg10"]["V"].items():
                for idx, hyp_action_set in enumerate(legal_action['__S__']):
                    hyp_action = hyp_action_set.marginal("TriageAg1's __ACTION__")
                    hyp_reward = hyp_action_set.marginal("TriageAg1's __REWARD__")
                    output_dict = dict(horizon=[idx], base_action=[str(la_key)], hypothetical_action=[str(hyp_action)],hypothetical_reward=[str(hyp_reward)])
                    output_data = output_data.append(pd.DataFrame.from_dict(output_dict))

            return output_data
        except KeyError as e:
            print(f"No key data for {e}")

    def query_state(self, data=None, agent=None, action=None, state=None, *args, **kwargs):
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
        try:
            data = data
            agent_id = agent
            action_id = action
            state_id = state
            output_data = pd.DataFrame()
            horizon = {}
            for step, step_data in data.data.items():
                if step == action_id:
                    for agent, agent_data in step_data["AGENT_STATE"].items():
                        if agent == agent_id:
                            for decision, decision_data in agent_data["__decision__"].items():
                                if type(decision_data) == dict:
                                    for element, element_data in decision_data["V"].items():
                                        if str(element) == state_id:
                                            for idx, hzn in enumerate(element_data["__S__"]):
                                                horizon[idx] = pd.DataFrame(self.__extract_numeric_values_fromVectorDistributionSet(hzn))
            #append all the horizons to one dictionary
            all_horizons = pd.concat(horizon.values())
            all_horizons.insert(loc=0, column='horizon', value=pd.Series(list(horizon.keys()), index=all_horizons.index))
            return all_horizons
        except:
            tb = traceback.format_exc()
            print(tb)

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

    def get_agents(self, *args, **kwargs):
        """
        get list of agents in the data. Data must be a PsychSimRun class
        :return: Dataframe containing the agents
        """
        agent_dict = dict(agent=[])
        for key, value in kwargs.items():
            if key == "data":
                for step_data in value.data.values():
                    if type(step_data['TRAJECTORY'][0][0].agents) == dict:
                    # if type(step_data['AGENT_STATE']) == dict:
                    #     for agent in list(step_data['AGENT_STATE'].keys()):
                        for agent in step_data['TRAJECTORY'][0][0].agents.keys():
                            if agent not in agent_dict['agent']:
                                agent_dict['agent'].append(agent)

        output_data = pd.DataFrame.from_dict(agent_dict)
        return output_data

    def get_actions(self, data=None, agent=None, *args, **kwargs):
        """
        Return a list of actions taken, and their corresponding steps
        :param data: Input data
        :param agent: string (key) Agent whose actions will be returned
        :return: Dataframe containing the actions for the selected agent
        """
        actions_dict = dict(step=[], action=[])
        try:
            for step, step_data in data.data.items():
                actions_dict['step'].append(step)
                action = str(step_data['TRAJECTORY'][0][1]).split('\t')[1]
                actions_dict['action'].append(action)
                # step_data[0][1]
                # for agent_i, agent_data in step_data['AGENT_STATE'].items():
                #     if agent_i == agent:
                #         for d in agent_data['__decision__'].values():
                #             if type(d) == dict:
                #                 for k, v in d.items():
                #                     if k == 'action':
                #                         actions_dict['action'].append(str(v))
                #                         actions_dict['step'].append(step)
        except:
            tb = traceback.format_exc()
            print(tb)

        output_data = pd.DataFrame.from_dict(actions_dict)
        return output_data

    def get_individual_agent_beliefs_numeric(self, data=None, agent=None, *args, **kwargs):
        """
        return a dataframe of beliefs for the agent at each step
        :return: Dataframe containing the actions and beliefs for the selected agent
        """
        try:
            data = data
            agent_id = agent
            steps = {}
            for step, step_data in data.data.items():
                for t, sa in enumerate(step_data['TRAJECTORY']):
                    world, action = sa
                    agent_obj = world.agents[agent]
                    beliefs = agent_obj.getBelief(world.state)
                    steps[step] = pd.DataFrame(self.__extract_numeric_values_fromVectorDistributionSet(list(beliefs.values())[0]))

            #append all the horizons to one dictionary
            all_steps = pd.concat(steps.values())
            all_steps.insert(loc=0, column='step', value=pd.Series(list(steps.keys()), index=all_steps.index))
            all_steps = all_steps.set_index('step', drop=False).T
            all_steps = all_steps.sort_index()
            return all_steps
        except:
            tb = traceback.format_exc()
            print(tb)

    def get_individual_agent_beliefs_values(self, data=None, agent=None, *args, **kwargs):
        """
        return a dataframe of beliefs for the agent at each step
        :return: Dataframe containing the actions and beliefs for the selected agent
        """
        try:
            data = data
            agent_id = agent
            steps = {}
            for step, step_data in data.data.items():
                for t, sa in enumerate(step_data['TRAJECTORY']):
                    world, action = sa
                    agent_obj = world.agents[agent]
                    beliefs = agent_obj.getBelief(world.state)
                    steps[step] = pd.DataFrame(self.__extract_values_fromVectorDistributionSet(list(beliefs.values())[0], world))

            #append all the horizons to one dictionary
            all_steps = pd.concat(steps.values())
            all_steps.insert(loc=0, column='step', value=pd.Series(list(steps.keys()), index=all_steps.index))
            all_steps = all_steps.set_index('step', drop=False).T
            return all_steps
        except:
            tb = traceback.format_exc()
            print(tb)

    def get_all_agents_beliefs(self, *args, **kwargs):
        """
        return a dataframe of beliefs for the agent at each step
        :return: Dataframe containing the actions and beliefs for the selected agent
        """
        try:
            data = kwargs['data']
            data_id = kwargs['data_id']
            agent_id = kwargs['agent']
            output_data = pd.DataFrame()
            for step, step_data in data.data.items():
                output_data = output_data.append(self.__get_debug_data(debug=step_data['AGENT_STATE'], step=step))
            return output_data
        except:
            tb = traceback.format_exc()
            print(tb)

    def get_world_state(self, *args, **kwargs):
        """
        Get the world state of an agent
        :param args:
        :param kwargs:
        :return:
        """
        try:
            data = kwargs['data']
            output_data = pd.DataFrame()
            steps = []
            for step, step_data in data.data.items():
                output_data = output_data.append(self.__extract_numeric_values_fromVectorDistributionSet(step_data['WORLD_STATE']))
                steps.append(str(step))
            step_col = pd.Series(steps)
            output_data.insert(loc=0, column='step', value=pd.Series(steps, index=output_data.index))
            return output_data
        except:
            tb = traceback.format_exc()
            print(tb)

    def __extract_numeric_values_fromVectorDistributionSet(self, vds):
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
        vds_values = vds_values.append(data)
        return vds_values

    def __extract_values_fromVectorDistributionSet(self, vds, world):
        # TODO: clean this up
        vds_values = pd.DataFrame()
        clean_header = []
        actor_values = []
        for key in vds.keyMap:
            # print(actor_distribution_set.marginal(key))
            actor_values.append(world.getFeature(key, unique=True))
            if "Actor" in key:
                key = key.split(' ')[-1]
            clean_header.append(key)
        data = pd.DataFrame(actor_values).T
        data.columns = clean_header
        vds_values = vds_values.append(data)
        return vds_values



