from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os
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
        self.step_back_button.clicked.connect(self.step_forward)
        self.step_forward_button.clicked.connect(self.step_backward)

        max_steps = self.query.results.shape[1]
        self.no_steps_label.setText(f"Select number of steps to view (max = {max_steps})")
        self.no_steps_spin.setMaximum(max_steps)

    def view_data(self):
        # create a new dataframe with only the variables we want
        step_through_data = self.query.results
        # only select the number of steps
        self.selection_window = (0, self.no_steps_spin.value())
        step_through_data = step_through_data.iloc[:, self.selection_window[0]:self.selection_window[1]]
        # display the data
        model = PandasModel(data=step_through_data)
        self.results_table.setModel(model)

    def step_forward(self):
        # adjust the selection window
        # create a new dataframe with the new selection window
        # display dataframe
        pass

    def step_backward(self):
        pass





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StepThroughResultsWindow()
    window.show()
    sys.exit(app.exec_())
