import sys
print(sys.path)
# sys.path.insert(1, "/home/chris/Documents/GLASGOW_MARSELLA/Sep2020/psychsim/")
# sys.path.insert(1, "/home/chris/Documents/GLASGOW_MARSELLA/Sep2020/atomic/")
sys.path.insert(1, "/home/christ/Documents/Sep2020/model-learning/")

import logging
import itertools
import os
import traceback
from atomic.bin.model_inference import Analyzer
from atomic.definitions.map_utils import DEFAULT_MAPS
from atomic.inference import DEFAULT_MODELS, DEFAULT_IGNORE
from psychsim.pwl import modelKey, stateKey
from model_learning.inference import track_reward_model_inference
from model_learning.trajectory import generate_trajectory, log_trajectories
from model_learning.util.io import create_clear_dir, save_object, change_log_handler
from model_learning.util.plot import plot_evolution
from atomic.inference import set_player_models
from atomic.scenarios.single_player import make_single_player_world
from atomic.parsing.parser import summarizeState
# from atomic.definitions.plotting import plot_trajectories
from atomic.definitions.map_utils import getSandRMap, getSandRVictims


LOG_FILE = "/home/chris/Documents/GLASGOW_MARSELLA/atomic/data/processed_ASIST_data_study_id_000001_condition_id_000001_trial_id_000001_messages.csv"

"""
Code taken from atomic/bin/model_inference.py
"""

class ModelInferenceReplayer:
    def __init__(self):

        self.sim_steps = 5 #THIS IS THE TOTAL NUMBR OF STEPS TO RUN

        # Set player models for observer agent

        ignore = []
        logging.basicConfig(level='WARNING')
        self.replayer = Analyzer([LOG_FILE], DEFAULT_MAPS, DEFAULT_MODELS, ignore, logging)

    def run_step(self):
        files = [LOG_FILE]
        # Get to work
        for fname in files:
            self.replayer.file_name = fname
            logger = self.replayer.logger.getLogger(os.path.splitext(os.path.basename(fname))[0])
            logger.debug('Full path: {}'.format(fname))
            self.replayer.conditions = self.replayer.read_filename(os.path.splitext(os.path.basename(fname))[0])

            # Parse events from log file
            try:
                self.replayer.parser = self.replayer.parser_class(fname, logger=logger.getChild(self.replayer.parser_class.__name__))
            except:
                logger.error(traceback.format_exc())
                logger.error('Unable to parse log file')
                continue

            map_name, self.replayer.map_table = self.replayer.get_map(logger)
            if map_name is None or self.replayer.map_table is None:
                continue

            if not self.replayer.pre_replay(map_name, logger=logger.getChild('pre_replay')):
                # Failure in creating world
                continue

            # Replay actions from log file
            try:
                aes, _ = self.replayer.parser.getActionsAndEvents(self.replayer.triage_agent.name, self.replayer.victims, self.replayer.world_map)
            except:
                logger.error(traceback.format_exc())
                logger.error('Unable to extract actions/events')
                continue
            # if num_steps == 0:
            #     last = len(aes)
            # else:
            #     last = num_steps + 1
            #
            # self.replayer.replay(aes, last, logger)

        return_result = {"WORLD_STATE": self.world.state,
                         "TRAJECTORY": aes,
                         "OBSERVER": self.observer}

        return return_result


if __name__ == "__main__":
    sim = ModelInferenceReplayer()
    for step in range(10):
        sim.run_step()