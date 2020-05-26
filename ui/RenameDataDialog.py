from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os

rename_data_view_file = os.path.join("ui", "rename_data_dialog.ui")
ui_renameDataView, QtBaseClass = uic.loadUiType(rename_data_view_file)

class RenameDataDialog(QDialog, ui_renameDataView):
    def __init__(self, old_name):
        super(RenameDataDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.new_name = ""
        self.old_data_name.setText(old_name)

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def get_new_name(old_name="", parent=None):
        dialog = RenameDataDialog(old_name)
        result = dialog.exec_()
        new_name = dialog.new_data_name_lineEdit.text()
        return new_name, result


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RenameDataDialog("this is the old name")
    window.show()
    sys.exit(app.exec_())
