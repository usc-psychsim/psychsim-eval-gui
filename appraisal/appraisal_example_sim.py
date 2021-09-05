"""
Example calculating appraisal dimensions from a sim in the sim_scripts folder.
This example runs the ImperfectMentalModel3 script, calculates the appraisals from the results, and pickles a 'query'
for use with the GUI.

NOTE: the psychsim path must be set in order to function
"""
import sys
print(sys.path)
sys.path.insert(1, "..")
sys.path.insert(1, "../../psychsim")  # Change this to the relevant paths

import logging
from functions import ASISTQueryFunctions as qf
import psychsim_gui_helpers as pgh
from sim_scripts.ImperfectMentalModel3 import ImperfectMentalModel3

DEBUG = False


def get_appraisal_dimensions(data=None, agent=None):
    """
    Get the appraisal dimensions
    """
    # Initialise the class for calculating and storing appraisals
    query_functions = qf.ASISTQueryFunctions()

    # Use the function defined for the gui to extract the appraisal dimensions
    player_appraisals = query_functions.get_appraisal_dimensions(data, agent, agent, normalise=True)

    return player_appraisals


if __name__ == "__main__":

    logging.basicConfig(format='%(message)s', level=logging.DEBUG if DEBUG else logging.INFO)

    # First, instantiate the sim script
    sim = ImperfectMentalModel3()
    test_data = {}

    # Run through 10 steps of the sim script (this calls world.step 10 times and saves data for each step)
    for step in range(10):
        logging.info('====================================')
        logging.info(f'Step {step}')
        test_data[step] = sim.run_step()

    # Set up the objecct to store the data for use with the GUI
    run_data = pgh.PsychSimRun(id="test",
                               data=test_data,
                               sim_file=__file__,
                               steps=None)
    run_data.data = test_data

    # Get the appraisals
    appraisals = get_appraisal_dimensions(data=run_data, agent=sim.ag_consumer.name)

    # Set up the query stucture for use with the GUI
    appraisal_results = pgh.PsySimQuery(
        id="test",
        params=[],
        function="test",
        results=appraisals[1],
        result_type=appraisals[0]
    )

    # Pickle the query so it can be loaded into the gui and plotted
    pgh.save_query_pickle(appraisal_results, "appraisal_test")
