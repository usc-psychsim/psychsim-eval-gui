
Interfacing With ASIST code
===========================
This page describes how to run the model_inference.py script for running through ASIST data files.
It also describes how to run this code and get appraisal dimensions through the GUI.

Gui config.ini
--------------
In order to use ASIST code, the `rddl2psychsim <https://github.com/usc-psychsim/rddl2psychsim>`_ and `pyrddl <https://github.com/usc-psychsim/pyrddl>`_ myst be cloned and paths added to the config so config.ini file looks like the following::

    [PATHS]
    psychsim: /Users/christopherturner/Documents/GLASGOW-MARSELLA/psychsim
    atomic: /Users/christopherturner/Documents/GLASGOW-MARSELLA/atomic
    model_learning: /Users/christopherturner/Documents/GLASGOW_MARSELLA/model_learning
    rddl2psychsim: /Users/christopherturner/Documents/GitHub/rddl2psychsim
    pyrddl: /Users/christopherturner/Documents/GitHub/pyrddl
    simulation: ./sim_scripts/ModelInference.py
    function_source: ./functions/ASISTQueryFunctions.py


Running model_inference.py
--------------------------
- model_inference.py is located in the `atomic github repository <https://github.com/usc-psychsim/atomic/blob/master/atomic/bin/model_inference.py>`_
- The script uses a config file such as `phase2.ini <https://github.com/usc-psychsim/atomic/blob/master/config/phase2.ini>`_ to set *domain*, *run*, and *model*, parameters.
- The number of steps that the script runs through is set with the *steps* parameter in the *[run]* section of the config.
- The config and the path to the data file must be passed from the command line. For example:

`python3 model_inference.py C:\\Users\\ChrisTurner\\Documents\\GitHub\\asist_data\\study-2_2021.06_HSRData_TrialMessages_Trial-T000485_Team-TM000143_Member-na_CondBtwn-2_CondWin-SaturnA_Vers-4.metadata --config C:/Users/ChrisTurner/Documents/GitHub/atomic/config/phase2.ini`

Running from the GUI
--------------------
The model_inference.py script has also been adapted to run through the GUI. The script is located in `sim_scripts/ModelInference.py <https://github.com/usc-psychsim/psychsim-eval-gui/blob/master/sim_scripts/ModelInference.py>`_.
and invokes the atomic script model_inference.py. This means changes to model_inference.py should be captured.

Notes:

- ModelInference.py has the commandline arguments for model_inference.py hardcoded. These should be changed within the script.
- The script must run through the whole simulation (or number specified in the *steps* parameter) first, then the data is collated for use in the GUI.
- It is run as any other sim script through the gui (loading the script, and clicking *RUN SIM*)

Differences with getting data from the debug dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There is one main difference with extracting data from model_inference.py than other PsychSim based sim scripts:

- model_inference.py accumulates decision objects explicitly instead of through the world.step debug output.
- this means that access to these values is different than other functions.
- therefore there is a different get_appraisal_dimension function (get_appraisal_dimensions_mi)