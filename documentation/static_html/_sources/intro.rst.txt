Introduction
************
.. image:: images/flow_chart.svg

The workflow of the GUI is described in the flowchart above. First, a simulation is loaded and run. This will generate some raw 'run data'. This data can be then be sampled (selecting a step range). The raw data, or the sampled data, can be queried using query functions. The results of these query functions can then be plotted.

PsychSim Gui can be used to run custom simulation scripts. These scripts can be generic but must follow a few rules (see: :ref:`function_definitions`). Once the simulation is run, the results are stored internally and can be saved to disk as a pickle file.
