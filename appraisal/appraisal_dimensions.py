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
    motivational_relevance: float = None
    motivational_congruence: float = None
    coerced: bool = False
    accountable: bool = False
    novelty: float = None
    consistency: float = None


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
    # sort out divide by 0 if initial utility is 0
    if pre_utility == 0:
        return abs(cur_utility) # TODO: check if this is valid
    return abs((cur_utility - pre_utility)/pre_utility)


def motivational_congruence(pre_utility, cur_utility):
    """
    Motivational congruence or incongruence measures the extent to which the encounter thwarts or facilitates personal goals

    cur_utility: utility after event has happened
    pre_utility: utility before event has happened
    """
    if pre_utility == 0:
        return cur_utility # TODO: check if this is valid
    return (cur_utility - pre_utility)/abs(pre_utility)


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


def control(preUtility):
    # preUtility: utility before the event happens
    # control ← 0 for m1in mental_models_about_agent1 do for m2in mental_models_about_agent2 do for m3in mental_models_about_sel f do #project limited steps into the future using this set of mental models lookahead(m1,m2,m3) #curUtili ty: utility after the lookahead process if curUtili ty ≥ preUtili ty then control ← control + p(m1) ∗ p(m2) ∗ p(m3)
    # Return control
    pass


def novelty(num_possible_actions, action_rank):
    """
    how novel (unexpected) an action is compared to agent's beliefs
    """
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
