"""
CSV appraisal dimension test.

This script reads in the test data in 2agent_test_blame.csv, calculates the appraisal dimensions, and saves the
output in a format that can be displayed in PsychSimGui """
import os

import psychsim_gui_helpers as pgh
from appraisal.appraisal_dimensions import AppraisalDimensions

if __name__ == "__main__":
    ad = AppraisalDimensions()
    csv_file = os.path.join("2agent_test_blame.csv")
    query_data = ad.get_appraisals_from_csv(csv_file)
    # convert to dict and save as query for GUI
    query = pgh.PsySimQuery(id="2agentTest", params=[], function="tset",
                            results=query_data, result_type="table")
    pgh.save_query_pickle(query, output_directory="appraisal_test_output")
