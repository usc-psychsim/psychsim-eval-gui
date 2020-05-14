from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import pandas as pd
from functools import partial
import re
import pickle

loaded_data_view_file = "loaded_data_view.ui"
ui_loadedDataView, QtBaseClass = uic.loadUiType(loaded_data_view_file)

class LoadedDataWindow(QMainWindow, ui_loadedDataView):
    def __init__(self):
        super(LoadedDataWindow, self).__init__()
        self.setupUi(self)
        # self.model = QStandardItemModel()
        # self.loaded_data_table.setModel(self.model)

        # self.loaded_data_table.setRowCount(1)
        columns = ['date', 'data_id', 'sim_file', 'steps', '', '']
        self.loaded_data_table.setColumnCount(len(columns))
        self.loaded_data_table.setHorizontalHeaderLabels(columns)

    def load_data_from_file(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Select Sim", "","psychsim csv (*.pickle)", options=options)
        with open(fileName, 'rb') as f:
            return pickle.load(f)



    def add_row_to_table(self, row):
        rowPosition = self.loaded_data_table.rowCount()
        self.loaded_data_table.insertRow(rowPosition)
        index = 0 #todo: figure out a better way to do this
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
