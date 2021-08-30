"""
Example calculating appraisal dimensions from a sim in the sim_scripts folder.
This example runs the ImperfectMentalModel3 script, calculates the appraisals from the results, and pickles a 'query'
for use with the GUI.

NOTE: the psychsim path must be set in order to function
"""
import sys
print(sys.path)
sys.path.insert(1, "..")
# sys.path.insert(1, "../../psychsim")  # Change this to the relevant paths

import logging
from functions import ASISTQueryFunctions as qf
import psychsim_gui_helpers as pgh
from sim_scripts.ImperfectMentalModel3 import ImperfectMentalModel3

DEBUG = False


def get_appraisal_dimensions(data=None, agent=None):
    """
    Get the appraisal dimensions
    """
    query_functions = qf.ASISTQueryFunctions()
    player_appraisals = query_functions.get_appraisal_dimensions(data, agent, agent, normalise=True)

    return player_appraisals


if __name__ == "__main__":
    logging.basicConfig(format='%(message)s', level=logging.DEBUG if DEBUG else logging.INFO)

    sim = ImperfectMentalModel3()
    test_data = {}
    for step in range(10):
        logging.info('====================================')
        logging.info(f'Step {step}')
        test_data[step] = sim.run_step()

    run_data = pgh.PsychSimRun(id="test",
                               data=test_data,
                               sim_file=__file__,
                               steps=None)
    run_data.data = test_data
    appraisals = get_appraisal_dimensions(data=run_data, agent=sim.ag_consumer.name)

    appraisal_results = pgh.PsySimQuery(
        id="test",
        params=[],
        function="test",
        results=appraisals[1],
        result_type=appraisals[0]
    )
    pgh.save_query_pickle(appraisal_results, "appraisal_test")
