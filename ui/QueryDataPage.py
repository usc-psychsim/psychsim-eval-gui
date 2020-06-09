from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import traceback
import inspect
import difflib
import os
import sys
import copy
import pandas as pd
import numpy as np

from PandasModel import PandasModel
import psychsim_gui_helpers as pgh
from functions.query_functions import PsychSimQuery

from ui.QuerySampleCategoryDialog import QuerySampleCategoryDialog
from ui.QuerySampleRangeDialog import QuerySampleRangeDialog
from ui.DiffResultsWindow import DiffResultsWindow
from ui.DeleteAreYouSureDialog import DeleteAreYouSure
from ui.QueryDataDialog import QueryDataDialog

query_data_page_file = os.path.join("ui", "query_data_page.ui")
ui_queryDataPage, QtBaseClass = uic.loadUiType(query_data_page_file)


class QueryDataPage(QWidget, ui_queryDataPage):
    """
    This class is for all functions relating to the query data page of the GUI
    This includes:
    """
    # SET UP SIGNALS
    new_query_signal = pyqtSignal(str, pgh.PsySimQuery)
    show_query_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.psychsim_query = PsychSimQuery()

        self.set_function_dropdown()

        # Setup buttons
        self.function_info_button.setToolTip('Click for how to write custom query functions')

        self.query_doc_button.clicked.connect(self.get_query_doc)
        self.query_doc_button.clicked.connect(self.get_query_doc)

        # self.data_combo.activated.connect(self.reset_params)
        # self.agent_combo.activated.connect(self.set_action_dropdown)
        # self.action_combo.activated.connect(self.set_state_dropdown)
        # # self.data_combo.activated.connect(self.set_cycle_dropdown)

        # self.query_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "query"))
        # self.function_info_button.clicked.connect(lambda: self.show_doc_window("function_definitions.html"))

        self.set_sample_function_dropdown()

    def execute_query(self, sim_data_dict, query_data_dict):
        """
        Execute the query with the given params. The query function is defined in functions/query_functions.py
        :param sim_data_dict: dictionarly containing the stored sim run data in the main window
        """
        # get the query function
        query_function = self.function_button.text()
        # get the params
        agent = self.agent_combo.currentText()
        state = self.state_combo.currentText()
        action_step = self.action_combo.currentData()  # This is actually the step value as it is easier to access the data by step rather than action
        data_id = self.data_combo.currentText()
        try:
            result = getattr(self.psychsim_query, query_function)(data=sim_data_dict[data_id], data_id=data_id,
                                                                  agent=agent, action=action_step, state=state)
            result = result.apply(pd.to_numeric,
                                  errors='ignore')  # convert the resulting dataframe to numeric where possible
            self.print_query_output(f"results for {query_function} on {self.data_combo.currentText()}:")
            self.print_query_output(str(result))
            new_query = self.create_new_query(query_function, data_id, result)
            self.update_query_data(new_query.id, new_query, query_data_dict)
            self.display_query(new_query.id, query_data_dict, sim_data_dict)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")


    def update_query_data(self, query_id, query_data, query_data_dict):
        query_data_dict[query_id] = query_data
        self.set_query_list_dropdown(query_data_dict)

    def create_new_query(self, query_function, data_id, query_data):
        """
        Create a new query object
        :param query_function: (str) name of query function
        :param data_id: (str) id of data used
        :param query_data: (DataFrame) results of query
        :return: PsySimQuery object
        """
        dt_string, run_date = pgh.get_time_stamp()
        query_id = f"{query_function}_{data_id}_{dt_string}"
        return pgh.PsySimQuery(id=query_id, data_id=data_id, params=[], function=query_function,
                               results=query_data)


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

    def update_query_info(self, query_data_dict, sim_data_dict):
        """
        Update the query info on the gui with appropriate values
        :param query_data_dict: dictionary of query data from main gui
        :param sim_data_dict: dictionary of sim data from main gui
        """
        selected_query_id = self.view_query_combo.currentText()
        selected_query = query_data_dict[selected_query_id]
        try:
            if selected_query.data_id in sim_data_dict.keys():
                selected_query_asc_data = sim_data_dict[selected_query.data_id]
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

    def save_csv_query(self, query_data_dict):
        """
        Write the query results as a csv file to disk
        :param query_data_dict: dictionary of query data from main gui
        """
        query_id = self.view_query_combo.currentText()
        if query_id in query_data_dict.keys():
            dt_string, _ = pgh.get_time_stamp()
            output_directory = 'sim_output'
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            output_path = os.path.join(output_directory, f"{query_id}_{dt_string}.csv")
            query_data_dict[query_id].results.to_csv(output_path)
            self.print_query_output(f"{query_id} saved to: {output_path}", "black")

    def delete_query(self, query_data_dict):
        """
        Show dialog and remove the selected query from the main window query data dictionary if selected
        :param query_data_dict: dictionary of query data from main gui
        """
        query_id = self.view_query_combo.currentText()
        try:
            if query_id in query_data_dict.keys():
                are_you_sure_dialog = DeleteAreYouSure()
                are_you_sure_dialog.query_name.setText(query_id)
                result = are_you_sure_dialog.exec_()
                if result:
                    self.remove_query_from_dict(query_id, query_data_dict)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def remove_query_from_dict(self, query_id, query_data_dict):
        """
        Remove an selected item from the main query_data_dict
        :param query_id: ID of query to remove
        :param query_data_dict: dict holding query objects from main window
        """
        query_data_dict.pop(query_id)
        self.clear_query_info()
        self.set_query_list_dropdown(query_data_dict)  # update the query lists across the gui

    def diff_query(self, query_data_dict):
        """
        Execute the diff between selected queries
        :param query_data_dict: dictionary containing query objects from main window
        """
        try:
            q1 = query_data_dict[self.query_diff_1.currentText()]
            q2 = query_data_dict[self.query_diff_2.currentText()]

            # check that the columns match regardless of order
            if pgh.dataframe_columns_equal(q1.results, q2.results):
                self.print_query_output(
                    f"DIFFING: {pgh._blue_str(q1.id)} and {pgh._blue_str(q2.id)}")
                self.diff_query_objects(q1, q2)
                self.diff_query_results(q1, q2)
            else:
                self.print_query_output("YOU CAN ONLY DIFF FUNCTIONS OF THE SAME TYPE", 'red')
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
        for member in [i for i in dir(q1) if not i.startswith("_") and not i.startswith("get") and not i.startswith("results")]:
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
        diff_results_window.format_diff_results(q1, q2)
        diff_results_window.show()

    def handle_sample_query_dropdown(self, query_data_dict):
        """
        Used to dete sample variable list depending on which data source is selected
        :param query_data_dict:
        """
        selection = self.sample_query_combo.currentText()
        current_query = query_data_dict[selection]
        vars = current_query.results.columns.to_list()
        self.sample_variable_combo.clear()
        self.sample_variable_combo.addItems(vars)

    def show_sample_dialog(self, query_data_dict):
        # TODO: the sampling here samples across all steps. Therefore if you want to track certain actors through steps based on their initial value this needs to be fixed
        result = None
        query_selection = self.sample_query_combo.currentText()
        variable_selection = self.sample_variable_combo.currentText()
        selected_query = query_data_dict[query_selection]
        try:
            if self.sample_function_combo.currentText() == "range":
                sample_dialog = QuerySampleRangeDialog()
                current_variable_max_value = selected_query.results[variable_selection].max()
                current_variable_min_value = selected_query.results[variable_selection].min()
                # test to see if the max and min are numeric
                if np.issubdtype(type(current_variable_max_value), np.number) and np.issubdtype(
                        type(current_variable_min_value), np.number):
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
                        query_data_dict[sample_id] = pgh.PsySimQuery(id=sample_id,
                                                                     data_id=selected_query.data_id,
                                                                     params=[],
                                                                     function="test",
                                                                     results=sampled_query)

                        self.print_query_output(f"sample saved as: {sample_id}", "black")

                        # update the query lists over the whole gui
                        self.set_query_list_dropdown(query_data_dict)
                else:
                    # IT IS NOT NUMERIC - DISPLAY WARNING
                    self.print_query_output(
                        "THE VARIABLE DOES NOT CONTAIN NUMERIC VALUES. USE THE CATEGORY FUNCTION INSTEAD", "red")
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
                    cat_values = sample_dialog.sample_combo_mult.currentData()

                    # convert the row to strings for sampling
                    sampled_query = copy.deepcopy(selected_query.results)
                    sampled_query[variable_selection] = sampled_query[variable_selection].astype(str)

                    # apply the sampling
                    sampled_query = pd.concat(
                        [sampled_query.loc[sampled_query[variable_selection] == i] for i in cat_values])

                    # save the new query as a sample

                    dt_string, _ = pgh.get_time_stamp()
                    sample_id = f"{query_selection}_{variable_selection}_{self.sample_function_combo.currentText()}_{dt_string}"
                    query_data_dict[sample_id] = pgh.PsySimQuery(id=sample_id,
                                                                 data_id=selected_query.data_id,
                                                                 params=[],
                                                                 function="test",
                                                                 results=sampled_query)

                    self.print_query_output(f"sample saved as: {sample_id}", "black")
                    # update the query lists over the whole gui
                    self.set_query_list_dropdown(query_data_dict)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def set_query_list_dropdown(self, query_data_dict):
        self.update_query_combo(self.view_query_combo, query_data_dict)
        self.update_query_combo(self.sample_query_combo, query_data_dict)
        self.update_query_diff_combo(self.query_diff_1, query_data_dict)
        self.update_query_diff_combo(self.query_diff_2, query_data_dict)
        # todo: connect plot query with self.set_axis_dropdowns function (parent = self) ??
        # pgh.update_toolbutton_list(list=query_items, button=self.plot_query, action_function=self.set_axis_dropdowns,
        #                            parent=self)

    def update_query_combo(self, combo_box, query_data_dict):
        combo_box.clear()
        new_items = [item for item in query_data_dict.keys()]
        combo_box.addItems(new_items)

    def update_query_diff_combo(self, combo_box, query_data_dict):
        combo_box.clear()
        new_items = [item for item in query_data_dict.keys() if not query_data_dict[item].diff_query]
        combo_box.addItems(new_items)

    def set_function_dropdown(self):
        # TODO: refactor these dropdowns so they are all combo boxes
        query_methods = [method_name for method_name in dir(self.psychsim_query)
                         if callable(getattr(self.psychsim_query, method_name))
                         and '__' not in method_name]
        pgh.update_toolbutton_list(list=query_methods, button=self.function_button, action_function=self.btnstate,
                                   parent=self)

    def set_sample_function_dropdown(self):
        # TODO: refactor
        functions = ["range", "category"]
        self.sample_function_combo.clear()
        self.sample_function_combo.addItems(functions)

    def set_agent_dropdown(self):
        # TODO: refactor
        if self.agent_combo.isEnabled():
            try:
                data_id = self.data_combo.currentText()
                if data_id:
                    agents = self.psychsim_query.get_agents(data=self.sim_data_dict[data_id], data_id=data_id)
                    self.agent_combo.clear()
                    self.agent_combo.addItems(agents['agent'].tolist())
                self.set_action_dropdown()
            except:
                tb = traceback.format_exc()
                self.print_query_output(tb, "red")

    def set_action_dropdown(self):
        # TODO: refactor
        if self.action_combo.isEnabled():
            try:
                data_id = self.data_combo.currentText()
                if data_id:
                    selected_agent = self.agent_combo.currentText()
                    actions = self.psychsim_query.get_actions(data=self.sim_data_dict[data_id], agent=selected_agent)
                    self.action_combo.clear()
                    for index, row in actions.iterrows():
                        self.action_combo.insertItem(index, row['action'], row['step'])
                self.set_state_dropdown()
            except:
                tb = traceback.format_exc()
                self.print_query_output(tb, "red")

    def set_cycle_dropdown(self):
        # TODO: refactor
        pass

    def set_horizon_dropdown(self):
        # TODO: refactor
        pass

    def set_state_dropdown(self):
        # TODO: refactor
        if self.state_combo.isEnabled():
            try:
                data_id = self.data_combo.currentText()
                action_id = self.action_combo.currentData()
                if data_id is not None and action_id is not None:
                    selected_agent = self.agent_combo.currentText()
                    predicted_actions = self.psychsim_query.query_action(data=self.sim_data_dict[data_id],
                                                                         agent=selected_agent, action=action_id)
                    self.state_combo.clear()
                    self.state_combo.addItems(predicted_actions['base_action'].unique().tolist())
                    # for index, row in predicted_actions.unique().iterrows():
                    #     self.state_combo.insertItem(index, row['base_action'], index)
            except:
                tb = traceback.format_exc()
                self.print_query_output(tb, "red")

    def btnstate(self, action, button):
        selection = action.checkedAction().text()
        button.setText(selection)
        self.handle_params(selection)

    def handle_params(self, function_name):
        function = getattr(self.psychsim_query, function_name)
        param_list = inspect.getfullargspec(function)
        print(param_list)
        self.set_params(param_list)

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
                    # Connect this to setting the action one
                elif name == "cycle":
                    self.set_cycle_dropdown()
                elif name == "horizon":
                    self.set_horizon_dropdown()
                elif name == "state":
                    pass
                    # self.set_state_dropdown()
                elif name == "action":
                    pass
                else:
                    self.reset_params()
                # TODO: if a particular combo box is enabled - then make sure it gets populated hireachically (Agent > Action | cycle |horizon)
            else:
                combo.setEnabled(False)

    def reset_params(self):
        self.agent_combo.clear()
        self.action_combo.clear()
        self.cycle_combo.clear()
        self.horizon_combo.clear()
        self.state_combo.clear()
        # Todo: populate combo boxes based on the function that is selected

    def show_query_dialog(self, model, query):
        query_dialog = QueryDataDialog(query, model)
        result = query_dialog.exec_()
        query = query_dialog.query_data
        if result:
            query.id = query_dialog.query_id_input.text()
        return query

    def get_query_doc(self):
        query_function = self.function_button.text()
        try:
            self.print_query_output(f"{query_function}: {getattr(self.psychsim_query, query_function).__doc__}")
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def view_query(self, query_data_dict, sim_data_dict):
        query_id = self.view_query_combo.currentText()
        self.display_query(query_id, query_data_dict, sim_data_dict)

    def display_query(self, query_id, query_data_dict, sim_data_dict):
        """
        Display the query in a dialog and rename if necessesary
        :param query_id: id of query to display
        :param query_data_dict:
        """
        try:
            if query_id in query_data_dict.keys():
                selected_query = query_data_dict[query_id]
                selected_query = self.show_query_dialog(model=PandasModel(selected_query.results), query=selected_query)
                query_data_dict[selected_query.id] = query_data_dict.pop(query_id)
                #TODO: fix bug that updates query list even if viewed
                self.set_query_list_dropdown(query_data_dict)
                self.update_query_info(query_data_dict, sim_data_dict)
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def print_query_output(self, msg, color="black"):
        pgh.print_output(self.query_output, msg, color)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueryDataPage()
