"""
Functions for appraisal dimensions
"""
import math
from dataclasses import dataclass


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
    novelty: float = None
    consistency: float = None
    control: float = None


def extract_expected_action_reward(player_decision, player_name):
    """
    Return a dictionary with actions: expected_reward
    player_decision = decision object returned by psychsim
    player_name = name of player
    """
    actions = {}
    for k, v in player_decision.items():
        if player_name in k:
            for k1, v1 in v.items():
                if k1 == "V":
                    actions = {k2: v2["__ER__"][-1] for k2, v2 in v1.items()}
    return actions


def motivational_relevance(pre_utility, cur_utility):
    """
    Motivational relevance evaluates the extent to which an encounter touches upon personal goals"
    Utility is essentially the agent's reward (from getReward)
    cur_utility: utility after event has happened (utility = state*goals) -> goals = reward functions
    pre_utility: utility before event has happened
    """
    m_rel = abs((cur_utility - pre_utility))
    return m_rel


def motivational_congruence(pre_utility, cur_utility):
    """
    Motivational congruence or incongruence measures the extent to which the encounter thwarts or facilitates
    personal goals

    cur_utility: utility after event has happened
    pre_utility: utility before event has happened
    """
    m_con = (cur_utility - pre_utility)
    return m_con


def blame(team_pre_utility, team_cur_utility):
    """
    Did the actor take an action that netatively impacted the team?
    i.e. did the action that the actor took
    return: scale of team utility difference

    team_pre_utility: utility of team before action
    team_cur_utility: utility of team after action
    """
    # If the actor did anything to negatively impact the team, they are to blame
    return team_cur_utility - team_pre_utility


def intended_blame(actor_pre_utility, actor_cur_utility, team_pre_utility, team_cur_utility):
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


def blame2(action, player_decision):
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


def control(player_decision):
    """
    This is a probability. For each predicted action that delivers a positive utility change, sum the probabilities.
    that is the control
    player_decision: decision object of the player from psychsim
    """
    player_control = 0
    for action, predictions in player_decision['V'].items():
        if predictions['__EV__'] > 0:
            player_control = player_control + player_decision['action'][action]
    return player_control


def novelty(num_possible_actions, action_rank):
    """
    how novel (unexpected) an action is compared to agent's beliefs
    num_possible_actions: the number of possible actions that can be taken
    action_rank: the rank of the action (actions are ranked from lowest to highest utility)
    """
    # TODO: fix this to take into account environment
    return 1 - consistency(num_possible_actions, action_rank)


def consistency(num_possible_actions, action_rank):
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

