"""
This example loads data from a pickle file that was created with Pedro Sequeira's benchmark.py script
"""
import sys
import os

print(sys.path)
sys.path.insert(1, "..")
sys.path.insert(1, "../../atomic")  # Change this to the relevant paths
sys.path.insert(1, "../../psychsim")  # Change this to the relevant paths

import pickle
from appraisal import appraisal_dimensions as ad


class AppraisalExample:
    def __init__(self):
        print(os.getcwd())
        file = open("../sim_scripts/output/benchmark/trajectories_pickle20210303-181549",
                    'rb')  # 7 steps, action selection = distribution, no obs
        self.trajectories = pickle.load(file)
        file.close()

    def get_appraisals(self):
        agent = 'Player'
        player_pre_utility = 0.0  # Assume that the players start with 0 utility
        step_appraisal_info = []

        for step, trajectory in enumerate(self.trajectories[0]):
            step_action = list(trajectory[1]._domain.values())[0]
            player_decision_key = list(trajectory[2][agent]["__decision__"])[0]
            player_cur_utility = trajectory[2][agent]["__decision__"][player_decision_key]["V*"]

            player_appraisal = ad.PlayerAppraisal()
            player_appraisal.motivational_relevance = ad.motivational_relevance(player_pre_utility,
                                                                                player_cur_utility)
            player_appraisal.motivational_congruence = ad.motivational_congruence(player_pre_utility,
                                                                                  player_cur_utility)
            player_appraisal.blame = ad.blame(player_pre_utility,
                                              player_cur_utility)
            player_appraisal.intended_blame = ad.intended_blame(player_pre_utility,
                                                                player_cur_utility,
                                                                player_pre_utility,
                                                                player_cur_utility)
            player_appraisal.blame2 = ad.blame2(step_action,
                                                trajectory[2][agent]["__decision__"][player_decision_key])
            player_appraisal.control = ad.control(trajectory[2][agent]["__decision__"][player_decision_key])

            step_appraisal_info.append(dict(step=step,
                                            action=str(step_action),
                                            appraisals=player_appraisal))

        return step_appraisal_info


if __name__ == "__main__":
    AE = AppraisalExample()
    appraisals = AE.get_appraisals()
