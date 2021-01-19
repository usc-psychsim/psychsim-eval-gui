import argparse
import json
import os
import logging
import numpy as np
import multiprocessing as mp
from collections import OrderedDict
from timeit import default_timer as timer
from atomic.definitions import victims, world_map
from atomic.inference import set_player_models
from atomic.definitions.map_utils import get_default_maps
from atomic.model_learning.parser import TrajectoryParser
from atomic.parsing.replayer import Replayer, SUBJECT_ID_TAG, COND_MAP_TAG
from atomic.scenarios.single_player import make_single_player_world
from model_learning.trajectory import generate_trajectories, generate_trajectory
from model_learning.util.cmd_line import none_or_int
from model_learning.util.plot import plot_bar
from model_learning.util.io import get_files_with_extension, create_clear_dir, change_log_handler


from appraisal import appraisal_dimentions as ad

__author__ = 'Pedro Sequeira'
__email__ = 'pedrodbs@gmail.com'
__desc__ = 'Simple test script that loads several player log files and creates a plot with the corresponding ' \
           'imported trajectories\' length.'

OUTPUT_DIR = 'output/benchmark'
DATA_FILE = None#'/Users/christopherturner/Documents/GLASGOW-MARSELLA/Data/ASU_2020_08/WithMissionTimer/processed_HSRData_TrialMessages_CondBtwn-NoTriageNoSignal_CondWin-FalconEasy-StaticMap_Trial-43_Team-na_Member-26_Vers-3.csv'#'/home/chris/Documents/GLASGOW_MARSELLA/processed_HSRData_TrialMessages_CondBtwn-NoTriageNoSignal_CondWin-FalconEasy-StaticMap_Trial-43_Team-na_Member-26_Vers-3.csv' #atomic/data/processed_ASIST_data_study_id_000001_condition_id_000002_trial_id_000010_messages.csv' #'data/glasgow/processed_20200724_Participant1_Cond1.csv'
# DATA_FILE = '/Users/christopherturner/Documents/GLASGOW-MARSELLA/Data/ASU_2020_08/WithMissionTimer/processed_HSRData_TrialMessages_CondBtwn-NoTriageNoSignal_CondWin-FalconEasy-StaticMap_Trial-43_Team-na_Member-26_Vers-3.csv'#'/home/chris/Documents/GLASGOW_MARSELLA/processed_HSRData_TrialMessages_CondBtwn-NoTriageNoSignal_CondWin-FalconEasy-StaticMap_Trial-43_Team-na_Member-26_Vers-3.csv' #atomic/data/processed_ASIST_data_study_id_000001_condition_id_000002_trial_id_000010_messages.csv' #'data/glasgow/processed_20200724_Participant1_Cond1.csv'


# params
NUM_TRAJECTORIES = 1#0
TRAJ_LENGTH = 25
RATIONALITY = 1 / 0.1  # inverse temperature
SELECTION = 'distribution'
PRUNE_THRESHOLD = 5e-2  # 1e-2 #'Likelihood below which stochastic outcomes are pruned.'
KEEP_K = 10
HORIZON = 2
SEED = 1
PROCESSES = None #'Number of processes/cores to use. If unspecified, all available cores will be used'

LIGHTS = False
NO_BEEP = 0.0

MAP_NAME = 'simple'#'FalconEasy' #'Name of the map for trajectory generation.'
PLAYER_NAME = 'Player'
FULL_OBS = True

YELLOW_VICTIM = 'Gold'
GREEN_VICTIM = 'Green'

# models
TRUE_MODEL = 'task_scores'
PREFER_NONE_MODEL = 'prefer_none'
PREFER_YELLOW_MODEL = 'prefer_gold'
PREFER_GREEN_MODEL = 'prefer_green'
RANDOM_MODEL = 'zero_rwd'

# agents properties
MODEL_SELECTION = 'distribution'  # TODO 'consistent' or 'random' gives an error
MODEL_RATIONALITY = .5

# victim reward values
HIGH_VAL = 200
LOW_VAL = 10
MEAN_VAL = (HIGH_VAL + LOW_VAL) / 2


def _signal_traj_completion():
    logging.info('\tTrajectory generation complete.')


