from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os

save_plot_dialog_file = os.path.join("ui", "save_plot_dialog.ui")
ui_savePlotDialog, QtBaseClass = uic.loadUiType(save_plot_dialog_file)

class SavePlotDialog(QDialog, ui_savePlotDialog):
    def __init__(self):
        super(SavePlotDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.new_name = ""

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def get_new_name(old_name="", parent=None):
        dialog = SavePlotDialog()
        result = dialog.exec_()
        new_name = dialog.new_data_name_lineEdit.text()
        return new_name, result


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SavePlotDialog()
    window.show()
    sys.exit(app.exec_())
