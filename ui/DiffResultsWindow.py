from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os
import pandas as pd
from ui.PandasModel import PandasModel
import traceback

diff_results_window_file = os.path.join("ui", "diff_results_window.ui")
ui_diffResultsWindow, QtBaseClass = uic.loadUiType(diff_results_window_file)


class DiffResultsWindow(QMainWindow, ui_diffResultsWindow):
    """
    Window to display diff results as side by side tables. Different rows are highlighted by colour
    """
    def __init__(self, parent=None, stepwise_diff=False):
        super(DiffResultsWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Diff Results")
        self.stepwise_diff = stepwise_diff

        self.changed_t1_label.setStyleSheet("color: red")
        # self.unique_t1_label.setStyleSheet("background-color : pink")
        self.changed_t2_label.setStyleSheet("color: blue")
        # self.unique_t2_label.setStyleSheet("background-color : lightblue")

    def set_table_headers(self, table, data):
        """
        Set the header of a table from the provided csv header
        :param table: table to set headers on
        :param data: table data
        """
        table.setColumnCount(data.shape[1])
        table.setRowCount(data.shape[0])
        table.setHorizontalHeaderLabels(data.columns)
        table.setVerticalHeaderLabels(data.index.array)

    def execute_diff(self, q1, q2):
        """
        Execute the diff operation
        :param q1: PsySimQuery to diff
        :param q2: PsySimQuery to diff
        """
        diff_rows = []
        index_i = 0
        for index, row_1 in q1.results.iterrows():
            # get the row of the other dataframe
            row_2 = q2.results.iloc[index_i, :]
            # get the difference row (we only really need one because the absolute difference is the same on both sides
            diff_rows.append(row_1 == row_2)
            index_i = index_i +1
        # combine the diff rows to a new dataframe
        diff_output = pd.concat(diff_rows, axis=1, keys=[s.name for s in diff_rows]).T
        # Use the new diff dataframe to format the table (color the cells)
        try:
            model_1 = PandasModel(data=q1.results, diff=diff_output, diff_colour="red")
            model_2 = PandasModel(data=q2.results, diff=diff_output)
            self.q1_table.setModel(model_1)
            self.q2_table.setModel(model_2)
        except:
            tb = traceback.format_exc()
            print(tb, "red")

        # todo: find a way to implement this without it killing the GUI
        # self.q1_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.q2_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiffResultsWindow()
    window.show()
    sys.exit(app.exec_())
