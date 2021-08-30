"""
Functions for appraisal dimensions
"""
from dataclasses import dataclass
import csv
import ast
import pandas as pd


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
    blame1: float = None
    blame2: float = None
    blame3: float = None
    control: float = None
    control2: int = None
    general_control: float = None
    specific_control: int = None
    surprise: float = None
    desirability: float = None
    memory_control: float = None


class AppraisalDimensions:
    """
    Class with methods to calculate appraisal dimensions
    """
    def __init__(self):
        self.player_pre_utility: float = 0.0
        self.actions_todo = []

    def motivational_relevance(self, pre_utility, cur_utility):
        """
        Motivational relevance evaluates the extent to which an encounter touches upon personal goals"
        Utility is essentially the agent's reward (from getReward). (utility = state*goals) -> goals = reward functions

        :param pre_utility: utility before event has happened
        :param cur_utility: utility after event has happened
        :return: motivational relevance
        :rtype: float
        """
        m_rel = abs((cur_utility - pre_utility))
        return m_rel

    def motivational_congruence(self, pre_utility, cur_utility):
        """
        Motivational congruence or incongruence measures the extent to which the encounter thwarts or facilitates
        personal goals

        :param pre_utility: utility before event has happened
        :param cur_utility: utility after event has happened
        :return: motivational congruence
        :rtype: float
        """
        m_con = (cur_utility - pre_utility)
        return m_con

    def blame1(self, cur_utility, cur_expected_utility, blamed_agent_action, believed_action):
        """
        Did the blamed_agent take an unexpected action that negatively affected the agent?

        :param cur_utility:  Utility after event has happened.
        :param cur_expected_utility:  Expected utility after event has happened.
        :param blamed_agent_action: Action that the other agent took.
        :param believed_action: Action the target agent believed the other agent took
        :return: Blame that target agent places on blamed agent.
        :rtype: float
        """

        if cur_utility < cur_expected_utility:
            # someone is to blame
            # Does the action that agent1 believes agent 2 would take match what action agent 2 actually took?
            if blamed_agent_action != believed_action:
                # The agent to blame did not do what was expected so is to blame proportionally to utility loss
                return abs(cur_utility - cur_expected_utility)
            pass
        return 0.0

    def blame2(self, cur_utility, cur_expected_utility, blamed_agent_action, blamed_agent_possible_actions):
        """
        from perspective of one agent could different agent take action that was not negative for other agent but better
        for perspective agent essentially this is the same as blame3 but with the added constraint that the action must
        have a positive outcome for the blamed agent (or at least non negative)

        :param cur_utility:  Utility after event has happened.
        :param cur_expected_utility:  Expected utility after event has happened.
        :param blamed_agent_action: Action that the other agent took.
        :param blamed_agent_possible_actions: Possible actions that the other agent could have taken.
        :return: Cumulative blame that target agent places on blamed agent.
        :rtype: float
        """

        cumulative_blame = 0
        for k, p_action in blamed_agent_possible_actions.items():
            cur_predicted_utility = p_action["__ER__"][0]
            if cur_utility <= cur_predicted_utility:
                if blamed_agent_action != p_action["blamed_predicted_action"] and \
                        float(p_action["blamed_predicted_utility"]) >= 0.0:
                    # blamed_agent is to blame because they could have taken a different action that would have
                    # resulted in better utility (according to agent)
                    cumulative_blame = cumulative_blame + (cur_utility - cur_expected_utility)
        return cumulative_blame

    def blame3(self, cur_utility, cur_expected_utility, blamed_agent_action, blamed_agent_possible_actions):
        """
        from perspective of the target agent, could the blamed agent take better action
        i.e. Did the blamed_agent take an unexpected action that negatively affected the agent AND could the
        blamed_agent have done something different?

        :param cur_utility:  Utility after event has happened.
        :param cur_expected_utility:  Expected utility after event has happened.
        :param blamed_agent_action: Action that the other agent took.
        :param blamed_agent_possible_actions: Possible actions that the other agent could have taken.
        :return: Cumulative blame that target agent places on blamed agent.
        :rtype: float
        """

        cumulative_blame = 0.0
        for k, p_action in blamed_agent_possible_actions.items():
            cur_predicted_utility = p_action["__ER__"][0]
            if cur_utility <= cur_predicted_utility:
                if blamed_agent_action != p_action["blamed_predicted_action"]:
                    # blamed_agent is to blame because they could have taken a different action that would have
                    # resulted in better utility (according to agent)
                    cumulative_blame = cumulative_blame + (cur_expected_utility - cur_utility)
        return cumulative_blame

    def control(self, possible_actions, agent_max_reward):
        """
        This is a probability. For each predicted action that delivers a positive utility change, sum the probabilities.

        :param possible_actions: Possible actions that the agent could take
        :param agent_max_reward: Max reward that the agent could get for their action
        :return: sum of probabilities of positive utility actions
        :rtype: float
        """

        player_control = 0.0
        for action, predictions in possible_actions.items():
            if predictions['__EV__'] > 0:
                # player_control = player_control + player_decision['action'][action]
                player_control = player_control + agent_max_reward
        return player_control

    def control2(self, cur_utility, cur_expected_utility, possible_actions):
        """
        If something bad has happened (negative, unexpected utility), does the agent have an action to rectify it
        (i.e. have any positive effect on their utility)?

        :param cur_utility: Utility after event has happened.
        :param cur_expected_utility:  Expected utility after event has happened.
        :param possible_actions:  Possible actions that the agent could take
        :return: number of possible positive utility actions
        :rtype: int
        """

        # are we in a 'bad' situation (we have less utility than we expected)
        control = 0
        if cur_utility < cur_expected_utility:
            for k, p_action in possible_actions.items():
                predicted_utility = p_action["__ER__"][0]
                if predicted_utility > 0:
                    # There is an action that can at least start to rectify the 'bad' situation
                    control += 1
        return control

    # def control3(self, cur_utility, cur_expected_utility, blamed_agent_action, possible_actions, believed_action):
    # """ If an agent didn't do a specific expected action that should have had a positive utility, can this agent do
    # that action?
    #
    #     :param cur_utility: Utility after event has happened.
    #     :param cur_expected_utility:  Expected utility after event has happened.
    #     :param blamed_agent_action: Action that the other agent took.
    #     :param possible_actions:  Possible actions that the agent could take
    #     :param believed_action: Action the target agent believed the other agent took
    #     :return: True if agent has control
    #     :rtype: bool
    #     """
    #     control = False
    #     # Did the other agent do something we didn't expect?
    #     if blamed_agent_action != believed_action:
    #         # are we in a 'bad' situation (we have less utility than we expected)?
    #         if cur_utility < cur_expected_utility:
    #             for p_action_name, p_action in possible_actions.items():
    #                 if p_action_name == believed_action:
    #                     # We can do the action the other agent didn't do
    #                     control = True
    #     return control

    def control3(self, cur_utility, cur_expected_utility, blamed_agent_action, possible_actions, believed_action):
        """
        A player has 'memory' so if they blame someone for a bad action, they will not feel in control until they have
        it in their power to rectify the situation, that might come a few actions later. This is done by checking at
        each step if they need to resolve something, if another player does it, and if they can do it

        :param cur_utility: Utility after event has happened.
        :param cur_expected_utility:  Expected utility after event has happened.
        :param blamed_agent_action: Action that the other agent took.
        :param possible_actions:  Possible actions that the agent could take
        :param believed_action: Action the target agent believed the other agent took
        :return: 1 if agent has control, 0 if not
        :rtype: int
        """
        control = 0
        # Did the other agent do something we didn't expect?
        if blamed_agent_action != believed_action:
            # are we in a 'bad' situation (we have less utility than we expected)?
            if cur_utility < cur_expected_utility:
                for p_action_name, p_action in possible_actions.items():
                    if p_action_name == believed_action:
                        # We can immediately do the action the other agent didn't do
                        control = 1
                    else:
                        # we need to remember to come back to this later
                        self.actions_todo.append(believed_action)  # todo: make this also have a decay factor (priority might be in their reward function so don't worry bout it)
                        control = 0
        return control

    def control5(self, blamed_agent_action, possible_actions):
        """
        This checks the 'memory' at each step to see if we now have control

        :param blamed_agent_action: Action that the other agent took.
        :param possible_actions:  Possible actions that the agent could take
        :return: 1 if agent has control, 0 if not
        :rtype: int
        """

        # Check to see if we can rectify any of the issues in our "to_do" list
        for idx, action in enumerate(self.actions_todo):
            # First, check to see if the other agent is doing that action
            if action == blamed_agent_action:
                # remove that action and exit with no control
                self.actions_todo.pop(idx)
                return 0
            # Second, check to see if we have the capability of fixing the issue
            if action in possible_actions:
                # we have the power to fix the issue we encountered before, therefore we have control
                return 1
        return 0

    def surprise(self, blamed_agent_action, believed_action):
        """
        Compare an actual action taken by a player to a projected action as calculated by psychsim

        :param blamed_agent_action:  Action that the other agent took.
        :param believed_action: Action that agent believed the other agent took
        :return: 1 if surprised, 0 if not
        :rtype: int
        """
        if blamed_agent_action == believed_action:
            return 0
        return 1

    def desirability(self, cur_utility, cur_expected_utility, blamed_agent_action, blamed_agent_possible_actions, believed_action):
        """
        This is a measure of how much utility has been lost by an unexpected negative action

        :param cur_utility: Utility after event has happened.
        :param cur_expected_utility:  Expected utility after event has happened.
        :param blamed_agent_action: Action that the other agent took.
        :param blamed_agent_possible_actions:  Possible actions that the other agent could take
        :param believed_action: Action the target agent believed the other agent took
        :return: utility lost by agent
        :rtype: float
        """
        # If you blame the other agent (they did something bad for you but could have done something better)
        lost_utility = 0.0
        if self.blame3(cur_utility, cur_expected_utility, blamed_agent_action, blamed_agent_possible_actions):
            # Calculate the difference in utility and what we should have gotten if the other agent did the right thing
            lost_utility = blamed_agent_possible_actions[believed_action]["__EV__"]
        return -lost_utility

    def get_appraisals_for_step(self, params, normalise=False):
        """
        Calculate all the appraisal dimensions for a particular step

        :param normalise: Normalise the output appraisals between -1 and 1
        :param params: dictionary of params representing variables needed for appraisal calculations.
        :return: Appraisal dimensions and info
        :rtype: PlayerAppraisalInfo
        """
        appraisals = PlayerAppraisalInfo()

        appraisals.blame1 = self.blame1(params["cur_utility"], params["cur_expected_utility"], params["blamed_agent_action"], params["believed_action"])
        appraisals.blame2 = self.blame2(params["cur_utility"], params["cur_expected_utility"], params["blamed_agent_action"], params["blamed_agent_possible_actions"])
        appraisals.blame3 = self.blame3(params["cur_utility"], params["cur_expected_utility"], params["blamed_agent_action"], params["blamed_agent_possible_actions"])
        appraisals.desirability = self.desirability(params["cur_utility"], params["cur_expected_utility"], params["blamed_agent_action"], params["blamed_agent_possible_actions"], params["believed_action"])
        appraisals.control = self.control(params["possible_actions"], params["agent_max_reward"])
        appraisals.general_control = self.control2(params["cur_utility"], params["cur_expected_utility"], params["possible_actions"])
        appraisals.specific_control = self.control3(params["cur_utility"], params["cur_expected_utility"], params["blamed_agent_action"], params["possible_actions"], params["believed_action"])
        appraisals.memory_control = self.control5(params["blamed_agent_action"], params["possible_actions"])
        appraisals.surprise = self.surprise(params['blamed_agent_action'], params['believed_action'])

        if normalise:
            for field in appraisals.__dataclass_fields__:
                value = getattr(appraisals, field)
                if isinstance(value, (int, float)) and value > 0:
                    setattr(appraisals, field, 1)
                elif isinstance(value, (int, float)) and value < 0:
                    setattr(appraisals, field, -1)

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
        The csv format defines:
        step = current step number
        a_action = current action of target player (human)
        a_proj_action = current action or target agent as projected by psychsim
        a_possible_actions = possible actions target agent could take as projected by psychsim
        a_current_utility = current utility of target agent calculated by psychsim
        a_expected_utility = expected utility of target agent calculated by psychsim
        a_believed_other_agent_action = current action target agent believed other action should take
        a_max_reward = max reward of target agent as calculated by psychsim
        b_action = current action of other player (human)
        b_proj_action = current action or other agent as projected by psychsim
        b_possible_actions = possible actions other agent could take as projected by psychsim
        b_current_utility = expected utility of other agent calculated by psychsim
        b_expected_utility = expected utility of other agent calculated by psychsim
        b_believed_other_agent_action = current action other agent believed target action should take
        b_max_reward = max reward of other agent as calculated by psychsim

        :param csv_row: row of csv file
        :type csv_row: OrderedDict
        :return: Params/ variables needed to calculate appraisal dimensions.
        :rtype: dict
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
                      blamed_agent_action=csv_row['b_action'],
                      cur_expected_utility=float(csv_row['a_expected_utility']),
                      believed_action=csv_row['a_believed_other_agent_action'],
                      agent_max_reward=float(csv_row['a_max_reward']))
        # Update the pre utility
        self.player_pre_utility = float(csv_row['a_current_utility'])
        return params

    def get_appraisal_params_psychsim(self, agent, blame_agent, world, debug_dict, debug_pred_dict):
        """
        get the params in an appropriate format for the appraisal functions from psychsim data.
        This function helps to hide the messiness of extracting data from psychsim objects.

        :param agent: name of target agent
        :type agent: str
        :param blame_agent: name of other agent (agent to blame)
        :type blame_agent: str
        :param world: psychsim world
        :type world: psychsim.world.World
        :param debug_dict: debug dictionary from real data
        :param debug_pred_dict: debug dictionary from psychsim projected step
        :return: Params/ variables needed to calculate appraisal dimensions.
        :rtype: dict
        """
        a_agent = world.agents[agent]
        player_decision_key = list(debug_dict[agent]["__decision__"])[0]  # This is because I don't know what the numbers appended to the player name are going to be
        blamed_decision_key = list(debug_dict[blame_agent]["__decision__"])[0]
        player_cur_utility = a_agent.reward()
        cur_action = debug_dict[agent]["__decision__"][player_decision_key]["action"]  # **This should be the actual action taken by the player
        proj_action = debug_pred_dict[agent]["__decision__"][player_decision_key]["action"]  # **This should be the action projected by psychsim
        cur_blamed_action = debug_dict[blame_agent]["__decision__"][blamed_decision_key]["action"]
        cur_expected_utility = debug_dict[agent]["__decision__"][player_decision_key]["V"][cur_action]["__ER__"][0]
        agent_belief = debug_dict[agent]["__decision__"][player_decision_key]["V"][cur_action]["__beliefs__"]
        agent_max_reward = a_agent.getState('__REWARD__').max()
        believed_action = world.getFeature(f"{blame_agent}'s __ACTION__", agent_belief, unique=True)
        possible_actions = debug_dict[agent]["__decision__"][player_decision_key]["V"]
        blamed_possible_actions = debug_dict[blame_agent]["__decision__"][blamed_decision_key]["V"]
        for action, value in possible_actions.items():
            value["blamed_predicted_action"] = world.getFeature(f"{blame_agent}'s __ACTION__", value["__S__"][0], unique=True)
            value["blamed_predicted_utility"] = world.getFeature(f"{blame_agent}'s __REWARD__", value["__S__"][0], unique=True)
        for action, value in blamed_possible_actions.items():
            value["blamed_predicted_action"] = world.getFeature(f"{blame_agent}'s __ACTION__", value["__S__"][0], unique=True)
            value["blamed_predicted_utility"] = world.getFeature(f"{blame_agent}'s __REWARD__", value["__S__"][0], unique=True)

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
