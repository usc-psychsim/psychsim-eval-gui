from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os

from ui.CheckableComboBox import CheckableComboBox


query_sample_category_file = os.path.join("ui", "query_sample_category_dialog.ui")
ui_querySampleCategory, QtBaseClass = uic.loadUiType(query_sample_category_file)


class QuerySampleCategoryDialog(QDialog, ui_querySampleCategory):
    """
    Dialog to select values (as categories) from a variable of a query result to filter the query result
    """
    def __init__(self):
        super(QuerySampleCategoryDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.sample_combo_mult = CheckableComboBox()
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.sample_combo_mult)
        self.multi_select_widget.setLayout(vbox_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QuerySampleCategoryDialog()
    window.show()
    sys.exit(app.exec_())
