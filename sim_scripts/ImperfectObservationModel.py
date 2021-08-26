"""
This script is adapted directly from: https://github.com/usc-psychsim/psychsim/blob/0571996689c1d9c3d6f42a9f954b6f51a26b2c4b/psychsim/examples/imperfect_observation_model.py
"""
import logging
from psychsim.agent import Agent
from psychsim.helper_functions import multi_set_matrix, multi_reward_matrix
from psychsim.pwl import makeTree, equalRow, setToFeatureMatrix, setToConstantMatrix, thresholdRow, CONSTANT
from psychsim.world import World

__author__ = 'Pedro Sequeira'
__email__ = 'pedrodbs@gmail.com'
__description__ = 'Example of setting a incorrect belief over another agent\'s feature. Two agents interact with each ' \
                  'other: a a consumer agent asks for a certain amount of product while a producer agent produces ' \
                  'that product. The produced amount depends on the producer\'s production capacity and the asked ' \
                  'amount, i.e., produced=asked*capacity. The consumer asks for product according to the producer\'s ' \
                  'capacity: if it observes that the capacity is "full", it will order a "normal" amount, otherwise ' \
                  'it will ask for double the "normal" amount if it observes that the capacity is "half". ' \
                  'The consumer\'s reward is dictated by the amount of product received: if it receives the normal ' \
                  'amount it receives a positive reward, if it receives more than the normal amount it will receive a ' \
                  'penalty to simulate an over-stock cost.' \
                  'We set a belief to the consumer agent so that it always believes the consumer is producing at half' \
                  'capacity when in reality it is not. The agent will therefore always ask for more, thinking that ' \
                  'this way it will receive what it really needs. This simulates hoarding behavior under false beliefs.'

# parameters
# NUM_STEPS = 4
HORIZON = 2

DEBUG = False


def get_fake_model_name(agent):
    return 'fake {} model'.format(agent.name)


class ImperfectObservationModel:
    def __init__(self):
        self.sim_steps = 10
        # sets up log to screen

        # create world and add agents
        self.world = World()
        ag_producer = Agent('Producer')
        self.world.addAgent(ag_producer)
        self.ag_consumer = Agent('Consumer')
        self.world.addAgent(self.ag_consumer)
        self.agents = [ag_producer, self.ag_consumer]

        # agent settings
        ag_producer.setAttribute('discount', 1)
        ag_producer.setHorizon(HORIZON)
        self.ag_consumer.setAttribute('discount', 1)
        self.ag_consumer.setHorizon(HORIZON)

        # add variables (capacity and asked/received amounts)
        self.var_half_cap = self.world.defineState(ag_producer.name, 'half capacity', bool)
        self.world.setFeature(self.var_half_cap, False)
        self.var_ask_amnt = self.world.defineState(ag_producer.name, 'asked amount', int, lo=0, hi=100)
        self.world.setFeature(self.var_ask_amnt, 0)
        self.var_rcv_amnt = self.world.defineState(self.ag_consumer.name, 'received amount', int, lo=0, hi=100)
        self.world.setFeature(self.var_rcv_amnt, 0)

        # add producer actions
        # produce capacity: if half capacity then 0.5*asked amount else asked amount)
        act_prod = ag_producer.addAction({'verb': '', 'action': 'produce'})
        tree = makeTree({'if': equalRow(self.var_half_cap, True),
                         True: multi_set_matrix(self.var_rcv_amnt, {self.var_ask_amnt: 0.5}),
                         False: setToFeatureMatrix(self.var_rcv_amnt, self.var_ask_amnt)})
        self.world.setDynamics(self.var_rcv_amnt, act_prod, tree)

        # add consumer actions (ask more = 10 / less = 5)
        act_ask_more = self.ag_consumer.addAction({'verb': '', 'action': 'ask_more'})
        tree = makeTree(setToConstantMatrix(self.var_ask_amnt, 10))
        self.world.setDynamics(self.var_ask_amnt, act_ask_more, tree)

        act_ask_less = self.ag_consumer.addAction({'verb': '', 'action': 'ask_less'})
        tree = makeTree(setToConstantMatrix(self.var_ask_amnt, 5))
        self.world.setDynamics(self.var_ask_amnt, act_ask_less, tree)

        # defines payoff for consumer agent: if received amount > 5 then 10 - rcv_amnt (penalty) else rcv_amount (reward)
        # this simulates over-stock cost, best is to receive max of 5, more than this has costs
        self.ag_consumer.setReward(
            makeTree({'if': thresholdRow(self.var_rcv_amnt, 5),
                      True: multi_reward_matrix(self.ag_consumer, {CONSTANT: 10, self.var_rcv_amnt: -2}),
                      False: multi_reward_matrix(self.ag_consumer, {self.var_rcv_amnt: 1})}),
            1)

        # define order (parallel execution)
        self.world.setOrder([{ag_producer.name, self.ag_consumer.name}])

        # sets consumer belief that producer is at half-capacity, making it believe that asking more has more advantage
        # - in reality, producer is always at full capacity, so best strategy would be to always ask less
        self.ag_consumer.setBelief(self.var_half_cap, True)
        self.total_rwd = 0

    def run_step(self):

        result = {'Consumer': {}, 'Producer': {}}
        # self.world.printBeliefs("Consumer")
        step = self.world.step(debug=result)
        reward = self.ag_consumer.reward()
        logging.info('Consumer action:\t\t\t\t{}'.format(str(self.world.getFeature(f"{self.ag_consumer.name}'s __ACTION__")).split("\t")[1]))
        logging.info('Half capacity:\t\t{}'.format(self.world.getValue(self.var_half_cap)))
        logging.info('Asked amount:\t\t{}'.format(self.world.getValue(self.var_ask_amnt)))
        logging.info('Received amount:\t{}'.format(self.world.getValue(self.var_rcv_amnt)))
        logging.info('Consumer reward:\t{}'.format(reward))
        self.total_rwd += reward

        logging.info('____________________________________')
        # world.explain(step, level=2)# todo step does not provide outcomes anymore

        return_result = {"WORLD": self.world,
                         "AGENT_DEBUG": result,
                         "AGENTS": self.agents}
        return return_result ## I'm only getting the end one out here


if __name__ == "__main__":
    # sets up log to screen
    logging.basicConfig(format='%(message)s', level=logging.DEBUG if DEBUG else logging.INFO)
    sim = ImperfectObservationModel()
    for step in range(10):
        logging.info('====================================')
        logging.info(f'Step {step}')
        result = sim.run_step()
    logging.info('====================================')
    logging.info('Total reward: {0}'.format(sim.total_rwd))
