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
        self.save_query_button.clicked.connect(self.save_query)
        self.saved_queries = dict()
        self.model = None

    def set_pandas_model(self, model):
        self.model = model
        self.raw_data_table.setModel(model)

    def set_query_info(self, query_name="...", funct="...", data_id="...", agent="...", actions="...", sim="..."):
        self.query_name_label.setText(query_name)
        self.data_id_label.setText(data_id)
        self.sim_file_label.setText(sim)
        self.function_label.setText(funct)
        self.agents_label.setText(agent)
        self.actions_label.setText(actions)

    def save_query(self):
        #todo: handle renaming
        new_name = self.query_name_save_input.text()
        if new_name is not None:
            self.query_name_label.setText(new_name)
            self.saved_queries[new_name] = dict(model=self.model,
                                                funct=self.function_label.text(),
                                                data_id=self.data_id_label.text(),
                                                agent=self.agents_label.text(),
                                                sim=self.sim_file_label.text())
            #todo: update the query_data window query lists from here (emit a signal?)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RawDataWindow()
    window.show()
    sys.exit(app.exec_())
