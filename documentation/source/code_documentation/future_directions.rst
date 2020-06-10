Future Directions
*****************

Here I describe known issues / bugs with the GUI and how to fix them.
I also describe features that would be nice to have but that I haven't gotten around to adding (and how to possibly implement them).

Known Bugs/issues
=================
- Dropdown options
    **Issue:**
    Some dropdown selections have a cascade effect of setting other dropdowns, or making them enabled.
    For example, selecting the data source to sample will populate the variable drop down with available varialbes in that source.
    Sometimes, when these optiosn are initialised, there will be a text value but they haven't initialised the subsequent dropdowns.

    **How to fix:**
    I think this is because when they are set, they don't trigger an action. Probably the easiest thing to do in these cases is at the point where the dropdown is set,
    emit an 'activated' action for the dropdown. This should then trigger any connected functions. (I connect them all to the activated signal)

- Query info updating
    **Issue:**
    The 'View Query Data' button automatically changes the query info back to the first query after close

    **How to fix:**
    This should be fixed from the 'display_query' function in the ui/QueryDataPage.py file. I am not entirely sure how just yet but it probably is just a conditional somewhere.

- Duplicate plot naming
    **Issue:**
    you can name two plots the same name. Plots are stored in a dictionary so only one key value pair will be saved. This will override your old plot.
    If you delete the plot, one of the items will remain on the list but the key no longer exists in the dictionary

    **How to fix:**
    This is probably easy and just involves protecting against having two names the same on the list somehow. To be extra fancy, a new dialog with a message like
    '<name> already exists!' could be shown to alert the user.

- Plot stats
    **Issue1:**
    The stats are calculated for each value of the x-axis. and not across the x-axis. This means if you have multiple agents (or datapoints per x-axis)
    The mean function will avearage over them. It does not, however, average across the x-axis. So, if you want to find the mean of a single agent over all x-values (e.g. time)
    A new function needs to be implemented.

    **How to fix:**
    Stats are applied in the *plot_data* function of *PlotWindow.py* in the following line

    .. code-block:: python

        data = getattr(data.groupby(data[self.x_combo.currentText()]), stat)()


    A new function should be added somewhere that doesn't groupby the x_axis but calculates the stat across all x values
    **Issue2:**
    The stats on the plotting work over some cases (e.g. the following plot showing a scatter plot with the mean over the top).
    However, i haven't tested it over all cases with psychsim data. Therefore it might end up not being the correct implementation.
    .. image:: images/plot_stat_issue_example.png

    **How to fix:**
    This probably needs a specific use case to test on. If a use case is known, then the functionality can be amended.

- Other plot functionality
    **Issue:**
    Similar to the stats, there might be issues with other functionality. I haven't fully tested using other plot types and different combinations
    such as using violin and histograms etc.

- Sim load on initialisation
    **Issue:**
    Currently you need to click the "Load Simulation" button to load a sim before running it.
    This functinoality is there so edits could be made to the sim, and it can be reloaded without having to re-search for the path (useful for debugging).
    It would be good, however, if the sim in the config is loaded on initialisation.

    **How to fix:**
    Probably just a matter of calling the 'load_sim' function in the SimulationInfoPage on initialisation. This is something I thought of at the end and didn't get around to implementing and testing.


Nice To Haves
=============
- Diff table cell highlighting
    **Issue:**
    The DIFF function currently highlights an entire row with either red or blue if something in that row is different.
    It would be good to highlight the individual cell where the difference occurs instead of the whole row, and keep the
    row numbers on the left highlighted to indicate that something within that row has changed.

    **How To Fix:**
    I use difflib which does give information on where the diff occurs and have started to implement this in the
    'get_diff_as_vector' function in ui/DiffResultsWindow.py. However, it is far from finished.

- Diff variable selectinon
    **Issue:**
    Currently, the diff compares an entire results dataframe. It might be useful to just diff one variable of interest

    **How to Fix:**
    This would need a new dropdown to select the variable you want to compare. Then, only selecting that variable from the dataframe to diff and display
    The dropdown would be added to the ui/query_data_page.ui and corresponding button connections in the ui/QueryDataPage.py. The filtering of the data would probably be done
    here, and just passed to the ui/DiffRestulsWindow.py as is.

- Sampling on first day
    **Issue:**
    Currently, when you sample some query data, the sample is applied to the whole data set.
    This is an issue if you want to track how agents progress over time. For example, if you want to see how an 'in danger' or a 'poor' agent
    performs over time, you would want to create a sample that includes only these groups on the first day. They might change groups (become out of danger or rich)
    over time. If you sample over the whole dataset, you would not capture them. You may want to sample over the whole dataset for other purposes, however. And you might
    want to track over a different variable than time.

    **How to fix:**
    There needs to be an option to sample on the first step (or first of any continuous variable) that can be checked.
    The sample group would then need to be determined on that first step (or other first value) and the resulting group sampled over the whole dataset.
    Sampling is currently all done in the ui/QueryDataPage.py file in the 'sample_by_range' and 'sample_by_category' functions.

- Saving queries to csv
    **Issue:**
    Currently, the queries are saved to csv to the default *sim_output* folder. This isn't flexible, and the only feedback is in the text area which might be missed.
    It would be useful to pull up a save file dialog here to allow saving anywhere, and also give the user feedback as to if it is saved.

    **How to fix:**
    The save function is located in the *save_csv_query* of *ui/QueryDataPage.py*

- Loading saved query results
    **Issue:**
    Currently, there is the ability to save query results as a csv. There isn't however, the ability to load saved query results.

    **How to fix:**
    This feature would likely be added in the ui/QueryDataPage.py file.
