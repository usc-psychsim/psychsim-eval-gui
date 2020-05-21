"""
This file has the classes and functions that are common across the gui windows
"""
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from dataclasses import dataclass, asdict
import pandas as pd


@dataclass
class PsychSimRun:
    id: str
    data: object
    sim_file: str
    steps: int
    run_date: str = ""


@dataclass
class PsySimQuery:
    id: str
    data_id: str
    params: list
    function: str
    results: pd.DataFrame

@dataclass
class PsySimPlot:
    id: str
    fig: str
    title: str
    x_name: str
    y_name: str


def get_directory(path_label, caption):
    options = QFileDialog.Options()
    options |= QFileDialog.ShowDirsOnly
    options |= QFileDialog.DontResolveSymlinks
    psychsim_path = QFileDialog.getExistingDirectory(None, caption)
    path_var = f"{str(psychsim_path)}"
    if psychsim_path:
        path_label.setText(path_var)
    return path_var


def get_file_path(path_label, file_type="Python Files (*.py)", parent=None):
    options = QFileDialog.Options()
    # options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(parent, "Select Sim", "", file_type, options=options)
    if fileName:
        path_label.setText(str(fileName).split('/')[-1])
    return fileName


def update_toolbutton_list(button, list, action_function, parent=None):
    toolmenu = QMenu(parent)
    alignmentGroup = QActionGroup(parent)
    actions = list
    for act in actions:
        a = alignmentGroup.addAction(act)
        a.setCheckable(True)
        toolmenu.addAction(a)
    alignmentGroup.triggered.connect(lambda: action_function(alignmentGroup, button))
    button.setMenu(toolmenu)
    button.setPopupMode(QToolButton.InstantPopup)


def set_toolbutton_text(action, button):
    selection = action.checkedAction().text()
    button.setText(selection)


def print_output(text_output_obj, msg, color):
    text_output_obj.setTextColor(QColor(color))
    text_output_obj.append(msg)


def print_debug(psychsim_module, debug, level=0):
    """
    Expand and print the minecraft sim debug dictionary
    :param psychsim_module:
    :param debug: debug dictionary
    :param level:
    :return:
    """
    reg_node = "".join(['│\t' for i in range(level)]) + "├─"
    end_node = "".join(['│\t' for i in range(level)]) + "├─"
    level = level + 1
    if type(debug) == dict:
        for k, v in debug.items():
            print(f"{reg_node} {k}")
            print_debug(v, level)
    elif type(debug) == psychsim_module.VectorDistributionSet:
        for key in debug.keyMap:
            print(f"{end_node} {key}: {str(debug.marginal(key)).split()[-1]}")
    elif type(debug) == psychsim_module.ActionSet:
        for key in debug:
            print(f"{end_node} {key}: ")
    else:
        print(f"{end_node} {debug}")


if __name__ == "__main__":
    df = pd.DataFrame()
    test_data = PsychSimRun(id="test_id", run_date="date", data=df, sim_file="simfile", steps=9)
    print(asdict(test_data))
