Directory Structure
*******************

The psychsim Gui is structured as follows:


GUI
===
Contains top level scripts, config, files, and helpers

* config.ini

    config file to set directories for psychsim, psychsim model, and simulation file

* gui_threading.py

    Threading functions used in the gui

* PsychSimGui.py

    This is the main app. Execute this script to run the app

* psychsim_gui_helpers.py

    helper functions used by the gui scripts


Documentation
=============
Contains files and scripts to generate the documentation you are reading

static_html
-----------
copy of the built documentation which is used by the gui to display these pages


functions
=========
* query_functions.py

    Query function definitions used by psychsim gui. Place functions within the PsychSimQuery class to extract data from simulation output.
    Functions placed in this class will appear in the query function dropdown on the 'create new query' tab of the 'create new query from data' page of the gui.

sim_output
==========
This is the default directory for data saved by the GUI. This can be either saved data from runs, or query results exported to csv.

sim_scripts
===========
This folder holds some example simulation scripts to run.

* GuiTestSim<x>.py

    search and rescue test simulations

* GenericSim.py
        an example simulation that creates three channels of sinusoid data with and without noise
* SimBase.py

    a blank template example

ui
==
This folder contains all the pyqt5 designer (ui) files and corresponding python scripts

