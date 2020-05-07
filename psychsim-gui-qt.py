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
from query_functions import PsychSimQuery
# import psychsim_helpers as ph

qtCreatorFile = "psychsim-gui-main.ui"
data_view_file = "data_view.ui"
loaded_data_view_file = "loaded_data_view.ui"
query_data_file = "query_data.ui"
sample_data_file = "sample_data.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
ui_dataView, QtBaseClass = uic.loadUiType(data_view_file)
ui_loadedDataView, QtBaseClass = uic.loadUiType(loaded_data_view_file)
ui_queryDataView, QtBaseClass = uic.loadUiType(query_data_file)
ui_sampleDataView, QtBaseClass = uic.loadUiType(sample_data_file)

#TODO: split this file into individual window python files, and separate generic gui stuff to other files
#TODO: try to get rid of class variables and use passed variables where possible (for readability)

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


class LoadedDataWindow(QMainWindow, ui_loadedDataView):
    def __init__(self):
        super(LoadedDataWindow, self).__init__()
        self.setupUi(self)
        # self.model = QStandardItemModel()
        # self.loaded_data_table.setModel(self.model)

        # self.loaded_data_table.setRowCount(1)
        self.loaded_data_table.setColumnCount(4)
        self.loaded_data_table.setHorizontalHeaderLabels(['id', 'name', 'steps', 'data'])

    def add_row_to_table(self, row):
        rowPosition = self.loaded_data_table.rowCount()
        self.loaded_data_table.insertRow(rowPosition)
        index = 0 #todo: figure out a better way to do this
        for item in row:
            if type(item) == str:
                self.loaded_data_table.setItem(rowPosition, index, QTableWidgetItem(item))
            elif type(item) == QPushButton:
                self.loaded_data_table.setCellWidget(rowPosition, index, item)
            index = index + 1


class RawDataWindow(QMainWindow, ui_dataView):
    #TODO: is this way better? https://www.codementor.io/@deepaksingh04/design-simple-dialog-using-pyqt5-designer-tool-ajskrd09n
    def __init__(self):
        super(RawDataWindow, self).__init__()
        self.setupUi(self)

    def set_pandas_model(self, model):
        self.raw_data_table.setModel(model)


class SampleDataWindow(QMainWindow, ui_sampleDataView):
    def __init__(self):
        super(SampleDataWindow, self).__init__()
        self.setupUi(self)

    def sample_data(self):
        pass

    def update_sample_table(self):
        pass


