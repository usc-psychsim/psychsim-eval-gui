"""
Functions for appraisal dimensions
"""
import math
from dataclasses import dataclass
import csv
import os
import ast
import pickle

import pandas
import pandas as pd
import psychsim_gui_helpers as pgh

# TODO: REFACTOR THIS (think about creating psychsim access functions)

# TODO: make this whole thing a class
@dataclass
class PlayerAppraisal:
    """
    Class to hold appraisal dimension info
    """
    motivational_relevance: float = None
    motivational_congruence: float = None
    coerced: bool = False
    accountable: bool = False
    blame: float = None
    intended_blame: bool = False
    blame2: bool = False
    blame3: float = None
    blame1_2: float = None
    novelty: float = None
    consistency: float = None
    control: float = None
    preControl: float = None
    postControl: float = None
    surprise: bool = False


class AppraisalDimensions:
    def __init__(self):
        self.player_pre_utility: float = 0.0
        self.player_appraisal = PlayerAppraisal()
        self.step_appraisal_info = dict(step=[],
                                   # a_loc=[],
                                   # b_loc=[],
                                   # a_role=[],
                                   # b_role=[],
                                   a_action=[],
                                   a_proj_action=[],
                                   a_expected_b=[],
                                   b_action=[],
                                   # b_expected_a=[],
                                   pre_utility=[],
                                   cur_utility=[],
                                   cur_expected_utility=[],
                                   # relevance=[],
                                   # congruence=[],
                                   # blame=[],
                                   # blame2=[],
                                   a_blames_b=[],
                                   # blame4=[],
                                   # blame1_2=[],
                                   # intended_blame=[],
                                   # control=[],
                                   general_control=[],
                                   specific_control=[],
                                   # cur_action_desired=[],
                                   desirability=[],
                                   a_surprised_at_b=[])

    # def extract_expected_action_reward(self, player_decision, player_name):
    #     """
    #     Return a dictionary with actions: expected_reward
    #     player_decision = decision object returned by psychsim
    #     player_name = name of player
    #     """
    #     actions = {}
    #     for k, v in player_decision.items():
    #         if player_name in k:
    #             for k1, v1 in v.items():
    #                 if k1 == "V":
    #                     actions = {k2: v2["__ER__"][-1] for k2, v2 in v1.items()}
    #     return actions


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


    def blame(self, team_pre_utility, team_cur_utility):
        """
        Did the actor take an action that negatively impacted the team?
        i.e. did the action that the actor took
        return: scale of team utility difference

        team_pre_utility: utility of team before action
        team_cur_utility: utility of team after action
        """
        # If the actor did anything to negatively impact the team, they are to blame
        return team_cur_utility - team_pre_utility


    def intended_blame(self, actor_pre_utility, actor_cur_utility, team_pre_utility, team_cur_utility):
        """
        Did the agent take an agent that negatively impacted the team, but positively impacted themselves?
        i.e. did the action that the actor took

        actor_pre_utility: utility of actor before action
        actor_cur_utility: utility of actor after action
        team_pre_utility: utility of team before action
        team_cur_utility: utility of team after action
        """
        # did the actor's action negatively affect the team?
        if team_cur_utility < team_pre_utility:
            # did the actor's action benefit the actor? - if so they are to blame
            if actor_cur_utility > actor_pre_utility:
                return True
            # did the actor's action negatively benefit the actor? if so - they are not to blame
            elif actor_cur_utility < actor_pre_utility:
                return False
        # if there was no change in utility then the actor isn't to blame
        return False


    def blame2(self, action, player_decision):
        """
        Did the actor take an action that wasn't the best (for the team - or for the actor who is asking)
        TODO: fix this
            for multi-player (the player_decision should be the belief about another player's decision) - this assumes the
            '__EV__' here corresponds to the observing player's utility not the expected utility of the observed player

        player_decision: decision object of the player from psychsim
        """
        # -- FOR USE WITH 'random' SELECTION
        # actual_action = player_decision['action']
        # actual_action_utility = player_decision['V'][actual_action]['__EV__']
        # for action in player_decision['V']:
        #     if action['__EV__'] > actual_action_utility: # the player could have taken a better option
        #         return True
        # return False

        # -- FOR USE WITH 'distribution' SELECTION
        actual_action_utility = player_decision['V'][action]['__EV__']
        for k, v in player_decision['V'].items():
            if v['__EV__'] > actual_action_utility:  # the player could have taken a better option
                return True
        return False

    # FOR BLAME FUNCTIONS: what is the psychological model of blame?
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

    def blame7():
        """
        did an agent take an action based on a false belief about the world that lead to a negative outcome?
        """

    def _extract_vars_from_psychim(self, world, agent, blamed_agent, debug):
        # agent_action = agent.getState("__ACTION__")
        agent_decision_key = list(debug[agent.name]["__decision__"])[0]
        agent_action = debug[agent.name]["__decision__"][agent_decision_key]["action"]
        agent_belief = debug[agent.name]["__decision__"][agent_decision_key]["V"][agent_action]["__beliefs__"]
        agent_state = debug[agent.name]["__decision__"][agent_decision_key]["V"][agent_action]["__S__"]
        cur_expected_utility = debug[agent.name]["__decision__"][agent_decision_key]["V"][agent_action]["__ER__"][0] #This is the expected reward for the current action
        cur_utility = agent.reward()

        # blamed_agent_action = blamed_agent.getState("__ACTION__")
        blamed_agent_decision_key = list(debug[blamed_agent.name]["__decision__"])[0]
        blamed_agent_action = debug[blamed_agent.name]["__decision__"][blamed_agent_decision_key]["action"]

        believed_action = world.getFeature(f"{blamed_agent.name}'s __ACTION__", agent_belief, unique=True)
        # if cur_utility < cur_expected_utility:
        # For all agent actions that lead to a higher utility - could blamed_agent have done something different?

        # get the possible actions in a nicer format
        possible_actions = debug[agent.name]["__decision__"][agent_decision_key]["V"]
        for action, value in possible_actions.items():
            value["blamed_predicted_action"] = world.getFeature(f"{blamed_agent.name}'s __ACTION__", value["__S__"][0], unique=True)
            value["blamed_predicted_utility"] = world.getFeature(f"{blamed_agent.name}'s __REWARD__", value["__S__"][0], unique=True)

        # get the agent decisions
        # agent_decision = debug[agent.name]["__decision__"][a_decision_key]

        # get the max reward for the agent
        agent_max_reward = agent.getState('__REWARD__').max()#TODO: why is this reward different to what is expected?

        return dict(possible_actions=possible_actions,
                    cur_utility=cur_utility,
                    blamed_agent_action=blamed_agent_action,
                    cur_expected_utility=cur_expected_utility,
                    believed_action=believed_action,
                    agent_max_reward=agent_max_reward)

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



    def preControl(self, player_decision, player):
        """
        agent's sense they are in control BEFORE action
        """
        # TODO: make this a percentage
        #TODO: Is this just the control of the next step?
        player_control = 0
        # for action, predictions in player_decision['V'].items():
        #     if predictions['__EV__'] > 0:
        #         player_control = player_control + 1
        return player_control

    def postControl(self, player_decision, player):
        """
        agent's sense they are in control AFTER action
        similar to control1 but just number of leaves
        """
        # TODO: forget about post control for now
        #TODO: look at Mei for this - . this needs to capture unexpected action of other agents
        player_control = 0
        for action, predictions in player_decision['V'].items():
            if predictions['__EV__'] > 0:
                player_control = player_control + 1
        return player_control

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


    def surprise(self, action, projected_action):
        """
        Compare an actual action taken by a player to a projected action as calculated by psychsim
        return: True if there is a difference, False if not
        """
        if action == projected_action:
            return False
        return True

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

    def get_appraisals_for_step_psychsim(self, agent, blame_agent, world, debug_dict, debug_pred_dict):
        """
        Populate all appraisal dimensions for a specific step from psychsim data
        """

        # TODO: make the appraisals a dict / pandas dataframe for easy use in the GUI
        a_agent = world.agents[agent]

        b_agent = world.agents[blame_agent]
        step_action = str(world.getFeature(f"{agent}'s __ACTION__")).split("\t")[1]

        player_decision_key = list(debug_dict[agent]["__decision__"])[0] #This is because I don't knwo what the numbers appended to the player name are going to be
        blamed_decision_key = list(debug_dict[blame_agent]["__decision__"])[0]
        player_cur_utility = a_agent.reward()
        cur_action = debug_dict[agent]["__decision__"][player_decision_key]["action"] # **This should be the actual action taken by the player
        proj_action = debug_pred_dict[agent]["__decision__"][player_decision_key]["action"] # **This should be the action projected by psychsim
        cur_blamed_action = debug_dict[blame_agent]["__decision__"][blamed_decision_key]["action"]

        params = self._extract_vars_from_psychim(world, a_agent, b_agent, debug_dict)

        self.step_appraisal_info['relevance'].append(self.motivational_relevance(self.player_pre_utility, player_cur_utility))
        self.step_appraisal_info['congruence'].append(self.motivational_congruence(self.player_pre_utility, player_cur_utility))
        self.step_appraisal_info['intended_blame'].append(self.intended_blame(self.player_pre_utility, player_cur_utility, self.player_pre_utility, player_cur_utility))
        self.step_appraisal_info['blame3'].append(self.blame3(params))
        self.step_appraisal_info['blame4'].append(self.blame4(params))
        self.step_appraisal_info['blame1_2'].append(self.blame1_2(params))
        self.step_appraisal_info['control'].append(self.control(params))
        self.step_appraisal_info['surprise'].append(self.surprise(cur_action, proj_action))

        self.step_appraisal_info['b_action'].append(cur_blamed_action)
        self.step_appraisal_info['a_action'].append(cur_action)
        self.step_appraisal_info['pre_utility'].append(self.player_pre_utility)
        self.step_appraisal_info['cur_utility'].append(player_cur_utility)

        self.player_pre_utility = player_cur_utility

    def get_appraisals_for_step_csv(self, csv_file):
        """
        Populate all appraisal dimensions for a specific step from a csv file
        """
        # TODO: refactor this (also for the psychsim based func) there are a few reused params going on...
        # read csv for agents
        csv_data = {}
        with open(csv_file, newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for step, row in enumerate(csv_reader):
                csv_data[step] = row
                # Convert the possible_action strings to actual dict objects
                csv_data[step]['b_possible_actions'] = ast.literal_eval(row['b_possible_actions'])
                csv_data[step]['a_possible_actions'] = ast.literal_eval(row['a_possible_actions'])
                cur_action = row['a_action'] # agent a is the target agent, b is the blamed agent
                player_cur_utility = float(row['a_current_utility'])
                player_cur_expected_utility = float(row['a_expected_utility'])
                cur_blamed_action = row['b_action']
                proj_action = row['a_proj_action']

                # Add the blamed actions to the possible actions
                for action, action_value in csv_data[step]['b_possible_actions'].items():
                    action_value["blamed_predicted_action"] = row['b_believed_other_agent_action']
                    action_value["blamed_predicted_utility"] = row['b_expected_utility']

                params = dict(blamed_agent_possible_actions=csv_data[step]['b_possible_actions'],
                              possible_actions=csv_data[step]['a_possible_actions'],
                              cur_utility=player_cur_utility,
                              blamed_agent_action=cur_blamed_action,
                              cur_expected_utility=player_cur_expected_utility,
                              believed_action=row['a_believed_other_agent_action'],
                              agent_max_reward=float(row['a_max_reward']))
                # TODO: populate the blamed action in the possible actions from the believed action column

                self.step_appraisal_info['step'].append(row['step'])

                self.step_appraisal_info['a_expected_b'].append(row['a_believed_other_agent_action'])
                # self.step_appraisal_info['b_expected_a'].append(row['b_believed_other_agent_action'])
                self.step_appraisal_info['a_proj_action'].append(row['a_proj_action'])

                # self.step_appraisal_info['relevance'].append(self.motivational_relevance(self.player_pre_utility, player_cur_utility))
                # self.step_appraisal_info['congruence'].append(self.motivational_congruence(self.player_pre_utility, player_cur_utility))
                # self.step_appraisal_info['blame'].append(self.blame(self.player_pre_utility, player_cur_utility))
                # self.step_appraisal_info['intended_blame'].append(self.intended_blame(self.player_pre_utility, player_cur_utility, self.player_pre_utility, player_cur_utility))
                # self.step_appraisal_info['blame2'].append(self.blame2(cur_action, debug_dict[agent]["__decision__"][player_decision_key]))
                self.step_appraisal_info['a_blames_b'].append(self.blame3(params))
                # self.step_appraisal_info['blame4'].append(self.blame4(params))
                # self.step_appraisal_info['blame1_2'].append(self.blame1_2(params))
                # self.step_appraisal_info['control'].append(self.control(params))
                self.step_appraisal_info['a_surprised_at_b'].append(self.surprise(row['b_action'], row['a_believed_other_agent_action']))

                self.step_appraisal_info['b_action'].append(cur_blamed_action)
                self.step_appraisal_info['a_action'].append(cur_action)
                self.step_appraisal_info['pre_utility'].append(self.player_pre_utility)
                self.step_appraisal_info['cur_utility'].append(player_cur_utility)
                self.step_appraisal_info['cur_expected_utility'].append(player_cur_expected_utility)
                # self.step_appraisal_info['cur_action_desired'].append(self.desirability(cur_action, row['a_possible_actions'])[0])
                self.step_appraisal_info['desirability'].append(self.desirability(params))
                self.step_appraisal_info['general_control'].append(self.control2(params))
                self.step_appraisal_info['specific_control'].append(self.control3(params))

                self.player_pre_utility = player_cur_utility

        self.normalise_appraisals("a_blames_b")
        pass

    def normalise_appraisals(self, appraisal_key):
        for i, value in enumerate(self.step_appraisal_info[appraisal_key]):
            if isinstance(value, (int, float)) and value > 0:
                self.step_appraisal_info[appraisal_key][i] = 1
            elif isinstance(value, (int, float)) and  value < 0:
                self.step_appraisal_info[appraisal_key][i] = -1

def save_query_pickle(query):
    dt_string, _ = pgh.get_time_stamp()
    output_directory = 'sim_output'
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    output_path = os.path.join(output_directory, f"{query.id}_{dt_string}.pickle")
    pickle.dump(query, open(output_path, "wb"))
    print(f"{query.id} saved to: {output_path}")

if __name__ == "__main__":
    ad = AppraisalDimensions()
    csv_file = os.path.join("2agent_test_blame.csv")
    ad.get_appraisals_for_step_csv(csv_file)
    # convert to dict and save as query for GUI
    query_data = pandas.DataFrame(ad.step_appraisal_info).T
    query = pgh.PsySimQuery(id="2agentTest", params=[], function="tset",
                        results=query_data, result_type="table")
    save_query_pickle(query)
    pass