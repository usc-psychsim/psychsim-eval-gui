from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os


delete_are_you_sure_file = os.path.join("ui", "delete_are_you_sure_dialog.ui")
ui_deleteAreYouSure, QtBaseClass = uic.loadUiType(delete_are_you_sure_file)


class DeleteAreYouSure(QDialog, ui_deleteAreYouSure):
    """
    Dialog to ask the user if they are sure about deleting a query
    """
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
