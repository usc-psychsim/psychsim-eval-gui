"""
Query function definitions used by psychsim gui

"""

import pandas as pd
import numpy as np
import traceback
from random import randint

from appraisal import appraisal_dimensions as ad
import psychsim_gui_helpers as pgh

TREE_TYPE = 'tree'
TABLE_TYPE = 'table'


class PsychSimQueryFunctions2:
    def __init__(self):
        pass

    def demo_function(self, data: pgh.PsychSimRun=None, agent: str=None, action: str=None, *args, **kwargs) -> pd.DataFrame:
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
                       action=[f"{action}_{randint(0, 3)}" for i in range(1, 11)],
                       reward=[f"{randint(0, 3)}" for i in range(1, 11)])
        output = pd.DataFrame(results)
        output = output.set_index('agent')
        return TABLE_TYPE, pd.DataFrame(output).T

    def query_action(self, data=None, agent=None, action=None, *args, **kwargs):
        """
         action specific query, which I can use to look at overall reasoning of a planning agent.

         This function answers the question "what was the agent's reasoning for taking the eventual action.
         It shows the hypothetical actions and rewards that were used to decide on the current action.
        :param planning_agent: agent to query
        :param action: action to query. This is actually the step value of the action
        :param cycle:
        :param planning_horizon:
        :return: Tree data
        """
        try:
            step = int(action.split(":")[0])
            action_of_interest = data.data[step]["TRAJECTORY"][2][agent]
            taken_action = str(data.data[step]["TRAJECTORY"][1]).split('\t')[1]
            world = data.data[step]["TRAJECTORY"][0]
            output_data = pd.DataFrame()
            for la_key, legal_action in next(iter(action_of_interest["__decision__"].items()))[1]["V"].items():
                for idx, hyp_action_set in enumerate(legal_action['__S__']):
                    index = []
                    hyp_action = world.symbolList[hyp_action_set.marginal(f"{agent}'s __ACTION__").max()]
                    hyp_reward = legal_action["__ER__"][idx] #hyp_action_set.marginal(f"{agent}'s __REWARD__")
                    base_action = str(la_key)
                    output_dict = dict(horizon=[idx],
                                       future_action=[str(hyp_action)],
                                       reward=[str(hyp_reward)])

                    index.append(base_action)
                    output_data = output_data.append(pd.DataFrame(output_dict, index))

            output_data.index.name = "base_action"
            return TREE_TYPE, output_data
        except KeyError as e:
            print(f"No key data for {e}")

    def get_agents(self, data: pd.DataFrame=None, *args, **kwargs):
        """
        get list of agents in the data. Data must be a PsychSimRun class
        :return: Dataframe containing the agents
        """
        agent_dict = dict(agent=[])
        # for key, value in kwargs.items():
        #     if key == "data":
        if data:
            for step_data in data.data.values():
                if type(step_data['AGENT_DEBUG']) == dict:
                    # if type(step_data['AGENT_STATE']) == dict:
                    #     for agent in list(step_data['AGENT_STATE'].keys()):
                    for agent in step_data['AGENT_DEBUG'].keys():
                        if agent not in agent_dict['agent']:
                            agent_dict['agent'].append(agent)

        output_data = pd.DataFrame.from_dict(agent_dict)
        return TABLE_TYPE, output_data.T

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
                action = str(step_data['TRAJECTORY'][1]).split('\t')[1]
                actions_dict['action'].append(f"{step}:{action}")
        except:
            tb = traceback.format_exc()
            print(tb)

        output_data = pd.DataFrame.from_dict(actions_dict)
        return TABLE_TYPE, output_data.T

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
                # for t, sa in enumerate(step_data['AGENT_STATE'].agents[agent]):
                #     world, action = sa
                #     agent_obj = world.agents[agent]
                #     beliefs = agent_obj.getBelief(world.state)
                #     steps[step] = pd.DataFrame(self.__extract_values_fromVectorDistributionSet(list(beliefs.values())[0], world))
                world = step_data["AGENT_STATE"] #TODO: fix this in the sin script (this name is strange as it's really the world state)
                beliefs = step_data['AGENT_STATE'].agents[agent].getBelief(world.state)
                steps[step] = pd.DataFrame(self.__extract_values_fromVectorDistributionSet(list(beliefs.values())[0], world))

            #append all the horizons to one dictionary
            all_steps = pd.concat(steps.values())
            all_steps.insert(loc=0, column='step', value=pd.Series(list(steps.keys()), index=all_steps.index))
            all_steps = all_steps.set_index('step', drop=False).T
            return TABLE_TYPE, all_steps
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
            steps = {}#[]
            for step, step_data in data.data.items():
                # output_data = output_data.append(self.__extract_numeric_values_fromVectorDistributionSet(step_data['WORLD_STATE']))
                # steps.append(str(step))
                world = step_data["AGENT_STATE"] #TODO: fix this in the sin script (this name is strange as it's really the world state)
                steps[step] = pd.DataFrame(self.__extract_values_fromVectorDistributionSet(world.state, world))

            # step_col = pd.Series(steps)
            # output_data.insert(loc=0, column='step', value=pd.Series(steps, index=output_data.index))
            all_steps = pd.concat(steps.values())
            all_steps.insert(loc=0, column='step', value=pd.Series(list(steps.keys()), index=all_steps.index))
            all_steps = all_steps.set_index('step', drop=False).T
            return TABLE_TYPE, all_steps
        except:
            tb = traceback.format_exc()
            print(tb)

    def get_appraisal_diemensions(self, data=None, agent=None, blame_agent=None, *args, **kwargs):
        """
        Get the appraisal dimensions
        """
        step_appraisal_info = dict(step=[],
                                   a_loc=[],
                                   b_loc=[],
                                   a_role=[],
                                   b_role=[],
                                   a_action=[],
                                   b_action=[],
                                   pre_utility=[],
                                   cur_utility=[],
                                   relevance=[],
                                   congruence=[],
                                   blame=[],
                                   blame2=[],
                                   blame3=[],
                                   blame4=[],
                                   blame1_2=[],
                                   intended_blame=[],
                                   novelty=[],
                                   control=[],
                                   preControl=[],
                                   postControl=[])
        player_pre_utility = 0.0 # Assume that the players start with 0 utility
        try:
            for step, step_data in data.data.items():

                # if step < len(data.data.items()) and step != len(data.data.items())-1:
                #     next_step = step+1
                # next_step_data = data.data[next_step]
                # next_traj_debug = next_step_data["AGENT_DEBUG"]
                # next_traj_agent = next_step_data['WORLD'].agents[agent]
                # next_player_decision_key = list(next_traj_debug[agent]["__decision__"])[0]




                # traj_world = step_data["TRAJECTORY"][0]
                traj_agent = step_data['WORLD'].agents[agent]
                b_agent = step_data['WORLD'].agents[blame_agent]
                traj_debug = step_data["AGENT_DEBUG"]
                # step_action = str(step_data["TRAJECTORY"][1]).split("\t")[1]
                # step_action = list(step_data["TRAJECTORY"][1]._domain.values())[0]
                step_action = str(step_data["WORLD"].getFeature(f"{agent}'s __ACTION__")).split("\t")[1]
                a_loc = self.__get_agent_loc(step_data["WORLD"], agent)
                b_loc = self.__get_agent_loc(step_data["WORLD"], blame_agent)
                a_role = self.__get_agent_role(step_data["WORLD"], agent)
                b_role = self.__get_agent_role(step_data["WORLD"], blame_agent)

                # player_loc = traj_world.getFeature(f"{agent}'s loc", traj_agent.world.state)
                player_decision_key = list(traj_debug[agent]["__decision__"])[0] #This is because I don't knwo what the numbers appended to the player name are going to be
                blamed_decision_key = list(traj_debug[blame_agent]["__decision__"])[0]
                # player_cur_utility = traj_debug[agent]["__decision__"][player_decision_key]["V*"
                player_cur_utility = traj_agent.reward()
                legal_actions = traj_agent.getLegalActions()
                # cur_action = traj_agent.getState('__ACTION__').domain()[0]
                cur_action = traj_debug[agent]["__decision__"][player_decision_key]["action"]
                cur_blamed_action = traj_debug[blame_agent]["__decision__"][blamed_decision_key]["action"]

                player_appraisal = ad.PlayerAppraisal()
                player_appraisal.motivational_relevance = ad.motivational_relevance(player_pre_utility, player_cur_utility)
                player_appraisal.motivational_congruence = ad.motivational_congruence(player_pre_utility, player_cur_utility)
                player_appraisal.blame = ad.blame(player_pre_utility, player_cur_utility)
                player_appraisal.intended_blame = ad.intended_blame(player_pre_utility, player_cur_utility, player_pre_utility, player_cur_utility)
                player_appraisal.blame2 = ad.blame2(cur_action, traj_debug[agent]["__decision__"][player_decision_key])
                player_appraisal.blame1_2 = ad.blame1_2(step_data["WORLD"], traj_agent, b_agent, traj_debug)
                player_appraisal.blame3 = ad.blame3(step_data["WORLD"], traj_agent, b_agent, traj_debug)
                player_appraisal.blame4 = ad.blame4(step_data["WORLD"], traj_agent, b_agent, traj_debug)
                player_appraisal.control = ad.control(traj_debug[agent]["__decision__"][player_decision_key], traj_agent)
                player_appraisal.postControl = ad.postControl(traj_debug[agent]["__decision__"][player_decision_key], traj_agent)
                # player_appraisal.preControl = ad.preControl(next_traj_debug[agent]["__decision__"][next_player_decision_key], next_traj_agent)

                # extract the possible actions and corresponding rewards from the trajectory
                agent_decision = traj_debug[agent]["__decision__"]
                expected_rewards = ad.extract_expected_action_reward(agent_decision, agent)
                num_possible_actions = len(expected_rewards)
                # get the position in the dict
                projected_actions = list(expected_rewards.keys())
                cur_action_rank = 0
                if cur_action in projected_actions:
                    cur_action_rank = projected_actions.index(cur_action)

                player_appraisal.novelty = ad.novelty(num_possible_actions, cur_action_rank)
                # player_appraisal.accountable = ad.accountability(...) # TODO: figure out who should be the observer (maybe this doesn't work in single player?)
                # player_appraisal.control = #TODO: figure out how to do the projected action stuff

                step_appraisal_info['step'].append(step)
                step_appraisal_info['a_loc'].append(str(a_loc))
                step_appraisal_info['b_loc'].append(str(b_loc))
                step_appraisal_info['a_role'].append(str(a_role))
                step_appraisal_info['b_role'].append(str(b_role))
                step_appraisal_info['a_action'].append(str(cur_action))
                step_appraisal_info['b_action'].append(str(cur_blamed_action))
                step_appraisal_info['pre_utility'].append(player_pre_utility)
                step_appraisal_info['cur_utility'].append(player_cur_utility)
                step_appraisal_info['relevance'].append(player_appraisal.motivational_relevance)
                step_appraisal_info['congruence'].append(player_appraisal.motivational_congruence)
                step_appraisal_info['blame'].append(player_appraisal.blame)
                step_appraisal_info['blame2'].append(player_appraisal.blame2)
                step_appraisal_info['blame1_2'].append(player_appraisal.blame1_2)
                step_appraisal_info['blame3'].append(player_appraisal.blame3)
                step_appraisal_info['blame4'].append(player_appraisal.blame3)
                step_appraisal_info['intended_blame'].append(player_appraisal.intended_blame)
                step_appraisal_info['novelty'].append(player_appraisal.novelty)
                step_appraisal_info['control'].append(player_appraisal.control)
                step_appraisal_info['postControl'].append(player_appraisal.postControl)
                step_appraisal_info['preControl'].append(player_appraisal.preControl)

                player_pre_utility = player_cur_utility # TODO: should this be cumulative?

            output_data = pd.DataFrame.from_dict(step_appraisal_info)
            return TABLE_TYPE, output_data.T

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

    def __get_agent_loc(self, world_state, agent):
        locations = [x for x in world_state.locals[agent].keys() if "Loc" in x]
        for loc in locations:
            p_loc = str(world_state.getFeature(f"{agent}'s {loc}")).split("\t")[1]
            if p_loc == "True":
                return loc

    def __get_agent_role(self, world_state, agent):
        roles = [x for x in world_state.locals[agent].keys() if "isRole" in x]
        for r in roles:
            p_role = str(world_state.getFeature(f"{agent}'s {r}")).split("\t")[1]
            if p_role == "True":
                return r