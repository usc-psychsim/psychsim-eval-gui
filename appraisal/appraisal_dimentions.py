"""
Functions for appraisal dimensions
"""

from dataclasses import dataclass, asdict

@dataclass
class PlayerAppraisal:
    """
    Class to hold appraisal dimension info
    """
    # TODO:
    #  fix this to have only the relevant ones
    #  figure out a better way to store this
    motivational_relevance: float = 0.0
    motivational_congruence: float = 0.0

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
    This is the accountability
    actor: the agent being studied
    pact: the action performed by actor
    pre_utility: actor’s utility before doing pact
    """
    for action in actor.actionOptions():
        if action != pact: #if there exists another action which does not hurt actor’s own utility
            if utility(action) >= pre_utility: #TODO: find out if utility should be part of a class? maybe we could inherit the actor class and add these functions so all this stuff is just available internaly?
                return False
    if utility(action) < pre_utility:
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


def control(preUtility):
    # preUtility: utility before the event happens
    # control ← 0 for m1in mental_models_about_agent1 do for m2in mental_models_about_agent2 do for m3in mental_models_about_sel f do #project limited steps into the future using this set of mental models lookahead(m1,m2,m3) #curUtili ty: utility after the lookahead process if curUtili ty ≥ preUtili ty then control ← control + p(m1) ∗ p(m2) ∗ p(m3)
    # Return control
    pass


def novelty():
    pass
