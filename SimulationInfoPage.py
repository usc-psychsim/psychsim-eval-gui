from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import importlib.util
import traceback
import configparser
from datetime import datetime
import os
import sys
import re

from gui_threading import Worker, WorkerSignals
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
        self.psychsim_path = ""
        self.definitions_path = ""
        self.sim_path = ""
        self.sim_name = ""

        # SET UP BUTTONS
        self.run_sim_button.setEnabled(True)
        self.rename_run_button.setEnabled(False)
        self.save_run_input.setEnabled(False)

        self.sel_psychsim_dir.clicked.connect(lambda: pgh.set_directory(path_label=self.psychsim_dir_path,
                                                                         path_var=self.psychsim_path,
                                                                         caption="Select Psychsim Directory"))
        self.sel_def_dir.clicked.connect(lambda: pgh.set_directory(path_label=self.def_dir_path,
                                                                    path_var=self.definitions_path,
                                                                    caption="Select Definitions Directory"))

        self.select_sim.clicked.connect(self.set_file_path)
        self.load_sim_button.clicked.connect(self.load_sim)
        self.run_sim_button.pressed.connect(self.start_sim_thread)
        self.stop_sim_button.pressed.connect(self.stop_thread)
        self.rename_run_button.clicked.connect(self.emit_rename_signal)
        self.save_run_input.returnPressed.connect(self.emit_rename_signal)
        self.sim_info_button.setToolTip('Click for how to write simulation files')
        # self.sim_info_button.clicked.connect(lambda: self.show_doc_window("simulation_script.html"))
        # self.sim_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "simulation"))

        # LOAD CONFIG
        self.load_config()

    def load_config(self, path=None):
        """
        Load the config file and set the paths for psychsim and the sim file
        :param path: (str) path to config file
        """
        config = configparser.ConfigParser()

        try:
            # read in the config in path if it exists, otherwise read the default
            if path:
                config.read(path)
            else:
                config.read('config.ini')

            # set the path variables
            self.psychsim_path = config['PATHS']['psychsim']
            self.definitions_path = config['PATHS']['definitions']
            self.sim_path = config['PATHS']['simulation']
            # set the paths on the gui
            self.psychsim_dir_path.setText(self.psychsim_path)
            self.def_dir_path.setText(self.definitions_path)
            self.sim_path_label.setText(str(self.sim_path).split('/')[-1])
            self.print_sim_output("config loaded", "green")
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

    def set_file_path(self):
        """
        Set the path to the simulation script (self.sim_path) and update the gui labels
        """
        new_path = pgh.get_file_path(path_label=self.sim_path_label)
        if new_path:
            self.sim_path = new_path
            self.sim_loaded_state.setText("...")

    def load_sim(self):
        """
        import the simulation script
        """
        self.add_psychsim_to_sys_path()
        self.print_sim_output(f"psychsim loaded from: {self.psychsim_path}", "green")
        try:
            # import the sim module
            self.sim_spec = importlib.util.spec_from_file_location(self.sim_name, self.sim_path)
            self.sim_module = importlib.util.module_from_spec(self.sim_spec)
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
        sys.path.insert(1, self.psychsim_path)
        sys.path.insert(1, self.definitions_path)

    def start_sim_thread(self):
        try:
            self.sim_spec.loader.exec_module(self.sim_module)

            # Pass the function to execute
            self.thread_running = True
            worker = Worker(self.simulation_thread)  # Any other args, kwargs are passed to the run function
            worker.signals.result.connect(self.handle_output)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)

            # Execute
            self.threadpool.start(worker)
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

    def simulation_thread(self, progress_callback):
        # initialise the sim class
        tester = getattr(self.sim_module, self.sim_name)()

        # initialise local vars
        step = 0
        output = dict()
        while self.thread_running:
            result = tester.run_sim()
            output[step] = result
            step = step + 1
            progress_callback.emit(step, tester.sim_steps)
            if step == tester.sim_steps:
                break
        return output

    def handle_output(self, output):
        # get timestamp
        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M%S")
        run_date = now.strftime("%Y-%m-%d %H:%M:%S")

        # set the current run name settings
        self.previous_run_id.setText(dt_string)
        self.rename_run_button.setEnabled(True)
        self.save_run_input.setEnabled(True)
        self.save_run_input.setText(dt_string)

        # store the data as a PsySimObject in the main dict
        output = pgh.PsychSimRun(id=dt_string,
                                 data=output,
                                 sim_file=self.sim_name,
                                 steps=len(output),
                                 run_date=run_date)

        # emit the signal with the dataid and data
        self.output_changed_signal.emit(dt_string, output)

    def progress_fn(self, step, max_step):
        self.print_sim_output(f"{step}/{max_step} steps completed", "black")

    def thread_complete(self):
        self.print_sim_output("SIMULATION FINISHED!", "black")

    def stop_thread(self):
        self.thread_running = False

    def print_sim_output(self, msg, color="black"):
        pgh.print_output(self.simulation_output, msg, color)

    def emit_rename_signal(self):
        if not self.save_run_input.text():
            self.print_sim_output("NO NEW NAME ENTERED", "red")
        else:
            old_key = self.previous_run_id.text()
            new_key = self.save_run_input.text()
            self.rename_data_signal.emit(old_key, new_key)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimulationInfoPage()
