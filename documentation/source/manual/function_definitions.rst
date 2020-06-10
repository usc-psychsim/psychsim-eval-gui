.. _function_definitions:

Function Definitions
********************

- Generic or custom functions can be written to handle different simulation output.
- Functions are added to the *functions/query_functions.py* script
- Once a function is added, it will be automatically detected by the GUI on startup and added to the functions list on the *query>create* page
- The docstring defined in the function will be available through the ‘DOC’ button on the *query>create* page
- Functions can be generic but must follow the following rules:
    - **Output**: Must be a pandas Dataframe
    - **Input**: should be generic, the parameters come from the *query>create* page
