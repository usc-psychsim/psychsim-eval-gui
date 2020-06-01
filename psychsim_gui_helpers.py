"""
This file has the classes and functions that are common across the gui windows
"""
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from dataclasses import dataclass, asdict, field
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


#todo: fix to base on d1, d2 objects (name, function, etc) rather than d1, d2 results
def print_diff(text_output_obj, d1, d2, diff_name1, diff_name2, diff_type):
    if d1 == d2:
        text_output_obj.append(f"{_green_str('NO DIFF IN')}: {_green_str(diff_type)}")
        text_output_obj.append(f"{diff_name1}: {_green_str(d1)}")
        text_output_obj.append(f"{diff_name2}: {_green_str(d2)}")
    else:
        text_output_obj.append(f"{_red_str('DIFF IN')}: {_red_str(diff_type)}")
        text_output_obj.append(f"{diff_name1}: {_red_str(d1)}")
        text_output_obj.append(f"{diff_name2}: {_red_str(d2)}")


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

if __name__ == "__main__":
    df = pd.DataFrame()
    test_data = PsychSimRun(id="test_id", run_date="date", data=df, sim_file="simfile", steps=9)
    print(asdict(test_data))
