from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os

from ui.PlotNameTakenDialog import PlotNameTakenDialog

save_plot_dialog_file = os.path.join("ui", "save_plot_dialog.ui")
ui_savePlotDialog, QtBaseClass = uic.loadUiType(save_plot_dialog_file)


class SavePlotDialog(QDialog, ui_savePlotDialog):
    """
    Dialog to save a plot. Allows to enter a name for the saved plot
    """
    def __init__(self, plot_keys=None):
        super(SavePlotDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.new_name = ""
        self.plot_keys = plot_keys

    @staticmethod
    def get_new_name(plot_keys=None):
        """
        static method to get the name for the saved plot from the user input
        :return: the new name as a string. result as a bool (True if OK clicked, False if Cancel)
        """
        dialog = SavePlotDialog(plot_keys)
        good_name = False
        while not good_name:
            result = dialog.exec_()
            new_name = dialog.new_data_name_lineEdit.text()
            if plot_keys and new_name in plot_keys:
                # plot name exists - display dialog to alert user
                name_taken_dialog = PlotNameTakenDialog()
                name_taken_dialog.name_taken_label.setText(f"{new_name} already taken. Enter different name")
                name_taken_dialog.exec_()
            elif new_name not in plot_keys:
                good_name = True
        return new_name, result


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SavePlotDialog()
    window.show()
    sys.exit(app.exec_())
