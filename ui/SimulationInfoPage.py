from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import importlib.util
import traceback
import configparser
import os
import sys
import re
import copy

from gui_threading import Worker
import psychsim_gui_helpers as pgh

sim_info_page_file = os.path.join("ui", "sim_info_page.ui")
ui_simInfoPage, QtBaseClass = uic.loadUiType(sim_info_page_file)


class SimulationInfoPage(QWidget, ui_simInfoPage):
    """
    This class is for all functions relating to the simulation info page of the GUI
    This includes; setting paths, running and stopping the sim, storing data from the sim
    """

    # SET UP SIGNALS
    output_changed_signal = pyqtSignal(str, pgh.PsychSimRun)
    rename_data_signal = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # SET UP THREADING
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # SET UP VARS FOR SIM MODULE AND PSYCHSIM
        self.sim_spec = None
        self.sim_module = None

        # SET UP VARS
        self.thread_running = False
        self.run_sim = False
        self.libpaths = {}
        self.sim_path = ""
        self.sim_name = ""

        # SET UP BUTTONS
        self.setup_buttons()

        # LOAD CONFIG
        self.config = self.load_config()

        # LOAD THE SIM DEFINED IN CONFIG
        self.load_sim()

    def setup_buttons(self):
        """
        Set up page buttons
        """
        self.run_sim_button.setEnabled(True)
        self.rename_run_button.setEnabled(False)
        self.save_run_input.setEnabled(False)
        self.select_sim.clicked.connect(lambda: self.set_file_path("sim_scripts"))
        self.run_sim_button.pressed.connect(self.start_sim_thread)
        self.stop_sim_button.pressed.connect(self.stop_thread)
        self.rename_run_button.clicked.connect(self.emit_rename_signal)
        self.save_run_input.returnPressed.connect(self.emit_rename_signal)
        self.sim_info_button.setToolTip('Click for how to write simulation files')

    def load_config(self, path=None):
        """
        Load the config file and set the paths for psychsim and the sim file
        :param path: (str) path to config file
        """
        # TODO: tidy this up - this function might go in the main window...
        config = configparser.ConfigParser()
        try:
            # read in the config in path if it exists, otherwise read the default
            if not path:
                path = 'config.ini'
            config.read(path)

            # set the path variables
            self.libpaths["psychsim"] = config['PATHS']['psychsim']
            self.libpaths["rddl2psychsim"] = config['PATHS']['rddl2psychsim']
            self.libpaths["atomic"] = config['PATHS']['atomic']
            self.libpaths["model_learning"] = config['PATHS']['model_learning']
            self.libpaths["pyrddl"] = config['PATHS']['pyrddl']
            self.sim_path = config['PATHS']['simulation']
            # set the paths on the gui
            self.sim_path_label.setText(str(self.sim_path).split('/')[-1])
            self.print_sim_output("loading config .....", "green")
            for k, p in self.libpaths.items():
                self.print_sim_output(f"{k} path: {p}", "green")
            self.print_sim_output(f"sim path: {self.sim_path}", "green")
            self.print_sim_output(f"config loaded {path}", "green")
            return config
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

    def set_file_path(self, default_dir=""):
        """
        Set the path to the simulation script (self.sim_path) and update the gui labels
        """
        new_path = pgh.get_file_path(path_label=self.sim_path_label, default_dir=default_dir)
        if new_path:
            self.sim_path = new_path
            self.load_sim()
            # self.sim_loaded_state.setText("...")

    def load_sim(self):
        """
        import the simulation script
        """
        self.add_psychsim_to_sys_path()
        self.print_sim_output(f"psychsim loaded from: {self.libpaths['psychsim']}", "green")
        try:
            # import the sim module
            self.sim_spec = importlib.util.spec_from_file_location(self.sim_name, self.sim_path)
            self.sim_module = importlib.util.module_from_spec(self.sim_spec)
            self.sim_spec.loader.exec_module(self.sim_module)
            # update buttons and print output
            self.sim_loaded_state.setText("LOADED")
            self.run_sim_button.setEnabled(True)
            self.print_sim_output(f"sim loaded: {self.sim_path}", "green")
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")
            self.sim_loaded_state.setText("ERROR")

    def add_psychsim_to_sys_path(self):
        """
        Add the selected psychsim and definitions path to the sym path variable
        This enables psychsim to be found by required elements of the gui
        """
        self.sim_name = re.split(r'[.,/]', self.sim_path)[-2]
        for k, p in self.libpaths.items():
            sys.path.insert(1, p)

    def start_sim_thread(self):
        """
        Set up thread for executing simulation
        """
        try:
            self.thread_running = True
            worker = Worker(self.simulation_thread)
            worker.signals.result.connect(self.handle_output)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            # Execute
            self.threadpool.start(worker)
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

    def simulation_thread(self, progress_callback):
        """
        Execute the run_sim() function of the simulation module and store the data in a dictionary
        :param progress_callback: callback signal to display progress of thread
        :return: dictionary with keys as step numbers and corresponding values as data from each step
        """
        simulation = getattr(self.sim_module, self.sim_name)()  # initialise the sim class
        step = 0
        output = dict()
        while self.thread_running:
            result = simulation.run_step()
            output[step] = copy.deepcopy(result)
            step = step + 1
            progress_callback.emit(step, simulation.sim_steps)
            if step == simulation.sim_steps:
                break
        return output

    def handle_output(self, sim_output):
        """
        Update the gui and store data from sim once sim thread has finished
        :param sim_output: data from simulation
        """
        dt_string, run_date = pgh.get_time_stamp()

        # set the current run name settings
        self.previous_run_id.setText(dt_string)
        self.rename_run_button.setEnabled(True)
        self.save_run_input.setEnabled(True)
        self.save_run_input.setText(dt_string)

        # store the data as a PsySimObject in the main dict
        sim_output = pgh.PsychSimRun(id=dt_string,
                                     data=sim_output,
                                     sim_file=self.sim_name,
                                     steps=len(sim_output),
                                     run_date=run_date)

        # emit the signal with the dataid and data
        self.output_changed_signal.emit(dt_string, sim_output)

    def progress_fn(self, step, max_step):
        """
        Print the progress of the simulation thread to the gui
        :param step: current step the simulation is on
        :param max_step: the maximum number of steps the simulation has
        """
        self.print_sim_output(f"{step}/{max_step} steps completed", "black")

    def thread_complete(self):
        """
        Print to gui when simulation has finished
        """
        self.print_sim_output("SIMULATION FINISHED!", "black")

    def stop_thread(self):
        """
        Sets the thread_running flag to false, stopping the simulation thread
        """
        self.thread_running = False

    def print_sim_output(self, msg, color="black"):
        """
        Print messages to the sim_output text area
        :param msg: message to print
        :param color: color of the string to be displayed
        """
        pgh.print_output(self.simulation_output, msg, color)

    def emit_rename_signal(self):
        """
        Emits the rename signal if user has attempted to rename data via the gui
        """
        if not self.save_run_input.text():
            self.print_sim_output("NO NEW NAME ENTERED", "red")
        else:
            old_key = self.previous_run_id.text()
            new_key = self.save_run_input.text()
            self.rename_data_signal.emit(old_key, new_key)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimulationInfoPage()