class QueryDataWindow(QMainWindow, ui_queryDataView):
    def __init__(self):
        super(QueryDataWindow, self).__init__()
        self.setupUi(self)
        self.psychsim_query = PsychSimQuery()
        self.set_function_dropdown()

        self.execute_query_button.clicked.connect(self.execute_query)
        self.data_combo.activated.connect(self.set_agent_dropdown)
        self.data_combo.activated.connect(self.set_action_dropdown)
        self.data = None

    def set_data_dropdown(self, data):
        self.data = data #TODO: FIX SO THERE ISN"T 2 COPIES OF THE DATA IN THE GUI (IN THE MAIN AND HERE)
        #TODO: make this a main set_dropdown function and refactor out the others
        all_items = [self.data_combo.itemText(i) for i in range(self.data_combo.count())]
        new_items = [item for item in data.keys() if item not in all_items]
        self.data_combo.addItems(new_items)

    def set_function_dropdown(self):
        query_methods = [method_name for method_name in dir(self.psychsim_query)
                         if callable(getattr(self.psychsim_query, method_name))
                         and '__' not in method_name]
        self.function_combo.addItems(query_methods)

    def set_agent_dropdown(self):
        #todo: refactor this and other dropdown generation functions
        #TODO: figure out how to set this based on the data set (i.e. remove old ones and add new ones)
        agents = self.data[self.data_combo.currentText()]['agent'].unique()
        all_items = [self.agent_combo.itemText(i) for i in range(self.agent_combo.count())]
        new_items = [item for item in agents if item not in all_items]
        self.agent_combo.addItems(new_items)

    def set_action_dropdown(self):
        actions = self.data[self.data_combo.currentText()]['action'].unique()
        all_items = [self.action_combo.itemText(i) for i in range(self.action_combo.count())]
        new_items = [item for item in actions if item not in all_items]
        self.action_combo.addItems(new_items)

    def execute_query(self):
        query_function = self.function_combo.currentText()
        result = getattr(self.psychsim_query, query_function)()
        print(result)

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
        self.sim_data_dict = dict()

        #SET UP BUTTONS
        self.run_sim_button.setEnabled(False)
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

        self.load_config()

    def progress_fn(self, step, max_step):
        self.print_sim_output(f"{step}/{max_step} steps completed", "black")

    def simulation_thread(self, progress_callback):
        tester = getattr(self.sim_module, self.sim_name)()
        # tester2 = self.sim_module.GuiTestSim()
        step = 0
        complete = dict(n=step, total=tester.sim_steps)
        sim_data = pd.DataFrame()
        while self.run_thread:
            result = tester.run_sim()
            self.print_debug(debug=result)
            sim_data = sim_data.append(self.get_debug_data(debug=result, step=step))
            model = pandasModel(sim_data)
            #TODO: emit output to print to screen
            step = step + 1
            progress_callback.emit(step, tester.sim_steps)
            if step == tester.sim_steps:
                break

        return dict(data=sim_data, step=step)#"Done."

    def print_output(self, output):
        data = output['data']
        step = output['step']
        #todo: rename this function
        #save the data in the class dict
        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M%S")
        self.sim_data_dict[dt_string] = data

        # create the button to access the data
        btn = QPushButton(self.loaded_data_window.loaded_data_table)
        btn.setText('view')
        btn.clicked.connect(partial(self.show_data_window, dt_string))

        # add a value to the data dropdown for querying (and sampling
        self.query_data_window.set_data_dropdown(self.sim_data_dict)

        #set the loaded data window row
        # self.sim_name = re.split(r'[.,/]', self.sim_path)[-2]
        self.loaded_data_window.add_row_to_table([dt_string, self.sim_name, str(step), btn])

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
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

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


    def print_sim_output(self, msg, color):
        self.simulation_output.setTextColor(QColor(color))
        self.simulation_output.append(msg)

    def show_data_window(self, key):
        #this should really accept a key to access the dict of data saved at the top level
        #then set the model based on this
        #todo: add some exception handling
        model = pandasModel(self.sim_data_dict[key])
        self.data_window.set_pandas_model(model)
        self.data_window.setWindowTitle(f"{key} data")
        self.data_window.show()

    def show_loaded_data_window(self):
        self.loaded_data_window.show()

    def show_query_data_window(self):
        self.query_data_window.show()

    def show_sample_data_window(self):
        self.sample_data_window.show()


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


    def get_debug_data(self, debug, step, level=0):
        # TODO: make this output some sort of dataframe
        # THIS ASSUMES THE STRUCTURE WON'T CHANGE
        sim_info = pd.DataFrame(columns=["step", "agent", "action"])
        step_info = []

        for k, v in debug.items():
            agent_info = dict(step=[step],agent=None, action=None, possible_actions=None, beliefs=None)
            agent_info["agent"] = k
            for k1, v1 in v.items():
                for k2, v2 in v1.items():
                    if type(v2) == dict:
                        for k3, v3 in v2.items():
                            if type(v3) == self.psychsim_module.ActionSet:
                                agent_info["action"] = v3
                            if type(v3) == dict:
                                agent_info["possible_actions"] = v3
            if agent_info["possible_actions"] is not None:
                agent_info["beliefs"] = [agent_info["possible_actions"][agent_info["action"]]["__beliefs__"]]
            step_info.append(agent_info)

        # TODO: turn ste_info rows into a dataframe here PROPERLY
        step_dataframes = []
        for info in step_info:
            info["action"] = [str(info["action"])]
            info.pop("possible_actions", None)
            # agent_info.pop("beliefs", None)
            agent_df = pd.DataFrame.from_dict(info) #TODO: FIX THIS
            if info['beliefs']:
                vds_vals = self.extract_values_fromVectorDistributionSet(info['beliefs'][0])
                agent_df = pd.concat([agent_df, vds_vals], axis=1)
            agent_df = agent_df.drop('beliefs', axis=1)
            step_dataframes.append(agent_df)
        output_df = pd.concat(step_dataframes)
        return output_df


    def extract_values_fromVectorDistributionSet(self, vds):
        vds_values = pd.DataFrame()
        clean_header = []
        actor_values = []
        for key in vds.keyMap:
            # print(actor_distribution_set.marginal(key))
            actor_values.append(str(vds.marginal(key)).split()[-1])
            if "Actor" in key:
                key = key.split(' ')[-1]
            clean_header.append(key)
        data = pd.DataFrame(actor_values).T
        data.columns = clean_header
        # TODO: create the region column
        vds_values = vds_values.append(data)
        return vds_values

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())