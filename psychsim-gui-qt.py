from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from PyQt5.QtWebEngineWidgets import QWebEngineView
import os
import pickle
import importlib.util
import sys
import re
import traceback
import pandas as pd
import configparser
from datetime import datetime
from functools import partial
import copy

import plotly
import plotly.graph_objects as go
import plotly.express as px

from gui_threading import Worker, WorkerSignals
from PandasModel import PandasModel
import psychsim_gui_helpers as pgh
from query_functions import PsychSimQuery

from LoadedDataWindow import LoadedDataWindow
from RenameDataDialog import RenameDataDialog
from QueryDataDialog import QueryDataDialog
from SavePlotDialog import SavePlotDialog
from PlotViewDialog import PlotViewDialog


qtCreatorFile = "psychsim-gui-main.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


# TODO: split generic gui stuff to other files
# TODO: try to get rid of class variables and use passed variables where possible (for readability)
# TODO: final refactor to make sure code is readable
# TODO: add docstrings


class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # SET UP OTHER WINDOWS
        self.loaded_data_window = LoadedDataWindow()

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
        self.run_sim_button.setEnabled(False)
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

        self.actionSelect_load_config.triggered.connect(self.open_config_loader)
        self.actionview_data.triggered.connect(self.loaded_data_window.show)
        self.actionmain.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.actionquery_data_page.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.actionplot.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.actionsample.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.actionload_data_from_file.triggered.connect(self.load_data_from_file)

        # LOAD CONFIG
        self.load_config()

        # SET UP QUERY WINDOW --------------
        self.psychsim_query = PsychSimQuery()
        self.set_function_dropdown()

        self.execute_query_button.clicked.connect(self.execute_query)
        self.view_query_button.clicked.connect(self.view_query)
        self.save_csv_query_button.clicked.connect(self.save_csv_query)
        self.diff_query_button.clicked.connect(self.diff_query)
        self.query_doc_button.clicked.connect(self.get_query_doc)
        self.data_combo.activated.connect(self.reset_params)
        # self.data_combo.activated.connect(self.set_action_dropdown)
        # self.data_combo.activated.connect(self.set_cycle_dropdown)

        # SET UP PLOT WINDOW ----------------
        self.current_plot = None

        self.plot_button.clicked.connect(self.plot_data)
        self.add_plot_button.clicked.connect(self.plot_data)
        self.clear_plot_button.clicked.connect(self.clear_plot)
        self.test_check.stateChanged.connect(self.setup_test_plot)
        self.save_plot_button.clicked.connect(self.save_plot)
        self.plot_listwidget.itemClicked.connect(self.add_plot_from_list)
        self.remove_plot_button.clicked.connect(self.remove_plot)

        self.set_type_dropdown()
        self.set_stat_dropdown()

        self.setup_plot_widget()

        self.current_fig = None

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
        self.set_data_dropdown()
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

    def open_config_loader(self):
        # open file dialog
        config_path = pgh.get_file_path(file_type="Config files (*.ini)", path_label="select config file")
        self.load_config(config_path)

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
        self.definitions_path = pgh.get_directory(self.def_dir_path, "Select Definitions Directory")

    def set_sim_path(self):
        self.sim_path = pgh.get_file_path(path_label=self.sim_path_label)

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
        with open(output_path, 'wb') as f:
            pickle.dump(self.sim_data_dict[data_id], f)
        self.print_sim_output(f"{data_id} saved to: {output_path}", "black")
        self.update_data_table()

    def print_query_output(self, msg, color="black"):
        pgh.print_output(self.query_output, msg, color)

    def print_sim_output(self, msg, color="black"):
        pgh.print_output(self.simulation_output, msg, color)

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
                self.set_data_dropdown()

    def show_rename_dialog(self, old_key):
        # show the rename dialog and get the new name
        new_key, accepted = RenameDataDialog.get_new_name(old_name=old_key)
        if accepted:
            self.rename_data_id(new_key, old_key)

    def rename_data_id(self, new_key, old_key):
        self.sim_data_dict[new_key] = self.sim_data_dict.pop(old_key)
        self.sim_data_dict[new_key].id = new_key
        self.update_data_table()
        self.set_data_dropdown()
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
        pgh.update_toolbutton_list(list=query_items, button=self.query_diff_1, action_function=pgh.set_toolbutton_text)
        pgh.update_toolbutton_list(list=query_items, button=self.query_diff_2, action_function=pgh.set_toolbutton_text)
        pgh.update_toolbutton_list(list=query_items, button=self.plot_query, action_function=self.set_axis_dropdowns,
                                   parent=self)

    def set_data_dropdown(self):
        self.data_combo.clear()
        new_items = [item for item in self.sim_data_dict.keys()]
        self.data_combo.addItems(new_items)

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

    def reset_params(self):
        self.agent_combo.clear()
        self.action_combo.clear()
        self.cycle_combo.clear()
        self.horizon_combo.clear()
        self.state_combo.clear()
        # Todo: populate combo boxes based on the function that is selected

    def btnstate(self, action, button):
        selection = action.checkedAction().text()
        button.setText(selection)
        if selection == "get_actions":
            self.set_agent_dropdown()
            # TODO: set inactive the params we don't want (think about a good way to do this - maybe from the query_function params list?

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
        data_id = self.data_combo.currentText()
        try:
            result = getattr(self.psychsim_query, query_function)(data=self.sim_data_dict[data_id], data_id=data_id,
                                                                  agent=agent)
            result = result.apply(pd.to_numeric, errors='ignore') #convert the resulting dataframe to numeric where possible
            self.print_query_output(f"results for {query_function} on {self.data_combo.currentText()}:")
            self.print_query_output(str(result))

            # create query ID
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
        try:
            query_id = self.view_query_list.text()
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
            selected_query_asc_data = self.sim_data_dict[selected_query.data_id]
            self.query_name_label.setText(selected_query.id)
            self.data_id_label.setText(selected_query.data_id)
            self.sim_file_label.setText(selected_query_asc_data.sim_file)
            self.function_label.setText(selected_query.function)
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

            # check that they are the same type
            if q1.function == q2.function:
                # diff the results
                self.print_query_output(f"DIFFING: {q1.id} and {q2.id}", 'green')
            else:
                self.print_query_output("YOU CAN ONLY DIFF FUNCTIONS OF THE SAME TYPE", 'red')
                self.print_query_output(f"{q1.id} = {q1.function}, {q2.id} = {q2.function}", 'red')
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    # PLOT FUNCTIONS -------------------------------------------
    def setup_test_plot(self):
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
            pgh.update_toolbutton_list(list=self.query_data_dict.keys(), button=self.plot_query, action_function=self.set_axis_dropdowns, parent=self)




    def plot_data(self):
        try:
            # get the type of plot ["line", "scatter", "box", "violin"]
            plot_type = self.plot_type.text()

            if self.plot_query.text() in self.query_data_dict.keys():
                data = self.query_data_dict[self.plot_query.text()].results
                print(data.dtypes)

                trace_name = ""

                #clear the plot if it's a new plot otherwise leave it
                if self.sender() == self.plot_button:
                    fig = go.Figure()
                    print("setting new figure")
                else:
                    fig = self.current_fig
                    print("adding new figure")

                stat = self.plot_stat.text()
                if self.plot_group.text() not in ["none", "..."]:
                    if stat in ["none", "..."]:
                        for group in data[self.plot_group.text()].unique().tolist():
                            group_data = data[data[self.plot_group.text()] == group]
                            x_data = group_data[self.plot_x.text()].tolist()
                            y_data = group_data[self.plot_y.text()].tolist()
                            name = f"{group}"
                            fig = self.add_trace_to_plot(fig, plot_type, x_data, y_data, name)
                    else:
                        data = getattr(data.groupby(data[self.plot_x.text()]), stat)()
                        data[self.plot_x.text()] = data.index
                        x_data = data[self.plot_x.text()].to_numpy()
                        y_data = data[self.plot_y.text()].to_numpy()
                        name = f"{self.plot_y.text()}_{stat}"
                        fig = self.add_trace_to_plot(fig, plot_type, x_data, y_data, name)
                else:
                    x_data = data[self.plot_x.text()].to_numpy()
                    y_data = data[self.plot_y.text()].to_numpy()
                    name = f"{self.plot_y.text()}"
                    fig = self.add_trace_to_plot(fig, plot_type, x_data, y_data, name)

                self.current_fig = fig
                self.add_new_plot(fig=fig, title="", x_name=self.plot_x.text(), y_name=self.plot_y.text())
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

    def add_trace_to_plot(self, fig, plot_type, x_data, y_data, name):
        # Group by the group variable
        if plot_type == "Scatter":
            fig.add_trace(getattr(go, plot_type)(x=x_data, y=y_data, mode='markers', name=name))
        elif plot_type == "Line":
            fig.add_trace(getattr(go, plot_type)(x=x_data, y=y_data, mode='lines+markers', name=name))
        elif plot_type == "Histogram":
            fig.add_trace(getattr(go, plot_type)(x=x_data, name=name))
        elif plot_type == "Violin":
            fig = go.Figure(data=getattr(go, plot_type)(y=y_data, box_visible=True, line_color='black',
                                     meanline_visible=True, fillcolor='lightseagreen', opacity=0.6,
                                     x0='', name=name))
        return fig


    def set_stat_dropdown(self):
        stats = ["none", "mean", "median", "count"]
        pgh.update_toolbutton_list(list=stats, button=self.plot_stat, action_function=pgh.set_toolbutton_text,
                                   parent=self)

    def set_type_dropdown(self):
        stats = ["Line", "Scatter", "Histogram", "Violin"]
        pgh.update_toolbutton_list(list=stats, button=self.plot_type, action_function=pgh.set_toolbutton_text,
                                   parent=self)

    def setup_plot_widget(self):
        # we create an instance of QWebEngineView and set the html code
        self.plot_widget = QWebEngineView()

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.plot_widget)
        self.plot_frame.setLayout(vbox_layout)

    def clear_plot(self):
        fig = px.bar(pd.DataFrame(dict(x=[], y=[])), x="x", y="y")
        self.add_new_plot(fig)
        self.current_plot = None

    def set_axis_dropdowns(self, action, button):
        # TODO: make sure these are the same types of queries (same function) - refactor with similar code
        selection = action.checkedAction().text()
        print(action.checkedAction().text())
        button.setText(action.checkedAction().text())

        # get the sample / data
        data_key = selection

        # set x and y axis dropdowns
        # axis_values = sorted(self.test_data_dict[data_key])
        axis_values = sorted(self.query_data_dict[data_key].results.columns)
        pgh.update_toolbutton_list(list=axis_values, button=self.plot_y, action_function=pgh.set_toolbutton_text,
                                   parent=self)
        pgh.update_toolbutton_list(list=axis_values, button=self.plot_x, action_function=pgh.set_toolbutton_text,
                                   parent=self)
        axis_values.append("none")
        pgh.update_toolbutton_list(list=axis_values, button=self.plot_group, action_function=pgh.set_toolbutton_text,
                                   parent=self)

    def add_new_plot(self, fig, title="", x_name="", y_name=""):
        # set up layout
        layout = dict(
            margin=dict(
                l=1,
                r=1,
                b=1,
                t=25,
                pad=4
            ),
            showlegend=True,
            title=title,
            xaxis_title=x_name,
            yaxis_title=y_name,
        )
        fig.update_layout(layout)
        # fig.update_yaxes(automargin=True)
        html = '<html><body>'
        html += plotly.offline.plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'
        self.plot_widget.setHtml(html)

        # set the current plot with the current details
        self.current_plot = pgh.PsySimPlot(id="current",
                                           fig=fig,
                                           title=title,
                                           x_name=x_name,
                                           y_name=y_name)

        #Open dialog
        # plot_dialog = PlotViewDialog()
        # plot_dialog.plot_widget.setHtml(html)
        # result = plot_dialog.exec_()

    def save_plot(self):
        #populate the list view with saved plots
        new_key, accepted = SavePlotDialog.get_new_name()
        if accepted:
            self.plot_data_dict[new_key] = copy.deepcopy(self.current_plot)
            item = QListWidgetItem(f"{new_key}")
            self.plot_listwidget.addItem(item)

    def add_plot_from_list(self, item):
        #TODO: fix updating old saved plts
        if item.text() in self.plot_data_dict.keys():
            selected_plot = self.plot_data_dict[item.text()]
            if selected_plot:
                self.clear_plot()
                self.add_new_plot(fig=selected_plot.fig,
                                  title=selected_plot.title,
                                  x_name=selected_plot.x_name,
                                  y_name=selected_plot.y_name)

    def remove_plot(self):
        pass
        #remove the item/key from the self.plot_data_dict of the plot selected

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
