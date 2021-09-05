


Directory Structure
*******************

The psychsim Gui code is structured as follows:


psychsim-eval-gui
=================
Contains top level scripts, config, files, and helpers

* config.ini

    config file to set directories needed for the gui to run

* gui_threading.py

    Threading functions used in the gui

* PsychSimGui.py

    This is the main app. Execute this script to run the app

* psychsim_gui_helpers.py

    helper functions used by the gui scripts

* Pipfile & Pipfile.lock

    dependency information required by pipenv to setup virtual environment

.. _directory_structure:

Appraisal
=========
Code relating to appraisal dimensions.

* appraisal_dimensions.py

    Code to calculate appraisal dimensions. Also contains interface code to extract appraisals from psych sim data

* appraisal_example_sim.py

    An example of how to calculate appraisal dimensions from a psychsim gui simulation script

\\test
-----
Contains code and 'fake' data in a .csv file to test the appraisal functionality


Documentation
=============
Contains files and scripts to generate the documentation you are reading

\\static_html
------------
copy of the built documentation which is used by the gui to display these pages


functions
=========
* ASISTQueryFunctions.py

    Function definitions used to extract data from ASIST based psychsim scripts

* DemoFunctions.py

    Function definitions used to extract data from sim_scripts/DemoSim.py


sim_scripts
===========
This folder holds some example simulation scripts to run.

* DemoSim.py

    An example simulation that creates three channels of sinusoid data with and without noise and two channels of randomly generated data.

* ForwardPlanningTom.py

    Sim script implementing the forward example definied `here <https://github.com/usc-psychsim/psychsim/blob/0571996689c1d9c3d6f42a9f954b6f51a26b2c4b/psychsim/examples/forward_planning_tom.py>`_

* SimTemplate.py

    a blank template example

ui
==
This folder contains all the pyqt5 designer (ui) files and corresponding python scripts that control the various parts of the gui.

