# -*- coding: utf-8 -*-

# import sys
# print(sys.path)
# psychsim_path = "../../atomic"
# definitions_path = "../../atomic_domain_definitions"
# sys.path.insert(1, psychsim_path)
# sys.path.insert(1, definitions_path)

import logging
from psychsim.agent import Agent
from psychsim.probability import Distribution
from psychsim.pwl import makeTree, equalRow, setToConstantMatrix, rewardKey
from psychsim.world import World

__author__ = 'Pedro Sequeira'
__email__ = 'pedrodbs@gmail.com'
__description__ = 'Example of using theory-of-mind in a game-theory scenario involving two agents in the Chicken ' \
                  'Game (https://en.wikipedia.org/wiki/Chicken_(game)#Game_theoretic_applications). ' \
                  'Both agents should choose the "go straight" action which is rationally optimal, independently of ' \
                  'the other agent\'s action.'

NUM_STEPS = 3
TIEBREAK = 'random'  # when values of decisions are the same, choose randomly

# decision labels
NOT_DECIDED = 'none'
WENT_STRAIGHT = 'straight'
SWERVED = 'swerved'

# payoff parameters (according to PD)
SUCKER = -1  # CD
TEMPTATION = 1  # DC
MUTUAL_COOP = 0  # CC
PUNISHMENT = -1000  # DD
INVALID = -10000

DEBUG = False

# defines a payoff matrix tree (0 = didn't decide, 1 = went straight, 2 = swerved)
def get_reward_tree(agent, my_dec, other_dec):
    reward_key = rewardKey(agent.name)
    return makeTree({'if': equalRow(my_dec, NOT_DECIDED),  # if I have not decided
                     True: setToConstantMatrix(reward_key, INVALID),
                     False: {'if': equalRow(other_dec, NOT_DECIDED),  # if other has not decided
                             True: setToConstantMatrix(reward_key, INVALID),
                             False: {'if': equalRow(my_dec, SWERVED),  # if I cooperated
                                     True: {'if': equalRow(other_dec, SWERVED),  # if other cooperated
                                            True: setToConstantMatrix(reward_key, MUTUAL_COOP),  # both cooperated
                                            False: setToConstantMatrix(reward_key, SUCKER)},
                                     False: {'if': equalRow(other_dec, SWERVED),
                                             # if I defected and other cooperated
                                             True: setToConstantMatrix(reward_key, TEMPTATION),
                                             False: setToConstantMatrix(reward_key, PUNISHMENT)}}}})  # both defected


class GameTheoryTom:
    def __init__(self):
        self.sim_steps = 50
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
            agent.setHorizon(1)
            # agent.setRecursiveLevel(1)

            # add "decision" variable (0 = didn't decide, 1 = went straight, 2 = swerved)
            dec = self.world.defineState(agent.name, 'decision', list, [NOT_DECIDED, WENT_STRAIGHT, SWERVED])
            self.world.setFeature(dec, NOT_DECIDED)
            self.agents_dec.append(dec)

            # define agents' actions (defect and cooperate)
            action = agent.addAction({'verb': '', 'action': 'go straight'})
            tree = makeTree(setToConstantMatrix(dec, WENT_STRAIGHT))
            self.world.setDynamics(dec, action, tree)
            action = agent.addAction({'verb': '', 'action': 'swerve'})
            tree = makeTree(setToConstantMatrix(dec, SWERVED))
            self.world.setDynamics(dec, action, tree)

        # defines payoff matrices
        self.agent1.setReward(get_reward_tree(self.agent1, self.agents_dec[0], self.agents_dec[1]), 1)
        self.agent2.setReward(get_reward_tree(self.agent2, self.agents_dec[1], self.agents_dec[0]), 1)

        # define order
        my_turn_order = [{self.agent1.name, self.agent2.name}]
        self.world.setOrder(my_turn_order)

        # add true mental model of the other to each agent
        self.world.setMentalModel(self.agent1.name, self.agent2.name, Distribution({self.agent2.get_true_model(): 1}))
        self.world.setMentalModel(self.agent2.name, self.agent1.name, Distribution({self.agent1.get_true_model(): 1}))

    def run_step(self):

        # decision per step (1 per agent): go straight or swerve?
        result = {self.agent1.name:  {}, self.agent2.name: {}}
        step = self.world.step(debug=result)
        for a in range(len(self.agents)):
            logging.info(f'{self.agents[a].name}: {self.world.getFeature(self.agents_dec[a], unique=True)}')

        return_result = {"WORLD": self.world,
                         "AGENT_DEBUG": result,
                         "AGENTS": self.agents}
        return return_result


if __name__ == "__main__":
    sim = GameTheoryTom()
    for step in range(10):
        logging.info('====================================')
        logging.info(f'Step {step}')
        print(step)
        result = sim.run_step()
