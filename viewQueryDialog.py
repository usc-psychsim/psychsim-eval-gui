from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys

view_data_view_file = "query_data_dialog.ui"
ui_viewDataView, QtBaseClass = uic.loadUiType(view_data_view_file)

class ViewQueryDialog(QDialog, ui_viewDataView):
    def __init__(self, model):
        super(ViewQueryDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.model = model

    @staticmethod
    def set_model(model, parent=None):
    #todo: add stuff here to view query results
        dialog = ViewQueryDialog(model)
        result = dialog.exec_()
        return result


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ViewQueryDialog("this is the old name")
    window.show()
    sys.exit(app.exec_())
