from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys

data_view_file = "data_view.ui"
ui_dataView, QtBaseClass = uic.loadUiType(data_view_file)


class RawDataWindow(QMainWindow, ui_dataView):
    #TODO: is this way better? https://www.codementor.io/@deepaksingh04/design-simple-dialog-using-pyqt5-designer-tool-ajskrd09n
    def __init__(self):
        super(RawDataWindow, self).__init__()
        self.setupUi(self)

    def set_pandas_model(self, model):
        self.raw_data_table.setModel(model)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RawDataWindow()
    window.show()
    sys.exit(app.exec_())
