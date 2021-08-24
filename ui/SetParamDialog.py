from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import os
import traceback

import psychsim_gui_helpers as pgh

ui_file = os.path.join("ui", "set_param_dialog.ui")
ui_obj, QtBaseClass = uic.loadUiType(ui_file)


class SetParamDialog(QDialog, ui_obj):
    """
    Dialog to ask the user if they are sure about deleting a query
    TODO:
        refactor this - i think storing the params as names, then getting the params later might be a round about way
    """
    def __init__(self, data_dict=None, query_dict=None):
        super(SetParamDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.select_value_combo.activated.connect(self.get_param)
        self.sel_var_combo.activated.connect(self.get_value_from_variable)
        self.sel_val_combo.activated.connect(self.update_param_name)

        self.selected_val = "test"

        self.data_dict = data_dict
        self.query_dict = query_dict

        self.param_type = None
        self.param_val = None
        self.param_name = None

        self.populate_combo()

    def populate_combo(self):
        self._set_query_interface_enable(True)
        pgh.update_combo(self.select_value_combo, self.query_dict.keys(), clear=True)
        self.select_value_combo.activated.emit(0)

    def _set_query_interface_enable(self, enable):
        self.sel_val_label.setEnabled(enable)
        self.sel_var_label.setEnabled(enable)
        self.sel_val_combo.setEnabled(enable)
        self.sel_var_combo.setEnabled(enable)

    def use_selected(self):
        self.selected_param_value.setText(f"{type(self.selected_val).__name__}: {self.selected_val}")
        self.param_type = type(self.selected_val).__name__
        self.param_val = self.selected_val

    def get_param(self):
        # todo: refactor this
        try:
            param_name = self.sender().currentText()
            if param_name in self.query_dict.keys():
                # populate the sel_var_combo with cols
                variables = self.query_dict[param_name].results.index.values
                pgh.update_combo(self.sel_var_combo, variables, clear=True)
            self.sel_var_combo.activated.emit(0)
        except:
            tb = traceback.format_exc()
            print(tb)

    def update_param_name(self):
        param_name = self.sender().currentText()
        self.selected_param_value.setText(f"{type(param_name).__name__}:{param_name}")
        self.param_type = type(param_name).__name__
        self.param_val = param_name

    def get_value_from_variable(self):
        try:
            if len(self.query_dict) == 0:
                print("There are no queries to select from")
            if len(self.data_dict) == 0:
                print("There are no loaded data objects to select from")
            # populate the sel_var_combo with cols
            variable = self.sel_var_combo.currentText()
            param_name = self.select_value_combo.currentText()
            if param_name in self.query_dict.keys():
                val = self.query_dict[param_name].results.loc[variable, :]
                pgh.update_combo(self.sel_val_combo, val.tolist(), clear=True)
                self.sel_val_combo.activated.emit(0)
        except:
            tb = traceback.format_exc()
            print(tb)

    def set_title(self, function_name, param_name):
        self.setWindowTitle(f"Set \"{param_name}\" param for {function_name}")
        self.function_name_label.setText(f"Function to set: {function_name}")
        self.param_name_label.setText(f"Param to set: {param_name}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SetParamDialog()
    window.show()
    sys.exit(app.exec_())
