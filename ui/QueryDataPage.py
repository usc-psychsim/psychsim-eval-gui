from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import traceback
import inspect
import os
import re
import pickle
import sys
import copy
import importlib.util
import pandas as pd
import numpy as np
from PyQt5.Qt import QStandardItemModel
from functools import partial

import psychsim_gui_helpers as pgh
from functions.PsychSimQueryFunctions import PsychSimQueryFunctions

from ui.PandasModel import PandasModel, TreeModel
from ui.QuerySampleCategoryDialog import QuerySampleCategoryDialog
from ui.QuerySampleRangeDialog import QuerySampleRangeDialog
from ui.DiffResultsWindow import DiffResultsWindow
from ui.StepThroughQueryWindow import StepThroughResultsWindow
from ui.DeleteAreYouSureDialog import DeleteAreYouSure
from ui.QueryDataDialog import QueryDataDialog
from ui.QueryDataTreeDialog import QueryDataTreeDialog
from ui.SetParamDialog import SetParamDialog

query_data_page_file = os.path.join("ui", "query_data_page.ui")
ui_queryDataPage, QtBaseClass = uic.loadUiType(query_data_page_file)


class QueryDataPage(QWidget, ui_queryDataPage):
    """
    This class is for all functions relating to the query data page of the GUI
    This includes:
    """
    def __init__(self, sim_data_dict, query_data_dict, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.sim_data_dict = sim_data_dict
        self.query_data_dict = query_data_dict

        # SET UP VARS
        self.func_spec = None
        self.func_module = None
        self.func_source = ""
        self.func_class_name = ""

        self.psychsim_query = PsychSimQueryFunctions()

        self.set_function_dropdown()

        # Setup buttons
        self.function_combo.activated.connect(self.handle_params)
        self.execute_query_button.clicked.connect(self.execute_query)
        self.view_query_button.clicked.connect(self.view_query)
        self.view_query_combo.activated.connect(self.update_query_info)
        self.save_csv_query_button.clicked.connect(self.save_csv_query)
        self.save_pickle_query_button.clicked.connect(self.save_pickle_query)
        self.load_pickle_query_button.clicked.connect(self.load_pickle_query)
        self.delete_query_buton.clicked.connect(self.delete_query)
        self.diff_query_button.clicked.connect(self.diff_query)
        self.query_step_view_button.clicked.connect(self.show_step_through_window)
        self.sample_query_combo.activated.connect(self.handle_sample_query_dropdown)
        self.select_query_sample_button.clicked.connect(self.show_sample_dialog)

        self.function_info_button.setToolTip('Click for how to write custom query functions')
        self.query_doc_button.clicked.connect(self.get_query_doc)
        self.query_doc_button.clicked.connect(self.get_query_doc)

        self.set_func_source_button.clicked.connect(self.set_func_source)
        self.reload_func_source_button.clicked.connect(self.reolaod_func_source)

        self.set_sample_function_dropdown(["range", "category"])

    def execute_query(self):
        """
        Execute the query with the given params. The query function is defined in functions/PsychSimQueryFunctions.py
        """
        # get the query function
        query_function = self.function_combo.currentText()
        # get the params
        agent = self.agent_combo.currentText()
        state = self.state_combo.currentText()
        action_step = self.action_combo.currentData()  # This is actually the step value as it is easier to access the data by step rather than action
        data_id = self.data_combo.currentText()
        try:
            query_result = getattr(self.psychsim_query, query_function)(data=self.sim_data_dict[data_id], data_id=data_id,
                                                                  agent=agent, action=action_step, state=state)
            result_type = query_result[0]
            result = query_result[1]
            # result = result.apply(pd.to_numeric,
            #                       errors='ignore')  # convert the resulting dataframe to numeric where possible
            self.print_query_output(f"results for {query_function} on {self.data_combo.currentText()}:")
            self.print_query_output(str(result))
            new_query = self.create_new_query_object(query_function, data_id, result, result_type=result_type)
            self.update_query_data(new_query.id, new_query)
            self.display_query(new_query.id)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def update_query_data(self, query_id, query_data):
        """
        Update the query data dictionary with new data, and update the query lists across the entire gui
        :param query_id: ID of new query
        :param query_data: new query data
        """
        self.query_data_dict[query_id] = query_data
        self.set_query_list_dropdown()

    def create_new_query_object(self, query_function, data_id, query_data, result_type="table", query_id=None):
        """
        Create a new query object
        :param query_function: (str) name of query function
        :param data_id: (str) id of data used
        :param query_data: (DataFrame) results of query
        :return: PsySimQuery object
        """
        dt_string, run_date = pgh.get_time_stamp()
        if not query_id:
            query_id = f"{query_function}_{data_id}_{dt_string}"
        return pgh.PsySimQuery(id=query_id, data_id=data_id, params=[], function=query_function,
                               results=query_data, result_type=result_type)

    def clear_query_info(self):
        """
        Clear the query info on the gui
        """
        try:
            self.sim_file_label.setText("...")
            self.query_name_label.setText("...")
            self.data_id_label.setText("...")
            self.function_label.setText("...")
            self.is_diff_label.setText("...")
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def update_query_info(self):
        """
        Update the query info on the gui with appropriate values
        """
        selected_query_id = self.view_query_combo.currentText()
        selected_query = self.query_data_dict[selected_query_id]
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
        """
        Write the query results as a csv file to disk
        """
        query_id = self.view_query_combo.currentText()
        if query_id in self.query_data_dict.keys():
            dt_string, _ = pgh.get_time_stamp()
            output_directory = 'sim_output'
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            output_path = os.path.join(output_directory, f"{query_id}_{dt_string}.csv")
            output_name = QFileDialog.getSaveFileName(self,
                                                      self.tr('Save File'),
                                                      output_path,
                                                      self.tr("csv (*.csv)"))[0]
            if output_name:
                if not QFileInfo(output_name).suffix():
                    output_name += ".csv"
                self.query_data_dict[query_id].results.to_csv(output_name)
                self.print_query_output(f"{query_id} saved to: {output_name}", "black")

    def save_pickle_query(self):
        """
        Write the query results as a pickle file to disk
        """
        query_id = self.view_query_combo.currentText()
        if query_id in self.query_data_dict.keys():
            dt_string, _ = pgh.get_time_stamp()
            output_directory = 'sim_output'
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            output_path = os.path.join(output_directory, f"{query_id}_{dt_string}.pickle")
            output_name = QFileDialog.getSaveFileName(self,
                                                      self.tr('Save File'),
                                                      output_path,
                                                      self.tr("pickle (*.pickle)"))[0]
            if output_name:
                if not QFileInfo(output_name).suffix():
                    output_name += ".pickle"
                pickle.dump(self.query_data_dict[query_id], open(output_name, "wb"))
                self.print_query_output(f"{query_id} saved to: {output_name}", "black")

    def load_pickle_query(self):
        """
        load previously saved pickled query data
        """
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self,
                                                  "Select data file",
                                                  "",
                                                  "query data (*.pickle)",
                                                  options=options)
        if fileName:
            # load the psychsim libs to read the pickle objects
            # self.sim_info_page.load_sim()
            with open(fileName, 'rb') as f:
                loaded_query = pickle.load(f)
                if type(loaded_query) == pgh.PsySimQuery:
                    self.update_query_data(loaded_query.id, loaded_query)
                    self.print_query_output(f"{loaded_query.id} loaded", "black")
                else:
                    self.print_query_output(f"{fileName} is not a query", "red")




    def delete_query(self):
        """
        Show dialog and remove the selected query from the main window query data dictionary if selected
        """
        query_id = self.view_query_combo.currentText()
        try:
            if query_id in self.query_data_dict.keys():
                are_you_sure_dialog = DeleteAreYouSure()
                are_you_sure_dialog.query_name.setText(query_id)
                result = are_you_sure_dialog.exec_()
                if result:
                    self.remove_query_from_dict(query_id)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def remove_query_from_dict(self, query_id):
        """
        Remove an selected item from the main query_data_dict
        :param query_id: ID of query to remove
        """
        self.query_data_dict.pop(query_id)
        self.clear_query_info()
        self.set_query_list_dropdown()  # update the query lists across the gui

    def diff_query(self):
        """
        Execute the diff between selected queries
        """
        try:
            q1 = self.query_data_dict[self.query_diff_1.currentText()]
            q2 = self.query_data_dict[self.query_diff_2.currentText()]

            # check that the columns match regardless of order
            if pgh.dataframe_columns_equal(q1.results, q2.results):
                self.print_query_output(
                    f"DIFFING: {pgh._blue_str(q1.id)} and {pgh._blue_str(q2.id)}")
                self.diff_query_objects(q1, q2)
                self.diff_query_results(q1, q2)
            else:
                self.print_query_output("YOU CAN ONLY DIFF SIMILAR QUERY RESULTS", 'red')
                self.print_query_output(f"{q1.id} = {q1.function}, {q2.id} = {q2.function}", 'red')
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def diff_query_objects(self, q1, q2):
        """
        Diff the members belonging to the query objects (except the get_ functions and results)
        Print the results to the GUI
        :param q1: object to diff
        :param q2: object to diff
        """
        for member in [i for i in dir(q1) if not i.startswith("_") and
                                             not i.startswith("get") and
                                             not i.startswith("results")]:
            pgh.print_diff(self.query_output, q1, q2, member)

    def diff_query_results(self, q1, q2):
        """
        Setup the DiffResultsWindow to display the diff results of the pandas dataframes
        :param q1: object to diff
        :param q2: object to diff
        """
        diff_results_window = DiffResultsWindow(parent=self)
        diff_results_window.diff_title.setText(f"Diff Results for {q1.id} and {q2.id}")
        diff_results_window.q1_diff_label.setText(f"{q1.id}")
        diff_results_window.q2_diff_label.setText(f"{q2.id}")
        diff_results_window.q2_diff_label.setText(f"{q2.id}")
        diff_results_window.execute_diff(q1, q2)
        diff_results_window.show()

    def handle_sample_query_dropdown(self):
        """
        Used to dete sample variable list depending on which data source is selected
        """
        selection = self.sample_query_combo.currentText()
        current_query = self.query_data_dict[selection]
        vars = current_query.results.T.columns.to_list() # Transpose to convert wide to long
        vars = list(map(str, vars)) # make sure vars are string type
        # vars = current_query.results.index.to_list() # use this for wide data (vars as row names)
        self.sample_variable_combo.clear()
        self.sample_variable_combo.addItems(vars)

    def show_sample_dialog(self):
        """
        Open the sample dialog and do the sampling depending on if range or category is selected
        :return:
        """
        query_selection = self.sample_query_combo.currentText()
        selected_query = copy.deepcopy(self.query_data_dict[query_selection])
        selected_query.results = selected_query.results.T # Transpose to account for wide data (this is a bit of a hack because the code was written for long data)
        variable_selection = self.sample_variable_combo.currentText()
        try:
            if self.sample_function_combo.currentText() == "range":
                self.sample_by_range(selected_query, variable_selection)
            elif self.sample_function_combo.currentText() == "category":
                self.sample_by_category(selected_query, variable_selection)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def sample_by_range(self, selected_query, variable_selection):
        """
        Sample the query results by a numeric range
        :param selected_query: queryobject to apply sampling to
        :param variable_selection: variable of query results to sample over
        """
        # get max and min values for specific variable
        range_max = selected_query.results[variable_selection].max() # use this for variables as columns
        range_min = selected_query.results[variable_selection].min()
        # range_max = selected_query.results.loc[variable_selection, :].max()
        # range_min = selected_query.results.loc[variable_selection, :].min()
        # test to see if the max and min are numeric
        if np.issubdtype(type(range_max), np.number) and np.issubdtype(type(range_min), np.number):
            sample_dialog = self.setup_range_sample_dialog(range_min, range_max, selected_query.id, variable_selection)
            result = sample_dialog.exec_()
            if result:
                filt_min = sample_dialog.min_spin.value()
                filt_max = sample_dialog.max_spin.value()

                # apply the sampling
                # TODO: make this more sophisiticated to enable sampling of only first step (if selected)
                sampled_query = copy.deepcopy(selected_query.results)
                sampled_query = sampled_query.loc[sampled_query[variable_selection] <= filt_max]
                sampled_query = sampled_query.loc[sampled_query[variable_selection] >= filt_min]
                sampled_query.reset_index(inplace=True, drop=True)

                # save the new sample as a query
                sample_id = f"{selected_query.id}_{variable_selection}_{self.sample_function_combo.currentText()}_" \
                            f"{filt_min}-{filt_max} "
                new_query = self.create_new_query_object(query_function=selected_query.function,
                                                         data_id=selected_query.data_id,
                                                         query_data=sampled_query.T, #TODO: fix the shape of the data throughout the whole gui
                                                         query_id=sample_id)
                self.update_query_data(new_query.id, new_query)
                self.print_query_output(f"sample saved as: {sample_id}", "black")
        else:
            self.print_query_output(
                "THE VARIABLE DOES NOT CONTAIN NUMERIC VALUES. USE THE CATEGORY FUNCTION INSTEAD", "red")

    def sample_by_category(self, selected_query, variable_selection):
        """
        Sample the query results by a string category
        :param selected_query: queryobject to apply sampling to
        :param variable_selection: variable of query results to sample over
        """
        sample_dialog = self.setup_category_sample_dialog(selected_query, variable_selection)
        result = sample_dialog.exec_()
        if result:
            cat_values = sample_dialog.sample_combo_mult.currentData()

            # convert the column (variable to sample) to string types to enable sampling
            sampled_query = copy.deepcopy(selected_query.results)
            sampled_query[variable_selection] = sampled_query[variable_selection].astype(str)

            # apply the sampling
            # TODO: make this more sophisiticated to enable sampling of only first step (if selected)
            sampled_query = pd.concat(
                [sampled_query.loc[sampled_query[variable_selection] == i] for i in cat_values])
            sampled_query.reset_index(inplace=True, drop=True)

            # save the new sample as a query
            dt_string, _ = pgh.get_time_stamp()
            sample_id = f"{selected_query.id}_{variable_selection}_{self.sample_function_combo.currentText()}_" \
                        f"{dt_string}"
            new_query = self.create_new_query_object(query_function=selected_query.function,
                                                     data_id=selected_query.data_id,
                                                     query_data=sampled_query.T,
                                                     query_id=sample_id)
            self.update_query_data(new_query.id, new_query)
            self.print_query_output(f"sample saved as: {sample_id}", "black")

    def setup_range_sample_dialog(self, range_min, range_max, query_selection, variable_selection):
        """
        Set up the range dialog for sampling
        :param range_min: min value for range selection
        :param range_max: max value for range selection
        :param query_selection: id of selected query to sample
        :param variable_selection: name of variable to sample over in selected query
        :return: the setup sample range dialog
        """
        sample_dialog = QuerySampleRangeDialog()
        sample_dialog.name_label.setText(f"{query_selection}")
        sample_dialog.value_label.setText(f"{variable_selection}")
        sample_dialog.range_label.setText(f"{range_min} : {range_max}")
        sample_dialog.min_spin.setRange(range_min, range_max)
        sample_dialog.max_spin.setRange(range_min, range_max)
        return sample_dialog

    def setup_category_sample_dialog(self, selected_query, variable_selection):
        """
        Set up the range dialog for sampling
        :param selected_query: query object to sample over
        :param variable_selection: name of variable to sample over in selected query
        :return: the setup sample category dialog
        """
        sample_dialog = QuerySampleCategoryDialog()
        sample_dialog.name_label.setText(f"{selected_query.id}")
        sample_dialog.value_label.setText(f"{variable_selection}")
        values_raw = selected_query.results[variable_selection].unique() # use this for variable as cols
        # values_raw = selected_query.results.loc[variable_selection, :].unique() # use this for variables as rows
        values_string = [str(i) for i in values_raw]
        sample_dialog.sample_combo_mult.addItems(values_string)
        return sample_dialog

    def set_query_list_dropdown(self):
        """
        Update the query lists across the whole gui
        """
        pgh.update_combo(self.view_query_combo, self.query_data_dict.keys())
        pgh.update_combo(self.sample_query_combo, self.query_data_dict.keys())
        pgh.update_combo(self.query_diff_1, self.query_data_dict.keys())
        pgh.update_combo(self.query_diff_2, self.query_data_dict.keys())
        pgh.update_combo(self.step_query_combo, self.query_data_dict.keys())
        # emit the query_combo activated signal to populate the other dropdowns
        self.sample_query_combo.activated.emit(0)

    def set_function_dropdown(self):
        """
        Populate the query function dropdown with functions from functions/PsychSimQueryFunctions.py
        """
        query_methods = [method_name for method_name in dir(self.psychsim_query)
                         if callable(getattr(self.psychsim_query, method_name))
                         and '__' not in method_name]
        pgh.update_combo(self.function_combo, query_methods)

    def set_sample_function_dropdown(self, function_list):
        """
        Populate the sample function dropdown with "range" and "category"
        """
        pgh.update_combo(self.sample_function_combo, function_list)

    def handle_params(self):
        """
        Get the parameters from the function definitions in functions/PsychSimQueryFunctions.py
        :return:
        """
        function_name = self.function_combo.currentText()
        function = getattr(self.psychsim_query, function_name)
        param_list = inspect.getfullargspec(function)
        self.set_params(param_list)

        # ---do the generic param stuff---
        # clear the table
        self.query_param_table.setRowCount(0)

        # Set table cols
        columns = ['name', 'set', 'expected type', 'value/view']
        self.query_param_table.setColumnCount(len(columns))
        self.query_param_table.setHorizontalHeaderLabels(columns)

        # add row to the table
        # get names
        param_names = param_list.args
        if 'self' in param_names:
            param_names.remove('self')

        for param in param_names:
            new_row = {'name': param,
                       'set': self._create_param_table_button("test_arg_val", "SET", self.set_param),
                       'expected type': "...",
                       'value': ".. Set type: set value/name .. "}

            if param in param_list.annotations:
                new_row["expected type"] = param_list.annotations[param].__name__

            self._add_row_to_table(self.query_param_table, new_row.values())

    def _create_param_table_button(self, arg_val, button_label, button_function):
        """
        TODO: refactor this out to helpers (it is also in the PsychSimGuiMainWindow.py)
        Create the button to save data in the data table
        :param data_id:
        :return:
        """
        btn = QPushButton(self.query_param_table)
        btn.setText(button_label)
        btn.clicked.connect(partial(button_function, arg_val))
        return btn

    def _add_row_to_table(self, table, row):
        """
        TODO: refactor this out to helpers (it is also in the LoadedDataWindow.py)
        Add a row to the data table
        :param row: list of items to add to table
        """
        rowPosition = table.rowCount()
        table.insertRow(rowPosition)
        index = 0
        for item in row:
            if type(item) == QPushButton:
                table.setCellWidget(rowPosition, index, item)
            else:
                table.setItem(rowPosition, index, QTableWidgetItem(item))
            index = index + 1

    def set_param(self, arg_val="test"):

        self.print_query_output("SET THE PARAM!!", "red")
        try:
            are_you_sure_dialog = SetParamDialog(data_dict=self.sim_data_dict, query_dict=self.query_data_dict)
            # are_you_sure_dialog.query_name.setText(query_id)
            result = are_you_sure_dialog.exec_()
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def set_params(self, param_list):
        """
        Enable the params on the gui according to the param_list
        :param param_list: list of parameters to enable
        """
        param_combo_boxes = dict(agent=self.agent_combo,
                                 action=self.action_combo,
                                 cycle=self.cycle_combo,
                                 horizon=self.horizon_combo,
                                 state=self.state_combo)

        for name, combo in param_combo_boxes.items():
            # 'agent' is the highest param in the heriachy so set this one first. set others after if necessesary
            if "agent" in param_list.args:
                self.set_agent_dropdown(param_list.args)
            else:
                combo.setEnabled(False)
                combo.clear()

    def set_agent_dropdown(self, param_list):
        """
        Set the agent dropdown based on the data
        :param param_list: list of params that should be activated
        """
        self.agent_combo.setEnabled(True)
        try:
            data_id = self.data_combo.currentText()
            if data_id:
                _, agents = self.psychsim_query.get_agents(data=self.sim_data_dict[data_id], data_id=data_id)
                self.agent_combo.clear()
                self.agent_combo.addItems(agents['agent'].tolist())
            self.set_action_dropdown(param_list)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def set_action_dropdown(self, param_list):
        """
        Set the action dropdown with actions from the selected agent
        :param param_list: list of params that should be activated
        """
        if "action" in param_list:
            self.action_combo.setEnabled(True)
            try:
                data_id = self.data_combo.currentText()
                if data_id:
                    selected_agent = self.agent_combo.currentText()
                    _, actions = self.psychsim_query.get_actions(data=self.sim_data_dict[data_id], agent=selected_agent)
                    self.action_combo.clear()
                    for index, row in actions.iterrows():
                        self.action_combo.insertItem(index, row['action'], row['step'])
                self.set_state_dropdown(param_list)
            except:
                tb = traceback.format_exc()
                self.print_query_output(tb, "red")

    def set_cycle_dropdown(self):
        # This isn't implemented yet as I don't have a function that needs it (I dont' know what the functions should be)
        pass

    def set_horizon_dropdown(self):
        # This isn't implemented yet as I don't have a function that needs it (I dont' know what the functions should be)
        pass

    def set_state_dropdown(self, param_list):
        """
        Set the state dropdown based on predicted actions from the selected agent
        :param param_list: list of params that should be activated
        """
        if "state" in param_list:
            self.state_combo.setEnabled(True)
            try:
                data_id = self.data_combo.currentText()
                action_id = self.action_combo.currentData()
                if data_id is not None and action_id is not None:
                    selected_agent = self.agent_combo.currentText()
                    _, predicted_actions = self.psychsim_query.query_action(data=self.sim_data_dict[data_id],
                                                                         agent=selected_agent, action=action_id)
                    self.state_combo.clear()
                    self.state_combo.addItems(predicted_actions['base_action'].unique().tolist())
            except:
                tb = traceback.format_exc()
                self.print_query_output(tb, "red")

    def display_query(self, query_id):
        """
        Display the query in a dialog and rename if necessesary
        :param query_id: id of query to display
        """
        try:
            if query_id in self.query_data_dict.keys():
                selected_query = self.query_data_dict[query_id]
                if selected_query.result_type == 'table':
                    selected_query = self.show_query_dialog(model=PandasModel(selected_query.results), query=selected_query)
                elif selected_query.result_type == 'tree':
                    selected_query = self.show_query_tree_dialog(model=TreeModel(selected_query.results), query=selected_query)
                self.query_data_dict[selected_query.id] = self.query_data_dict.pop(query_id)
                # TODO: fix bug that updates query list even if viewed
                self.set_query_list_dropdown()
                self.update_query_info()
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def show_query_dialog(self, model, query):
        """
        Show the dialog that shows the query results
        :param model: PandasModel with query results
        :param query: PsySimQuery object of selected query
        """
        query_dialog = QueryDataDialog(query, model)
        result = query_dialog.exec_()
        query = query_dialog.query_data
        if result:
            query.id = query_dialog.query_id_input.text()
        return query

    def show_query_tree_dialog(self, model, query):
        """
        Show the dialog that shows the query results
        :param model: PandasModel with query results
        :param query: PsySimQuery object of selected query
        """
        #----
        #for standardItem lists
        # rootNode = model.invisibleRootItem()
        # for node in query.results:
        #     rootNode.appendRow(node)
        #----
        query_dialog = QueryDataTreeDialog(query, model)
        query_dialog.Query_data_tree.expandAll()
        result = query_dialog.exec_()
        query = query_dialog.query_data
        if result:
            query.id = query_dialog.query_id_input.text()
        return query

    def get_query_doc(self):
        """
        Get the docstring of the selected query
        """
        query_function = self.function_combo.currentText()
        try:
            self.print_query_output(f"{query_function}: {getattr(self.psychsim_query, query_function).__doc__}")
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def view_query(self):
        """
        Display the query selectedon the GUI
        """
        query_id = self.view_query_combo.currentText()
        self.display_query(query_id)

    def print_query_output(self, msg, color="black"):
        """
        Print to the textarea on the query page
        :param msg: message to print
        :param color: color to display message
        """
        pgh.print_output(self.query_output, msg, color)

    def set_func_source(self):
        """
        Set the path to the simulation script (self.sim_path) and update the gui labels
        """
        new_path = pgh.get_file_path(path_label=self.func_source_label)
        if new_path:
            self.func_source = new_path
            # self.func_source_label.setText("...")

    def reolaod_func_source(self):
        """
        import the functions script
        """
        #todo: refactor with similar function in simulationInfoPage?
        self.add_to_sys_path()
        self.print_query_output(f"attempting to load functions from: {self.func_source}", "green")
        try:
            # import the sim module
            self.func_spec = importlib.util.spec_from_file_location(self.func_class_name, self.func_source)
            self.func_module = importlib.util.module_from_spec(self.func_spec)
            self.func_spec.loader.exec_module(self.func_module)
            # update buttons and print output
            self.print_query_output(f"functions loaded: {self.func_source}", "green")
            #update functions dropdown
            self.psychsim_query = getattr(self.func_module, self.func_class_name)()
            self.set_function_dropdown()
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def add_to_sys_path(self):
        """
        Add the selected functions source sys path variable
        This enables the functions to be found by required elements of the gui
        """
        # todo: refactor with similar function in simulationInfoPage
        try:
            self.func_class_name = re.split(r'[.,/]', self.func_source)[-2]
        # sys.path.insert(1, self.psychsim_path)
        # sys.path.insert(1, self.definitions_path)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def show_step_through_window(self):
        try:
            query = self.query_data_dict[self.step_query_combo.currentText()]
            step_through_results_window = StepThroughResultsWindow(parent=self, query=query)
            step_through_results_window.results_title.setText(f"Step through results for query:{query.id}")
            step_through_results_window.show()
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueryDataPage()
