from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import traceback
import inspect
import os
import sys
import pandas as pd

from PandasModel import PandasModel
import psychsim_gui_helpers as pgh
from functions.query_functions import PsychSimQuery


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

        self.view_query_button.clicked.connect(self.view_query)
        # self.save_csv_query_button.clicked.connect(self.save_csv_query)
        # self.diff_query_button.clicked.connect(self.diff_query)
        self.query_doc_button.clicked.connect(self.get_query_doc)
        # self.data_combo.activated.connect(self.reset_params)
        # self.agent_combo.activated.connect(self.set_action_dropdown)
        # self.action_combo.activated.connect(self.set_state_dropdown)
        # # self.data_combo.activated.connect(self.set_cycle_dropdown)
        # self.delete_query_buton.clicked.connect(self.delete_query)
        # self.query_help_button.clicked.connect(lambda: self.show_doc_window("gui_functionality.html", "query"))
        # self.function_info_button.clicked.connect(lambda: self.show_doc_window("function_definitions.html"))

        self.set_sample_function_dropdown()
        # self.select_query_sample_button.clicked.connect(self.show_sample_dialog)

    def set_function_dropdown(self):
        # TODO: refactor these dropdowns so they are all combo boxes
        query_methods = [method_name for method_name in dir(self.psychsim_query)
                         if callable(getattr(self.psychsim_query, method_name))
                         and '__' not in method_name]
        pgh.update_toolbutton_list(list=query_methods, button=self.function_button, action_function=self.btnstate,
                                   parent=self)

    def set_sample_function_dropdown(self):
        functions = ["range", "category"]
        self.sample_function_combo.clear()
        self.sample_function_combo.addItems(functions)

    def set_agent_dropdown(self):
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
        pass

    def set_horizon_dropdown(self):
        pass

    def set_state_dropdown(self):
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

    def set_query_sample_var_dropdown(self, current_query):
        vars = current_query.results.columns.to_list()
        self.sample_variable_combo.clear()
        self.sample_variable_combo.addItems(vars)

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
                    #Connect this to setting the action one
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
                #TODO: if a particular combo box is enabled - then make sure it gets populated hireachically (Agent > Action | cycle |horizon)
            else:
                combo.setEnabled(False)

    def reset_params(self):
        self.agent_combo.clear()
        self.action_combo.clear()
        self.cycle_combo.clear()
        self.horizon_combo.clear()
        self.state_combo.clear()
        # Todo: populate combo boxes based on the function that is selected


    def execute_query(self, sim_data_dict):
        query_function = self.function_button.text()
        agent = self.agent_combo.currentText()
        state = self.state_combo.currentText()
        action_step = self.action_combo.currentData() #This is actually the step value as it is easier to access the data by step rather than action
        data_id = self.data_combo.currentText()
        try:
            result = getattr(self.psychsim_query, query_function)(data=sim_data_dict[data_id], data_id=data_id,
                                                                  agent=agent, action=action_step, state=state)
            result = result.apply(pd.to_numeric, errors='ignore') #convert the resulting dataframe to numeric where possible
            self.print_query_output(f"results for {query_function} on {self.data_combo.currentText()}:")
            self.print_query_output(str(result))

            # create query ID
            #TODO: refactor this as create_new() in the query class?
            dt_string, run_date = pgh.get_time_stamp()
            query_id = f"{query_function}_{data_id}_{dt_string}"

            # create a new query object
            new_query = pgh.PsySimQuery(id=query_id, data_id=data_id, params=[], function=query_function,
                                        results=result)

            # create new dialog and show results + query ID
            new_query = self.show_query_dialog(model=PandasModel(result), query=new_query)

            # emit the new query signal
            self.new_query_signal.emit(query_id, new_query)

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

    def get_query_doc(self):
        query_function = self.function_button.text()
        try:
            self.print_query_output(f"{query_function}: {getattr(self.psychsim_query, query_function).__doc__}")
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def view_query(self):
        query_id = self.view_query_combo.currentText()
        self.show_query_signal.emit(query_id)

    def view_diff_query(self):
        query_id = self.new_diff_query_name.text()
        self.show_query_signal.emit(query_id)

    def handle_sample_query_dropdown(self):
        selection = self.sample_query_combo.currentText()
        self.set_query_sample_var_dropdown(self.query_data_dict[selection])

    def print_query_output(self, msg, color="black"):
        pgh.print_output(self.query_output, msg, color)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueryDataPage()
