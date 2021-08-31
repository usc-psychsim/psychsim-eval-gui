.. _function_definitions:

Function Definitions
********************

- Generic or custom functions can be written to handle different simulation output.
- Functions can be loaded from anywhere but the default, pre-written functions are located in the `functions` directory
- Once a function definition file is loaded, functions are automatically detected by the GUI and added to the functions list on the *query>create* page
- The docstring defined in the function will be available through the ‘DOC’ button on the *query>create* page
- Functions can be generic but must follow the following rules:
    - **Return type**: Must be a pandas Dataframe with variable names as rownames (as opposed to columns)
    - **Return format**: Return in the format (returnType, return_data) where `returnType` is from the following: `(tree|table)`.
            tree: display data on the gui as a tree
            table: display data on the gui as a table

Function Parameters
===================
- Parameters names will populate the `Set function parameters` table.
- Parameters named `data` or of type `bool` will enable a dropdown option for setting parameters in the table
- Data types can be specified in the parameter signature to populate the `expected type` column in the table

for example the following function definition creates the parameter table below::

    def demo_function(self, data: pgh.PsychSimRun=None, agent: str=None, action: str=None, rand_action: bool=False)

.. image:: images/demo_param_table.png