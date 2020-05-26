from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtWebEngineWidgets import QWebEngineView
import sys

doc_window_file = "doc_window.ui"
ui_docWindow, QtBaseClass = uic.loadUiType(doc_window_file)

class DocWindow(QMainWindow, ui_docWindow):
    def __init__(self):
        super(DocWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Manual")
        self.setup_web_engine()

    def setup_web_engine(self):
        # we create an instance of QWebEngineView and set the html code
        self.web_widget = QWebEngineView()
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.web_widget)
        self.doc_frame.setLayout(vbox_layout)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DocWindow()