from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os
import traceback
import pandas as pd

from ui.PandasModel import PandasModel
from ui.CheckableComboBox import CheckableComboBox

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

        # set up the multi-select-combo
        self.variable_combo_mult = CheckableComboBox()
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.variable_combo_mult)
        self.variable_select_widget.setLayout(vbox_layout)
        self.variable_combo_mult.addItems(sorted(query.results.index.values))

        self.query = query
        # self.display_data = self.query.results

        self.selection_window = (0, 1)  # (starting time step, number of time steps to view)

        # connect the buttons
        self.veiw_data_button.clicked.connect(self.view_data)
        self.step_forward_button.clicked.connect(lambda: self.step_through_data(type="forward"))
        self.step_back_button.clicked.connect(lambda: self.step_through_data(type="backward"))
        self.to_end_button.clicked.connect(lambda: self.step_through_data(type="end"))
        self.to_start_button.clicked.connect(lambda: self.step_through_data(type="start"))
        self.no_steps_spin.valueChanged.connect(self.set_no_steps)
        self.no_steps_view_spin.valueChanged.connect(self.set_no_steps_view)

        # set the steps to view and step through
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
        try:
            cat_values = self.variable_combo_mult.currentData()
            display_data = self.query.results.loc[cat_values]

            # only select the number of steps
            self.selection_window = (0, self.no_steps_view)
            display_data = display_data.iloc[:, self.selection_window[0]:self.selection_window[1]]
            # display the data
            model = PandasModel(data=display_data)
            self.results_table.setModel(model)
        except:
            tb = traceback.format_exc()
            print(tb)

    def step_through_data(self, type):
        # todo refactor this with the view_data function
        cat_values = self.variable_combo_mult.currentData()
        display_data = self.query.results.loc[cat_values]
        try:
            # create a new dataframe with the new selection window
            if type == "forward":
                step_start = self.selection_window[0] + self.no_steps
                step_end = self.selection_window[1] + self.no_steps
            elif type == "backward":
                step_start = self.selection_window[0] - self.no_steps
                step_end = self.selection_window[1] - self.no_steps
            elif type == "start":
                step_start = 0
                step_end = 0 + self.no_steps_view
            elif type == "end":
                step_start = display_data.shape[1] - self.no_steps_view
                step_end = display_data.shape[1]




            # deal with viewing the extreme ends (and stopping)
            if step_start < 0:
                step_start = 0
                step_end = 0 + self.no_steps_view
            elif step_end > display_data.shape[1]:
                step_start = display_data.shape[1] - self.no_steps_view
                step_end = display_data.shape[1]

            self.selection_window = (step_start, step_end)

            display_data = display_data.iloc[:, step_start:step_end]

            # display dataframe
            model = PandasModel(data=display_data)
            self.results_table.setModel(model)
        except:
            tb = traceback.format_exc()
            print(tb)





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StepThroughResultsWindow()
    window.show()
    sys.exit(app.exec_())