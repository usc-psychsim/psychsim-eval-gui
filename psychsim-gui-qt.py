from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import time
import os
import importlib.util
import sys
import re
import traceback
import pandas
import configparser
import time

from gui_threading import Worker, WorkerSignals

qtCreatorFile = "psychsim-gui-main.ui"
data_view_file = "data_view.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
ui_dataView, QtBaseClass2 = uic.loadUiType(data_view_file)


class pandasModel(QAbstractTableModel):

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

class RawDataWindow(QMainWindow, ui_dataView):
    #TODO: is this way better? https://www.codementor.io/@deepaksingh04/design-simple-dialog-using-pyqt5-designer-tool-ajskrd09n
    def __init__(self):
        super(RawDataWindow, self).__init__()
        self.setupUi(self)

    def set_pandas_model(self, model):
        self.raw_data_table.setModel(model)


class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        #SET UP OTHER WINDOWS
        self.data_window = RawDataWindow()

        #SET UP THREADING
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        #VARS FOR SIM MODULE
        self.spec = None
        self.sim_module = None

        #SET UP VARS
        self.run_thread = False
        self.run_sim = False
        self.psychsim_path = ""
        self.definitions_path = ""
        self.sim_path = ""

        #SET UP BUTTONS
        self.run_sim_button.setEnabled(False)
        # self.run_sim_button.clicked.connect(self.start_sim_thread)
        self.run_sim_button.pressed.connect(self.start_sim_thread)
        self.stop_sim_button.pressed.connect(self.stop_thread)
        self.actionSelect_load_config.triggered.connect(self.open_config_loader)
        self.select_sim.clicked.connect(self.set_sim_path)
        self.sel_psychsim_dir.clicked.connect(self.set_psychsim_path)
        self.sel_def_dir.clicked.connect(self.set_definitions_path)
        self.actionview_data.triggered.connect(self.show_data_window)
        self.load_sim_button.clicked.connect(self.load_sim)

        self.load_config()


    def progress_fn(self, n):
        self.print_sim_output("%d%% done" % n, "black")

    def simulation_thread(self, progress_callback):
        tester = self.sim_module.GuiTestSim()
        step = 0
        complete = dict(n=step, total=tester.sim_steps)

        while self.run_thread:
            result = tester.run_sim()
            tester.print_debug(debug=result)
            step_info = tester.get_debug_data(debug=result, step=step)
            model = pandasModel(step_info)
            #TODO: emit output to print to screen
            progress_callback.emit(step)
            step = step + 1
            if step == tester.sim_steps:
                break

        return model#"Done."

    def print_output(self, s):
        self.data_window.set_pandas_model(s)

    def thread_complete(self):
        self.print_sim_output("THREAD COMPLETE!", "black")

    def stop_thread(self):
        self.run_thread = False

    def start_sim_thread(self):
        try:
            self.spec.loader.exec_module(self.sim_module)
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

        #THEIR STUFF---------------------------
        # Pass the function to execute
        self.run_thread = True
        worker = Worker(self.simulation_thread)  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)


    def recurring_timer(self):
        self.counter += 1
        self.l.setText("Counter: %d" % self.counter)

#--------------------------------

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
            self.psychsim_dir_path.setText(self.definitions_path)
            self.def_dir_path.setText(self.definitions_path)
            self.sim_path_label.setText(str(self.sim_path).split('/')[-1])
            self.print_sim_output("config loaded", "green")
        except:
            self.print_sim_output("no config", "red")
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

        #set the display

    def set_psychsim_path(self):
        psychsim_path = self.get_directory_path()
        self.definitions_path = f"{str(psychsim_path)}"
        self.psychsim_dir_path.setText(self.definitions_path)

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
            sim_name = re.split(r'[.,/]', self.sim_path)[-2]
            os.environ["PYTHONPATH"] += os.pathsep + os.pathsep.join(pathlist)
            sys.path.insert(1, self.psychsim_path)
            import psychsim  # this can be imported because of the above line
            sys.path.insert(1, self.definitions_path)  # this needs to be done to get the path of the other repo

            self.spec = importlib.util.spec_from_file_location(sim_name, self.sim_path)
            self.sim_module = importlib.util.module_from_spec(self.spec)
            self.sim_loaded_state.setText("LOADED")
            self.run_sim_button.setEnabled(True)
            self.print_sim_output(f"sim loaded: {self.sim_path}", "green")
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")
            #TODO: push the error up to the text area
            self.sim_loaded_state.setText("ERROR")


    def print_sim_output(self, msg, color):
        self.simulation_output.setTextColor(QColor(color))
        self.simulation_output.append(msg)

    def show_data_window(self):
        self.data_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())