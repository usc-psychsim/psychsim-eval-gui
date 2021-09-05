
Appraisal Dimensions
********************

Code Location
=============
- Appraisal code is located in the `appraisal` directory. This includes code for calculating and testing the appraisal dimensions (see: :ref:`directory_structure` )

Code structure
==============
- Appraisal dimensions are calculated in methods of the `AppraisalDimensions` class in `appraisal/appraisal_dimensions.py <https://github.com/usc-psychsim/psychsim-eval-gui/blob/master/appraisal/appraisal_dimensions.py>`_.
- Appraisal dimension results are stored in the `PlayerAppraisalInfo` data class in the same file
- the `get_appraisal_params_psychsim` function extracts the relevent parameters from psychsim objects. This is passed to `get_appraisals_for_step` to extract the apprasial dimensions as a pandas dataframe.
- see :ref:`appraisal_code` for code structure and specific function documentation.

How to use
==========
- An example of how to implement the appraisal code is described in `appraisal/appraisal_example_sim.py <https://github.com/usc-psychsim/psychsim-eval-gui/blob/master/appraisal/appraisal_example_sim.py>`_

Testing
=======
- the directory `appraisal/test <https://github.com/usc-psychsim/psychsim-eval-gui/tree/master/appraisal/test>`_ contains code and data for testing the appraisal dimensions
- `appraisal_csv_test.py <https://github.com/usc-psychsim/psychsim-eval-gui/blob/master/appraisal/test/appraisal_csv_test.py>`_ imports test data in csv format and uses the `get_appraisals_from_csv` function to extract appraisal dimensions
- the script pickles the result for use with the GUI
