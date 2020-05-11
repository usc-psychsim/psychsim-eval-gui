from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import os
import importlib.util
import sys
import re
import traceback
import pandas as pd
import configparser
from datetime import datetime
from functools import partial

from gui_threading import Worker, WorkerSignals
from PandasModel import PandasModel
# import psychsim_helpers as ph

from QueryDataWindow import QueryDataWindow
from LoadedDataWindow import LoadedDataWindow
from DataViewWindow import RawDataWindow
from SampleDataWindow import SampleDataWindow
from renameDataDialog import RenameDataDialog

qtCreatorFile = "psychsim-gui-main.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

#TODO: split generic gui stuff to other files
#TODO: try to get rid of class variables and use passed variables where possible (for readability)

class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        #SET UP OTHER WINDOWS
        self.data_window = RawDataWindow()
        self.loaded_data_window = LoadedDataWindow()
        self.query_data_window = QueryDataWindow()
        self.sample_data_window = SampleDataWindow()

        #SET UP THREADING
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        #VARS FOR SIM MODULE
        self.sim_spec = None
        self.psysim_spec = None
        self.sim_module = None
        self.psychsim_module = None

        #SET UP VARS
        self.run_thread = False
        self.run_sim = False
        self.psychsim_path = ""
        self.definitions_path = ""
        self.sim_path = ""
        self.sim_name = ""

        #SET UP DICT FOR DATA
        self.sim_data_dict = dict() #this one is for the debug output

        #SET UP BUTTONS
        self.run_sim_button.setEnabled(False)
        self.rename_run_button.setEnabled(False)
        self.save_run_input.setEnabled(False)
        self.run_sim_button.pressed.connect(self.start_sim_thread)
        self.stop_sim_button.pressed.connect(self.stop_thread)
        self.actionSelect_load_config.triggered.connect(self.open_config_loader)
        self.select_sim.clicked.connect(self.set_sim_path)
        self.sel_psychsim_dir.clicked.connect(self.set_psychsim_path)
        self.sel_def_dir.clicked.connect(self.set_definitions_path)
        self.actionview_data.triggered.connect(self.show_loaded_data_window)
        self.actionquery_data.triggered.connect(self.show_query_data_window)
        self.actioncreate_samples.triggered.connect(self.show_sample_data_window)
        self.load_sim_button.clicked.connect(self.load_sim)
        self.actionload_data_from_file.triggered.connect(self.load_data_from_file)
        self.rename_run_button.clicked.connect(self.rename_data_id)

        self.load_config()

    def progress_fn(self, step, max_step):
        self.print_sim_output(f"{step}/{max_step} steps completed", "black")

    def simulation_thread(self, progress_callback):
        tester = getattr(self.sim_module, self.sim_name)()
        # tester2 = self.sim_module.GuiTestSim()
        step = 0
        complete = dict(n=step, total=tester.sim_steps)
        sim_data = pd.DataFrame()
        output = dict()
        while self.run_thread:
            step_data = dict()
            #get the result of the step
            result = tester.run_sim()

            #append the raw output
            step_data['step_data'] = result
            step_data['step'] = step
            output[step] = step_data

            #Get the beliefs (not needed here?)
            self.print_debug(debug=result)

            step = step + 1
            progress_callback.emit(step, tester.sim_steps)
            if step == tester.sim_steps:
                break
        return output

    def handle_output(self, output):
        """
        update the query_data_window dropwdown to select data
        :param output:
        :return:
        """
        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M%S")
        self.previous_run_id.setText(dt_string)
        self.sim_data_dict[dt_string] = output
        self.query_data_window.set_data_dropdown(self.sim_data_dict)
        self.rename_run_button.setEnabled(True)
        self.save_run_input.setEnabled(True)
        self.save_run_input.setText(dt_string)

        self.update_data_table()

    def update_data_table(self):
        self.loaded_data_window.clear_table()#TODO: find better way to do this so it isn't loaded a new each time
        for data_id, data in self.sim_data_dict.items():
            #save the data in the class dict
            now = datetime.now()
            date_string = now.strftime("%d/%m/%Y %H:%M:%S")
            # self.sim_data_dict_beliefs[dt_string] = data

            # create the button to rename the data
            btn = QPushButton(self.loaded_data_window.loaded_data_table)
            btn.setText('RENAME')
            btn.clicked.connect(partial(self.rename_data, data_id))

            # create the button to save the data to csv
            btn2 = QPushButton(self.loaded_data_window.loaded_data_table)
            btn2.setText('save')
            btn2.clicked.connect(partial(self.save_data_window, data_id))

            # # add a value to the data dropdown for querying (and sampling
            # self.query_data_window.set_data_dropdown(self.sim_data_dict_beliefs)

            #set the loaded data window row
            # self.sim_name = re.split(r'[.,/]', self.sim_path)[-2]
            # columns = ['date', 'data_id', 'sim_file', '', '']
            self.loaded_data_window.add_row_to_table([date_string, data_id, self.sim_name, btn, btn2])

    def test_print_out(self, tst):
        print(tst)

    def thread_complete(self):
        self.print_sim_output("THREAD COMPLETE!", "black")

    def stop_thread(self):
        self.run_thread = False

    def start_sim_thread(self):
        try:
            self.sim_spec.loader.exec_module(self.sim_module)
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

        #THEIR STUFF---------------------------
        # Pass the function to execute
        self.run_thread = True
        worker = Worker(self.simulation_thread)  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.handle_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

