from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os

dialog_file = os.path.join("ui", "plot_name_taken_dialog.ui")
ui_Dialog, QtBaseClass = uic.loadUiType(dialog_file)


class PlotNameTakenDialog(QDialog, ui_Dialog):
    """
    Dialog to save a plot. Allows to enter a name for the saved plot
    """
    def __init__(self):
        super(PlotNameTakenDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SavePlotDialog()
    window.show()
    sys.exit(app.exec_())
