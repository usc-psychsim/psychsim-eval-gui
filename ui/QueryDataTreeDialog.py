from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os

query_data_view_file = os.path.join("ui", "query_data_dialog_tree.ui")
ui_queryDataView, QtBaseClass = uic.loadUiType(query_data_view_file)


class QueryDataTreeDialog(QDialog, ui_queryDataView):
    """
    Shows the query results in a tree.
    Query data can also be renamed through this window
    """
    def __init__(self, query_data, model):
        super(QueryDataTreeDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.query_data = query_data

        self.query_id_input.returnPressed.connect(self.rename_query)
        self.rename_query_button.clicked.connect(self.rename_query)

        self.query_id_input.setText(query_data.id)

        self.set_pandas_model(model)
        self.model = None

    def set_pandas_model(self, model):
        """
        Set the table model to handle pandas dataframes
        :param model: pandas model to set
        """
        self.model = model
        self.Query_data_tree.setModel(model)

    def rename_query(self):
        self.query_data.id = self.query_id_input.text()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueryDataTreeDialog("this is the old name")
    window.show()
    sys.exit(app.exec_())
