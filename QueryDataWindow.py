from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import sys
import inspect
import pandas as pd

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

        self.execute_query_button.clicked.connect(self.execute_query)
        self.function_combo.activated.connect(self.set_dropdowns_for_function)
        self.data_combo.activated.connect(self.set_agent_dropdown)
        self.data_combo.activated.connect(self.set_action_dropdown)
        self.data_combo.activated.connect(self.set_cycle_dropdown)
        self.data = None


        self.data_window = RawDataWindow()

    def set_data_dropdown(self, data):
        self.data = data #TODO: FIX SO THERE ISN"T 2 COPIES OF THE DATA IN THE GUI (IN THE MAIN AND HERE)
        #TODO: make this a main set_dropdown function and refactor out the others
        # all_items = [self.data_combo.itemText(i) for i in range(self.data_combo.count())]
        # new_items = [item for item in data.keys() if item not in all_items]
        self.data_combo.clear()
        new_items = [item for item in data.keys()]
        self.data_combo.addItems(new_items)

    def set_function_dropdown(self):
        query_methods = [method_name for method_name in dir(self.psychsim_query)
                         if callable(getattr(self.psychsim_query, method_name))
                         and '__' not in method_name]
        self.function_combo.addItems(query_methods)

    def set_dropdowns_for_function(self):
        #TODO: make this set the dropdowns based on the arguments in the function (then have to make sure that when clicking execute it only gets the appropriate ones also...
        arglist = inspect.getfullargspec(getattr(self.psychsim_query, self.function_combo.currentText()))
        print(arglist)


    def set_agent_dropdown(self):
        #todo: refactor this and other dropdown generation functions
        #TODO: figure out how to set this based on the data set (i.e. remove old ones and add new ones)
        pass
        # agents = self.data[self.data_combo.currentText()]['agent'].unique()
        # all_items = [self.agent_combo.itemText(i) for i in range(self.agent_combo.count())]
        # new_items = [item for item in agents if item not in all_items]
        # self.agent_combo.addItems(new_items)

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
        query_function = self.function_combo.currentText()
        result = getattr(self.psychsim_query, query_function)(data=self.data)
        self.print_query_output(f"agents in {self.data_combo.currentText()}:")
        if type(result) == dict:
            for agent in result:
                self.print_query_output(f"{agent}")
        elif type(result) == pd.DataFrame:
            key = f"{self.data_combo.currentText()} actions"
            model = PandasModel(result)
            self.data_window.set_pandas_model(model)
            self.data_window.setWindowTitle(f"{key} data")
            self.data_window.show()
            self.print_query_output(str(result))

    def print_query_output(self, msg, color="black"):
        self.query_output.setTextColor(QColor(color))
        self.query_output.append(msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueryDataWindow()
    window.show()
    sys.exit(app.exec_())
