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


if __name__ == "__main__":
    df = pd.DataFrame()
    test_data = PsychSimRun(id="test_id", run_date="date", data=df, sim_file="simfile", steps=9)
    print(asdict(test_data))
