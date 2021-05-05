from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import Qt
import sys
import os

from ui.PandasModel import PandasModel

ui_file = os.path.join("ui", "query_string_select.ui")
ui_obj, QtBaseClass = uic.loadUiType(ui_file)


class QueryStringSelect(QDialog, ui_obj):
    """
    Dialog to ask the user if they are sure about deleting a query
    """
    def __init__(self, data=None):
        super(QueryStringSelect, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.close_dialog)
        self.buttonBox.rejected.connect(self.reject)

        self.query_dict = data
        self.type = type
        self.selected_string = ""

        self.label = QLabel()
        self.table = None
        vbox = QVBoxLayout()
        vbox.addWidget(self.label)
        if not data:
            self.label.setText("There is no query selected, or data is checked, cannot select string from data")
            self.label.setAlignment(Qt.AlignCenter)
        else:
            self.label.setText("select the value from the table to use as the param string")
            self.table = QTableView()
            vbox.addWidget(self.table)
            model = PandasModel(data.results)
            self.table.setModel(model)
        vbox.addStretch()
        self.table_frame.setLayout(vbox)

    def close_dialog(self):
        self.selected_string = "test selected"
        if self.table:
            index = self.table.currentIndex()
            self.selected_string = self.table.model().data(index)
        self.accept()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueryStringSelect()
    window.show()
    sys.exit(app.exec_())
