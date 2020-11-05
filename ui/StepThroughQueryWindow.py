from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os
import traceback
import pandas as pd
from ui.PandasModel import PandasModel

ui_file = os.path.join("ui", "step_through_query_window.ui")
ui_window, QtBaseClass = uic.loadUiType(ui_file)


class StepThroughResultsWindow(QMainWindow, ui_window):
    """
    Window to display diff results as side by side tables. Different rows are highlighted by colour
    """
    def __init__(self, query, parent=None):
        super(StepThroughResultsWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Step Through Results")

        self.query = query
        self.selection_window = (0, 1)  # (starting time step, number of time steps to view)

        self.veiw_data_button.clicked.connect(self.view_data)
        self.step_forward_button.clicked.connect(lambda: self.step_through_data(type="forward"))
        self.step_back_button.clicked.connect(lambda: self.step_through_data(type="backward"))
        self.no_steps_spin.valueChanged.connect(self.set_no_steps)
        self.no_steps_view_spin.valueChanged.connect(self.set_no_steps_view)

        max_steps = self.query.results.shape[1]
        self.no_steps_view_label.setText(f"Select number of steps to view (max = {max_steps})")
        self.no_steps_view_spin.setMinimum(1)
        self.no_steps_view_spin.setMaximum(max_steps)
        self.no_steps_spin.setMinimum(1)
        self.no_steps_spin.setMaximum(max_steps)

        self.no_steps = 1
        self.no_steps_view = 1

    def set_no_steps_view(self):
        self.no_steps_view = self.no_steps_view_spin.value()

    def set_no_steps(self):
        self.no_steps = self.no_steps_spin.value()
        self.step_back_button.setText(f"< Step {self.no_steps} steps back")
        self.step_forward_button.setText(f"Step {self.no_steps} steps forward >")


    def view_data(self):
        step_through_data = self.query.results
        #todo: create a new dataframe with only the variables we want

        # only select the number of steps
        self.selection_window = (0, self.no_steps_view)
        step_through_data = step_through_data.iloc[:, self.selection_window[0]:self.selection_window[1]]
        # display the data
        model = PandasModel(data=step_through_data)
        self.results_table.setModel(model)

    def step_through_data(self, type):
        try:
            step_through_data = self.query.results
            # create a new dataframe with the new selection window
            if type == "forward":
                step_start = self.selection_window[0] + self.no_steps
                step_end = self.selection_window[1] + self.no_steps
            if type == "backward":
                step_start = self.selection_window[0] - self.no_steps
                step_end = self.selection_window[1] - self.no_steps

            # deal with viewing the extreme ends (and stopping)
            if step_start < 0:
                step_start = 0
                step_end = 0 + self.no_steps_view
            elif step_end > step_through_data.shape[1]:
                step_start = step_through_data.shape[1] - self.no_steps_view
                step_end = step_through_data.shape[1]

            self.selection_window = (step_start, step_end)

            step_through_data = step_through_data.iloc[:, step_start:step_end]

            # display dataframe
            model = PandasModel(data=step_through_data)
            self.results_table.setModel(model)
        except:
            tb = traceback.format_exc()
            print(tb)





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StepThroughResultsWindow()
    window.show()
    sys.exit(app.exec_())