class BenchmarkReplayer(Replayer):
    parser_class = TrajectoryParser

    def __init__(self, replays, maps=None):
        super().__init__(replays, maps, {}, create_observer=False)

        self.timings = {}
        self.subject_ids = {}
        self.trajectories = {}

    def replay(self, duration, logger):
        start = timer()
        super(BenchmarkReplayer, self).replay(duration, logger)
        elapsed = timer() - start
        self.logger.info('Parsed {} in {:.3f}s'.format(self.parser.filename, elapsed))
        self.subject_ids[self.parser.filename] = \
            '{}-{}'.format(self.conditions[SUBJECT_ID_TAG], self.conditions[COND_MAP_TAG][0]) \
                if SUBJECT_ID_TAG in self.conditions and COND_MAP_TAG in self.conditions else \
                self.parser.player_name()
        self.timings[self.parser.filename] = elapsed
        self.trajectories[self.parser.filename] = self.parser.trajectory


if __name__ == '__main__':

    # create output and log file
    create_clear_dir(OUTPUT_DIR, False)
    change_log_handler(os.path.join(OUTPUT_DIR, 'learning.log'))

    # TODO hacks to avoid stochastic beep and lights
    world_map.MODEL_LIGHTS = LIGHTS

    # checks input files
    files = []
    if DATA_FILE is None:
        logging.info('No replay file provided, skipping parsing benchmark.'.format(DATA_FILE))
    elif os.path.isfile(DATA_FILE):
        files = [DATA_FILE]
    elif os.path.isdir(DATA_FILE):
        files = list(get_files_with_extension(DATA_FILE, 'csv'))
    else:
        logging.info('Provided replay path is not a valid file or directory: {}.'.format(DATA_FILE))

    # create replayer and process all files
    if len(files) > 0:
        replayer = BenchmarkReplayer(files)
        replayer.process_files()

        files = sorted(replayer.trajectories.keys())
        lengths = np.array([len(replayer.trajectories[filename]) for filename in files])
        times = np.array([replayer.timings[filename] for filename in files])
        logging.info('Parsing of {} files took a total of {:.3f}s (mean: {:.3f}s per file, {:.3f}s per step)'.format(
            len(replayer.timings), np.sum(times), np.mean(times), np.mean(times / lengths)))

        # prints results
        files = sorted(replayer.timings.keys())
        times = [replayer.timings[filename] for filename in files]
        subject_ids = [replayer.subject_ids[filename] for filename in files]
        plot_bar(OrderedDict(zip(subject_ids, times)), 'Parsing Times', os.path.join(OUTPUT_DIR, 'parse-times.pdf'))
        plot_bar(OrderedDict(zip(subject_ids, lengths)), 'Trajectory Lengths',
                 os.path.join(OUTPUT_DIR, 'parse-lengths.pdf'))

    # generate trajectories
    victims.PROB_NO_BEEP = NO_BEEP  # otherwise agent will reason about 'none' values (non-zero prob)
    default_maps = get_default_maps()
    if NUM_TRAJECTORIES == 0 or MAP_NAME not in default_maps:
        msg = 'Skipping generation benchmark. '
        if MAP_NAME not in default_maps:
            msg += 'Map name {} not in default maps.'.format(MAP_NAME)
        logging.info(msg)

    else:
        # create world, agent and observer
        map_table = default_maps[MAP_NAME]
        world, agent, observer, victims, world_map = make_single_player_world(
            PLAYER_NAME, map_table.init_loc, map_table.adjacency, map_table.victims,
            False, FULL_OBS, create_observer=True)

        # agent params
        agent.setAttribute('rationality', RATIONALITY)
        agent.setAttribute('selection', SELECTION)
        agent.setAttribute('horizon', HORIZON)

        # model_list = [{'name': PREFER_NONE_MODEL, 'reward': {GREEN_VICTIM: MEAN_VAL, YELLOW_VICTIM: MEAN_VAL},
        #                'rationality': MODEL_RATIONALITY, 'selection': MODEL_SELECTION},
        #               {'name': PREFER_GREEN_MODEL, 'reward': {GREEN_VICTIM: HIGH_VAL, YELLOW_VICTIM: LOW_VAL},
        #                'rationality': MODEL_RATIONALITY, 'selection': MODEL_SELECTION},
        #               {'name': PREFER_YELLOW_MODEL, 'reward': {GREEN_VICTIM: LOW_VAL, YELLOW_VICTIM: HIGH_VAL},
        #                'rationality': MODEL_RATIONALITY, 'selection': MODEL_SELECTION}]
        #
        # model_list = [{'name': PREFER_GREEN_MODEL, 'reward': {GREEN_VICTIM: HIGH_VAL, YELLOW_VICTIM: LOW_VAL},
        #                'rationality': MODEL_RATIONALITY, 'selection': MODEL_SELECTION}]
        # set_player_models(world, observer.name, agent.name, victims, model_list)
        # #
        # model_list = agent.modelList.copy()
        # # ADDING THIS SEEMS TO ADD MASSIVELY TO THE TIME (MAYBE JUST TRY ONE?)

        # generate trajectories
        logging.info('Generating {} trajectories of length {} using {} parallel processes...'.format(
            NUM_TRAJECTORIES, TRAJ_LENGTH, PROCESSES if PROCESSES is not None else mp.cpu_count()))
        start = timer()

        # player_name = agent.name
        # player = agent  # world.agents[player_name]

        player_step_appraisal_info = {}

        step = 0
        trajectories = []
        # NOTE: use the while loop for generate_trajectory()
        #       otherwise you can just do generate_trajectories() and then loop over the results.
        while step <= TRAJ_LENGTH:

            player_appraisal = ad.PlayerAppraisal()
            player_pre_utility = {}

            if step == 0:
                player_loc = player_loc_actual = world.getFeature(f"{agent.name}'s loc", agent.world.state)
                for m in agent.models.keys():
                    player_pre_utility[m] = agent.getState("__REWARD__").domain()[0]
            else:
                # player_pre_utility = traj_agent.getState("__REWARD__").domain()[0]
                player_loc = player_loc_actual = traj_world.getFeature(f"{agent.name}'s loc", traj_world.state)

                for m in traj_agent.models.keys():
                    player_pre_utility[m] = traj_agent.getState("__REWARD__").domain()[0]

            logging.info("=================")
            logging.info(f"STEP: {step}")
            logging.info(f"PRE UTILITY: {player_pre_utility}")
            logging.info(f"PRE LOC: {player_loc}")


            # trajectories.append(generate_trajectories(
            #     agent, NUM_TRAJECTORIES, step, threshold=PRUNE_THRESHOLD, processes=PROCESSES, seed=SEED,
            #     verbose=True))
            debug = {'Player': {}}
            # trajectories.append(generate_trajectory(agent, 1, threshold=PRUNE_THRESHOLD,
            #             seed=SEED, verbose=None, debug=debug))

            step_info = {}
            step_info["trajectory"] = generate_trajectory(agent, 1, threshold=PRUNE_THRESHOLD,
                        seed=SEED, verbose=None, debug=debug)
            step_info["debug"] = debug

            trajectories.append(step_info.copy())

            traj_world = step_info["trajectory"][0][0]
            traj_agent = traj_world.agents[agent.name]
            logging.info(f"Action: {step_info['trajectory'][0][1]}")
            logging.info(f"Action: {traj_world.getAction(agent.name, unique=True)}")
            logging.info(f"Action: {traj_agent.getState('__ACTION__').domain()[0]}")
            player_cur_utility = traj_agent.getState("__REWARD__").domain()[0]
            logging.info(f"CUR UTILITY: {player_cur_utility}")

            # for key, model_name in model_list.items(): #this is set earlier because each new step from generate_trajectory creates a bunch more models
            # for model in model_list:  # this is set earlier because each new step from generate_trajectory creates a bunch more models
            #     model_name = model['name']
            #     pass
            #     # player_cur_utility = player.getReward(m)# this is actually the reward function!!
            #     player_appraisal = ad.PlayerAppraisal()
            #     player_appraisal.motivational_relevance = ad.motivational_relevance(player_pre_utility[model_name],
            #                                                                         player_cur_utility)
            #     logging.info(f"MOTIVATIONAL REL: {player_appraisal.motivational_relevance}")
            #     player_appraisal.motivational_congruence = ad.motivational_congruence(player_pre_utility[model_name],
            #                                                                           player_cur_utility)
            #     logging.info(f"MOTIVATIONAL CONG: {player_appraisal.motivational_congruence}")
            #     # player_appraisal.novelty = #TODO: figure out what the possible actions are (legal?) and how to rank them
            #     # player_appraisal.accountable = ad.accountability(...) # TODO: figure out who should be the observer (maybe this doesn't work in single player?)
            #     # player_appraisal.control = #TODO: figure out how to do the projected action stuff
            #     player_step_appraisal_info[step] = player_appraisal

            step = step + 1
        pass

        elapsed = timer() - start
        logging.info('(mean: {:.3f}s per trajectory, {:.3f}s per step)'.format(
            elapsed / NUM_TRAJECTORIES, elapsed / (NUM_TRAJECTORIES * TRAJ_LENGTH)))
