from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from PyQt5.QtWebEngineWidgets import QWebEngineView
import os
import pickle
import importlib.util
import inspect
import sys
import re
import traceback
import pandas as pd
import configparser
from datetime import datetime
from functools import partial
import copy
import difflib

import plotly
import plotly.graph_objects as go
import plotly.express as px

from gui_threading import Worker, WorkerSignals
from PandasModel import PandasModel
import psychsim_gui_helpers as pgh
from CheckableComboBox import CheckableComboBox
from functions.query_functions import PsychSimQuery

from ui.LoadedDataWindow import LoadedDataWindow
from ui.RenameDataDialog import RenameDataDialog
from ui.QueryDataDialog import QueryDataDialog
from ui.SavePlotDialog import SavePlotDialog
from ui.DocWindow import DocWindow
from ui.PlotWindow import PlotWindow
from ui.DiffResultsWindow import DiffResultsWindow
from ui.PlotViewDialog import PlotViewDialog


qtCreatorFile = os.path.join("ui", "psychsim-gui-main.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


# TODO: split generic gui stuff to other files
# TODO: try to get rid of class variables and use passed variables where possible (for readability)
# TODO: final refactor to make sure code is readable
# TODO: add docstrings


class PsychSimGuiMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.setWindowTitle("PyschSim GUI")

        # SET UP OTHER WINDOWS
        self.loaded_data_window = LoadedDataWindow()
        self.loaded_data_window.load_data_button.clicked.connect(self.load_data_from_file)
        self.doc_window = DocWindow()

        # SET UP THREADING
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # VARS FOR SIM MODULE AND PSYCHSIM
        self.sim_spec = None
        self.psysim_spec = None
        self.sim_module = None
        self.psychsim_module = None

        # SET UP MAIN WINDOW VARS
        self.run_thread = False
        self.run_sim = False
        self.psychsim_path = ""
        self.definitions_path = ""
        self.sim_path = ""
        self.sim_name = ""
        self.sim_data_dict = dict()
        self.query_data_dict = dict()
        self.plot_data_dict = dict()

        # SET UP MAIN WINDOW BUTTONS
        self.sim_info_button.setToolTip('Click for how to write simulation files')
        self.run_sim_button.setEnabled(True)
        self.rename_run_button.setEnabled(False)
        self.save_run_input.setEnabled(False)

        self.sel_psychsim_dir.clicked.connect(self.set_psychsim_path)
        self.sel_def_dir.clicked.connect(self.set_definitions_path)
        self.select_sim.clicked.connect(self.set_sim_path)
        self.load_sim_button.clicked.connect(self.load_sim)

        self.run_sim_button.pressed.connect(self.start_sim_thread)
        self.stop_sim_button.pressed.connect(self.stop_thread)

        self.rename_run_button.clicked.connect(self.rename_data_from_input)
        self.save_run_input.returnPressed.connect(self.rename_data_from_input)

        self.actionview_data.triggered.connect(self.loaded_data_window.show)
        self.actionrun_sim.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.actionquery.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.actionplot.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.actionsample_data.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.actionmanual.triggered.connect(lambda: self.show_doc_window("index.html"))

        #help buttons
        self.sim_info_button.clicked.connect(lambda: self.show_doc_window("simulation_script.html"))
        self.sim_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "simulation"))
        self.query_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "query"))
        self.function_info_button.clicked.connect(lambda: self.show_doc_window("function_definitions.html"))
        self.plot_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "plot"))
        self.sample_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "sample"))

        # LOAD CONFIG
        self.load_config()

        # SET UP QUERY WINDOW --------------
        self.psychsim_query = PsychSimQuery()
        self.set_function_dropdown()
        self.function_info_button.setToolTip('Click for how to write custom query functions')

        self.execute_query_button.clicked.connect(self.execute_query)
        self.view_query_button.clicked.connect(self.view_query)
        self.save_csv_query_button.clicked.connect(self.save_csv_query)
        self.diff_query_button.clicked.connect(self.diff_query)
        self.query_doc_button.clicked.connect(self.get_query_doc)
        self.data_combo.activated.connect(self.reset_params)
        self.agent_combo.activated.connect(self.set_action_dropdown)
        # self.data_combo.activated.connect(self.set_action_dropdown)
        # self.data_combo.activated.connect(self.set_cycle_dropdown)


        # SET UP PLOT WINDOW ----------------
        self.current_plot = None

        self.create_new_plot_button.clicked.connect(lambda: self.create_new_plot())#self.plot_data)
        # self.add_plot_button.clicked.connect(self.plot_data)
        # self.clear_plot_button.clicked.connect(self.clear_plot) #TODO: remove associated function
        self.test_check.stateChanged.connect(self.setup_test_plot)
        # self.save_plot_button.clicked.connect(self.save_plot)
        self.plot_listwidget.itemClicked.connect(self.add_plot_from_list)
        self.remove_plot_button.clicked.connect(self.remove_plot)

        # self.set_type_dropdown()
        # self.set_stat_dropdown()

        # self.setup_plot_widget()

        self.current_fig = None

        # SET UP SAMPLE WINDOW ----------------
        self.sample_agent_combo_mult = CheckableComboBox()
        self.sample_agent_combo_mult.setEnabled(False)
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.sample_agent_combo_mult)
        self.agent_sample_combo_widget.setLayout(vbox_layout)

        self.sample_data_combo.activated.connect(self.set_sample_params)
        self.sample_data_combo.activated.connect(self.set_sample_agent)
        self.save_sample_button.clicked.connect(self.save_sample)
        self.sample_step_check.stateChanged.connect(self.enable_step_sample)
        self.sample_agents_check.stateChanged.connect(self.enable_agent_sample)

    def simulation_thread(self, progress_callback):
        # initialise the sim class
        tester = getattr(self.sim_module, self.sim_name)()

        # initialise local vars
        step = 0
        output = dict()
        while self.run_thread:
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
        self.sim_data_dict[dt_string] = pgh.PsychSimRun(id=dt_string,
                                                        data=output,
                                                        sim_file=self.sim_name,
                                                        steps=len(output),
                                                        run_date=run_date)
        # Update appropriate places
        self.set_data_dropdown(self.data_combo)
        self.set_data_dropdown(self.sample_data_combo)
        self.update_data_table()

    def update_data_table(self):
        self.loaded_data_window.clear_table()
        for data_id, data in self.sim_data_dict.items():
            # create the button to rename the data
            btn = QPushButton(self.loaded_data_window.loaded_data_table)
            btn.setText('RENAME')
            btn.clicked.connect(partial(self.show_rename_dialog, data_id))

            # create the button to save the data to csv
            btn2 = QPushButton(self.loaded_data_window.loaded_data_table)
            btn2.setText('save')
            btn2.clicked.connect(partial(self.save_data_window, data_id))

            # update the loaded data table
            new_row = [data.run_date, data.id, data.sim_file, str(data.steps), btn, btn2]
            self.loaded_data_window.add_row_to_table(new_row)

    def progress_fn(self, step, max_step):
        self.print_sim_output(f"{step}/{max_step} steps completed", "black")

    def thread_complete(self):
        self.print_sim_output("SIMULATION FINISHED!", "black")

    def stop_thread(self):
        self.run_thread = False

    def start_sim_thread(self):
        try:
            self.sim_spec.loader.exec_module(self.sim_module)

            # Pass the function to execute
            self.run_thread = True
            worker = Worker(self.simulation_thread)  # Any other args, kwargs are passed to the run function
            worker.signals.result.connect(self.handle_output)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)

            # Execute
            self.threadpool.start(worker)
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

    def load_config(self, path=None):
        config = configparser.ConfigParser()
        try:
            if path:
                config.read(path)
            else:
                # read the default
                config.read('config.ini')

            # set the path variables
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

    def set_psychsim_path(self):
        self.psychsim_path = pgh.get_directory(self.psychsim_dir_path, "Select Psychsim Directory")

    def set_definitions_path(self):
        new_path = pgh.get_directory(self.def_dir_path, "Select Definitions Directory")
        if new_path:
            self.definitions_path = new_path

    def set_sim_path(self):
        new_path = pgh.get_file_path(path_label=self.sim_path_label)
        if new_path:
            self.sim_path = new_path
            self.sim_loaded_state.setText("...")

    def load_sim(self):
        try:
            # add the psychsim paths to the sys PATH environment var
            self.sim_name = re.split(r'[.,/]', self.sim_path)[-2]
            sys.path.insert(1, self.psychsim_path)
            sys.path.insert(1, self.definitions_path)

            # import the psychsim module
            import psychsim
            psychsim_spec = importlib.util.spec_from_file_location("psychsim.pwl", self.sim_path)
            self.psychsim_module = importlib.util.module_from_spec(psychsim_spec)
            psychsim_spec.loader.exec_module(self.psychsim_module)
            self.print_sim_output(f"psychsim loaded from: {self.psychsim_path}", "green")
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")
            self.sim_loaded_state.setText("ERROR")

        try:
            # import the sim module
            self.sim_spec = importlib.util.spec_from_file_location(self.sim_name, self.sim_path)
            self.sim_module = importlib.util.module_from_spec(self.sim_spec)
            self.sim_loaded_state.setText("LOADED")
            self.run_sim_button.setEnabled(True)
            self.print_sim_output(f"sim loaded: {self.sim_path}", "green")
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")
            self.sim_loaded_state.setText("ERROR")

    def save_data_window(self, data_id):
        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M%S")
        output_directory = 'sim_output'
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        output_path = os.path.join(output_directory, f"{data_id}_{dt_string}.pickle")

        output_name = QFileDialog.getSaveFileName(self,
                                               self.tr('Save File'),
                                               output_path,
                                               self.tr("pickle (*.pickle)"))[0]
        if output_name:
            if not QFileInfo(output_name).suffix():
                output_name += ".pickle"

            pickle.dump(self.sim_data_dict[data_id], open(output_name, "wb"))
            self.print_sim_output(f"{data_id} saved to: {output_name}", "black")
            self.update_data_table()

    def print_query_output(self, msg, color="black"):
        pgh.print_output(self.query_output, msg, color)

    def print_sim_output(self, msg, color="black"):
        pgh.print_output(self.simulation_output, msg, color)

    def print_sample_output(self, msg, color="black"):
        pgh.print_output(self.sample_output, msg, color)

    def print_plot_output(self, msg, color="black"):
        pgh.print_output(self.plot_output, msg, color)

    def load_data_from_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self,
                                                  "Select data file",
                                                  "",
                                                  "psychsim data (*.pickle)",
                                                  options=options)
        if fileName:
            # load the psychsim libs to read the pickle objects
            self.load_sim()
            with open(fileName, 'rb') as f:
                data = pickle.load(f)

                # update the data #todo: refactor these 3 lines (they appear in some form together)
                self.sim_data_dict[data.id] = data
                self.update_data_table()
                self.set_data_dropdown(self.data_combo)
                self.set_data_dropdown(self.sample_data_combo)

    def show_rename_dialog(self, old_key):
        # show the rename dialog and get the new name
        new_key, accepted = RenameDataDialog.get_new_name(old_name=old_key)
        if accepted:
            self.rename_data_id(new_key, old_key)

    def rename_data_id(self, new_key, old_key):
        self.sim_data_dict[new_key] = self.sim_data_dict.pop(old_key)
        self.sim_data_dict[new_key].id = new_key
        self.update_data_table()
        self.set_data_dropdown(self.data_combo)
        self.set_data_dropdown(self.sample_data_combo)
        self.update_query_dataid(old_key=old_key, new_key=new_key)

    def update_query_dataid(self, old_key,  new_key):
        for query_id, query in self.query_data_dict.items():
            if query.data_id == old_key:
                self.query_data_dict[query_id].data_id = new_key

    def rename_data_from_input(self):
        old_key = self.previous_run_id.text()
        if self.save_run_input.text():
            new_key = self.save_run_input.text()
            if new_key in self.sim_data_dict.keys():
                self.print_sim_output(f"{new_key} ALREADY EXISTS", "red")
            else:
                self.rename_data_id(new_key, old_key)
                self.previous_run_id.setText(new_key)
                self.print_sim_output(f"{old_key} renamed to {new_key}", "green")
        else:
            self.print_sim_output("NO NEW NAME ENTERED", "red")

    # QUERY FUNCTIONS-------------------------------------------
    def set_query_list_dropdown(self):
        query_items = [item for item in self.query_data_dict.keys()]
        pgh.update_toolbutton_list(list=query_items, button=self.view_query_list, action_function=self.update_view_query_list,
                                   parent=self)
        # pgh.update_toolbutton_list(list=query_items, button=self.plot_query, action_function=self.set_axis_dropdowns,
        #                            parent=self)

        non_diff_query_items = [item for item in self.query_data_dict.keys() if not self.query_data_dict[item].diff_query]
        pgh.update_toolbutton_list(list=non_diff_query_items, button=self.query_diff_1, action_function=pgh.set_toolbutton_text, parent=self)
        pgh.update_toolbutton_list(list=non_diff_query_items, button=self.query_diff_2, action_function=pgh.set_toolbutton_text, parent=self)

    def set_data_dropdown(self, combo_box):
        combo_box.clear()
        new_items = [item for item in self.sim_data_dict.keys()]
        combo_box.addItems(new_items)

    def set_function_dropdown(self):
        query_methods = [method_name for method_name in dir(self.psychsim_query)
                         if callable(getattr(self.psychsim_query, method_name))
                         and '__' not in method_name]
        pgh.update_toolbutton_list(list=query_methods, button=self.function_button, action_function=self.btnstate,
                                   parent=self)

    def set_agent_dropdown(self):
        data_id = self.data_combo.currentText()
        if data_id:
            agents = self.psychsim_query.get_agents(data=self.sim_data_dict[data_id], data_id=data_id)
            self.agent_combo.clear()
            self.agent_combo.addItems(agents['agent'].tolist())

    def set_action_dropdown(self):
        data_id = self.data_combo.currentText()
        if data_id:
            selected_agent = self.agent_combo.currentText()
            actions = self.psychsim_query.get_actions(data=self.sim_data_dict[data_id], agent=selected_agent)
            self.action_combo.clear()
            for index, row in actions.iterrows():
                self.action_combo.insertItem(index, row['action'], row['step'])


    def set_cycle_dropdown(self):
        pass

    def set_horizon_dropdown(self):
        pass

    def set_state_dropdown(self):
        pass

    def reset_params(self):
        self.agent_combo.clear()
        self.action_combo.clear()
        self.cycle_combo.clear()
        self.horizon_combo.clear()
        self.state_combo.clear()
        # Todo: populate combo boxes based on the function that is selected

    def set_params(self, param_list):
        param_combo_boxes = dict(agent=self.agent_combo,
                                 action=self.action_combo,
                                 cycle=self.cycle_combo,
                                 horizon=self.horizon_combo,
                                 state=self.state_combo)

        for name, combo in param_combo_boxes.items():
            if name in param_list.args:
                combo.setEnabled(True)
                if name == "agent":
                    print("SETTING AGENT")
                    self.set_agent_dropdown()
                    #Connect this to setting the action one
                elif name == "cycle":
                    self.set_cycle_dropdown()
                elif name == "horizon":
                    self.set_horizon_dropdown()
                elif name == "state":
                    self.set_state_dropdown()
                elif name == "action":
                    pass
                else:
                    self.reset_params()
                #TODO: if a particular combo box is enabled - then make sure it gets populated hireachically (Agent > Action | cycle |horizon)
            else:
                combo.setEnabled(False)

    def btnstate(self, action, button):
        selection = action.checkedAction().text()
        button.setText(selection)
        self.handle_params(selection)

    def handle_params(self, function_name):
        function = getattr(self.psychsim_query, function_name)
        param_list = inspect.getfullargspec(function)
        print(param_list)
        self.set_params(param_list)

    def update_view_query_list(self, action, button):
        selection = action.checkedAction().text()
        button.setText(selection)
        if button == self.view_query_list:
            self.update_query_info(self.query_data_dict[selection])

    def get_query_doc(self):
        query_function = self.function_button.text()
        try:
            self.print_query_output(f"{query_function}: {getattr(self.psychsim_query, query_function).__doc__}")
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def execute_query(self):
        query_function = self.function_button.text()
        agent = self.agent_combo.currentText()
        action_step = self.action_combo.currentData() #This is actually the step value as it is easier to access the data by step rather than action
        data_id = self.data_combo.currentText()
        try:
            result = getattr(self.psychsim_query, query_function)(data=self.sim_data_dict[data_id], data_id=data_id,
                                                                  agent=agent, action=action_step)
            result = result.apply(pd.to_numeric, errors='ignore') #convert the resulting dataframe to numeric where possible
            self.print_query_output(f"results for {query_function} on {self.data_combo.currentText()}:")
            self.print_query_output(str(result))

            # create query ID
            #TODO: refactor this as create_new() in the query class?
            now = datetime.now()
            dt_string = now.strftime("%Y%m%d_%H%M%S")
            query_id = f"{query_function}_{data_id}_{dt_string}"

            # create a new query object
            new_query = pgh.PsySimQuery(id=query_id, data_id=data_id, params=[], function=query_function,
                                        results=result)

            # create new dialog and show results + query ID
            new_query = self.show_query_dialog(model=PandasModel(result), query=new_query)
            self.query_data_dict[new_query.id] = new_query
            self.set_query_list_dropdown()

        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def show_query_dialog(self, model, query):
        query_dialog = QueryDataDialog(query, model)
        result = query_dialog.exec_()
        query = query_dialog.query_data
        if result:
            query.id = query_dialog.query_id_input.text()
        return query

    def view_query(self):
        query_id = self.view_query_list.text()
        self.display_query(query_id)

    def view_diff_query(self):
        query_id = self.new_diff_query_name.text()
        self.display_query(query_id)

    def display_query(self, query_id):
        try:
            if query_id in self.query_data_dict.keys():
                selected_query = self.query_data_dict[query_id]
                selected_query = self.show_query_dialog(model=PandasModel(selected_query.results), query=selected_query)
                self.query_data_dict[selected_query.id] = self.query_data_dict.pop(query_id)
                self.set_query_list_dropdown()
                self.update_query_info(selected_query)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def update_query_info(self, selected_query):
        try:
            if selected_query.data_id in self.sim_data_dict.keys():
                selected_query_asc_data = self.sim_data_dict[selected_query.data_id]
                self.sim_file_label.setText(selected_query_asc_data.sim_file)
            else:
                self.sim_file_label.setText("...")
            self.query_name_label.setText(selected_query.id)
            self.data_id_label.setText(selected_query.data_id)
            self.function_label.setText(selected_query.function)
            self.is_diff_label.setText(str(selected_query.diff_query))
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def save_csv_query(self):
        query_id = self.view_query_list.text()
        if query_id in self.query_data_dict.keys():
            now = datetime.now()
            dt_string = now.strftime("%Y%m%d_%H%M%S")
            output_directory = 'sim_output'
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            output_path = os.path.join(output_directory, f"{query_id}_{dt_string}.csv")
            self.query_data_dict[query_id].results.to_csv(output_path)
            self.print_query_output(f"{query_id} saved to: {output_path}", "black")

    def diff_query(self):
        try:
            # get the two queries
            q1 = self.query_data_dict[self.query_diff_1.text()]
            q2 = self.query_data_dict[self.query_diff_2.text()]

            # check that the columns match regardless of order
            if pgh.dataframe_columns_equal(q1.results, q2.results):
            # check that they are the same type
            # if q1.function == q2.function:
                self.print_query_output(f"DIFFING: {pgh._blue_str(q1.id)} and {pgh._blue_str(q2.id)}") #TODO: be consistant with colour coding of text
                # Diff the data ID
                pgh.print_diff(self.query_output, q1.data_id, q2.data_id, f"{q1.id} data_id", f"{q2.id} data_id", "data_id")

                # Diff length
                pgh.print_diff(self.query_output, len(q1.results.index), len(q2.results.index), f"{q1.id} steps", f"{q2.id} steps", "steps")

                # Diff the results
                diff_results = pgh.dataframe_difference(q1.results, q2.results)
                if len(diff_results.index) > 0:
                    self.query_output.append(f"{pgh._red_str('DIFF IN')}: {pgh._red_str('query results')}")
                else:
                    self.query_output.append(f"{pgh._green_str('NO DIFF IN')}: {pgh._green_str('query results')}")
                now = datetime.now()
                dt_string = now.strftime("%Y%m%d_%H%M%S")
                query_id = f"{q1.id}-{q2.id}_{q1.function}_diff"
                data_id = f"{q1.data_id}-{q2.data_id}"

                #--------
                # Convert the two query results to csv
                q1_csv = q1.results.to_csv(index=False).splitlines(keepends=False)
                q2_csv = q2.results.to_csv(index=False).splitlines(keepends=False)

                # Diff the CSVs
                d = difflib.Differ()
                result = list(d.compare(q1_csv, q2_csv))

                # Display results
                diff_results_window = DiffResultsWindow(parent=self)
                diff_results_window.diff_title.setText(f"Diff Results for {q1.id} and {q2.id}")
                diff_results_window.q1_diff_label.setText(f"{q1.id}")
                diff_results_window.q2_diff_label.setText(f"{q2.id}")
                diff_results_window.q2_diff_label.setText(f"{q2.id}")
                diff_results_window.format_diff_results(q1_csv, q2_csv, result)
                diff_results_window.show()

                # create a new query object #TODO: rethink if an object with differences is really needed.
                # new_query = pgh.PsySimQuery(id=query_id, data_id=data_id, params=[], function=q1.function,
                #                             results=diff_results, diff_query=True)
                #
                # # create new dialog and show results + query ID
                # # new_query = self.show_query_dialog(model=PandasModel(diff_results), query=new_query)
                # self.query_data_dict[new_query.id] = new_query
                # self.set_query_list_dropdown()
                # self.new_diff_query_name.setText(query_id)
            else:
                self.print_query_output("YOU CAN ONLY DIFF FUNCTIONS OF THE SAME TYPE", 'red')
                self.print_query_output(f"{q1.id} = {q1.function}, {q2.id} = {q2.function}", 'red')
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    # PLOT FUNCTIONS -------------------------------------------
    def setup_test_plot(self):
        #TODO: remove this if this is unchecked
        if self.test_check.isChecked():
            data_id = "test_query"
            xx = px.data
            self.test_data_dict = dict(iris=px.data.iris(), wind=px.data.wind(), gapminder=px.data.gapminder())

            for key, data in self.test_data_dict.items():
                self.query_data_dict[key] = pgh.PsySimQuery(id=key,
                                                                    data_id=key,
                                                                    params=[],
                                                                    function="test",
                                                                    results=data)
            # pgh.update_toolbutton_list(list=self.query_data_dict.keys(), button=self.plot_query, action_function=self.set_axis_dropdowns, parent=self)

    def create_new_plot(self, plot_name="New plot"):
        plot_window = PlotWindow(query_data_dict=self.query_data_dict, window_name=plot_name, parent=self)
        #connect the save figure
        plot_window.save_plot_button.clicked.connect(lambda: self.save_plot(plot_window.current_plot))
        #set the query dropdown
        pgh.update_toolbutton_list(list=self.query_data_dict.keys(), button=plot_window.plot_query,
                                   action_function=plot_window.set_axis_dropdowns, parent=self)
        plot_window.show()
        return plot_window

    def save_plot(self, plot=None):
        #populate the list view with saved plots
        sending_window = self.sender().window()
        if plot:
            new_key, accepted = SavePlotDialog.get_new_name()
            if accepted:
                self.plot_data_dict[new_key] = copy.deepcopy(plot)
                item = QListWidgetItem(f"{new_key}")
                self.plot_listwidget.addItem(item)
                sending_window.close()


    def add_plot_from_list(self, item):
        #TODO: fix updating old saved plts
        if item.text() in self.plot_data_dict.keys():
            selected_plot = self.plot_data_dict[item.text()]
            if selected_plot:
                new_plot = self.create_new_plot(plot_name=item.text())
                new_plot.add_new_plot(fig=selected_plot.fig,
                                  title=selected_plot.title,
                                  x_name=selected_plot.x_name,
                                  y_name=selected_plot.y_name)

    def remove_plot(self):
        listItems = self.plot_listwidget.selectedItems()
        if not listItems: return
        for item in listItems:
            self.plot_listwidget.takeItem(self.plot_listwidget.row(item))
            self.plot_data_dict.pop(item.text())


    # SAMPLE FUNCTIONS -------------------------------------------
    def set_sample_params(self):
        #Set the sample_step_start_spinBox and sample_step_end_spinBox values based on the data steps
        try:
            sample_data_source = self.sim_data_dict[self.sample_data_combo.currentText()].data
            max_steps = max(sample_data_source.keys())
            min_steps = min(sample_data_source.keys())
            self.sample_step_check.setText(f"step range (min:{min_steps}, max:{max_steps})")
            self.sample_step_start_spinBox.setRange(min_steps, max_steps)
            self.sample_step_end_spinBox.setRange(min_steps, max_steps)
        except:
            tb = traceback.format_exc()
            self.print_sample_output(tb, 'red')
            pass

    def set_sample_agent(self): #TODO: refactor (this is similar to theo ther function for querying)

        data_id = self.sample_data_combo.currentText()
        if data_id:
            agents = self.psychsim_query.get_agents(data=self.sim_data_dict[data_id], data_id=data_id)
            self.sample_agent_combo_mult.clear()
            self.sample_agent_combo_mult.addItems(agents['agent'].tolist())

    def save_sample(self):

        sample_data = copy.deepcopy(self.sim_data_dict[self.sample_data_combo.currentText()])
        sample_id = ""
        sample_length = len(range(self.sample_step_end_spinBox.minimum(), self.sample_step_end_spinBox.maximum() + 1))
        if self.sample_agents_check.isChecked():
            sample_data.data, agent_id = self.sample_on_agent(sample_data)
            sample_id = f"{sample_id}_{agent_id}"
            self.print_sample_output(f"Sampled with {agent_id} agents", "black")

        if self.sample_step_check.isChecked():
            step_min = self.sample_step_start_spinBox.value()
            step_max = self.sample_step_end_spinBox.value()
            step_range = range(step_min, step_max + 1)
            sample_length = len(step_range)
            sample_data.data, step_id = self.sample_on_step(sample_data, step_min=step_min, step_max=step_max)
            sample_id = f"{sample_id}_{step_id}"
            self.print_sample_output(f"Sampled with {sample_length} steps from {step_min} to {step_max}", "black")

        if not self.sample_agents_check.isChecked() and not self.sample_step_check.isChecked():
            self.print_sample_output("No sample selected", "black")

        else:
            data_id = f"{sample_data.id}_sample_{sample_id}"
            # store the data as a PsySimObject in the main dict
            sample_data.id = data_id
            sample_data.steps = sample_length

            self.sim_data_dict[data_id] = sample_data

            # Update appropriate places
            self.set_data_dropdown(self.data_combo)
            self.set_data_dropdown(self.sample_data_combo)
            self.update_data_table()
            self.print_sample_output(f"New sample saved as: {data_id}", "black")

    def sample_on_step(self, sample_data_source, step_min, step_max):
        step_range = range(step_min, step_max + 1)
        if step_min > step_max:
            self.print_sample_output("THE END STEP MUST BE LESS THAN THE START STEP", "red")
        else:
            sampled_data = {k: v for k, v in sample_data_source.data.items() if k in step_range}
            return sampled_data, f"{step_min}-{step_max}"

    def sample_on_agent(self, sample_data_source):
        sampled_data = dict()
        for step, step_data in sample_data_source.data.items():
            sampled_data[step] = {agent: agent_data for agent, agent_data in step_data.items() if agent in self.sample_agent_combo_mult.currentData()}
            sample_id = "_".join(self.sample_agent_combo_mult.currentData())
        return sampled_data, sample_id


    def enable_agent_sample(self):
        self.sample_agent_combo_mult.setEnabled(self.sample_agents_check.isChecked())

    def enable_step_sample(self):
        self.sample_step_start_spinBox.setEnabled(self.sample_step_check.isChecked())
        self.sample_step_end_spinBox.setEnabled(self.sample_step_check.isChecked())


    def show_doc_window(self, doc_file, doc_section=""):
        file_path = os.path.abspath(os.path.join(os.getcwd(), "documentation", "static_html", f"{doc_file}"))
        local_url = QUrl.fromLocalFile(file_path)
        local_url.setFragment(f"{doc_section}")
        doc_window = DocWindow(parent=self)
        doc_window.web_widget.load(local_url)
        doc_window.show()


if __name__ == "__main__":
    sys.argv.append("--disable-web-security")
    app = QApplication(sys.argv)
    window = PsychSimGuiMainWindow()
    window.show()
    sys.exit(app.exec_())
