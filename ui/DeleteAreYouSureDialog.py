from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView
import os

from CheckableComboBox import CheckableComboBox


delete_are_you_sure_file = os.path.join("ui", "delete_are_you_sure_dialog.ui")
ui_deleteAreYouSure, QtBaseClass = uic.loadUiType(delete_are_you_sure_file)


class DeleteAreYouSure(QDialog, ui_deleteAreYouSure):
    def __init__(self):
        super(DeleteAreYouSure, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DeleteAreYouSure()
    window.show()
    sys.exit(app.exec_())
