.. _simulation_script:

Simulation Script
*****************

- Simulation scripts can contain any code, and output results in any type. The GUI will execute each step in a thread, saving the results of all steps in a data structure. Therefore, simulation scripts must adhere to some general rules:

    1. **Class**: The simulation script must be defined as a class with the following members and methods:
        a. **sim_steps**: Defines the total number of steps the simulation will run
        b. **run_sim**: Contains code to execute a single step of the simulation
    2. **File name**: This must be identical to the class name e.g. for a sim class: TestSim, the filename must be *TestSim.py*
- An example simulation that computes some simple sinusoids and saves the results in a dictionary can be found under: *sim_scripts/GenericSim.py* This simulation has the corresponding *get_generic_data* function to extract information as a query.
