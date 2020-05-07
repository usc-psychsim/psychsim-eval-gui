from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys

sample_data_file = "sample_data.ui"
ui_sampleDataView, QtBaseClass = uic.loadUiType(sample_data_file)


class SampleDataWindow(QMainWindow, ui_sampleDataView):
    def __init__(self):
        super(SampleDataWindow, self).__init__()
        self.setupUi(self)

    def sample_data(self):
        pass

    def update_sample_table(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SampleDataWindow()
    window.show()
    sys.exit(app.exec_())
