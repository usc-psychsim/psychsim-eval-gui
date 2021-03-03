# pyshsim-gui-qt

## Installation and Running instructions:
1. make sure you have the following repositories cloned
   
   * https://github.com/usc-psychsim/psychsim
   * https://github.com/usc-psychsim/atomic
   * https://github.com/usc-psychsim/model-learning
   
2. if not already installed, install pip. Instructions can be found [here](https://pip.pypa.io/en/stable/installing/)
3. install pipenv using instructions [here](https://pipenv-fork.readthedocs.io/en/latest/install.html#installing-pipenv)
4. cd to the root directory

    `$ cd psychsim-eval-gui`
5. install from the Pipfile

    `$ pipenv install`
6. activate the pipenv shell

    `$ pipenv shell`

7. edit the paths in `config.ini` for the cloned repos in step 1 for your local environment
   
   The gui will add these to the system path
   
8. execute the main gui script

    `$ python3 PsychSimGui.py`
    
9. when finished, exit the pipenv

    `$ exit`

