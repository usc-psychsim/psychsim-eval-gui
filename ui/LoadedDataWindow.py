from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import pickle
import os

loaded_data_view_file = os.path.join("ui", "loaded_data_view.ui")
ui_loadedDataView, QtBaseClass = uic.loadUiType(loaded_data_view_file)


class LoadedDataWindow(QMainWindow, ui_loadedDataView):
    """
    Shows a table with stored sim run data.
    Data can be saved, renamed, and loaded from this window
    """
    def __init__(self):
        super(LoadedDataWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("View Data")
        columns = ['date', 'data_id', 'sim_file', 'steps', '', '']
        self.loaded_data_table.setColumnCount(len(columns))
        self.loaded_data_table.setHorizontalHeaderLabels(columns)

    def load_data_from_pickle(self):
        """
        Open dialog to get file name of data to load (pickle files)
        """
        fileName, _ = QFileDialog.getOpenFileName(self,"Select Sim", "","psychsim csv (*.pickle)")
        with open(fileName, 'rb') as f:
            return pickle.load(f)

    def add_row_to_table(self, row):
        """
        Add a row to the data table
        :param row: list of items to add to table
        """
        rowPosition = self.loaded_data_table.rowCount()
        self.loaded_data_table.insertRow(rowPosition)
        index = 0
        for item in row:
            if type(item) == QPushButton:
                self.loaded_data_table.setCellWidget(rowPosition, index, item)
            else:
                self.loaded_data_table.setItem(rowPosition, index, QTableWidgetItem(item))
            index = index + 1

    def clear_table(self):
        self.loaded_data_table.setRowCount(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoadedDataWindow()
    window.show()
    sys.exit(app.exec_())
