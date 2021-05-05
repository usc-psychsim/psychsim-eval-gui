from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os

import psychsim_gui_helpers as pgh

from ui.QueryStringSelect import QueryStringSelect

ui_file = os.path.join("ui", "set_param_dialog.ui")
ui_obj, QtBaseClass = uic.loadUiType(ui_file)


class SetParamDialog(QDialog, ui_obj):
    """
    Dialog to ask the user if they are sure about deleting a query
    """
    def __init__(self, data_dict=None, query_dict=None):
        super(SetParamDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.select_query_radio.toggled.connect(self.populate_combo)
        self.select_query_radio.name = "sel_query"
        self.select_data_radio.toggled.connect(self.populate_combo)
        self.select_data_radio.name = "sel_data"
        self.select_string_button.clicked.connect(self.select_string)
        self.select_value_combo.activated.connect(self.update_param_string)

        self.selected_val = "test"

        self.data_dict = data_dict
        self.query_dict = query_dict

    def populate_combo(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.selected_param_value.setText(f"{type(self.selected_val).__name__}: {self.selected_val}")
            if radioButton.name == "sel_data":
                pgh.update_combo(self.select_value_combo, self.data_dict.keys())
                self.update_param_string()
            elif radioButton.name == "sel_query":
                pgh.update_combo(self.select_value_combo, self.query_dict.keys())

    def select_string(self):
        data = None
        if self.select_query_radio.isChecked():
            query_name = self.select_value_combo.currentText()
            if query_name:
                data = self.query_dict[query_name]
        select_string_dialog = QueryStringSelect(data=data)
        result = select_string_dialog.exec_()
        if result:
            param_name = select_string_dialog.selected_string
            self.selected_param_value.setText(f"{type(param_name).__name__}:{param_name}")

    def use_selected(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            # if it is sel_obj then just pass the name of the object (to pass the whole object as a param)
            # if it is sel_str then just pass the string
            self.selected_param_value.setText(f"{type(self.selected_val).__name__}: {self.selected_val}")

    def update_param_string(self):
        # todo: refactor this
        if self.select_data_radio.isChecked():
            param_name = self.sender().currentText()
            self.selected_param_value.setText(f"{type(self.data_dict[param_name]).__name__}:{param_name}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SetParamDialog()
    window.show()
    sys.exit(app.exec_())
