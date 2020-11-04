from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os
import pandas as pd
from ui.PandasModel import PandasModel

ui_file = os.path.join("ui", "step_through_query_window.ui")
ui_window, QtBaseClass = uic.loadUiType(ui_file)


class StepThroughResultsWindow(QMainWindow, ui_window):
    """
    Window to display diff results as side by side tables. Different rows are highlighted by colour
    """
    def __init__(self, parent=None):
        super(StepThroughResultsWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Step Through Results")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StepThroughResultsWindow()
    window.show()
    sys.exit(app.exec_())
