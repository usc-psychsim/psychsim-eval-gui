from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os

diff_results_window_file = os.path.join("ui", "diff_results_window.ui")
ui_diffResultsWindow, QtBaseClass = uic.loadUiType(diff_results_window_file)


class DiffResultsWindow(QMainWindow, ui_diffResultsWindow):
    def __init__(self, parent=None):
        super(DiffResultsWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Diff Results")

    def format_diff_results(self, q1, q2, diff):
        for line_no, line in enumerate(diff):
            line_elements = line.split(',')
            if line_no == 0: # set the header with the first line (because queries always have to be the same, there will never be a difference here
                self.q1_table.setColumnCount(len(line_elements))
                self.q1_table.setHorizontalHeaderLabels(line_elements)
                self.q2_table.setColumnCount(len(line_elements))
                self.q2_table.setHorizontalHeaderLabels(line_elements)
            else:
                for element_no, element in enumerate(line_elements):
                    if element_no == 0 and element.startswith(" "):
                        # The row is common in both frames, put the element in both and colour it black
                        self.set_table_row(self.q1_table, line_elements)
                        self.set_table_row(self.q2_table, line_elements)
                    if element_no == 0 and element.startswith("-"):
                        # The row contains an element that is unique to q1
                        # pass the following line_no (containing the change) and formatt the row accordingly
                        self.set_table_row(self.q1_table, line_elements, color="red")
                    if element_no == 0 and element.startswith("+"):
                        # The row contains an element that is unique to q2
                        # pass the following line_no (containing the change) and formatt the row accordingly
                        self.set_table_row(self.q2_table, line_elements, color="blue")

    def set_table_row(self, table, line_items, color="black"):
        #TODO: highlight the specific charachters that are different rather than the whole row
        rowPosition = table.rowCount()
        table.insertRow(rowPosition)
        table.setColumnCount(len(line_items))
        line_items[0][1:]  # strip the first characther with diff info
        for idx, item in enumerate(line_items):
            cell_item = QTableWidgetItem(item)
            cell_item.setForeground(QColor(color))
            table.setItem(rowPosition, idx, QTableWidgetItem(cell_item))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiffResultsWindow()
    window.show()
    sys.exit(app.exec_())
