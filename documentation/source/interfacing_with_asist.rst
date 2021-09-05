
Interfacing With ASIST code
===========================
This page describes how to run the model_inference.py script for running through ASIST data files.
It also describes how to run this code and get appraisal dimensions through the GUI.

Running model_inference.py
--------------------------
...brief description...
- where the script is
- what the comand line params are
- where the config is

Running through the GUI
-----------------------
- where ModelInference.py is
- what ModelInference.py does (instantiate model_inference, pass command line params from script, etc)
- how it has to run through the whole sim first. Can specifiy number of steps in config

Differences with getting data from the debug dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- model_inference.py accumulates decision objects explicitely instead of through the world.step debug output.
- this means that access to these values is different than other functions.
- therefore there is a different get_appraisal_dimension function (get_appraisal_dimensions_mi)