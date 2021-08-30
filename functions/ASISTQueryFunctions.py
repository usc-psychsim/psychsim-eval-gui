"""
Query function definitions used by psychsim gui

TODO: fix this bit defining what the data should look like from the sim scripts
dict contatining the folloiwng:
                        "WORLD": self.world (psychsim world object)
                        "AGENT_DEBUG": result (Debug dictionary from world.step)
                        "AGENTS": self.agents (list contianing agents)
"""

# TODO:
#  [ ]Make it so the params define the function which they should take a variable (e.g. action comes from get_action)
#   -[ ]document this
#   -[ ]test the whole structure still works when this isn't done (just by defining functions and setting variables from wherever)


import pandas as pd
import numpy as np
import traceback
from random import randint

from appraisal import appraisal_dimensions as ad
import psychsim_gui_helpers as pgh

TREE_TYPE = 'tree'
TABLE_TYPE = 'table'


class ASISTQueryFunctions:
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

    def get_agents(self, data: pgh.PsychSimRun=None):
        """
        get list of agents in the data. Data must be a PsychSimRun class

        :param data: Data from sim script
        :return: Dataframe containing the agents
        :rtype: pandas.DataFrame
        """

        agent_dict = dict(agent=[])
        if data:
            for step_data in data.data.values():
                if type(step_data['AGENT_DEBUG']) == dict:
                    for agent in step_data['AGENT_DEBUG'].keys():
                        if agent not in agent_dict['agent']:
                            agent_dict['agent'].append(agent)
        output_data = pd.DataFrame.from_dict(agent_dict)
        return TABLE_TYPE, output_data.T

    def get_actions(self, data: pgh.PsychSimRun=None, agent: str=None):
        """
        Return actions taken by a specific agent, and their corresponding steps

        :param data: Data from sim script
        :param agent: string (key) Agent whose actions will be returned
        :return: Dataframe containing the actions for the agent
        :rtype: pandas.DataFrame
        """
        actions_dict = dict(step=[], action=[])
        try:
            for step, step_data in data.data.items():
                actions_dict['step'].append(step)
                action = str(step_data['WORLD'].agents[agent].getState("__ACTION__")).split('\t')[1]
                actions_dict['action'].append(f"{step}:{action}")
        except:
            tb = traceback.format_exc()
            print(tb)

        output_data = pd.DataFrame.from_dict(actions_dict)
        return TABLE_TYPE, output_data.T

    def get_action_choice(self, data: pgh.PsychSimRun=None, agent: str=None, action: str=None):
        """
         action specific query, which can be used to look at overall reasoning of a planning agent.

         This function answers the question "what was the agent's reasoning for taking the eventual action.
         It shows the hypothetical actions and rewards that were used to decide on the current action.

        :param data: Data from sim script
        :param agent: agent to query
        :param action: action to query. This is actually the step value of the action
        :return: Tree data
        """
        try:
            step = int(action.split(":")[0])
            agent_decision = next(iter(data.data[step]['AGENT_DEBUG'][agent]["__decision__"].items()))[1]
            world = data.data[step]['WORLD']
            output_data = pd.DataFrame()
            for la_key, legal_action in agent_decision["V"].items():
                for idx, hyp_action_set in enumerate(legal_action['__S__']):
                    index = []
                    hyp_action = world.symbolList[hyp_action_set.marginal(f"{agent}'s __ACTION__").max()]
                    hyp_reward = legal_action["__ER__"][idx]
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

    def get_individual_agent_beliefs_values(self,  data: pgh.PsychSimRun=None, agent: str=None):
        """
        return a dataframe of beliefs for the agent at each step

        :param data: Data from sim script
        :param agent: agent to query
        :return: Dataframe containing the actions and beliefs for the selected agent
        """
        try:
            steps = {}
            for step, step_data in data.data.items():
                world = step_data["WORLD"]
                beliefs = world.agents[agent].getBelief(world.state)
                steps[step] = pd.DataFrame(self.__extract_values_fromVectorDistributionSet(list(beliefs.values())[0], world))

            #append all the horizons to one dictionary
            all_steps = pd.concat(steps.values())
            all_steps.insert(loc=0, column='step', value=pd.Series(list(steps.keys()), index=all_steps.index))
            all_steps = all_steps.set_index('step', drop=False).T
            return TABLE_TYPE, all_steps
        except:
            tb = traceback.format_exc()
            print(tb)

    def get_world_state(self,  data: pgh.PsychSimRun=None):
        """
        Get the world state across steps

        :param data: Data from sim script
        :return: world state at each step
        """
        try:
            steps = {}
            for step, step_data in data.data.items():
                world = step_data["WORLD"]
                steps[step] = pd.DataFrame(self.__extract_values_fromVectorDistributionSet(world.state, world))
            all_steps = pd.concat(steps.values())
            all_steps.insert(loc=0, column='step', value=pd.Series(list(steps.keys()), index=all_steps.index))
            all_steps = all_steps.set_index('step', drop=False).T

            return TABLE_TYPE, all_steps
        except:
            tb = traceback.format_exc()
            print(tb)

    def get_world_state_long(self,  data: pgh.PsychSimRun=None):
        """
        Get the world state across steps but in long format

        :param data: Data from sim script
        :return: world state at each step
        """
        try:
            steps = {}
            for step, step_data in data.data.items():
                world = step_data["WORLD"]
                steps[step] = pd.DataFrame(self.__extract_values_fromVectorDistributionSet(world.state, world))
            all_steps = pd.concat(steps.values())
            all_steps.insert(loc=0, column='step', value=pd.Series(list(steps.keys()), index=all_steps.index))
            all_steps = all_steps.set_index('step', drop=False).T

            # --- Get Long data ----
            df1 = all_steps.T.melt(id_vars=['step'],
                                   value_vars=["Agent A's __ACTION__", "Agent B's __ACTION__"],
                                   var_name='Agent', value_name='Action')
            df1["Agent"] = df1["Agent"].str.split("'", n = 1, expand = True)[0]
            df1["Action"] = df1["Action"].map(str)
            df2 = all_steps.T.melt(id_vars=['step'],
                                   value_vars=["Agent A's __REWARD__", "Agent B's __REWARD__"],
                                   var_name='Agent', value_name='Reward')
            df2["Agent"] = df2["Agent"].str.split("'", n = 1, expand = True)[0]
            df1 = df1.set_index(['step', df1.groupby(['step']).cumcount()])
            df2 = df2.set_index(['step', df2.groupby(['step']).cumcount()])
            df3 = (pd.concat([df1, df2],axis=1)
                   .sort_index(level=1)
                   .reset_index(level=1, drop=True)
                   .reset_index())
            df3 = df3.loc[:,~df3.columns.duplicated()]

            return TABLE_TYPE, df3.T
        except:
            tb = traceback.format_exc()
            print(tb)

    def get_appraisal_dimensions(self,  data: pgh.PsychSimRun=None, agent: str=None, blame_agent: str=None, normalise=False):
        """
        Get the appraisal dimensions

        :param data: Data from sim script
        :param agent: name of target agent
        :type agent: str
        :param blame_agent: name of other agent (agent to blame)
        :return: player appraisals at each step
        """
        player_ad = ad.AppraisalDimensions()
        try:
            step_appraisals = []
            for step, step_data in data.data.items():
                # Get params
                params = player_ad.get_appraisal_params_psychsim(agent=agent,
                                                                 blame_agent=blame_agent,
                                                                 world=step_data["WORLD"],
                                                                 debug_dict=step_data["AGENT_DEBUG"],
                                                                 debug_pred_dict=step_data["AGENT_DEBUG"])
                # Get appraisals for each step
                appraisal = player_ad.get_appraisals_for_step(params, normalise=normalise)
                appraisal.step = step
                step_appraisals.append(appraisal)
            # Return the appraisals as a dataframe
            return TABLE_TYPE, pd.DataFrame(step_appraisals).T
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