import sys
import os

print(sys.path)
sys.path.insert(1, "..")
# sys.path.insert(1, "../../atomic")  # Change this to the relevant paths
# sys.path.insert(1, "../../psychsim")  # Change this to the relevant paths

import logging
import pandas as pd
from appraisal import appraisal_dimensions as ad
from sim_scripts.ImperfectMentalModel3 import ImperfectMentalModel3

DEBUG = False


def get_appraisal_dimensions(data=None, agent=None, *args, **kwargs):
    """
    Get the appraisal dimensions
    """
    player_appraisals = ad.AppraisalDimensions()
    for step, step_data in data.items():
        player_appraisals.get_appraisals_for_step_psychsim(agent, agent, step_data["WORLD"], step_data["AGENT_DEBUG"], step_data["AGENT_DEBUG"])
        player_appraisals.step_appraisal_info['step'].append(step)

    return player_appraisals
    # output_data = pd.DataFrame.from_dict(player_appraisals.step_appraisal_info)
    # return output_data.T


if __name__ == "__main__":
    logging.basicConfig(format='%(message)s', level=logging.DEBUG if DEBUG else logging.INFO)

    sim = ImperfectMentalModel3()
    test_data = {}
    for step in range(10):
        logging.info('====================================')
        logging.info(f'Step {step}')
        test_data[step] = sim.run_step()

    appraisals = get_appraisal_dimensions(data=test_data, agent=sim.ag_consumer.name)
    pass