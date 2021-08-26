"""
This script is adapted from: https://github.com/usc-psychsim/psychsim/blob/0571996689c1d9c3d6f42a9f954b6f51a26b2c4b/psychsim/examples/forward_planning_tom.py
"""

import logging
import random
from psychsim.agent import Agent
from psychsim.probability import Distribution
from psychsim.pwl import makeTree, equalRow, setToConstantMatrix, rewardKey
from psychsim.world import World

__author__ = 'Pedro Sequeira'
__email__ = 'pedrodbs@gmail.com'
__description__ = 'Example of using theory-of-mind in a game-theory scenario involving two agents in the iterated' \
                  'version of the Prisoner\'s dilemma ' \
                  '(https://en.wikipedia.org/wiki/Prisoner%27s_dilemma#The_iterated_prisoner%27s_dilemma)' \
                  'Both agents follow a strategy inspired on tit-for-tat (https://en.wikipedia.org/wiki/Tit_for_tat)' \
                  'Namely, the first action is open and depends on the beliefs of the agent about the other\'s ' \
                  'behavior. From there on, retaliation is applied by always choosing defect after the first defection ' \
                  'of the other agent (non-forgiving).' \
                  'Hence the planning horizon has an influence on the agents\' decision to cooperate or defect:' \
                  '- if horizon is 0, first action for each agent will be random (0 reward), then tit-fot-tat' \
                  '- if horizon is 1, agents will always defect (one-shot decision, other\'s action does not matter' \
                  '- if horizon is 2, first action for each agent will be random, because CC followed by CC == ' \
                  'DC followed by DD = -2, so C or D have the same value independently of the other; then tit-fot-tat' \
                  '- if horizon is >2, agents will always cooperate because they can see each other\'s tit-for-tat ' \
                  'strategy using ToM, and hence believe the other will cooperate if they also cooperate, leading to ' \
                  'highest mutual payoff in the long run.' \
                  'Note: imperfect models can break this belief and make the agents cynical towards each other.'

# parameters
MAX_HORIZON = 4
NUM_STEPS = 4
TIEBREAK = 'random'  # when values of decisions are the same, choose randomly
SEED = 0

# decision labels
NOT_DECIDED = 'none'
DEFECTED = 'defected'
COOPERATED = 'cooperated'

# payoff parameters (according to PD)
SUCKER = -3  # CD
TEMPTATION = 0  # DC
MUTUAL_COOP = -1  # CC
PUNISHMENT = -2  # DD
INVALID = -10000

DEBUG = False


# defines a payoff matrix tree (0 = didn't decide, 1 = Defected, 2 = Cooperated)
def get_reward_tree(agent, my_dec, other_dec):
    reward_key = rewardKey(agent.name)
    return makeTree({'if': equalRow(my_dec, NOT_DECIDED),  # if I have not decided
                     True: setToConstantMatrix(reward_key, INVALID),
                     False: {'if': equalRow(other_dec, NOT_DECIDED),  # if other has not decided
                             True: setToConstantMatrix(reward_key, INVALID),
                             False: {'if': equalRow(my_dec, COOPERATED),  # if I cooperated
                                     True: {'if': equalRow(other_dec, COOPERATED),  # if other cooperated
                                            True: setToConstantMatrix(reward_key, MUTUAL_COOP),  # both cooperated
                                            False: setToConstantMatrix(reward_key, SUCKER)},
                                     False: {'if': equalRow(other_dec, COOPERATED),
                                             # if I defected and other cooperated
                                             True: setToConstantMatrix(reward_key, TEMPTATION),
                                             False: setToConstantMatrix(reward_key, PUNISHMENT)}}}})


