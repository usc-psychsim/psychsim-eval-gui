"""
Functions for appraisal dimensions
"""
import math
from dataclasses import dataclass, asdict

@dataclass
class PlayerAppraisal:
    """
    Class to hold appraisal dimension info
    """
    # TODO:
    #  fix this to have only the relevant ones
    #  figure out a better way to store this
    motivational_relevance: bool = False
    motivational_congruence: float = None
    coerced: bool = False
    accountable: bool = False
    blame: bool = False
    blame2: bool = False
    novelty: float = None
    consistency: float = None
    control: float = None


    def desirability(self):
        """
        Something is desirable if it is relevant, and if it has a positive effect on the utility
        """
        if self.motivational_relevance and self.motivational_congruence > 0:
            return True
        else:
            return False



def calculate_utility(reward_fn, state):
    """
    This is a weighted sum of the reward for the current state
    reward_fn = reward function
    state = state
    """
    pass


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
    if m_rel > 0:
        return True
    return False


def motivational_congruence(pre_utility, cur_utility):
    """
    Motivational congruence or incongruence measures the extent to which the encounter thwarts or facilitates personal goals

    cur_utility: utility after event has happened
    pre_utility: utility before event has happened
    """
    m_con = (cur_utility - pre_utility)
    return m_con


def blame(actor_pre_utility, actor_cur_utility, team_pre_utility, team_cur_utility):
    """
    was the action that the actor took, the best for the agent?
    i.e. did the action that the actor took
    """
    # TODO: change if the action simply benefited the team to if it was the best (when we actually have the team info
    # 1. did the actor's action benefit the team? if so - they are not to blame
    if team_cur_utility > team_pre_utility:
        return True
    # 2. did the actor's action negatively affect the team?
    if team_cur_utility < team_pre_utility:
        # did the actor's action benefit the actor? - if so they are to blame
        if actor_cur_utility > actor_pre_utility:
            return True
        # did the actor's action negatively benefit the actor? if so - they are not to blame
        elif actor_cur_utility < actor_pre_utility:
            return False
    return False


def blame2(player_decision):
    """
    Did the actor take an action that wasn't the best (for the team - or for the actor who is asking)
    TODO: fix this for multi-player (the player_decision should be the belief about another player's decision) - this assumes the '__EV__' here corresponds to the observing player's utility not the expected utility of the observed player
    """
    actual_action = player_decision['action']
    actual_action_utility = player_decision['V'][actual_action]['__EV__']
    for action in player_decision['V']:
        if action['__EV__'] > actual_action_utility: # the player could have taken a better option
            return True
    return False

def if_coerced(actor, pact, pre_utility):
    """
    Determines if the agent coerced to perform a specific action
    actor: the agent being studied
    pact: the action performed by actor
    pre_utility: actor’s utility before doing pact (as observed by observing actor)
    action_utility: the actor's utility after completing the action (as observed by observing actor) #TOOD: check this
    """
    action_utility = actor.getState("__REWARD__").domain()[0] # this is the current utility of the agent (afther the action was completed)
    for action in actor.actionOptions(): #todo: fix this to be the correct code
        if action != pact: #if there exists another action which does not hurt actor’s own utility
            if action_utility >= pre_utility: #TODO: find out if utility should be part of a class? maybe we could inherit the actor class and add these functions so all this stuff is just available internaly?
                return False
    if action_utility < pre_utility:
        return False
    return True


def is_coercer_for(agent, actor, agent_pact, actor_pact):
    """
    check if agent coerced actor
    agent_pact: the action performed by agent
    actor_pact: the action performed by actor
    """
    # for action in agent.actionOptions():
    #     if action != agent_pact:
    #         simulate action agent_pact #TODO: figure out this code
    #         if not if_coerced(actor, actor_pact):
    #             return True
    # return False
    pass


def accountability(agent, actor, agent_pact, actor_pact, pre_utility):
    """
    Determines if an actor is accountable for a specific action
    agent: agent who might be coerced
    actor: the agent being studied
    agent_pact: the action performed by agent
    actor_pact: the action performed by actor
    pre_utility: actor’s utility before doing pact (as observed by observing actor)
    action_utility: the actor's utility after completing the action (as observed by observing actor) #TOOD: check this
    """
    if not if_coerced(actor, actor_pact, pre_utility):
        return True  # This actor was responsible as there was no coercer
    if not is_coercer_for(actor, agent, agent_pact, actor_pact):
        return False  # the actor was at least partially responsible for coercing the agent
    return False


def control(player_decision):
    """
    This is a probability. For each predicted action that delivers a positive utility change, sum the probabilities.
    that is the control
    """
    control = 0
    for action, predictions in player_decision['V'].items():
        if predictions['__EV__'] > 0: # TODO: check this is ok (is it always if the expected reward is any positive value?)
            control = control + player_decision['action'][action]
    return control



def novelty(num_possible_actions, action_rank):
    """
    how novel (unexpected) an action is compared to agent's beliefs
    """
    # TODO: fix this to take into account environment
    return 1-consistency(num_possible_actions, action_rank)


def consistency(num_possible_actions, action_rank):
    """
    How consistent (expected) an action is compared an agent's beliefs
    num_possible_actions: the number of possible actions that can be taken
    action_rank: the rank of the action (actions are ranked from lowest to highest utility)
    """
    #TODO: Question - what if actions are equally ranked? Should they just count as one action?
    denom = 0
    for i in range(num_possible_actions):
        denom = denom + math.exp(i)
    return math.exp(action_rank) / denom





# EMA DIMENSIONS
# Desirability. The value of a proposition to the agent (such as Does it ad- vance or inhibit its utility?) can be posi- tive or negative;
# Likelihood. A measure of the likelihood of propositions;
# Expectedness. The extent to which a state could have been predicted from the causal interpretation; = NOVELTY
# Causal attribution. Who deserves credit/blame?;
# Controllability. Can the outcome be altered through an agent’s actions?; and
# Changeability. Can the outcome be altered by another agent?
