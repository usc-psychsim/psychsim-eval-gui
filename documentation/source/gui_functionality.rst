GUI Functionalty
****************


Simulation
==========

run sim (start screen)
----------------------

- The ‘run sim’ screen lets you set the paths for psychsim, and the simulation file, load the sim, run the sim (and stop it), and rename the output data.

.. image:: images/run_sim.png

1. **Select PsychSim Dir**: Set the path to the psychsim root directory
2. **Select Definitions Dir**: Set the path to the psychsim definitions root directory
3. **Select Sim**: set the path to the simulation script
4. **Load Sim**: load the simulation file (import it) into the GUI. *NOTE* a simulation MUST be loaded after selected. This button allows changes to simulation code to be quickly implemented, then ‘re-loaded’ in the sim without having to re-find the path.
5. **RUN**: becomes active when a valid simulation is loaded. Start the simulation thread
6. **STOP**: Stop the simulation thread and save the data
7. **RENAME**: Rename the run to a desired name

data
====
view loaded raw
---------------

- View loaded raw shows you info about data loaded in the GUI. These could come from simulation runs, or from loading saved data sets.
- Data is saved and loaded from Pickle file

.. image:: images/view_data.png

1. **RENAME**: rename the data ID for use through the GUI.
2. **Save**: Save the data to disk (as a pickle file). Data is saved to the ‘sim_output’ directory
3. **Load data from file**: Load saved (pickle) data

sample
------
- Raw data from simulation runs can be sampled. Currently, this data can only be sampled on step (sampling on agent and action does not work).
- Sampled data sets can be viewed, renamed, and saved as raw loaded data from the view raw loaded screen.

.. image:: images/sample.png

1. **Data**: select the data to sample
2. **Step range**: select the start and end step to sample the data over
3. **SAVE**: saves the new data. Saved data can be viewed from the “data>view” loaded raw screen


query
-----
- Data can be saved as any arbitrary python object. The query screen allows custom functions to be run to extract desired information from simulation outputs. Different queries results can also be compared (Diff)
- New functions can be written to handle different queries, and different simulation output types (see: ::ref:`function_definitions`.)
- Queries are saved for viewing, diffing, and plotting.

Create
^^^^^^
- Create and save a new query

.. image:: images/query_create.png

1. **Function**: select the custom function to run on the data. E.g. get_beliefs will extract beliefs for agents after a psychsim simulation run. Get_actions: extracts only actions, etc.
2. **Agent, action, cycle, horizon, state**: these are parameters to pass to the selected function *NOTE* only ‘agent’ is currently implemented.
3. **Doc**: display the docstring of the function
4. **Execute**: execute the function. This pops up the results dialog
5. **Results Dialog**: allows you to rename the query

View
^^^^
- View saved queries, and save as a CSV to disk

.. image:: images/query_view.png

1. **Select Query**: Shows saved queries *NOTE* These are saved internally, not saved to disk
2. **Save as CSV**: Save the query as a CSV file to disk

Diff
^^^^
- Diff two queries created by the same function. Queries cannot be diffed if they were created by different functions.
- Diff queries are saved as a special ‘diff’ query. These can be viewed and plotted, but not re-diffed. I.e. you cannot diff a query that was created by diffing two other queries.

.. image:: images/query_diff.png

1. **Select Query**: Shows saved queries *NOTE* These are saved internally, not saved to disk
2. **Save as CSV**: Save the query as a CSV file to disk


plot
====
plot
----
- Allows you to plot queries as plotly plots.
- Only queries can be plotted, not raw or sampled data.

.. image:: images/query_diff.png

1. **Test datasets enabled**: for testing, allows you to use built-in datasets to test plotting functionality
2. **query**: select the query to plot
3. **X-axis**: select the variable to put on the x-axis
4. **Y-axis**: select the variable to put on the y-axis
5. **Group**: select the variable to group traces by. e.g. if you want to view the actions of multiple agents over time. You might want to group by agents. Do differentiate the traces.
6. **Plot type**: select the type of plot to display. *NOTE* not all plot types are suitable for all plots. It is up to the user to know which plot is useful for the given variables.
7. **Stat**: select the stat to apply. This is applied over the ‘group’ variable
8. **Plot New**: create a new plot with the given parameters
9. **Add to plot:** add the trace with given parameters to the current plot
10. **Clear**: clear the current plot
11. **Save current plot**: Save the current plot. Saved plots appear in the list below this button. Saved plots can be viewed by clicking on the name in the list.
12. **Remove selected**: Remove a saved plot from the list