#--------------------------------

    def rename_data(self, old_key):
        #show the rename dialog and get the new name
        new_key, accepted = RenameDataDialog.get_new_name(old_name=old_key)
        if accepted:
            self.sim_data_dict[new_key] = self.sim_data_dict.pop(old_key)
            self.update_data_table()
            self.query_data_window.set_data_dropdown(self.sim_data_dict)


    def open_config_loader(self):
        #open file dialog
        config_path = self.get_file_path(file_type="Config files (*.ini)")
        self.load_config(config_path)

    def load_config(self, path=None):
        config = configparser.ConfigParser()
        try:
            if path:
                config.read(path)
            else:
                #read the default
                config.read('config.ini')

            #set the path variables
            self.psychsim_path = config['PATHS']['psychsim']
            self.definitions_path = config['PATHS']['definitions']
            self.sim_path = config['PATHS']['simulation']
            self.psychsim_dir_path.setText(self.psychsim_path)
            self.def_dir_path.setText(self.definitions_path)
            self.sim_path_label.setText(str(self.sim_path).split('/')[-1])
            self.print_sim_output("config loaded", "green")
        except:
            self.print_sim_output("INVALID CONFIG", "red")
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

        #set the display

    def set_psychsim_path(self):
        psychsim_path = self.get_directory_path()
        self.psychsim_path = f"{str(psychsim_path)}"
        self.psychsim_dir_path.setText(self.psychsim_path)

    def set_definitions_path(self):
        definitions_path = self.get_directory_path()
        self.definitions_path = f"{str(definitions_path)}"
        self.def_dir_path.setText(self.definitions_path)

    def set_sim_path(self):
        sim_file_path = self.get_file_path()
        self.sim_path = f"{str(sim_file_path)}"
        self.sim_path_label.setText(str(sim_file_path).split('/')[-1])

    def get_directory_path(self):
        return str(QFileDialog.getExistingDirectory(self, "Select Directory"))

    def get_file_path(self, file_type="Python Files (*.py)"):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Select Sim", "",file_type, options=options)
        if fileName:
            print(fileName)
        return fileName


    def load_sim(self):
        try:
            pathlist = [self.psychsim_path, self.definitions_path, self.sim_path]
            self.sim_name = re.split(r'[.,/]', self.sim_path)[-2]
            sys.path.insert(1, self.psychsim_path)
            import psychsim  # this can be imported because of the above line
            sys.path.insert(1, self.definitions_path)  # this needs to be done to get the path of the other repo
            #Import psychsim
            self.psychsim_spec = importlib.util.spec_from_file_location("psychsim.pwl", self.sim_path)
            self.psychsim_module = importlib.util.module_from_spec(self.psychsim_spec)
            self.psychsim_spec.loader.exec_module(self.psychsim_module)

            #import the sim module
            self.sim_spec = importlib.util.spec_from_file_location(self.sim_name, self.sim_path)
            self.sim_module = importlib.util.module_from_spec(self.sim_spec)
            self.sim_loaded_state.setText("LOADED")
            self.run_sim_button.setEnabled(True)
            self.print_sim_output(f"sim loaded: {self.sim_path}", "green")
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")
            #TODO: push the error up to the text area
            self.sim_loaded_state.setText("ERROR")

    def save_data_window(self, data_id):
        data = self.sim_data_dict_beliefs[data_id]
        output_directory = 'sim_output'
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        csv_file = f"{data_id}.csv"
        data.to_csv(os.path.join(output_directory, csv_file))



    def print_sim_output(self, msg, color):
        self.simulation_output.setTextColor(QColor(color))
        self.simulation_output.append(msg)

    def show_data_window(self, key):
        #this should really accept a key to access the dict of data saved at the top level
        #then set the model based on this
        #todo: add some exception handling
        model = PandasModel(self.sim_data_dict_beliefs[key])
        self.data_window.set_pandas_model(model)
        self.data_window.setWindowTitle(f"{key} data")
        self.data_window.show()

    def show_loaded_data_window(self):
        self.loaded_data_window.show()

    def show_query_data_window(self):
        self.query_data_window.show()

    def show_sample_data_window(self):
        self.sample_data_window.show()

    def load_data_from_file(self):
        data, data_id = self.loaded_data_window.load_data_from_file()
        self.sim_data_dict_beliefs[data_id] = data

        # TODO: refactor this as it is copied from the main window code
        btn = QPushButton(self.loaded_data_window.loaded_data_table)
        btn.setText('view')
        btn.clicked.connect(partial(self.show_data_window, data_id)) #TODO: figure out how to connect this back to the main window

        btn2 = QPushButton(self.loaded_data_window.loaded_data_table)
        btn2.setText('save')
        btn2.clicked.connect(partial(self.save_data_window, data_id))

        # add a value to the data dropdown for querying (and sampling
        self.query_data_window.set_data_dropdown(self.sim_data_dict_beliefs)

        #set the loaded data window row
        # self.sim_name = re.split(r'[.,/]', self.sim_path)[-2]
        self.loaded_data_window.add_row_to_table([data_id, self.sim_name, str("x"), btn, btn2])

    def rename_data_id(self, old_key=None):
        #TODO: refactor this with other rename function
        old_key = self.previous_run_id.text()
        if self.save_run_input.text():
            new_key = self.save_run_input.text()
            if new_key in self.sim_data_dict.keys():
                self.print_sim_output(f"{new_key} ALREADY EXISTS", "red")
            else:
                try:
                    self.sim_data_dict[new_key] = self.sim_data_dict.pop(old_key)
                    self.update_data_table()
                except KeyError as e:
                    self.print_sim_output(f"{old_key} has been renamed to {new_key}", "red")
                self.previous_run_id.setText(new_key)
                #update the dropdown menu
                #TODO: maybe move this code to when the window gets shown? (though that wouldn't update it if the window remains open...)
                self.query_data_window.set_data_dropdown(self.sim_data_dict)
                self.print_sim_output(f"{old_key} renamed to {new_key}", "green")
        else:
            self.print_sim_output("NO NEW NAME ENTERED", "red")


    def print_debug(self, debug, level=0):
        reg_node = "".join(['│\t' for i in range(level)]) + "├─"
        end_node = "".join(['│\t' for i in range(level)]) + "├─"
        level = level + 1
        if type(debug) == dict:
            for k, v in debug.items():
                print(f"{reg_node} {k}")
                self.print_debug(v, level)
        elif type(debug) == self.psychsim_module.VectorDistributionSet:
            for key in debug.keyMap:
                print(f"{end_node} {key}: {str(debug.marginal(key)).split()[-1]}")
        elif type(debug) == self.psychsim_module.ActionSet:
            for key in debug:
                print(f"{end_node} {key}: ")
        else:
            print(f"{end_node} {debug}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())