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

import plotly
import plotly.graph_objects as go
import plotly.express as px

from gui_threading import Worker, WorkerSignals
from PandasModel import PandasModel
import psychsim_gui_helpers as pgh
from query_functions import PsychSimQuery

# from QueryDataWindow import QueryDataWindow
from LoadedDataWindow import LoadedDataWindow
from DataViewWindow import RawDataWindow
from SampleDataWindow import SampleDataWindow
from renameDataDialog import RenameDataDialog
from query_data_dialog import QueryDataDialog

# from PlotWindow import PlotWindow

qtCreatorFile = "psychsim-gui-main.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


# TODO: split generic gui stuff to other files
# TODO: try to get rid of class variables and use passed variables where possible (for readability)


class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # SET UP OTHER WINDOWS
        self.data_window = RawDataWindow()
        self.loaded_data_window = LoadedDataWindow()
        # self.query_data_window = QueryDataWindow()#TODO: remove this
        self.sample_data_window = SampleDataWindow()
        # self.plot_window = PlotWindow()

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
        self.actionview_data.triggered.connect(self.show_loaded_data_window)
        # self.actionquery_data.triggered.connect(self.show_query_data_window)#TODO: remove this (and associated function if necessesary)
        self.actionmain.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.actionquery_data_page.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.actionplot.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.actioncreate_samples.triggered.connect(self.show_sample_data_window)
        self.actionload_data_from_file.triggered.connect(self.load_data_from_file)
        # self.actioncreate_plot.triggered.connect(self.show_plot_window)

        # LOAD CONFIG
        self.load_config()

        # SET UP QUERY WINDOW --------------
        self.psychsim_query = PsychSimQuery()
        self.set_function_dropdown()
        self.current_query_function = None

        self.execute_query_button.clicked.connect(self.execute_query)
        self.view_query_button.clicked.connect(self.view_query)
        self.save_csv_query_button.clicked.connect(self.save_csv_query)
        self.diff_query_button.clicked.connect(self.diff_query)
        # self.data_combo.activated.connect(self.set_agent_dropdown)
        # self.data_combo.activated.connect(self.set_action_dropdown)
        # self.data_combo.activated.connect(self.set_cycle_dropdown)

        # SET UP PLOT WINDOW ----------------

        # TEST DATA
        # data_id = "test_data"
        # data = px.data.iris()
        # self.test_data_dict = {data_id: data}
        # pgh.update_toolbutton_list(list=self.test_data_dict.keys(), button=self.plot_query, action_function=self.set_axis_dropdowns, parent=self)
        # END TEST DATA

        self.plot_button.clicked.connect(self.plot_data)
        self.add_plot_button.clicked.connect(self.plot_data)
        self.clear_plot_button.clicked.connect(self.clear_plot)

        self.set_type_dropdown()
        self.set_stat_dropdown()

        self.setup_plot_widget()

        self.current_fig = None

    def simulation_thread(self, progress_callback):
        # initialise the sim class
        tester = getattr(self.sim_module, self.sim_name)()
        step = 0
        output = dict()
        while self.run_thread:
            # step_data = dict()

            # get the result of the step
            result = tester.run_sim()

            # append the raw output
            # step_data['step_data'] = result
            # step_data['step'] = step
            # output[step] = step_data
            output[step] = result

            # Get the beliefs (not needed here?)
            # self.print_debug(debug=result)

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
        # get timestamp
        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M%S")
        run_date = now.strftime("%Y-%m-%d %H:%M:%S")

        # set the current run name settings
        self.previous_run_id.setText(dt_string)
        self.rename_run_button.setEnabled(True)
        self.save_run_input.setEnabled(True)
        self.save_run_input.setText(dt_string)

        # store the data in the main dict
        self.sim_data_dict[dt_string] = pgh.PsychSimRun(id=dt_string,
                                                        data=output,
                                                        sim_file=self.sim_name,
                                                        steps=len(output),
                                                        run_date=run_date)
        self.set_data_dropdown()

        self.update_data_table()

    def update_data_table(self):
        self.loaded_data_window.clear_table()  # TODO: find better way to do this so it isn't loaded a new each time
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
        except:
            tb = traceback.format_exc()
            self.print_sim_output(tb, "red")

        # Pass the function to execute
        self.run_thread = True
        worker = Worker(self.simulation_thread)  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.handle_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def open_config_loader(self):
        # open file dialog
        config_path = self.get_file_path(file_type="Config files (*.ini)")
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
            self.sim_name = re.split(r'[.,/]', self.sim_path)[-2]
            sys.path.insert(1, self.psychsim_path)
            sys.path.insert(1, self.definitions_path)

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

    # todo: refactor these types of functions
    def print_query_output(self, msg, color="black"):
        self.query_output.setTextColor(QColor(color))
        self.query_output.append(msg)

    def print_sim_output(self, msg, color="black"):
        self.simulation_output.setTextColor(QColor(color))
        self.simulation_output.append(msg)

    def show_data_window(self, key):
        # this should really accept a key to access the dict of data saved at the top level
        # then set the model based on this
        # todo: add some exception handling
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

    def show_plot_window(self):
        self.plot_window.show()

    def load_data_from_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select data file", "", "psychsim data (*.pickle)",
                                                  options=options)
        if fileName:
            # load the psychsim libs
            self.load_sim()
            with open(fileName, 'rb') as f:
                data = pickle.load(f)

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

    def rename_data_from_input(self, old_key=None):
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

    # QUERY FUNCTIONS-------------------------------------------
    def set_query_list_dropdown(self):
        query_items = [item for item in self.query_data_dict.keys()]
        pgh.update_toolbutton_list(list=query_items, button=self.view_query_list, action_function=self.btnstate,
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
        # todo: refactor this and other dropdown generation functions
        # TODO: figure out how to set this based on the data set (i.e. remove old ones and add new ones)
        data_id = self.data_combo.currentText()
        if data_id:
            agents = self.psychsim_query.get_agents(data=self.sim_data_dict[data_id], data_id=data_id)
            self.agent_combo.clear()
            self.agent_combo.addItems(agents['agent'].tolist())

    def btnstate(self, action, button):
        selection = action.checkedAction().text()
        if button == self.function_button:
            self.current_query_function = selection
        button.setText(action.checkedAction().text())
        # TODO: make this conditional functionality smarter
        if selection == "get_actions":
            self.set_agent_dropdown()
            # TODO: set inactive the params we don't want (think about a good way to do this - maybe from the query_function params list?
        if button == self.view_query_list:
            self.update_query_info(self.query_data_dict[selection])

    def execute_query(self):
        # query_function = self.function_combo.currentText()
        query_function = self.current_query_function
        agent = self.agent_combo.currentText()
        data_id = self.data_combo.currentText()
        try:
            result = getattr(self.psychsim_query, query_function)(data=self.sim_data_dict[data_id], data_id=data_id,
                                                                  agent=agent)
            self.print_query_output(f"results for {query_function} on {self.data_combo.currentText()}:")
            self.print_query_output(str(result))
            if type(result) == pd.DataFrame:

                # create query ID
                now = datetime.now()
                dt_string = now.strftime("%Y%m%d_%H%M%S")
                query_id = f"{query_function}_{data_id}_{dt_string}"

                # create a new query object
                id: str
                data_id: str
                params: list
                function: str
                results: pd.DataFrame
                new_query = pgh.PsySimQuery(id=query_id, data_id=data_id, params=[], function=query_function,
                                            results=result)

                # create new dialog and show results + query ID
                model = PandasModel(result)
                query_dialog = QueryDataDialog(new_query, model)
                result = query_dialog.exec_()
                new_query = query_dialog.query_data
                if result:
                    new_query.id = query_dialog.query_id_input.text()

                # get new/old ID from dialog and save in query dict
                self.query_data_dict[new_query.id] = new_query

                # update the query list
                self.set_query_list_dropdown()

        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def save_query(self):
        pass

    def view_query(self):
        # get the current query
        query_id = self.view_query_list.text()
        if query_id in self.query_data_dict.keys():
            selected_query = self.query_data_dict[query_id]

            # show the dialog for it
            query_dialog = QueryDataDialog(selected_query, model=PandasModel(selected_query.results))
            result = query_dialog.exec_()
            selected_query = query_dialog.query_data
            print(selected_query.id)

            # get new/old ID from dialog and save in query dict
            self.query_data_dict[selected_query.id] = self.query_data_dict.pop(query_id)

            # update the query dropdown and info
            self.set_query_list_dropdown()
            self.update_query_info(selected_query)

    def update_query_info(self, selected_query):
        selected_query_asc_data = self.sim_data_dict[selected_query.data_id]
        self.query_name_label.setText(selected_query.id)
        self.data_id_label.setText(selected_query.data_id)
        self.sim_file_label.setText(selected_query_asc_data.sim_file)
        self.function_label.setText(selected_query.function)

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
    def plot_data(self):
        # data = self.test_data_dict[self.plot_query.text()]
        if self.plot_query.text() in self.query_data_dict.keys():
            data = self.query_data_dict[self.plot_query.text()].results
        x_axis = self.plot_x.text()
        y_axis = self.plot_y.text()

        # get the stat and do the operation on the data
        stat = self.plot_stat.text()
        if stat == "mean":
            data.groupby(x_axis).mean()
        elif stat == "median":
            pass
        elif stat == "count":
            pass
        elif stat == "none":
            pass



        # get the type of plot ["line", "scatter", "box", "violin"]
        plot_type = self.plot_type.text()
        if plot_type == "scatter":
            fig = px.scatter(data, x=x_axis, y=y_axis, trendline="ols", color=data.index)
            # self.add_scatter_plot(data=data, x=x_axis, y=y_axis)
        elif plot_type == "line":
            fig = px.line(data, x=x_axis, y=y_axis)
            # self.add_line_plot(data=data, x=x_axis, y=y_axis)
        elif plot_type == "histogram":
            fig = px.histogram(data, x=x_axis, y=y_axis)
            # self.add_histogram_plot(data=data, x=x_axis, y=y_axis)
        elif plot_type == "violin":
            fig = px.violin(data, y=x_axis, x=y_axis, box=True, points="all", hover_data=data.columns)
            # self.add_violin_plot(data=data, x=x_axis, y=y_axis)
        elif plot_type == "test":
            iris = px.data.iris()
            fig = px.scatter(iris, x="sepal_width", y="sepal_length", color="species")

        #clear the plot if it's a new plot otherwise leave it
        if self.sender() == self.plot_button:
            self.clear_plot()
            self.add_new_plot(fig=fig)
        else:
            self.add_additional_plot(fig=fig)

    def set_stat_dropdown(self):
        stats = ["none", "mean", "median", "count"]
        pgh.update_toolbutton_list(list=stats, button=self.plot_stat, action_function=pgh.set_toolbutton_text,
                                   parent=self)

    def set_type_dropdown(self):
        stats = ["line", "scatter", "histogram", "violin", "test"]
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

    def add_new_plot(self, fig):
        #update stored fig
        self.current_fig = fig
        # set up layout
        layout = dict(
            margin=dict(
                l=1,
                r=1,
                b=1,
                t=1,
                pad=4
            ),
        )
        fig.update_layout(layout)
        fig.update_yaxes(automargin=True)
        html = '<html><body>'
        html += plotly.offline.plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'
        self.plot_widget.setHtml(html)

    def add_additional_plot(self, fig):
        if self.current_fig:
            self.current_fig.add_trace(fig.data[0])
            html = '<html><body>'
            html += plotly.offline.plot(self.current_fig, output_type='div', include_plotlyjs='cdn')
            html += '</body></html>'
            self.plot_widget.setHtml(html)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
