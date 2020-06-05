from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os
from dataclasses import dataclass, asdict, field

diff_results_window_file = os.path.join("ui", "diff_results_window.ui")
ui_diffResultsWindow, QtBaseClass = uic.loadUiType(diff_results_window_file)


class DiffResultsWindow(QMainWindow, ui_diffResultsWindow):
    def __init__(self, parent=None):
        super(DiffResultsWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Diff Results")

        self.changed_t1_label.setStyleSheet("color: red")
        # self.unique_t1_label.setStyleSheet("background-color : pink")
        self.changed_t2_label.setStyleSheet("color: blue")
        # self.unique_t2_label.setStyleSheet("background-color : lightblue")

    def format_diff_results(self, q1, q2, diff):
        fixed_diff = self.get_diff_as_vector(diff)
        for line_no, line in enumerate(q1):
            line_elements = line.split(',')
            if line_no == 0:
                self.q1_table.setColumnCount(len(line_elements))
                self.q1_table.setHorizontalHeaderLabels(line_elements)

        for line_no, line in enumerate(q2):
            line_elements = line.split(',')
            if line_no == 0:
                self.q2_table.setColumnCount(len(line_elements))
                self.q2_table.setHorizontalHeaderLabels(line_elements)

        for line_no, line in enumerate(diff):
            line_elements = line.split(',')
            if line_no == 0: # set the header with the first line (because queries always have to be the same, there will never be a difference here
                pass
                # self.q1_table.setColumnCount(len(line_elements))
                # self.q1_table.setHorizontalHeaderLabels(line_elements)
                # self.q2_table.setColumnCount(len(line_elements))
                # self.q2_table.setHorizontalHeaderLabels(line_elements)
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
                        # self.q1_table.verticalHeader().setStyleSheet("color: red")#todo: fix this to only edit one item of the header
                    if element_no == 0 and element.startswith("+"):
                        # The row contains an element that is unique to q2
                        # pass the following line_no (containing the change) and formatt the row accordingly
                        self.set_table_row(self.q2_table, line_elements, color="blue")
                        # self.q2_table.verticalHeader().setStyleSheet("color: blue")#todo: fix this to only edit one item of the header

    def set_table_row(self, table, line_items, color="black"):
        #TODO: highlight the specific charachters that are different rather than the whole row
        rowPosition = table.rowCount()
        table.insertRow(rowPosition)
        table.setColumnCount(len(line_items))
        line_items[0] = line_items[0][1:]  # strip the first characther with diff info
        for idx, item in enumerate(line_items):
            cell_item = QTableWidgetItem(item)
            cell_item.setForeground(QColor(color))
            table.setItem(rowPosition, idx, QTableWidgetItem(cell_item))

    def get_diff_as_vector(self, diff):
        #go through the diff results, if a line starts with '?' then separate it based on the lengths of the previous line split
        fixed_diff = []
        for line_idx, line in enumerate(diff):
            if line.startswith('?'):
                #THE QUESTION MARK MEANS THAT THINGS WERE CHANGED, BUT NOT UNIQUE
                prev_line = diff[line_idx-1].split(',')
                line_diff_info = [line[i:i+len(e)] for i, e in enumerate(prev_line)]
                fixed_diff.append(line_diff_info)
            else:
                #NO QUESTION MARK BUT A + or - MEANS THAT THE ITEM IS ONLY IN ONE SIDE
                fixed_diff.append(line.split(','))

        return fixed_diff

        # diff_dict = dict()
        # for line_idx, line in enumerate(diff):
        #     if line.startswith('-'):
        #         #strip the first charachter
        #         line = line[0][1:]
        #         if (next line is possible) and (nextline startswith ?)
        #             line_diff_info = [[i:i+len(e)] for i, e in enumerate(x_split) ]
        #             diff_dict[line_idx] = [DiffCellInfo(info_type="-", data=i, type="changed") for i in line.split(',')]


@dataclass
class DiffCellInfo:
    info_type: str # (+, -, ?)
    data: str # cell information
    type: str # changed, unique, common


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiffResultsWindow()
    window.show()
    sys.exit(app.exec_())
