from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtGui
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
from functools import partial

import psychsim_gui_helpers as pgh
# from functions.PsychSimQueryFunctions2 import PsychSimQueryFunctions

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
        self._param_table_cache = {}

        # self.psychsim_query = PsychSimQueryFunctions()

        # self.set_function_dropdown()

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

        self.query_doc_button.clicked.connect(self.get_query_doc)
        self.query_doc_button.clicked.connect(self.get_query_doc)

        self.set_func_source_button.clicked.connect(self.set_func_source)
        self.reload_func_source_button.clicked.connect(self.reload_func_source)

        # Set tooltips
        self.function_info_button.setToolTip('Click for how to write custom query functions')
        self.execute_query_button.setToolTip('Click to execute selected function. NOTE: set parameters first!')
        self.set_func_source_button.setToolTip('Select the path to the function definitions file')
        self.reload_func_source_button.setToolTip('Reload the functions definition file')
        self.function_combo.setToolTip('Reload the functions definition file')

        self.set_sample_function_dropdown(["range", "category"])

        self.type_match_label.setStyleSheet("background-color: #00FF00")
        self.type_no_match_label.setStyleSheet("background-color: red")
        self.type_unknown_label.setStyleSheet("background-color: yellow")

    def _get_param_value(self, param_type, param_name):
        if param_type == "str":
            return param_name
        elif param_type == "bool":
            return eval(param_name)
        elif param_type == pgh.PsychSimRun.__name__:
            return self.sim_data_dict[param_name]
        elif param_type == pgh.PsySimQuery.__name__:
            return self.query_data_dict[param_name]

    def execute_query(self):
        """
        Execute the query with the given params. The query function is defined in functions/ASISTQueryFunctions.py
        """
        params = {}
        for row in range(self.query_param_table.rowCount()):
            _item = self.query_param_table.item(row, 3)
            if _item:
                # param_values.append(self.query_param_table.item(row, 3).text())
                param_name = self.query_param_table.item(row, 0).text()
                param_type = self.query_param_table.item(row, 3).text()
                param_value = self.query_param_table.item(row, 4).text()
                params[param_name] = self._get_param_value(param_type, param_value)
        query_function = self.function_combo.currentText()
        self.cache_table(query_function, self.query_param_table)
        try:
            query_result = getattr(self.psychsim_query, query_function)(**params)
            if len(query_result) == 2:
                result_type = query_result[0]
                result = query_result[1]
            elif len(query_result) == 1:
                # if the result type isn't specified, then make it a table
                result_type = "table"
                result = query_result[1]

            # result = result.apply(pd.to_numeric,
            #                       errors='ignore')  # convert the resulting dataframe to numeric where possible
            self.print_query_output(f"results for {query_function}:")
            self.print_query_output(str(result))
            new_query = self.create_new_query_object(query_function, params, result, result_type=result_type)
            self.update_query_data(new_query.id, new_query)
            self.display_query(new_query.id)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def cache_table(self, table_name, table):
        try:
            table_items = []
            for row in range(table.rowCount()):
                row_items = []
                for col in range(table.columnCount()):
                    cur_item = table.item(row, col)
                    if cur_item:
                        row_items.append(cur_item.text())
                    if col == 1:
                        row_items.append("set_button")
                table_items.append(row_items)
            self._param_table_cache[table_name] = table_items
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

    def create_new_query_object(self, query_function, params, query_data, result_type="table", query_id=None):
        """
        Create a new query object
        :param query_function: (str) name of query function
        :param query_data: (DataFrame) results of query
        :param params: (dict) parameters of query function defined in functions file
        :param result_type: (str) "table" to display results in table. "tree" to display results as tree
        :param query_id: (str) id of query to find it in the query dict
        :return: PsySimQuery object
        """
        dt_string, run_date = pgh.get_time_stamp()
        if not query_id:
            query_id = f"{query_function}_{dt_string}"
        return pgh.PsySimQuery(id=query_id, params=params, function=query_function,
                               results=query_data, result_type=result_type)

    def clear_query_info(self):
        """
        Clear the query info on the gui
        """
        try:
            self.sim_file_label.setText("...")
            self.query_name_label.setText("...")
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
        try:
            selected_query = self.query_data_dict[selected_query_id]
            self.sim_file_label.setText("...")
            self.query_name_label.setText(selected_query.id)
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
        file_name, _ = QFileDialog.getOpenFileName(self,
                                                   "Select data file",
                                                   "",
                                                   "query data (*.pickle)",
                                                   options=options)
        if file_name:
            # load the psychsim libs to read the pickle objects
            # self.sim_info_page.load_sim()
            with open(file_name, 'rb') as f:
                loaded_query = pickle.load(f)
                if type(loaded_query) == pgh.PsySimQuery:
                    self.update_query_data(loaded_query.id, loaded_query)
                    self.print_query_output(f"{loaded_query.id} loaded", "black")
                else:
                    self.print_query_output(f"{file_name} is not a query", "red")

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
        self.set_query_list_dropdown(clear=True)  # update the query lists across the gui

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
                    f"DIFFING: {pgh.blue_str(q1.id)} and {pgh.blue_str(q2.id)}")
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
        Used to update sample variable list depending on which data source is selected
        """
        selection = self.sample_query_combo.currentText()
        if len(self.query_data_dict) > 0:
            current_query = self.query_data_dict[selection]
            variables = current_query.results.T.columns.to_list()  # Transpose to convert wide to long
            variables = list(map(str, variables))  # make sure vars are string type
            # vars = current_query.results.index.to_list() # use this for wide data (vars as row names)
            self.sample_variable_combo.clear()
            self.sample_variable_combo.addItems(variables)

    def show_sample_dialog(self):
        """
        Open the sample dialog and do the sampling depending on if range or category is selected
        :return:
        """
        query_selection = self.sample_query_combo.currentText()
        selected_query = copy.deepcopy(self.query_data_dict[query_selection])

        # Transpose to account for wide data (this is a bit of a hack because the code was written for long data)
        selected_query.results = selected_query.results.T

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
        range_max = selected_query.results[variable_selection].max()  # use this for variables as columns
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
                # TODO: make this more sophisticated to enable sampling of only first step (if selected)
                sampled_query = copy.deepcopy(selected_query.results)
                sampled_query = sampled_query.loc[sampled_query[variable_selection] <= filt_max]
                sampled_query = sampled_query.loc[sampled_query[variable_selection] >= filt_min]
                sampled_query.reset_index(inplace=True, drop=True)

                # save the new sample as a query
                sample_id = f"{selected_query.id}_{variable_selection}_{self.sample_function_combo.currentText()}_" \
                            f"{filt_min}-{filt_max} "
                new_query = self.create_new_query_object(query_function=selected_query.function,
                                                         query_data=sampled_query.T,
                                                         query_id=sample_id,
                                                         params=None)
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
            # TODO: make this more sophisticated to enable sampling of only first step (if selected)
            sampled_query = pd.concat(
                [sampled_query.loc[sampled_query[variable_selection] == i] for i in cat_values])
            sampled_query.reset_index(inplace=True, drop=True)

            # save the new sample as a query
            dt_string, _ = pgh.get_time_stamp()
            sample_id = f"{selected_query.id}_{variable_selection}_{self.sample_function_combo.currentText()}_" \
                        f"{dt_string}"
            new_query = self.create_new_query_object(query_function=selected_query.function,
                                                     query_data=sampled_query.T,
                                                     query_id=sample_id,
                                                     params=None)
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
        values_raw = selected_query.results[variable_selection].unique()  # use this for variable as cols
        # values_raw = selected_query.results.loc[variable_selection, :].unique() # use this for variables as rows
        values_string = [str(i) for i in values_raw]
        sample_dialog.sample_combo_mult.addItems(values_string)
        return sample_dialog

    def set_query_list_dropdown(self, clear=False):
        """
        Update the query lists across the whole gui
        """
        pgh.update_combo(self.view_query_combo, self.query_data_dict.keys(), clear)
        pgh.update_combo(self.sample_query_combo, self.query_data_dict.keys(), clear)
        pgh.update_combo(self.query_diff_1, self.query_data_dict.keys(), clear)
        pgh.update_combo(self.query_diff_2, self.query_data_dict.keys(), clear)
        pgh.update_combo(self.step_query_combo, self.query_data_dict.keys(), clear)
        # emit the query_combo activated signal to populate the other dropdowns
        self.sample_query_combo.activated.emit(0)

    def set_function_dropdown(self):
        """
        Populate the query function dropdown with functions from functions/ASISTQueryFunctions.py
        """
        query_methods = [method_name for method_name in dir(self.psychsim_query)
                         if callable(getattr(self.psychsim_query, method_name))
                         and '__' not in method_name]
        pgh.update_combo(self.function_combo, query_methods, clear=True)
        # self.func_source_label.setText(new_path)
        # Make the function param table appear on loading
        self.function_combo.activated.emit(0)

    def set_sample_function_dropdown(self, function_list):
        """
        Populate the sample function dropdown with "range" and "category"
        """
        pgh.update_combo(self.sample_function_combo, function_list)

    def handle_params(self):
        """
        Get the parameters from the function definitions in functions/ASISTQueryFunctions.py
        :return:
        """

        try:
            function_name = self.function_combo.currentText()

            function = getattr(self.psychsim_query, function_name)
            param_list = inspect.getfullargspec(function)

            # ---do the generic param stuff---
            # clear the table
            self.query_param_table.setRowCount(0)

            # Set table cols
            columns = ['name', 'set', 'expected type', 'received type', 'value']
            self.query_param_table.setColumnCount(len(columns))
            self.query_param_table.setHorizontalHeaderLabels(columns)

            param_names = param_list.args
            if 'self' in param_names:
                param_names.remove('self')

            # if a cached table exists, use that, otherwise make a new one
            if function_name in self._param_table_cache.keys() and self._param_table_cache[function_name]:
                for row_number, row in enumerate(self._param_table_cache[function_name]):
                    # If the param is 'data', add a combo box and populate it with data objects
                    set_param_object = None
                    if row[0] == "data":
                        set_param_object = QComboBox()
                        pgh.update_combo(set_param_object, self.sim_data_dict.keys(), clear=True)
                        set_param_object.activated.connect(partial(self.set_type_param, row_number, pgh.PsychSimRun.__name__))
                    elif row[2] == "bool":
                        set_param_object = QComboBox()
                        pgh.update_combo(set_param_object, [False, True], clear=True)
                        set_param_object.activated.connect(partial(self.set_type_param, row_number, "bool"))
                    else:
                         set_param_object = self._create_param_table_button(row_number, "SET", self.set_param)
                    new_row = {'name': row[0],
                               'set': set_param_object,
                               'expected type': row[2],
                               'received type': row[3],
                               'value': row[4]}
                    self._add_row_to_table(self.query_param_table, new_row.values())
                    tab_item = self.query_param_table.item(row_number, 3)
                    self._color_table_params(row[3], row[2], tab_item)
            else:
                param_names = param_list.args
                if 'self' in param_names:
                    param_names.remove('self')

                query_methods = [method_name for method_name in dir(self.psychsim_query)
                                 if callable(getattr(self.psychsim_query, method_name))
                                 and '__' not in method_name]

                for row_number, param in enumerate(param_names):
                    param_type = None
                    if param in param_list.annotations:
                        # Get the param type if defined
                        param_type = param_list.annotations[param]

                    # If the param is 'data', add a combo box and populate it with data objects
                    set_param_object = None
                    if param == "data":
                        set_param_object = QComboBox()
                        pgh.update_combo(set_param_object, self.sim_data_dict.keys(), clear=True)
                        set_param_object.activated.connect(partial(self.set_type_param, row_number, pgh.PsychSimRun.__name__))
                    # elif param_type and param_type[0].__name__ in query_methods:
                    #     # the param attribute lists a query method so set the dropdown box with results from the executed query.
                    #     set_param_object = QComboBox()
                    #     # Get the results to populate the combo box with
                    #     # results = param_type[0]() # TODO: fix this, or come up with a better way to do it
                    elif param_type == bool:
                        set_param_object = QComboBox()
                        pgh.update_combo(set_param_object, [False, True], clear=True)
                        set_param_object.activated.connect(partial(self.set_type_param, row_number, "bool"))

                    else:
                        set_param_object = self._create_param_table_button(row_number, "SET", self.set_param)


                    new_row = {'name': param,
                               'set': set_param_object,
                               'expected type': "...",
                               'received type': "...",
                               'value': "... "}

                    if param in param_list.annotations:
                        new_row["expected type"] = param_list.annotations[param].__name__

                    self._add_row_to_table(self.query_param_table, new_row.values())
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

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
            elif type(item) == QTableWidgetItem:
                table.setItem(rowPosition, index, item)
            elif type(item) == QComboBox:
                table.setCellWidget(rowPosition, index, item)
            else:
                table.setItem(rowPosition, index, QTableWidgetItem(item))
            index = index + 1

    def set_param(self, button_row):
        try:
            set_param_dialog = SetParamDialog(data_dict=self.sim_data_dict, query_dict=self.query_data_dict)
            # are_you_sure_dialog.query_name.setText(query_id)
            param_name = self.query_param_table.item(button_row, 0).text()
            function_name = self.function_combo.currentText()
            set_param_dialog.sel_val_combo.setToolTip(
                f'Select the value to use to pass as a parameter to {function_name}')
            set_param_dialog.set_title(function_name, param_name)
            result = set_param_dialog.exec_()
            if result:
                param_type = set_param_dialog.param_type
                param_val = set_param_dialog.param_val
                # param = are_you_sure_dialog.param_val
                name_item = QTableWidgetItem(param_type)  # create a new Item
                expected_type = self.query_param_table.item(button_row, 2).text()
                self._color_table_params(param_type, expected_type, name_item)
                self.query_param_table.setItem(button_row, 3, name_item)
                name_item = QTableWidgetItem(param_val)  # create a new Item
                self.query_param_table.setItem(button_row, 4, name_item)
                self.cache_table(function_name, self.query_param_table)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def set_type_param(self, button_row, param_type):
        sender = self.sender()
        function_name = self.function_combo.currentText()
        # param_type = pgh.PsychSimRun.__name__
        param_val = sender.currentText()
        name_item = QTableWidgetItem(param_type)  # create a new Item
        expected_type = self.query_param_table.item(button_row, 2).text()
        self._color_table_params(param_type, expected_type, name_item)
        self.query_param_table.setItem(button_row, 3, name_item)
        name_item = QTableWidgetItem(param_val)  # create a new Item
        self.query_param_table.setItem(button_row, 4, name_item)
        self.cache_table(function_name, self.query_param_table)

    def _color_table_params(self, param_type, expected_type, tab_item):
        if param_type == expected_type:
            tab_item.setBackground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
        elif expected_type == "...":
            tab_item.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 0)))
        else:
            tab_item.setBackground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
        return tab_item

    def display_query(self, query_id):
        """
        Display the query in a dialog and rename if necessary
        :param query_id: id of query to display
        """
        sender = self.sender()
        try:
            if query_id in self.query_data_dict.keys():
                selected_query = self.query_data_dict[query_id]
                if selected_query.result_type == 'table':
                    selected_query = self.show_query_dialog(model=PandasModel(selected_query.results),
                                                            query=selected_query)
                elif selected_query.result_type == 'tree':
                    selected_query = self.show_query_tree_dialog(model=TreeModel(selected_query.results),
                                                                 query=selected_query)

                if selected_query.id not in self.query_data_dict.keys():
                    self.query_data_dict[selected_query.id] = self.query_data_dict.pop(query_id)
                    clear = True
                    # if sender.objectName() == "execute_query_button":
                        # clear = True
                    self.set_query_list_dropdown(clear=clear)
                    self.update_query_info()
                elif selected_query.id in self.query_data_dict.keys() and selected_query.id != query_id:
                    self.print_query_output(f"{selected_query.id} already exists! saved instead as {query_id}", "red")
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
        # ----
        # for standardItem lists
        # rootNode = model.invisibleRootItem()
        # for node in query.results:
        #     rootNode.appendRow(node)
        # ----
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
        Display the query selection on the GUI
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
        new_path = pgh.get_file_path(path_label=self.func_source_label, default_dir="functions")
        if new_path:
            self.func_source = new_path
            self.reload_func_source()
            # self.func_source_label.setText(new_path)

    def reload_func_source(self):
        """
        import the functions script
        """
        # todo: refactor with similar function in simulationInfoPage?
        self.add_to_sys_path()
        self.print_query_output(f"attempting to load functions from: {self.func_source}", "green")
        try:
            # import the sim module
            self.func_spec = importlib.util.spec_from_file_location(self.func_class_name, self.func_source)
            self.func_module = importlib.util.module_from_spec(self.func_spec)
            self.func_spec.loader.exec_module(self.func_module)
            # update buttons and print output
            self.print_query_output(f"functions loaded: {self.func_source}", "green")
            # update functions dropdown
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
