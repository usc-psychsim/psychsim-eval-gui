import sys
from PyQt5 import QtCore, QtGui, QtWidgets,   uic
from data_view import dataView
import os
import importlib.util
import sys
import re
import traceback
import pandas
import configparser


qtCreatorFile = "psychsim-gui-main.ui"
data_view_file = "data_view.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
ui_dataView, QtBaseClass2 = uic.loadUiType(data_view_file)

class pandasModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        QtCore.QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        return None

class RawDataWindow(QtWidgets.QMainWindow, ui_dataView):
    #TODO: is this way better? https://www.codementor.io/@deepaksingh04/design-simple-dialog-using-pyqt5-designer-tool-ajskrd09n
    def __init__(self):
        super(RawDataWindow, self).__init__()
        self.setupUi(self)

    def set_pandas_model(self, model):
        self.raw_data_table.setModel(model)


class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        #SET UP OTHER WINDOWS
        self.data_window = RawDataWindow()

        #VARS FOR SIM MODULE
        self.spec = None
        self.sim_module = None

        #SET UP VARS
        self.sim_running = False
        self.psychsim_path = ""
        self.definitions_path = ""
        self.sim_path = ""

        #SET UP BUTTONS
        self.run_sim_button.setEnabled(False)
        self.run_sim_button.clicked.connect(self.run_simulation)
        self.actionSelect_load_config.triggered.connect(self.open_config_loader)
        self.select_sim.clicked.connect(self.set_sim_path)
        self.sel_psychsim_dir.clicked.connect(self.set_psychsim_path)
        self.sel_def_dir.clicked.connect(self.set_definitions_path)
        self.actionview_data.triggered.connect(self.show_data_window)
        self.load_sim_button.clicked.connect(self.load_sim)

        self.load_config()

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
        return str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))

    def get_file_path(self, file_type="Python Files (*.py)"):
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,"Select Sim", "",file_type, options=options)
        if fileName:
            print(fileName)
        return fileName

    def run_simulation(self):
        #RUN SIM CODE FROM DASH GUI
        if self.sim_running:
            self.run_sim_button.setText("STOP")
            self.sim_running = False
            self.print_sim_output("SIM RUNNING", "black")
        else:
            self.run_sim_button.setText("RUN")
            self.sim_running = True
            self.print_sim_output("SIM STOPPED", "black")

        step = 0
        try:
            self.spec.loader.exec_module(self.sim_module)
            tester = self.sim_module.GuiTestSim()
            #TODO: multi thread this ? figure out how to stop the sim
            while step <= tester.sim_steps:
                self.print_sim_output(f"running sim {step}/{tester.sim_steps}", "black")
                result = tester.run_sim()
                tester.print_debug(debug=result)
                step_info = tester.get_debug_data(debug=result, step=step)
                # self.print_sim_output(step_info, "black") #TODO: fix this output
                # TODO: concatenate to new dataframe with new step column
                step = step + 1

                model = pandasModel(step_info)
                self.data_window.set_pandas_model(model)
            # self.data_window.raw_data_table.view.resize(800, 600)
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")



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
        self.simulation_output.setTextColor(QtGui.QColor(color))
        self.simulation_output.append(msg)

    def show_data_window(self):
        self.data_window.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
