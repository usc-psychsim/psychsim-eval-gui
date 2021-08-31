
Future Directions
*****************

Here I describe known issues / bugs with the GUI and how to fix them.
I also describe features that would be nice to have but that I haven't gotten around to adding (and how to possibly implement them).

Known Bugs/issues
=================


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


- Other plot functionality
    **Issue:**
    There might be issues with other functionality. I haven't fully tested using other plot types and different combinations
    such as using violin and histograms etc. However, I haven't yet found a case it doesn't work on.


- Query data as dialogs
    **Issue:**
    Currently, query data is displayed as a dialog instead of a separate window. This is an issue becuase you cannot have more than one query results window open at any one time.

    **How to fix:**
    Currently, the dialogs are shown with the _exec() function in `show_query_dialog` function in `ui/QueryDataPage.py`. This is done to get a return value, but sets the dialog as modal (blocks other windows).
    The show() function can be used but the dialog window code must be changed to get a return value (e.g. detecting if the `CANCEL`or `OK` buttons are clicked. Additionally, care must be taken as the dialog allows the query name to be changed. This could cause possibly issues in other parts of the GUI if not handled correctly.


- Query param setting
    **Issue:**
    The Gui has been created to be generic and flexible. This allows any simulation scripts to be run and any functions to be used to create queries from the data. However, this results in a tradeoff with complexity for the user.
    This means that setting params must be done in a specific order (e.g. to set the 'agent' param, a query must first be generated that has an 'agent'variable).
    A new, creative way of handling this needs to be implemented.


Nice To Haves
=============
- Deleting data
    **Issue:**
    Currently, it is not possible to remove datasets from the GUI. This could only be an issue if you create too many data sets that it is annoying to search for, and select the one you want.

    **How to Fix:**
    A new `Delete` button should be added to the table that shows datasets similar to how `RENAME` and `save` are in the `update_data_table` function in `ui/PsychSimMainWindow.py` file.


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


- Scripting the gui
    **Issue:**
    It would be useful to be able to call gui functions from a script. This could help with things like running separate ASSIST code, then putting the results through the gui to create a query, and plot all from a script