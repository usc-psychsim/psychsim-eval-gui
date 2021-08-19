"""
This file has the classes and functions that are common across the gui windows
"""
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from dataclasses import dataclass, asdict
import pandas as pd
from datetime import datetime


@dataclass
class PsychSimRun:
    """
    Class to hold information for each psychsim run
    """
    id: str
    data: object
    sim_file: str
    steps: int
    run_date: str = ""


@dataclass
class PsySimQuery:
    """
    Class to hold information for each query that is created
    """
    id: str
    # data_id: str
    params: list
    function: str
    results: pd.DataFrame
    result_type: str
    diff_query: bool = False

    def get_steps(self):
        return self.results.index.to_list()


@dataclass
class PsySimPlot:
    """
    Class to hold information for each plot
    """
    id: str
    fig: str
    title: str
    type: str
    x_name: str
    y_name: str


def get_file_path(path_label, file_type="Python Files (*.py)", default_dir=""):
    """
    Get the path to a file from the native file selection dialog
    :param path_label: (Qlabel) displays path string on GUI
    :param file_type: (str) type of files to be selected
    :param default_dir: (str) directory to open as default
    :return: (str) selected file name
    """
    file_name, _ = QFileDialog.getOpenFileName(None, "Select Sim", default_dir, file_type)
    if file_name:
        path_label.setText(str(file_name).split('/')[-1])
    return file_name


def get_time_stamp():
    """
    get formatted time stamp
    :return: dt_string: nicely formatted string for uniquely identifying data; run_date: nicely formatted date for
             display purposes
    """
    now = datetime.now()
    dt_string = now.strftime("%Y%m%d_%H%M%S")
    run_date = now.strftime("%Y-%m-%d %H:%M:%S")
    return dt_string, run_date


def print_diff(text_output_obj, d1, d2, diff_var):
    """
    Nicely print the difference between two query objects
    :param text_output_obj: qtextarea object to print to
    :param d1: query object to diff
    :param d2: query object to diff
    :param diff_var: member of query object to diff over
    """
    if getattr(d1, diff_var) == getattr(d2, diff_var):
        text_output_obj.append(f"{green_str('NO DIFF IN')}: {green_str(diff_var)}")
        text_output_obj.append(f"{d1.id}: {green_str(getattr(d1, diff_var))}")
        text_output_obj.append(f"{d2.id}: {green_str(getattr(d2, diff_var))}")
    else:
        text_output_obj.append(f"{red_str('DIFF IN')}: {red_str(diff_var)}")
        text_output_obj.append(f"{d1.id}: {red_str(getattr(d1, diff_var))}")
        text_output_obj.append(f"{d2.id}: {red_str(getattr(d2, diff_var))}")


def print_output(text_output_obj, msg, color):
    text_output_obj.setTextColor(QColor(color))
    text_output_obj.append(msg)


def green_str(s):
    return f'<span style=\" color: #008000;\">{s}</span>'


def red_str(s):
    return f'<span style=\" color: #ff0000;\">{s}</span>'


def black_str(s):
    return f'<span style=\" color: #000000;\">{s}</span>'


def blue_str(s):
    return f'<span style=\" color: #0000ff ;\">{s}</span>'


def print_debug(psychsim_module, debug, level=0):
    """
    Expand and print the search and rescue sim debug dictionary
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


def dataframe_columns_equal(df1, df2):
    """
    Check if dataframe columns are the same length, and also contain the same elements
    :param df1: pandas dataframe
    :param df2: pandas dataframe
    :return: bool
    """
    if len(df1.columns) != len(df2.columns):
        return False
    for col in df1.columns:
        if col not in df2.columns:
            return False
        else:
            return True


def update_combo(combo_box, item_list, clear=False):
    """
    Generic combo box update function
    :param combo_box: qcomboBox to be updated
    :param item_list: list data to populate the combo box with
    :param clear: flag to clear the combo before repopulating
    :return:
    """
    all_items = []
    if clear:
        combo_box.clear()
    else:
        all_items = [combo_box.itemText(i) for i in range(combo_box.count())]
    new_items = [str(item) for item in item_list if item not in all_items]
    combo_box.addItems(new_items)
    dropdown_view = combo_box.view()
    dropdown_view.setMinimumWidth(dropdown_view.sizeHintForColumn(0))

def save_query_pickle(query, output_directory="sim_output"):
    """
    Pickle a query and write it to file
    query: PsySimQuery query
    output_directory: directory to save the file
    """
    dt_string, _ = pgh.get_time_stamp()
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    output_path = os.path.join(output_directory, f"{query.id}_{dt_string}.pickle")
    pickle.dump(query, open(output_path, "wb"))
    print(f"{query.id} saved to: {output_path}")


if __name__ == "__main__":
    df = pd.DataFrame()
    test_data = PsychSimRun(id="test_id", run_date="date", data=df, sim_file="simfile", steps=9)
    print(asdict(test_data))


def set_table_headers(table, data):
    """
    Set the header of a table from the provided csv header
    :param table: table to set headers on
    :param data: table data
    """
    table.setColumnCount(data.shape[1])
    table.setRowCount(data.shape[0])
    table.setHorizontalHeaderLabels(data.columns)
    table.setVerticalHeaderLabels(data.index.array)

def create_plot_test_data():
    """
    Generate some test data for checking the plot functionality.
    """
    v1 = ["v1"] * 10
    v1_data = [1, 2, 3, 5, 5, 0, -5, -5, 2, 0]
    v_type = ["V"] * 10
    v2 = ["v2"] * 10
    v2_data = [5, 8, 10, 6, 5, 1, -10, 10, -4, -5]
    r1 = ["r1"] * 10
    r1_data = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    r_type = ["R"] * 10
    step_data = [x for x in range(10)]
    stat_test_data = pd.DataFrame(dict(
        step=step_data * 3,
        variable=v1 + v2 + r1,
        value=v1_data + v2_data + r1_data,
        type= v_type + v_type + r_type
    )).T
    return stat_test_data