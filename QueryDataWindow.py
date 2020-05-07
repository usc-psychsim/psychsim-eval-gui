from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys

from query_functions import PsychSimQuery

query_data_file = "query_data.ui"
ui_queryDataView, QtBaseClass = uic.loadUiType(query_data_file)

class QueryDataWindow(QMainWindow, ui_queryDataView):
    def __init__(self):
        super(QueryDataWindow, self).__init__()
        self.setupUi(self)
        self.psychsim_query = PsychSimQuery()
        self.set_function_dropdown()

        self.execute_query_button.clicked.connect(self.execute_query)
        self.data_combo.activated.connect(self.set_agent_dropdown)
        self.data_combo.activated.connect(self.set_action_dropdown)
        self.data = None

    def set_data_dropdown(self, data):
        self.data = data #TODO: FIX SO THERE ISN"T 2 COPIES OF THE DATA IN THE GUI (IN THE MAIN AND HERE)
        #TODO: make this a main set_dropdown function and refactor out the others
        all_items = [self.data_combo.itemText(i) for i in range(self.data_combo.count())]
        new_items = [item for item in data.keys() if item not in all_items]
        self.data_combo.addItems(new_items)

    def set_function_dropdown(self):
        query_methods = [method_name for method_name in dir(self.psychsim_query)
                         if callable(getattr(self.psychsim_query, method_name))
                         and '__' not in method_name]
        self.function_combo.addItems(query_methods)

    def set_agent_dropdown(self):
        #todo: refactor this and other dropdown generation functions
        #TODO: figure out how to set this based on the data set (i.e. remove old ones and add new ones)
        agents = self.data[self.data_combo.currentText()]['agent'].unique()
        all_items = [self.agent_combo.itemText(i) for i in range(self.agent_combo.count())]
        new_items = [item for item in agents if item not in all_items]
        self.agent_combo.addItems(new_items)

    def set_action_dropdown(self):
        actions = self.data[self.data_combo.currentText()]['action'].unique()
        all_items = [self.action_combo.itemText(i) for i in range(self.action_combo.count())]
        new_items = [item for item in actions if item not in all_items]
        self.action_combo.addItems(new_items)

    def execute_query(self):
        query_function = self.function_combo.currentText()
        result = getattr(self.psychsim_query, query_function)()
        print(result)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueryDataWindow()
    window.show()
    sys.exit(app.exec_())
