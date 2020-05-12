from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import sys
import inspect
import pandas as pd
import traceback

from query_functions import PsychSimQuery
from DataViewWindow import RawDataWindow


from PandasModel import PandasModel

query_data_file = "query_data.ui"
ui_queryDataView, QtBaseClass = uic.loadUiType(query_data_file)

class QueryDataWindow(QMainWindow, ui_queryDataView):
    def __init__(self):
        super(QueryDataWindow, self).__init__()
        self.setupUi(self)
        self.psychsim_query = PsychSimQuery()
        self.set_function_dropdown()

        #set windows
        self.data_window = RawDataWindow()

        #set buttons
        self.execute_query_button.clicked.connect(self.execute_query)
        self.diff_query_button.clicked.connect(self.diff_query)
        self.data_combo.activated.connect(self.set_agent_dropdown)
        self.data_combo.activated.connect(self.set_action_dropdown)
        self.data_combo.activated.connect(self.set_cycle_dropdown)
        self.main_tab.currentChanged.connect(self.update_query_lists)
        self.data = None

        self.current_query_function = ""



    def set_data_dropdown(self, data):
        self.data = data #TODO: FIX SO THERE ISN"T 2 COPIES OF THE DATA IN THE GUI (IN THE MAIN AND HERE)
        #TODO: make this a main set_dropdown function and refactor out the others
        # all_items = [self.data_combo.itemText(i) for i in range(self.data_combo.count())]
        # new_items = [item for item in data.keys() if item not in all_items]
        self.data_combo.clear()
        new_items = [item for item in data.keys()]
        self.data_combo.addItems(new_items)

    def set_function_dropdown(self):
        #set as list
        query_methods = [method_name for method_name in dir(self.psychsim_query)
                         if callable(getattr(self.psychsim_query, method_name))
                         and '__' not in method_name]
        self.update_toolbutton_list(list=query_methods, button=self.function_button, action_function=self.btnstate)


    def btnstate(self, action, button):
        selection = action.checkedAction().text()
        if button == self.function_button:
            self.current_query_function = selection
        print(action.checkedAction().text())
        button.setText(action.checkedAction().text())
        #TODO: make this conditional functionality smarter
        if selection == "get_actions":
            self.set_agent_dropdown()

    def set_dropdowns_for_function(self):
        #TODO: make this set the dropdowns based on the arguments in the function (then have to make sure that when clicking execute it only gets the appropriate ones also...
        arglist = inspect.getfullargspec(getattr(self.psychsim_query, self.function_combo.currentText()))
        print(arglist)


    def set_agent_dropdown(self):
        #todo: refactor this and other dropdown generation functions
        #TODO: figure out how to set this based on the data set (i.e. remove old ones and add new ones)
        data_id = self.data_combo.currentText()
        agents = self.psychsim_query.get_agents(data=self.data, data_id=data_id)
        self.agent_combo.clear()
        self.agent_combo.addItems(agents)

    def set_action_dropdown(self):
        pass
        # actions = self.data[self.data_combo.currentText()]['action'].unique()
        # all_items = [self.action_combo.itemText(i) for i in range(self.action_combo.count())]
        # new_items = [item for item in actions if item not in all_items]
        # self.action_combo.addItems(new_items)

    def set_cycle_dropdown(self):
        #TODO: add ability to set range here (if needed?)
        self.cycle_combo.clear()
        steps = self.data.keys()
        self.cycle_combo.addItems(steps)

    def execute_query(self):
        # query_function = self.function_combo.currentText()
        query_function = self.current_query_function
        agent = self.agent_combo.currentText()
        data_id = self.data_combo.currentText()
        try:
            result = getattr(self.psychsim_query, query_function)(data=self.data, data_id=data_id, agent=agent)
            self.print_query_output(f"agents in {self.data_combo.currentText()}:")
            if type(result) == dict:
                for agent in result:
                    self.print_query_output(f"{agent}")
            elif type(result) == pd.DataFrame:
                key = f"{self.data_combo.currentText()} actions"
                model = PandasModel(result)
                self.data_window.set_pandas_model(model)
                self.data_window.query_name_save_input.setText("")
                self.data_window.setWindowTitle(f"{key} data")
                self.data_window.set_query_info(funct=query_function, data_id=data_id, agent=agent)
                self.data_window.show()
                self.print_query_output(str(result))
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")

    def update_query_lists(self):
        query_list = [method_name for method_name in self.data_window.saved_queries.keys()]
        self.update_toolbutton_list(list=query_list, button=self.view_query_list, action_function=self.show_query)
        self.update_toolbutton_list(list=query_list, button=self.query_diff_1, action_function=self.set_toolbutton_text)
        self.update_toolbutton_list(list=query_list, button=self.query_diff_2, action_function=self.set_toolbutton_text)

    def update_toolbutton_list(self, button, list, action_function):
        toolmenu = QMenu(self)
        alignmentGroup = QActionGroup(self)
        actions = list
        for act in actions:
            a = alignmentGroup.addAction(act)
            a.setCheckable(True)
            toolmenu.addAction(a)
        alignmentGroup.triggered.connect(lambda: action_function(alignmentGroup, button))
        button.setMenu(toolmenu)
        button.setPopupMode(QToolButton.InstantPopup)

    def show_query(self, action, button):
    #TODO: refactor this with btnstate and diff_query (maybe think of a better way to do this..)
        selection = action.checkedAction().text()
        print(action.checkedAction().text())
        button.setText(action.checkedAction().text())

        current_query = self.data_window.saved_queries[selection] #TODO: maybe this isn't in the right place (the dict)model=self.model, and possibly make the whole query a separate class

        #TODO: this code is copied (refactor)
        self.data_window.set_pandas_model(current_query['model'])
        self.data_window.setWindowTitle(f"{selection} data")

        #TODO: <BUG> if we rename the data - we don't get the new name...
        self.data_window.set_query_info(query_name=selection, funct=current_query['funct'], data_id=current_query['data_id'], agent=current_query['agent']) #TODO: maybe better to pass the key to the dict/
        self.data_window.show()

    def set_toolbutton_text(self, action, button):
        #TODO: make sure these are the same types of queries (same function)
        selection = action.checkedAction().text()
        print(action.checkedAction().text())
        button.setText(action.checkedAction().text())

    def diff_query(self):
        #get the two queries
        try:
            q1 = self.data_window.saved_queries[self.query_diff_1.text()]
            q2 = self.data_window.saved_queries[self.query_diff_2.text()]

            #check that they are the same type
            if q1['funct'] == q2['funct']:
                #diff the results
                self.print_query_output(f"DIFFING: {q1['query_name']} and {q2['query_name']}", 'green')
            else:
                self.print_query_output("YOU CAN ONLY DIFF FUNCTIONS OF THE SAME TYPE", 'red')
                self.print_query_output(f"{q1['query_name']} = {q1['funct']}, {q2['query_name']} = {q2['funct']}", 'red')
        except:
            tb = traceback.format_exc()
            self.print_query_output(tb, "red")


    def print_query_output(self, msg, color="black"):
        self.query_output.setTextColor(QColor(color))
        self.query_output.append(msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueryDataWindow()
    window.show()
    sys.exit(app.exec_())
