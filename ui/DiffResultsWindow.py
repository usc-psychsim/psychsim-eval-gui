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
    def __init__(self, parent=None, stepwise_diff=False):
        super(DiffResultsWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Diff Results")
        self.stepwise_diff = stepwise_diff

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

        diff = []
        #If step selected - do a line by line diff
        if self.stepwise_diff:
            for i, row in enumerate(q1_csv):
                diff = diff + (list(d.compare([row], [q2_csv[i]])))
        else:
            diff = list(d.compare(q1_csv, q2_csv))
        return diff

    def set_table_headers(self, table, horizontal_header_list, vertical_header_list):
        """
        Set the header of a table from the provided csv header
        :param table: table to set headers on
        :param horizontal_header_list: csv header (i.e. first line from csv file)
        :param vertical_header_list: lsit of row names from data
        """
        line_elements = horizontal_header_list.split(',')
        table.setColumnCount(len(line_elements))
        table.setRowCount(len(vertical_header_list))
        table.setHorizontalHeaderLabels(line_elements)
        table.setVerticalHeaderLabels(vertical_header_list)

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
        pass

    def execute_diff(self, q1, q2):
        """
        Execute the diff operation
        :param q1: PsySimQuery to diff
        :param q2: PsySimQuery to diff
        """
        diff = self.get_diff_from_queries(q1, q2)
        rownames = q1.results.index.values
        self.set_table_headers(self.q1_table, diff[0], rownames)
        self.set_table_headers(self.q2_table, diff[0], q2.results.index.values)
        diff.pop(0) #remove the header
        diff_v = self.get_diff_as_vector(diff)
        diff_row_info1, diff_row_info2 = self.get_diff_table_rows(diff_v)
        self.format_diff_tables(self.q1_table, diff_row_info1, "-", "red")
        self.format_diff_tables(self.q2_table, diff_row_info2, "+", "blue")

    def format_diff_tables(self, table, diff_row_info, diff_type, diff_colour):
        """
        Populate the tables with items and colour according to if a difference exists or not
        :param table: table to render diff results to
        :param diff_row_info: dict containing rows to populate table with and the diff info for what has changed
        :param diff_type: '+' or '-' mean that the diff is unique to one table.
        :param diff_colour: colour to colour the cell with if a difference exists
        """
        for row_number, row in enumerate(diff_row_info["rows"]):
            if row[0].startswith(" "):
                self.set_table_row(table, row)
            elif row[0].startswith(diff_type):
                row_diff = diff_row_info["info"][row_number]
                self.set_table_row(table, row, row_diff, color=diff_colour)
                self.set_vertical_header(table, row_number, diff_colour)

    def get_diff_table_rows(self, diff):
        """
        Sort the lines of the diff for a specific table
        :return: lists with elements corresponding to table rows
        """
        diff_rows1 = []
        diff_info1 = []
        diff_rows2 = []
        diff_info2 = []
        for line_no, line in enumerate(diff):
            if line[0].startswith(" "):
                diff_rows1.append(line)
                diff_rows2.append(line)
                diff_info1.append([])
                diff_info2.append([])
            elif line[0].startswith("-"):
                diff_rows1.append(line)
                # if next line exists AND starts with '?' then also append to info list
                if line_no >= 0 and line_no + 1 < len(diff) and diff[line_no + 1][0].startswith("?"): #TODO: CLEAN THIS UP COS IT'S CONFUSING
                    diff_info1.append(diff[line_no + 1])
                elif line_no >= 0 and line_no + 1 < len(diff) and not diff[line_no + 1][0].startswith("?"): #TODO: CLEAN THIS UP COS IT'S CONFUSING
                    diff_info1.append([])
                elif line_no >= 0 and line_no + 1 == len(diff):
                    diff_info1.append([])
            elif line[0].startswith("+"):
                diff_rows2.append(line)
                if line_no >= 0 and line_no + 1 < len(diff) and diff[line_no + 1][0].startswith("?"):
                    diff_info2.append(diff[line_no + 1])
                elif line_no >= 0 and line_no + 1 < len(diff) and not diff[line_no + 1][0].startswith("?"):
                    diff_info2.append([])
                elif line_no >= 0 and line_no + 1 == len(diff):
                    diff_info2.append([])

        return dict(rows=diff_rows1, info=diff_info1), dict(rows=diff_rows2, info=diff_info2)

    def set_table_row(self, table, line, line_diff=None, color="black"):
        """
        For a given csv line, separate the elements and create a table item (cell) for each
        :param line_diff: info about which cells have changed
        :param table: table to populate
        :param line: csv line ifnormation
        :param color: color to render the cell text
        """
        line_items = line  # line.split(',') todo: refactor this (remove)
        row_position = table.rowCount()
        table.insertRow(row_position)
        table.setColumnCount(len(line_items))
        line_items[0] = line_items[0][1:]  # strip the first characther with diff info
        for idx, item in enumerate(line_items):
            cell_item = QTableWidgetItem(item)
            cell_item.setForeground(QColor(color))
            if line_diff and "^" in line_diff[idx]:
                cell_item.setForeground(QColor("black"))
                cell_item.setBackground(QColor(color))
            table.setItem(row_position, idx, QTableWidgetItem(cell_item))

    def get_diff_as_vector(self, diff):
        """

        :param diff:
        :return:
        """
        for line in diff:
            print(line)

        #go through the diff results, if a line starts with '?' then separate it based on the lengths of the previous line split
        fixed_diff = []
        for line_idx, line in enumerate(diff):
            if line.startswith('?'):
                #THE QUESTION MARK MEANS THAT THINGS WERE CHANGED, BUT NOT UNIQUE
                prev_line = re.split(('(,)'), diff[line_idx-1])
                line_diff_info = self._split_str_on_pattern(line, prev_line)
                fixed_diff.append(line_diff_info)
            else:
                #NO QUESTION MARK BUT A + or - MEANS THAT THE ITEM IS ONLY IN ONE SIDE
            #todo: artifically insert a ? row if it doesn't exist (compare each element) IF it starts with a '-' or '+'
                fixed_diff.append(re.split((','), diff[line_idx]))
        return fixed_diff

    def _split_str_on_pattern(self, string_to_split, patterns):
        #TODO: refactor this (maybe it doesn't belong here?)

        # there might also be an easier way to do it like:
        # prev_line = re.split(('(,)'), diff[line_idx - 1]) - but this doesn't move the index
        split_string = []
        idx = 0
        for p in patterns:
            # ignore commas
            if "," not in p:
                split_string.append(string_to_split[idx:idx+len(p)])
            idx = idx + len(p)
        return split_string


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiffResultsWindow()
    window.show()
    sys.exit(app.exec_())
