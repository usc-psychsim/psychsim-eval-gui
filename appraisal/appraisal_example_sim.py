import sys
import os

print(sys.path)
sys.path.insert(1, "..")
sys.path.insert(1, "../../atomic")  # Change this to the relevant paths
sys.path.insert(1, "../../psychsim")  # Change this to the relevant paths

import logging
import pandas as pd
from appraisal import appraisal_dimensions as ad
from sim_scripts.GameTheoryTom import GameTheoryTom

DEBUG = False


def get_appraisal_dimensions(data=None, agent=None, *args, **kwargs):
    """
    Get the appraisal dimensions
    """
    step_appraisal_info = dict(step=[],
                               action=[],
                               pre_utility=[],
                               cur_utility=[],
                               relevance=[],
                               congruence=[],
                               blame=[],
                               blame2=[],
                               intended_blame=[],
                               novelty=[],
                               control=[])
    player_pre_utility = 0.0 # Assume that the players start with 0 utility
    for step, step_data in data.items():

        traj_agent = step_data['WORLD'].agents[agent]
        traj_debug = step_data["AGENT_DEBUG"]
        player_decision_key = list(traj_debug[agent]["__decision__"])[0] #This is because I don't knwo what the numbers appended to the player name are going to be
        player_cur_utility = traj_debug[agent]["__decision__"][player_decision_key]["V*"]
        cur_action = traj_agent.getState('__ACTION__').domain()[0]

        player_appraisal = ad.PlayerAppraisal()
        player_appraisal.motivational_relevance = ad.motivational_relevance(player_pre_utility, player_cur_utility)
        player_appraisal.motivational_congruence = ad.motivational_congruence(player_pre_utility, player_cur_utility)
        player_appraisal.blame = ad.blame(player_pre_utility, player_cur_utility)
        player_appraisal.intended_blame = ad.intended_blame(player_pre_utility, player_cur_utility, player_pre_utility, player_cur_utility)
        player_appraisal.blame2 = ad.blame2(cur_action, traj_debug[agent]["__decision__"][player_decision_key])
        player_appraisal.control = ad.control(traj_debug[agent]["__decision__"][player_decision_key], traj_agent)

        # extract the possible actions and corresponding rewards from the trajectory
        agent_decision = traj_debug[agent]["__decision__"]
        expected_rewards = ad.extract_expected_action_reward(agent_decision, agent)
        num_possible_actions = len(expected_rewards)
        # get the position in the dict
        projected_actions = list(expected_rewards.keys())
        cur_action_rank = 0
        if cur_action in projected_actions:
            cur_action_rank = projected_actions.index(cur_action)

        player_appraisal.novelty = ad.novelty(num_possible_actions, cur_action_rank)

        step_appraisal_info['step'].append(step)
        step_appraisal_info['action'].append(str(cur_action))
        step_appraisal_info['pre_utility'].append(player_pre_utility)
        step_appraisal_info['cur_utility'].append(player_cur_utility)
        step_appraisal_info['relevance'].append(player_appraisal.motivational_relevance)
        step_appraisal_info['congruence'].append(player_appraisal.motivational_congruence)
        step_appraisal_info['blame'].append(player_appraisal.blame)
        step_appraisal_info['blame2'].append(player_appraisal.blame2)
        step_appraisal_info['intended_blame'].append(player_appraisal.intended_blame)
        step_appraisal_info['novelty'].append(player_appraisal.novelty)
        step_appraisal_info['control'].append(player_appraisal.control)

        player_pre_utility = player_cur_utility

    output_data = pd.DataFrame.from_dict(step_appraisal_info)
    return output_data.T


if __name__ == "__main__":
    logging.basicConfig(format='%(message)s', level=logging.DEBUG if DEBUG else logging.INFO)

    sim = GameTheoryTom()
    test_data = {}
    for step in range(10):
        logging.info('====================================')
        logging.info(f'Step {step}')
        print(step)
        test_data[step] = sim.run_step()

    appraisals = get_appraisal_dimensions(data=test_data, agent=sim.agent1.name)