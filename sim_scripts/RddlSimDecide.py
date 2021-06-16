# -*- coding: utf-8 -*-

# import sys
# print(sys.path)
# psychsim_path = "../../atomic"
# definitions_path = "../../atomic_domain_definitions"
# sys.path.insert(1, psychsim_path)
# sys.path.insert(1, definitions_path)


import argparse
import logging
import sys

from rddl2psychsim.conversion.converter import Converter

THRESHOLD = 0
RDDL_FILE = '../../atomic/data/rddl_psim/role_big_2_rooms_2_agents.rddl'
DEBUG = False

class RddlSimDecide:
    def __init__(self):
        self.sim_steps = 7
        # sets up log to screen
        logging.root.setLevel(logging.INFO)

        logging.basicConfig(
            handlers=[logging.StreamHandler(sys.stdout)],
            format='%(message)s', level=logging.INFO)
        parser = argparse.ArgumentParser()
        parser.add_argument('--input', '-i', type=str, default=RDDL_FILE, help='RDDL file to be converted to PsychSim.')
        parser.add_argument('--threshold', '-t', type=float, default=THRESHOLD,
                            help='Stochastic outcomes with a likelihood below this threshold are pruned.')
        parser.add_argument('--select', action='store_true',
                            help='Whether to select an outcome if dynamics are stochastic.')
        parser.add_argument('--log-actions', action='store_true',
                            help='Whether to log agents\' actions in addition to current state.')
        parser.add_argument('--log-rewards', action='store_true',
                            help='Whether to log agents\' rewards wrt chosen actions in addition to current state.')
        self.args = parser.parse_args()
        self.args.log_rewards = True

        self.conv = Converter()
        self.conv.convert_file(RDDL_FILE, verbose=True)

    def _log_agent_reward(self, ag_name, debug):
        if '__decision__' not in debug[ag_name]:
            return
        true_model = self.conv.world.agents[ag_name].get_true_model()
        decision = debug[ag_name]['__decision__'][true_model]
        action = decision['action']
        rwd = decision['V'][action]['__ER__'] if 'V' in decision else []
        rwd = None if len(rwd) == 0 else rwd[0]
        logging.info(f'{ag_name}\'s action: {action} reward: {rwd}')

    def run_step(self):

        debug = {ag_name: {'preserve_states': True} for ag_name in self.conv.actions.keys()} if self.args.log_rewards else dict()
        self.conv.world.step(debug=debug, threshold=self.args.threshold, select=self.args.select)

        return_result = {"WORLD": self.conv.world,
                         "AGENT_DEBUG": debug,}
        return return_result


if __name__ == "__main__":
    sim = RddlSimDecide()
    for step in range(sim.sim_steps):
        logging.info('====================================')
        logging.info(f'Step {step}')
        print(step)
        result = sim.run_step()
    pass