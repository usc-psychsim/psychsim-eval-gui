"""
This file has the classes and functions that are common across the gui windows
"""
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from dataclasses import dataclass, asdict, field
import pandas as pd
from datetime import datetime


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
    diff_query: bool=False

    def get_steps(self):
        return self.results.index.to_list()

@dataclass
class PsySimPlot:
    id: str
    fig: str
    title: str
    type: str
    x_name: str
    y_name: str


def set_directory(path_label, path_var, caption):
    """
    Set the directory passed in path_var if a directory is selected
    :param path_label: (Qlabel) displays path string on GUI
    :param path_var: (str) class variable to hold the set path
    :param caption: (str) caption to display on path selection dialog
    """
    psychsim_path = QFileDialog.getExistingDirectory(None, caption)
    new_path = f"{str(psychsim_path)}"
    if psychsim_path:
        path_label.setText(new_path)
        path_var = new_path


def get_file_path(path_label, file_type="Python Files (*.py)"):
    """
    Get the path to a file from the native file selection dialog
    :param path_label: (Qlabel) displays path string on GUI
    :param file_type: (str) type of files to be selected
    :return: (str) selected file name
    """
    fileName, _ = QFileDialog.getOpenFileName(None, "Select Sim", "", file_type)
    if fileName:
        path_label.setText(str(fileName).split('/')[-1])
    return fileName


def get_time_stamp():
    """
    get formatted time stamp
    :return: dt_string: nicely formatted string for uniquely identifying data; run_date: nicely formatted date for display purposes
    """
    now = datetime.now()
    dt_string = now.strftime("%Y%m%d_%H%M%S")
    run_date = now.strftime("%Y-%m-%d %H:%M:%S")
    return dt_string, run_date

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


def print_diff(text_output_obj, d1, d2, diff_var):
    """
    Nicely print the difference between two query objects
    :param text_output_obj: qtextarea object to print to
    :param d1: query object to diff
    :param d2: query object to diff
    :param diff_var: member of query object to diff over
    """
    if getattr(d1, diff_var) == getattr(d2, diff_var):
        text_output_obj.append(f"{_green_str('NO DIFF IN')}: {_green_str(diff_var)}")
        text_output_obj.append(f"{d1.id}: {_green_str(getattr(d1, diff_var))}")
        text_output_obj.append(f"{d2.id}: {_green_str(getattr(d2, diff_var))}")
    else:
        text_output_obj.append(f"{_red_str('DIFF IN')}: {_red_str(diff_var)}")
        text_output_obj.append(f"{d1.id}: {_red_str(getattr(d1, diff_var))}")
        text_output_obj.append(f"{d2.id}: {_red_str(getattr(d2, diff_var))}")


#Todo: fix these output functinos for a more generic formatting
def set_toolbutton_text(action, button):
    selection = action.checkedAction().text()
    button.setText(selection)


def print_output(text_output_obj, msg, color):
    text_output_obj.setTextColor(QColor(color))
    text_output_obj.append(msg)


def _green_str(s):
    return f'<span style=\" color: #008000;\">{s}</span>'


def _red_str(s):
    return f'<span style=\" color: #ff0000;\">{s}</span>'


def _black_str(s):
    return f'<span style=\" color: #000000;\">{s}</span>'


def _blue_str(s):
    return f'<span style=\" color: #0000ff ;\">{s}</span>'


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


def dataframe_difference(df1, df2, which=None):
    """Find rows which are different between two DataFrames."""
    comparison_df = df1.merge(df2,
                              indicator=True,
                              how='outer')
    if which is None:
        diff_df = comparison_df[comparison_df['_merge'] != 'both']
    else:
        diff_df = comparison_df[comparison_df['_merge'] == which]
    return diff_df

def dataframe_columns_equal(df1, df2):
    for col in df1.columns:
        if col not in df2.columns:
            return False
        else:
            return True

if __name__ == "__main__":
    df = pd.DataFrame()
    test_data = PsychSimRun(id="test_id", run_date="date", data=df, sim_file="simfile", steps=9)
    print(asdict(test_data))
