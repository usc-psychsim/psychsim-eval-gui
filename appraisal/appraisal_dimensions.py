"""
Functions for appraisal dimensions
"""
import math
from dataclasses import dataclass, asdict
import csv
import os
import ast
import pickle

import pandas
import pandas as pd
import psychsim_gui_helpers as pgh

# TODO: REFACTOR THIS (think about creating psychsim access functions)


@dataclass
class PlayerAppraisalInfo:
    """
    Class to hold appraisal dimension info
    """
    step: int = None
    a_action: str = None
    a_proj_action: str = None
    a_expected_b: str = None
    b_action: str = None
    pre_utility: float = None
    cur_utility: float = None
    cur_expected_utility: float = None
    motivational_relevance: float = None
    motivational_congruence: float = None
    blame3: float = None
    blame1_2: float = None
    novelty: float = None
    consistency: float = None
    control: float = None
    surprise: bool = False
    desirability: float = None
    general_control: float = None
    specific_control: bool = False
    memory_control: float = None


class AppraisalDimensions:
    def __init__(self):
        self.player_pre_utility: float = 0.0
        self.actions_todo = []


    def motivational_relevance(self, pre_utility, cur_utility):
        """
        Motivational relevance evaluates the extent to which an encounter touches upon personal goals"
        Utility is essentially the agent's reward (from getReward)
        cur_utility: utility after event has happened (utility = state*goals) -> goals = reward functions
        pre_utility: utility before event has happened
        """
        m_rel = abs((cur_utility - pre_utility))
        return m_rel


    def motivational_congruence(self, pre_utility, cur_utility):
        """
        Motivational congruence or incongruence measures the extent to which the encounter thwarts or facilitates
        personal goals

        cur_utility: utility after event has happened
        pre_utility: utility before event has happened
        """
        m_con = (cur_utility - pre_utility)
        return m_con

    def blame1_2(self, blame_params):
        """
        Did the blamed_agent take an unexpected action that negatively affected the agent?
        """
        if blame_params["cur_utility"] < blame_params["cur_expected_utility"]:
            # someone is to blame
            # Does the action that agent1 believes agent 2 would take match what action agent 2 actually took?
            if blame_params["blamed_agent_action"] != blame_params["believed_action"]:
                # The agent to blame did not do what was expected so is to blame proportionally to utility loss
                return blame_params["cur_utility"] - blame_params["cur_expected_utility"]
            pass
        return 0

    def blame3(self, blame_params):
        """
        from perspective of one agent1, could agent2 take better action
        i.e. Did the blamed_agent take an unexpected action that negatively affected the agent AND could the balmed_agent have done something different?
        """
        cumulative_blame = 0
        for k, p_action in blame_params["blamed_agent_possible_actions"].items():
            cur_predicted_utility = p_action["__ER__"][0] #TODO: check that this is indeed the utility that they should get for this action (i.e. not the actions in the future that haven't taken place  yet)
            if blame_params["cur_utility"] <= cur_predicted_utility:
                if blame_params["blamed_agent_action"] != p_action["blamed_predicted_action"]:
                    # blamed_agent is to blame because they could have taken a different action that would have resulted in better utility (according to agent)
                    cumulative_blame = cumulative_blame + (blame_params["cur_expected_utility"] - blame_params["cur_utility"]) #TODO: make sure this bit actually makes sense
        return cumulative_blame


    def blame4(self, blame_params):
        """
        from perspective of one agent could different agent take action that was not negative for other agent but better for perspective agent
        essentially this is the same as blame3 but with the added constraint that the action must have a positive outcome for the blame dagent (or at least non negative)
        """
        cumulative_blame = 0
        for k, p_action in blame_params["possible_actions"].items():
            cur_predicted_utility = p_action["__ER__"][0] #TODO: check that this is indeed the utility that they should get for this action (i.e. not the actions in the future that haven't taken place  yet)
            if blame_params["cur_utility"] <= cur_predicted_utility:
                if blame_params["blamed_agent_action"] != p_action["blamed_predicted_action"] and p_action["blamed_predicted_utility"] >= 0:
                    # blamed_agent is to blame because they could have taken a different action that would have resulted in better utility (according to agent)
                    cumulative_blame = cumulative_blame + (blame_params["cur_utility"] - blame_params["cur_expected_utility"]) #TODO: make sure this bit actually makes sense
        return cumulative_blame


    def control(self, control_params):
        """
        This is a probability. For each predicted action that delivers a positive utility change, sum the probabilities.
        that is the control
        player_decision: decision object of the player from psychsim
        """
        player_control = 0
        for action, predictions in control_params["possible_actions"].items():
            if predictions['__EV__'] > 0:
                # player_control = player_control + player_decision['action'][action]
                player_control = player_control + control_params["agent_max_reward"]
        return player_control

    def control2(self, params):
        """
        If something bad has happened (negatively unexpected utility), does the agent have an action to rectify it (i.e. have any positive effect on their utility)?
        """
        # TODO: make sure all these params are relevant to one agent looking at another agent
        # are we in a 'bad' situation (we have less utility than we expected)
        control = 0
        if params["cur_utility"] < params["cur_expected_utility"]:
            for k, p_action in params["possible_actions"].items():
                predicted_utility = p_action["__ER__"][0]
                if predicted_utility > 0:
                    # There is an action that can at least start to rectify the 'bad' situation
                    control += 1
        return control

    def control3(self, params):
        """
        If an agent didn't do a specific expected action that should have had a positive utility, can this agent do that action?
        """
        control = False
        # Did the other agent do something we didn't expect?
        if params["blamed_agent_action"] != params["believed_action"]:
            # are we in a 'bad' situation (we have less utility than we expected)?
            if params["cur_utility"] < params["cur_expected_utility"]:
                for p_action_name, p_action in params["possible_actions"].items(): # TODO: (This should be our possible actions)
                    if p_action_name == params["believed_action"]:
                        # We can do the action the other agent didn't do
                        control = True
        return control

    def control4(self, params):
        """
        Similar to control3 BUT:
        A player has 'memory' so if they blame someone for a bad action, they will not feel in control until they have it
        in their power to rectify the situation, that might come a few actions later.
        This is done by checking at each step if they need to resolve something, if another player does it, and if they can do it
        """
        # todo: maybe get rid of control3 as this basically does the same thing...
        control = False
        # Did the other agent do something we didn't expect?
        if params["blamed_agent_action"] != params["believed_action"]:
            # are we in a 'bad' situation (we have less utility than we expected)?
            if params["cur_utility"] < params["cur_expected_utility"]:
                for p_action_name, p_action in params["possible_actions"].items(): # TODO: (This should be our possible actions)
                    if p_action_name == params["believed_action"]:
                        # We can immediately do the action the other agent didn't do
                        control = True
                    else:
                        # we need to remember to come back to this later
                        self.actions_todo.append(params["believed_action"]) # todo: make this also have a decay factor (priority might be in their reward function so don't worry bout it)
                        control = False
        return control

    def control5(self, params):
        """
        This checks the 'memory' at each step to see if we now have control
        """
        # TODO: combine this with other control functions

        # Check to see if we can rectify any of the issues in our "to_do" list
        for idx, action in  enumerate(self.actions_todo):
            # First, check to see if the other agent is doing that action
            if action == params["blamed_agent_action"]:
                # remove that action and exit with no control
                self.actions_todo.pop(idx)
                return 0
            # Second, check to see if we have the capability of fixing the issue
            if action in params["possible_actions"]:
                # we have the power to fix the issue we encountered before, therefore we have control
                return 1
        return 0


    def novelty(self, num_possible_actions, action_rank):
        """
        how novel (unexpected) an action is compared to agent's beliefs
        num_possible_actions: the number of possible actions that can be taken
        action_rank: the rank of the action (actions are ranked from lowest to highest utility)
        """
        # TODO: fix this to take into account environment
        return 1 - consistency(num_possible_actions, action_rank)


    def consistency(self, num_possible_actions, action_rank):
        """
        How consistent (expected) an action is compared an agent's beliefs
        num_possible_actions: the number of possible actions that can be taken
        action_rank: the rank of the action (actions are ranked from lowest to highest utility)
        """
        # TODO: Question - what if actions are equally ranked? Should they just count as one action?
        denom = 0
        for i in range(num_possible_actions):
            denom = denom + math.exp(i)
        return math.exp(action_rank) / denom

    def surprise(self, params):
        """
        Compare an actual action taken by a player to a projected action as calculated by psychsim
        return: True if there is a difference, False if not
        """
        if params['blamed_agent_action'] == params['believed_action']:
            return 0
        return 1

    def desirability(self, params):
        """
        This is a measure of how much utility has been lost by an unexpected negative action
        """
        # If you blame the other agent (they did something bad for you but could have done something better)
        lost_utility = 0
        if self.blame3(params):
            # Calculate the difference in utility and what we should have gotten if the other agent did the right thing
            lost_utility = params["blamed_agent_possible_actions"][params["believed_action"]]["__EV__"]
        return -lost_utility


    def get_appraisals_for_step(self, params):
        """
        Calculate all the appraiasl dimensions for a particiular step
        """
        appraisals = PlayerAppraisalInfo()

        # TODO: refactor all these so they only take in the params they need (pass the params from params object here)
        appraisals.blame3 = self.blame3(params)
        appraisals.desirability = self.desirability(params)
        appraisals.general_control = self.control2(params)
        appraisals.specific_control = self.control4(params)
        appraisals.memory_control = self.control5(params)
        appraisals.surprise = self.surprise(params)
        appraisals.a_action = params["cur_action"]
        appraisals.a_proj_action = params["projected_action"]
        appraisals.a_expected_b = params["believed_action"]
        appraisals.b_action = params["blamed_agent_action"]
        appraisals.pre_utility = params["pre_utility"]
        appraisals.cur_utility = params["cur_utility"]
        appraisals.cur_expected_utility = params["cur_expected_utility"]
        return appraisals

    def get_appraisal_params_csv(self, csv_row):
        """
        get the params in an appropriate format for the appraisal functions from csv data
        The csv format defines: agent_a = target agent, agent_b = blamed agent
        """
        # Add the blamed actions to the possible actions
        csv_row['b_possible_actions'] = ast.literal_eval(csv_row['b_possible_actions'])
        csv_row['a_possible_actions'] = ast.literal_eval(csv_row['a_possible_actions'])
        for action, action_value in csv_row['b_possible_actions'].items():
            action_value["blamed_predicted_action"] = csv_row['b_believed_other_agent_action']
            action_value["blamed_predicted_utility"] = csv_row['b_expected_utility']

        params = dict(cur_action=csv_row['a_action'],
                      projected_action=csv_row['a_proj_action'],
                      blamed_agent_possible_actions=csv_row['b_possible_actions'],
                      possible_actions=csv_row['a_possible_actions'],
                      cur_utility=float(csv_row['a_current_utility']),
                      pre_utility=self.player_pre_utility,
                      blamed_agent_action= csv_row['b_action'],
                      cur_expected_utility= float(csv_row['a_expected_utility']),
                      believed_action=csv_row['a_believed_other_agent_action'],
                      agent_max_reward=float(csv_row['a_max_reward']))
        # Update the pre utility
        self.player_pre_utility = float(csv_row['a_current_utility'])
        return params

    def get_appraisal_params_psychsim(self, agent, blame_agent, world, debug_dict, debug_pred_dict):
        """
        get the params in an appropriate format for the appraisal functions from psychsim data
        """
        a_agent = world.agents[agent]
        player_decision_key = list(debug_dict[agent]["__decision__"])[0] #This is because I don't knwo what the numbers appended to the player name are going to be
        blamed_decision_key = list(debug_dict[blame_agent]["__decision__"])[0]
        player_cur_utility = a_agent.reward()
        cur_action = debug_dict[agent]["__decision__"][player_decision_key]["action"] # **This should be the actual action taken by the player
        proj_action = debug_pred_dict[agent]["__decision__"][player_decision_key]["action"] # **This should be the action projected by psychsim
        cur_blamed_action = debug_dict[blame_agent]["__decision__"][blamed_decision_key]["action"]
        cur_expected_utility = debug_dict[agent]["__decision__"][player_decision_key]["V"][cur_action]["__ER__"][0]
        agent_belief = debug_dict[agent]["__decision__"][player_decision_key]["V"][cur_action]["__beliefs__"]
        agent_max_reward = a_agent.getState('__REWARD__').max()
        believed_action = world.getFeature(f"{blame_agent}'s __ACTION__", agent_belief, unique=True)
        possible_actions = debug_dict[agent]["__decision__"][player_decision_key]["V"]
        for action, value in possible_actions.items():
            value["blamed_predicted_action"] = world.getFeature(f"{blame_agent}'s __ACTION__", value["__S__"][0], unique=True)
            value["blamed_predicted_utility"] = world.getFeature(f"{blame_agent}'s __REWARD__", value["__S__"][0], unique=True)

        blamed_possible_actions = debug_dict[blame_agent]["__decision__"][blamed_decision_key]["V"]

        params = dict(cur_action=cur_action,
                      projected_action=proj_action,
                      blamed_agent_possible_actions=blamed_possible_actions,
                      possible_actions=possible_actions,
                      cur_utility=player_cur_utility,
                      pre_utility=self.player_pre_utility,
                      blamed_agent_action=cur_blamed_action,
                      cur_expected_utility=cur_expected_utility,
                      believed_action=believed_action,
                      agent_max_reward=agent_max_reward)
        # Update the pre utility
        self.player_pre_utility = player_cur_utility
        return params

    def get_appraisals_from_csv(self, csv_file):
        """
        Get appraisals for each step in a csv file
        """
        step_appraisals = []
        with open(csv_file, newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for step, row in enumerate(csv_reader):
                # Get the params for calculating the appraisals
                params = self.get_appraisal_params_csv(row)
                # Calculate the appraisals for each step
                appraisal = self.get_appraisals_for_step(params)
                appraisal.step = step
                step_appraisals.append(appraisal)

        # Return the appraisals as a dataframe
        return pd.DataFrame(step_appraisals).T


    def get_appraisals_from_psychsim(self, psychsim_data, agent, blamed_agent):
        """
        Get appraisals for each step from psychsim
        """
        step_appraisals = []
        for step, step_data in psychsim_data.items():
            # Get params
            params = self.get_appraisal_params_psychsim(agent, agent, step_data["WORLD"], step_data["AGENT_DEBUG"], step_data["AGENT_DEBUG"])
            # Get appraisals for each step
            appraisal = self.get_appraisals_for_step(params)
            appraisal.step = step
            step_appraisals.append(appraisal)
        # Return the appraisals as a dataframe
        return pd.DataFrame(step_appraisals).T

    def normalise_appraisals(self, appraisal_key):
        for i, value in enumerate(self.step_appraisal_info[appraisal_key]):
            if isinstance(value, (int, float)) and value > 0:
                self.step_appraisal_info[appraisal_key][i] = 1
            elif isinstance(value, (int, float)) and  value < 0:
                self.step_appraisal_info[appraisal_key][i] = -1


if __name__ == "__main__":
    ad = AppraisalDimensions()
    csv_file = os.path.join("2agent_test_blame.csv")
    query_data = ad.get_appraisals_from_csv(csv_file)
    # convert to dict and save as query for GUI
    query = pgh.PsySimQuery(id="2agentTest", params=[], function="tset",
                        results=query_data, result_type="table")
    pgh.save_query_pickle(query)
    pass