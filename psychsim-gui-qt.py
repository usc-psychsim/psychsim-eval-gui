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

qtCreatorFile = "psychsim-gui-main.ui"
data_view_file = "data_view.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
ui_dataView, QtBaseClass2 = uic.loadUiType(data_view_file)

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


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
        # self.run_sim_button.clicked.connect(self.oh_no)
        # self.run_sim_button.clicked.connect(self.stop_sim_thread)
        self.actionSelect_load_config.triggered.connect(self.open_config_loader)
        self.select_sim.clicked.connect(self.set_sim_path)
        self.sel_psychsim_dir.clicked.connect(self.set_psychsim_path)
        self.sel_def_dir.clicked.connect(self.set_definitions_path)
        # self.actionview_data.triggered.connect(self.show_data_window)
        self.load_sim_button.clicked.connect(self.load_sim)

        self.load_config()

#------------------------
        self.counter = 0

        self.run_thread = False

        self.b.pressed.connect(self.oh_no)
        self.b2.pressed.connect(self.stop_thread)
        self.show()

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()

    def progress_fn(self, n):
        self.print_sim_output("%d%% done" % n, "black")

    def execute_this_fn(self, progress_callback):
        tester = self.sim_module.GuiTestSim()
        step = 0
        complete = dict(n=step, total=tester.sim_steps)

        #THEIR STUFF----------------
        # for n in range(0, 5):
        #     time.sleep(1)
        #     progress_callback.emit(n * 100 / 4)
        #
        time_sleep = 0
        while self.run_thread:
            result = tester.run_sim()
            tester.print_debug(debug=result)
            step_info = tester.get_debug_data(debug=result, step=step)
            #TODO: emit model
            #TODO: emit output to print to screen
            time.sleep(1)
            progress_callback.emit(time_sleep)
            time_sleep = time_sleep + 1
            step = step + 1
            if step == tester.sim_steps:
                break

        return "Done."

    def print_output(self, s):
        self.print_sim_output(s, "black")

    def thread_complete(self):
        self.print_sim_output("THREAD COMPLETE!", "black")

    def stop_thread(self):
        self.run_thread = False

    def oh_no(self):
        try:
            self.spec.loader.exec_module(self.sim_module)
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

        #THEIR STUFF---------------------------
        # Pass the function to execute
        self.run_thread = True
        worker = Worker(self.execute_this_fn)  # Any other args, kwargs are passed to the run function
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