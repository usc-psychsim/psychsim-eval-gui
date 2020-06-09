from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os

from CheckableComboBox import CheckableComboBox


query_sample_range_file = os.path.join("ui", "query_sample_range_dialog.ui")
ui_querySampleRange, QtBaseClass = uic.loadUiType(query_sample_range_file)


class QuerySampleRangeDialog(QDialog, ui_querySampleRange):
    """
    Dialog to select values (between a range) from a variable of a query result to filter the query result
    """
    def __init__(self):
        super(QuerySampleRangeDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.category_combo = CheckableComboBox()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QuerySampleRangeDialog()
    window.show()
    sys.exit(app.exec_())