class ForwardPlanningTom:
    def __init__(self):
        self.sim_steps = 1
        random.seed(0)

        # sets up log to screen
        logging.basicConfig(format='%(message)s', level=logging.DEBUG if DEBUG else logging.INFO)

        # create world and add agent
        self.world = World()
        self.agent1 = Agent('Agent 1')
        self.world.addAgent(self.agent1)
        self.agent2 = Agent('Agent 2')
        self.world.addAgent(self.agent2)

        self.agents_dec = []
        self.agents = [self.agent1, self.agent2]
        for agent in self.agents:
            # set agent's params
            agent.setAttribute('discount', 1)
            agent.setAttribute('selection', TIEBREAK)
            # agent.setRecursiveLevel(1)

            # add "decision" variable (0 = didn't decide, 1 = Defected, 2 = Cooperated)
            dec = self.world.defineState(agent.name, 'decision', list, [NOT_DECIDED, DEFECTED, COOPERATED])
            self.world.setFeature(dec, NOT_DECIDED)
            self.agents_dec.append(dec)

        self.agents[0].setHorizon(2)
        self.agents[1].setHorizon(2)
        # define agents' actions inspired on TIT-FOR-TAT: first decision is open, then retaliate non-cooperation.
        # as soon as one agent defects it will always defect from there on
        for i, agent in enumerate(self.agents):
            my_dec = self.agents_dec[i]
            other_dec = self.agents_dec[0 if i == 1 else 1]

            # defect (not legal if other has cooperated before, legal only if agent itself did not defect before)
            action = agent.addAction({'verb': '', 'action': 'defect'},
                                     makeTree({'if': equalRow(other_dec, COOPERATED),
                                               True: {'if': equalRow(my_dec, DEFECTED),
                                                      True: True,
                                                      False: False},
                                               False: True}))
            tree = makeTree(setToConstantMatrix(my_dec, DEFECTED))
            self.world.setDynamics(my_dec, action, tree)

            # cooperate (not legal if other or agent itself defected before)
            action = agent.addAction({'verb': '', 'action': 'cooperate'},
                                     makeTree({'if': equalRow(other_dec, DEFECTED),
                                               True: False,
                                               False: {'if': equalRow(my_dec, DEFECTED),
                                                       True: False,
                                                       False: True}}))
            tree = makeTree(setToConstantMatrix(my_dec, COOPERATED))
            self.world.setDynamics(my_dec, action, tree)

        # defines payoff matrices (equal to both agents)
        self.agent1.setReward(get_reward_tree(self.agent1, self.agents_dec[0], self.agents_dec[1]), 1)
        self.agent2.setReward(get_reward_tree(self.agent2, self.agents_dec[1], self.agents_dec[0]), 1)

        # define order
        my_turn_order = [{self.agent1.name, self.agent2.name}]
        self.world.setOrder(my_turn_order)

        # add true mental model of the other to each agent
        self.world.setMentalModel(self.agent1.name, self.agent2.name, Distribution({self.agent2.get_true_model(): 1}))
        self.world.setMentalModel(self.agent2.name, self.agent1.name, Distribution({self.agent1.get_true_model(): 1}))

    def run_step(self):

        result = {self.agent1.name:  {}, self.agent2.name: {}}
        # decision per step (1 per agent): cooperate or defect?
        step = self.world.step(debug=result)
        for i in range(len(self.agents)):
            logging.info(f'{self.agents[i].name}: {self.world.getFeature(self.agents_dec[i], unique=True)}')

        return_result = {"WORLD": self.world,
                         "AGENT_DEBUG": result,
                         "AGENTS": self.agents}
        return return_result


if __name__ == "__main__":
    # sets up log to screen
    logging.basicConfig(format='%(message)s', level=logging.DEBUG if DEBUG else logging.INFO)
    sim = ForwardPlanningTom()
    result = []
    # for h in range(MAX_HORIZON + 1):
    #     logging.info('====================================')
    #     logging.info(f'Horizon {h}')
    #
    #     # set horizon (also to the true model!) and reset decisions
    #     for i in range(len(sim.agents)):
    #         sim.agents[i].setHorizon(h)
    #         sim.agents[i].setHorizon(h, sim.agents[i].get_true_model())
    #         sim.world.setFeature(sim.agents_dec[i], NOT_DECIDED, recurse=True)
    #         for step in range(4):
    #             logging.info('====================================')
    #             logging.info(f'Step {step}')
    #             result.append(sim.run_step())
    for step in range(4):
        logging.info('====================================')
        logging.info(f'Step {step}')
        result.append(sim.run_step())
    pass