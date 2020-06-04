from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView
import os

from CheckableComboBox import CheckableComboBox


query_sample_category_file = os.path.join("ui", "query_sample_category_dialog.ui")
ui_querySampleCategory, QtBaseClass = uic.loadUiType(query_sample_category_file)


class QuerySampleCategoryDialog(QDialog, ui_querySampleCategory):
    def __init__(self):
        super(QuerySampleCategoryDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.category_combo = CheckableComboBox()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QuerySampleCategoryDialog()
    window.show()
    sys.exit(app.exec_())
