from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView
import os


plot_view_file = os.path.join("ui", "plot_dialog.ui")
ui_plotView, QtBaseClass = uic.loadUiType(plot_view_file)


class PlotViewDialog(QDialog, ui_plotView):
    def __init__(self):
        super(PlotViewDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.setup_plot_widget()

    def setup_plot_widget(self):
        # we create an instance of QWebEngineView and set the html code
        self.plot_widget = QWebEngineView()

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.plot_widget)
        self.plot_frame.setLayout(vbox_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotViewDialog()
    window.show()
    sys.exit(app.exec_())
