from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import re
import os
import difflib
from dataclasses import dataclass

diff_results_window_file = os.path.join("ui", "diff_results_window.ui")
ui_diffResultsWindow, QtBaseClass = uic.loadUiType(diff_results_window_file)


class DiffResultsWindow(QMainWindow, ui_diffResultsWindow):
    """
    Window to display diff results as side by side tables. Different rows are highlighted by colour
    """
    def __init__(self, parent=None):
        super(DiffResultsWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Diff Results")

        self.changed_t1_label.setStyleSheet("color: red")
        # self.unique_t1_label.setStyleSheet("background-color : pink")
        self.changed_t2_label.setStyleSheet("color: blue")
        # self.unique_t2_label.setStyleSheet("background-color : lightblue")

    def get_diff_from_queries(self, q1, q2):
        """
        Convert the dataframes of the query results to csv format and diff using difflib
        :param q1: PsySimQuery object to diff
        :param q2: PsySimQuery object to diff
        :return: diff results and csv_headers
        """
        q1_csv = q1.results.to_csv(index=False).splitlines(keepends=False)
        q2_csv = q2.results.to_csv(index=False).splitlines(keepends=False)
        d = difflib.Differ()
        diff = list(d.compare(q1_csv, q2_csv))
        return diff

    def set_table_headers(self, table, header_list):
        """
        Set the header of a table from the provided csv header
        :param table: table to set headers on
        :param header_list: csv header (i.e. first line from csv file)
        """
        line_elements = header_list.split(',')
        table.setColumnCount(len(line_elements))
        table.setHorizontalHeaderLabels(line_elements)

    def set_vertical_header(self, table, line_no, color):
        """
        Set the color of the vertical header (line numbers)
        :param table: table to set color to
        :param line_no: line to set color
        :param color: color to set
        """
        item1 = QTableWidgetItem(str(line_no))
        item1.setBackground(QColor(color))
        table.setVerticalHeaderItem(line_no, item1)

    def execute_diff(self, q1, q2):
        """
        Execute the diff operation
        :param q1: PsySimQuery to diff
        :param q2: PsySimQuery to diff
        """
        diff = self.get_diff_from_queries(q1, q2)
        self.set_table_headers(self.q1_table, diff[0])
        self.set_table_headers(self.q2_table, diff[0])
        diff.pop(0) #remove the header
        diff_rows1, diff_rows2 = self.get_diff_table_rows(diff)
        self.format_diff_tables(self.q1_table, diff_rows1, "-", "red")
        self.format_diff_tables(self.q2_table, diff_rows2, "+", "blue")

    def format_diff_tables(self, table, diff_rows, diff_type, diff_colour):
        """
        Populate the tables with items and colour according to if a difference exists or not
        :param table: table to render diff results to
        :param diff_rows: list containing rows to populate table with
        :param diff_type: '+' or '-' mean that the diff is unique to one table.
        :param diff_colour: colour to colour the cell with if a difference exists
        """
        for row_number, row in enumerate(diff_rows):
            if row.startswith(" "):
                self.set_table_row(table, row)
            elif row.startswith(diff_type):
                self.set_table_row(table, row, color=diff_colour)
                self.set_vertical_header(table, row_number, diff_colour)

    def get_diff_table_rows(self, diff):
        """
        Sort the lines of the diff for a specific table
        :return: lists with elements corresponding to table rows
        """
        diff_rows1 = []
        diff_rows2 = []
        for line_no, line in enumerate(diff):
            if line.startswith(" "):
                diff_rows1.append(line)
                diff_rows2.append(line)
            elif line.startswith("-"):
                diff_rows1.append(line)
            elif line.startswith("+"):
                diff_rows2.append(line)
        return diff_rows1, diff_rows2

    def set_table_row(self, table, line, color="black"):
        """
        For a given csv line, separate the elements and create a table item (cell) for each
        :param table: table to populate
        :param line: csv line ifnormation
        :param color: color to render the cell text
        """
        line_items = line.split(',')
        row_position = table.rowCount()
        table.insertRow(row_position)
        table.setColumnCount(len(line_items))
        line_items[0] = line_items[0][1:]  # strip the first characther with diff info
        for idx, item in enumerate(line_items):
            cell_item = QTableWidgetItem(item)
            cell_item.setForeground(QColor(color))
            table.setItem(row_position, idx, QTableWidgetItem(cell_item))

    def get_diff_as_vector(self, diff):
        # TODO: Fix this function to get information for each cell (the actual text to display, and if it was different from the previous line)
        #  A difference is indicated by a '^', '+', or '-' in the previous line by a line that starts with a '?'
        #  (see difflib documentation https://docs.python.org/3/library/difflib.html)

        #go through the diff results, if a line starts with '?' then separate it based on the lengths of the previous line split
        fixed_diff = []
        for line_idx, line in enumerate(diff):
            if line.startswith('?'):
                #THE QUESTION MARK MEANS THAT THINGS WERE CHANGED, BUT NOT UNIQUE
                prev_line = re.split((','), diff[line_idx-1])
                line_diff_info = [line[i:i+len(e)] for i, e in enumerate(prev_line)]
                fixed_diff.append(line_diff_info)
            else:
                #NO QUESTION MARK BUT A + or - MEANS THAT THE ITEM IS ONLY IN ONE SIDE
                fixed_diff.append(line.split(','))
        return fixed_diff


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiffResultsWindow()
    window.show()
    sys.exit(app.exec_())
