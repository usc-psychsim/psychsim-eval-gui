GUI Functionalty
****************


Simulation
==========

view simulation info (start screen)
-----------------------------------

- The ‘run sim’ screen lets you set the paths for psychsim, and the simulation file, load the sim, run the sim (and stop it), and rename the output data.

.. image:: images/run_sim.png

1. **Select PsychSim Dir**: Set the path to the psychsim root directory
2. **Select Definitions Dir**: Set the path to the psychsim definitions root directory
3. **Select Simulation file**: set the path to the simulation script
4. **Load Simulation**: load the simulation file (import it) into the GUI. *NOTE* a simulation MUST be loaded after selected. This button allows changes to simulation code to be quickly implemented, then ‘re-loaded’ in the sim without having to re-find the path.
5. **RUN SIM**: becomes active when a valid simulation is loaded. Start the simulation thread
6. **STOP SIM**: Stop the simulation thread and save the data
7. **RENAME**: Rename the run to a desired name

data
====
view table of stored data
-------------------------

- View loaded raw shows you info about data loaded in the GUI. These could come from simulation runs, or from loading saved data sets.
- Data is saved and loaded from Pickle file

.. image:: images/view_data.png

- **RENAME**: rename the data ID for use through the GUI.
- **Save**: Save the data to disk (as a pickle file). Data is saved to the ‘sim_output’ directory
- **Load data from file**: Load saved (pickle) data

create sample from data
-----------------------
- Raw data from simulation runs can be sampled. Currently, this data can only be sampled on step (sampling on agent and action does not work).
- Sampled data sets can be viewed, renamed, and saved as raw loaded data from the view raw loaded screen.

.. image:: images/sample.png

- **Select data / sample**: select the data to sample
- **Step range**: select the start and end step to sample the data over
- **SAVE**: saves the new data. Saved data can be viewed from the “data>view” loaded raw screen


create query from data/sample
-----------------------------
- Data can be saved as any arbitrary python object. The query screen allows custom functions to be run to extract desired information from simulation outputs. Different queries results can also be compared (Diff)
- New functions can be written to handle different queries, and different simulation output types (see: ::ref:`function_definitions`.)
- Queries are saved for viewing, diffing, and plotting.

Create new query
^^^^^^^^^^^^^^^^
- Create and save a new query

.. image:: images/query_create.png

- **Select function to query data**: select the custom function to run on the data. E.g. get_beliefs will extract beliefs for agents after a psychsim simulation run. Get_actions: extracts only actions, etc.
- **Agent, action, cycle, horizon, state**: these are parameters to pass to the selected function *NOTE* only ‘agent’ is currently implemented.
- **Show function doc**: display the docstring of the function
- **Execute function**: execute the function. This pops up the results dialog
- **Results Dialog**: allows you to rename the query

View saved queries
^^^^^^^^^^^^^^^^^^
- View saved queries, and save as a CSV to disk

.. image:: images/query_view.png

- **Select Query**: Shows saved query info *NOTE* These are saved internally, not saved to disk
- **View Query Data**: Shows saved queries data
- **Save as CSV**: Save the query as a CSV file to disk

Compare saved query results
^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Diff two queries created by the same function. Queries cannot be diffed if they were created by different functions.
- Diff queries are saved as a special ‘diff’ query. These can be viewed and plotted, but not re-diffed. I.e. you cannot diff a query that was created by diffing two other queries.

.. image:: images/query_diff.png

1. **Select Query**: Shows saved queries *NOTE* These are saved internally, not saved to disk
2. **Save as CSV**: Save the query as a CSV file to disk


plot
====
plot query results
------------------
- Allows you to plot queries as plotly plots.
- Only queries can be plotted, not raw or sampled data.
- creating a new plot opens a new plot window
- multiple plot windows can be open at once

.. image:: images/plot.png

- **Test datasets enabled**: for testing, allows you to use built-in datasets to test plotting functionality
- **Create new plot**: opens a new plot window
- **Remove selected from list**: Remove a saved plot from the list



.. image:: images/new_plot.png

- **query**: select the query to plot
- **X-axis**: select the variable to put on the x-axis
- **Y-axis**: select the variable to put on the y-axis
- **Group**: select the variable to group traces by. e.g. if you want to view the actions of multiple agents over time. You might want to group by agents. Do differentiate the traces.
- **Plot type**: select the type of plot to display. *NOTE* not all plot types are suitable for all plots. It is up to the user to know which plot is useful for the given variables.
- **Stat**: select the stat to apply. This is applied over the ‘group’ variable
- **Add to plot:** add the trace with given parameters to the current plot
- **Save plot**: Save the current plot. Saved plots appear in the list below this button. Saved plots can be viewed by clicking on the name in the list.


