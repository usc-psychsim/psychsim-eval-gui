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
import numbers
import traceback
import pandas as pd
import configparser
from datetime import datetime
from functools import partial
import copy
import difflib
import numpy as np
import plotly
import plotly.graph_objects as go
import plotly.express as px

from gui_threading import Worker, WorkerSignals
from PandasModel import PandasModel
import psychsim_gui_helpers as pgh
from CheckableComboBox import CheckableComboBox
from functions.query_functions import PsychSimQuery

from ui.SimulationInfoPage import SimulationInfoPage
from ui.QueryDataPage import QueryDataPage

from ui.LoadedDataWindow import LoadedDataWindow
from ui.RenameDataDialog import RenameDataDialog
from ui.SavePlotDialog import SavePlotDialog
from ui.DocWindow import DocWindow
from ui.PlotWindow import PlotWindow
from ui.DiffResultsWindow import DiffResultsWindow
from ui.QuerySampleCategoryDialog import QuerySampleCategoryDialog
from ui.QuerySampleRangeDialog import QuerySampleRangeDialog
from ui.DeleteAreYouSureDialog import DeleteAreYouSure
from ui.PlotViewDialog import PlotViewDialog


qtCreatorFile = os.path.join("ui", "psychsim-gui-main.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


# TODO: split generic gui stuff to other files
# TODO: try to get rid of class variables and use passed variables where possible (for readability)
# TODO: remove functions that aren't used
# TODO: final refactor to make sure code is readable
# TODO: add docstrings


class PsychSimGuiMainWindow(QMainWindow, Ui_MainWindow):
    """
    This class is responsible for initialising child widgets and windows, and creating connections between signals and slots between these
    Internal signal and slots for each page is maintained by the respective classes
    It also initialises variables for use between each of the sections e.g. for storing data
    """
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.setWindowTitle("PyschSim GUI")

        # SET UP OTHER WINDOWS
        self.loaded_data_window = LoadedDataWindow()
        self.loaded_data_window.load_data_button.clicked.connect(self.load_data_from_file)
        self.doc_window = DocWindow()

        # set up the containers for storing data
        self.sim_data_dict = dict()
        self.query_data_dict = dict()
        self.plot_data_dict = dict()

        # Set up the sim info page
        self.sim_info_page = SimulationInfoPage()
        self.sim_info_page.output_changed_signal.connect(self.update_data_info)
        self.sim_info_page.rename_data_signal.connect(self.rename_data_from_input)

        # Set up the query data page
        self.query_data_page = QueryDataPage()
        self.query_data_page.new_query_signal.connect(self.update_query_data)
        self.query_data_page.show_query_signal.connect(self.display_query)
        self.query_data_page.execute_query_button.clicked.connect(lambda: self.query_data_page.execute_query(self.sim_data_dict))
        self.query_data_page.view_query_combo.activated.connect(self.update_query_info)

        # Set up the main window stacked widget
        self.main_window_stack_widget.insertWidget(0, self.sim_info_page)
        self.main_window_stack_widget.insertWidget(1, self.query_data_page)
        self.main_window_stack_widget.setCurrentIndex(0)

        # set up dropdown menus
        self.actionview_data.triggered.connect(self.loaded_data_window.show)
        self.actionrun_sim.triggered.connect(lambda: self.main_window_stack_widget.setCurrentIndex(0))
        self.actionquery.triggered.connect(lambda: self.main_window_stack_widget.setCurrentIndex(1))
        self.actionplot.triggered.connect(lambda: self.main_window_stack_widget.setCurrentIndex(2))
        # self.actionsample_data.triggered.connect(lambda: self.main_window_stack_widget.setCurrentIndex(3)) #TODO: fix sample from data functionality (mostly moved to sampling at query level)
        self.actionmanual.triggered.connect(lambda: self.show_doc_window("index.html"))

        #help buttons
        # self.sim_info_button.clicked.connect(lambda: self.show_doc_window("simulation_script.html"))
        # self.sim_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "simulation"))
        # self.query_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "query"))
        # self.function_info_button.clicked.connect(lambda: self.show_doc_window("function_definitions.html"))
        self.plot_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "plot"))
        self.sample_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "sample"))



        # SET UP QUERY WINDOW --------------
        # self.psychsim_query = PsychSimQuery()
        # self.set_function_dropdown()
        # self.function_info_button.setToolTip('Click for how to write custom query functions')
        #
        # self.execute_query_button.clicked.connect(self.execute_query)
        # self.view_query_button.clicked.connect(self.view_query)
        # self.save_csv_query_button.clicked.connect(self.save_csv_query)
        # self.diff_query_button.clicked.connect(self.diff_query)
        # self.query_doc_button.clicked.connect(self.get_query_doc)
        # self.data_combo.activated.connect(self.reset_params)
        # self.agent_combo.activated.connect(self.set_action_dropdown)
        # self.action_combo.activated.connect(self.set_state_dropdown)
        # # self.data_combo.activated.connect(self.set_cycle_dropdown)
        # self.delete_query_buton.clicked.connect(self.delete_query)
        #
        # self.set_sample_function_dropdown()
        # self.select_query_sample_button.clicked.connect(self.show_sample_dialog)

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

    def update_data_info(self, data_id, data):
        #APPEND THE DATA DICT
        self.sim_data_dict[data_id] = data
        # Update appropriate places
        self.set_data_dropdown(self.query_data_page.data_combo)
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



    # def print_sim_output(self, msg, color="black"):
    #     pgh.print_output(self.simulation_output, msg, color)

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

    def rename_data_from_input(self, old_key, new_key):
        if new_key in self.sim_data_dict.keys():
            self.sim_info_page.print_sim_output(f"{new_key} ALREADY EXISTS", "red")
        else:
            self.rename_data_id(new_key, old_key)
            self.sim_info_page.previous_run_id.setText(new_key)
            self.sim_info_page.print_sim_output(f"{old_key} renamed to {new_key}", "green")


    # QUERY FUNCTIONS-------------------------------------------
    def set_query_list_dropdown(self):
        self.update_query_combo(self.query_data_page.view_query_combo)
        self.update_query_combo(self.query_data_page.sample_query_combo)
        self.update_query_diff_combo(self.query_data_page.query_diff_1)
        self.update_query_diff_combo(self.query_data_page.query_diff_2)
        #todo: connect plot query with self.set_axis_dropdowns function (parent = self) ??
        # pgh.update_toolbutton_list(list=query_items, button=self.plot_query, action_function=self.set_axis_dropdowns,
        #                            parent=self)

        
    def set_data_dropdown(self, combo_box):
        combo_box.clear()
        new_items = [item for item in self.sim_data_dict.keys()]
        combo_box.addItems(new_items)

    def update_query_combo(self, combo_box):
        combo_box.clear()
        new_items = [item for item in self.query_data_dict.keys()]
        combo_box.addItems(new_items)

    def update_query_diff_combo(self, combo_box):
        combo_box.clear()
        new_items = [item for item in self.query_data_dict.keys() if not self.query_data_dict[item].diff_query]
        combo_box.addItems(new_items)


    def update_query_data(self, query_id, query_data):
        self.query_data_dict[query_id] = query_data
        self.set_query_list_dropdown()






    def delete_query(self):
        query_id = self.view_query_list.text()
        try:
            if query_id in self.query_data_dict.keys():
                are_you_sure_dialog = DeleteAreYouSure()
                are_you_sure_dialog.query_name.setText(query_id)

                result = are_you_sure_dialog.exec_()
                if result:
                    #delete the query
                    self.query_data_dict.pop(query_id)
                    self.set_query_list_dropdown()
                    self.clear_query_info()

        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def display_query(self, query_id):
        #TODO: move this to query_data_page
        try:
            if query_id in self.query_data_dict.keys():
                selected_query = self.query_data_dict[query_id]
                selected_query = self.query_data_page.show_query_dialog(model=PandasModel(selected_query.results), query=selected_query)
                self.query_data_dict[selected_query.id] = self.query_data_dict.pop(query_id)
                self.set_query_list_dropdown()
                self.update_query_info()
        except:
            tb = traceback.format_exc()
            self.query_data_page.print_query_output(tb, "red")

    def update_query_info(self):
        #TODO: move this to query_data_page
        selected_query_id = self.query_data_page.view_query_combo.currentText()
        selected_query = self.query_data_dict[selected_query_id]
        try:
            if selected_query.data_id in self.sim_data_dict.keys():
                selected_query_asc_data = self.sim_data_dict[selected_query.data_id]
                self.query_data_page.sim_file_label.setText(selected_query_asc_data.sim_file)
            else:
                self.query_data_page.sim_file_label.setText("...")
            self.query_data_page.query_name_label.setText(selected_query.id)
            self.query_data_page.data_id_label.setText(selected_query.data_id)
            self.query_data_page.function_label.setText(selected_query.function)
            self.query_data_page.is_diff_label.setText(str(selected_query.diff_query))
        except:
            tb = traceback.format_exc()
            self.query_data_page.print_query_output(tb, "red")

    def clear_query_info(self):
        try:
            self.view_query_list.setText("...")
            self.sim_file_label.setText("...")
            self.query_name_label.setText("...")
            self.data_id_label.setText("...")
            self.function_label.setText("...")
            self.is_diff_label.setText("...")
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

                # # Diff the results
                # diff_results = pgh.dataframe_difference(q1.results, q2.results)
                # if len(diff_results.index) > 0:
                #     self.query_output.append(f"{pgh._red_str('DIFF IN')}: {pgh._red_str('query results')}")
                # else:
                #     self.query_output.append(f"{pgh._green_str('NO DIFF IN')}: {pgh._green_str('query results')}")
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



    def show_sample_dialog(self):
        #TODO: the sampling here samples across all steps. Therefore if you want to track certain actors through steps based on their initial value this needs to be fixed
        result = None
        query_selection = self.sample_query_list.text() #todo: replace with sample_query_combo
        variable_selection = self.sample_variable_combo.currentText()
        selected_query = self.query_data_dict[query_selection]
        try:
            if self.sample_function_combo.currentText() == "range":
                sample_dialog = QuerySampleRangeDialog()
                current_variable_max_value = selected_query.results[variable_selection].max()
                current_variable_min_value = selected_query.results[variable_selection].min()
                #test to see if the max and min are numeric
                if np.issubdtype(type(current_variable_max_value), np.number) and np.issubdtype(type(current_variable_min_value), np.number):
                    sample_dialog.name_label.setText(f"{query_selection}")
                    sample_dialog.value_label.setText(f"{variable_selection}")
                    sample_dialog.range_label.setText(f"{current_variable_min_value} : {current_variable_max_value}")
                    sample_dialog.min_spin.setRange(current_variable_min_value, current_variable_max_value)
                    sample_dialog.max_spin.setRange(current_variable_min_value, current_variable_max_value)
                    result = sample_dialog.exec_()
                    if result:
                        # get the range values if range
                        filt_min = sample_dialog.min_spin.value()
                        filt_max = sample_dialog.max_spin.value()

                        # apply the sampling
                        sampled_query = copy.deepcopy(selected_query.results)
                        sampled_query = sampled_query.loc[sampled_query[variable_selection] <= filt_max]
                        # sampled_query.reset_index()
                        sampled_query = sampled_query.loc[sampled_query[variable_selection] >= filt_min]

                        # save the new query as a sample
                        sample_id = f"{query_selection}_{variable_selection}_{self.sample_function_combo.currentText()}_{filt_min}-{filt_max}"
                        self.query_data_dict[sample_id] = pgh.PsySimQuery(id=sample_id,
                                                                    data_id=selected_query.data_id,
                                                                    params=[],
                                                                    function="test",
                                                                    results=sampled_query)

                        self.print_query_output(f"sample saved as: {sample_id}", "black")

                        # update the query lists over the whole gui
                        self.set_query_list_dropdown()
                else:
                    #IT IS NOT NUMERIC - DISPLAY WARNING
                    self.print_query_output("THE VARIABLE DOES NOT CONTAIN NUMERIC VALUES. USE THE CATEGORY FUNCTION INSTEAD", "red")
            elif self.sample_function_combo.currentText() == "category":
                sample_dialog = QuerySampleCategoryDialog()
                sample_dialog.name_label.setText(f"{query_selection}")
                sample_dialog.value_label.setText(f"{variable_selection}")
                values_raw = selected_query.results[variable_selection].unique()
                values_string = [str(i) for i in values_raw]
                print("STRINGGG", values_string)
                sample_dialog.sample_combo_mult.clear()
                sample_dialog.sample_combo_mult.addItems(values_string)
                result = sample_dialog.exec_()
                if result:
                    # get the categorical values if range
                    cat_values =sample_dialog.sample_combo_mult.currentData()

                    #convert the row to strings for sampling
                    sampled_query = copy.deepcopy(selected_query.results)
                    sampled_query[variable_selection] = sampled_query[variable_selection].astype(str)

                    # apply the sampling
                    sampled_query = pd.concat([sampled_query.loc[sampled_query[variable_selection] == i] for i in cat_values])

                    # save the new query as a sample

                    now = datetime.now()
                    dt_string = now.strftime("%Y%m%d_%H%M%S")
                    sample_id = f"{query_selection}_{variable_selection}_{self.sample_function_combo.currentText()}_{dt_string}"
                    self.query_data_dict[sample_id] = pgh.PsySimQuery(id=sample_id,
                                                                      data_id=selected_query.data_id,
                                                                      params=[],
                                                                      function="test",
                                                                      results=sampled_query)

                    self.print_query_output(f"sample saved as: {sample_id}", "black")
                    # update the query lists over the whole gui
                    self.set_query_list_dropdown()
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
