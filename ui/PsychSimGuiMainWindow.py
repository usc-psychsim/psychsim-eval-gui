from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import os
import pickle
import sys
from functools import partial

import psychsim_gui_helpers as pgh

from ui.SimulationInfoPage import SimulationInfoPage
from ui.QueryDataPage import QueryDataPage
from ui.PlotQueryPage import PlotQueryPage

from ui.LoadedDataWindow import LoadedDataWindow
from ui.RenameDataDialog import RenameDataDialog
from ui.DocWindow import DocWindow

qtCreatorFile = os.path.join("ui", "psychsim-gui-main.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


# TODO: add logging instead of all the print statements in all files
# TODO: remove all functions that aren't used in all files


class PsychSimGuiMainWindow(QMainWindow, Ui_MainWindow):
    """
    This class is responsible for initialising child widgets and windows, and creating connections between signals and
    slots between these Internal signal and slots for each page is maintained by the respective classes
    It also initialises variables for use between each of the sections e.g. for storing data
    """

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.setWindowTitle("PyschSim GUI")

        # SET UP OTHER WINDOWS
        self.loaded_data_window = LoadedDataWindow()
        self.loaded_data_window.pickle_load_data_button.clicked.connect(self.load_data_from_pickle)
        self.doc_window = DocWindow()

        # set up the containers for storing data
        self.sim_data_dict = dict()
        self.query_data_dict = dict()
        self.plot_data_dict = dict()

        # Set up the sim info page
        self.sim_info_page = SimulationInfoPage()
        self.sim_info_page.output_changed_signal.connect(self.update_data_info)
        self.sim_info_page.rename_data_signal.connect(self.rename_data_from_input)

        # Set up the query data page
        self.query_data_page = QueryDataPage(self.sim_data_dict, self.query_data_dict)
        self.query_data_page.func_source = self.sim_info_page.config['PATHS']['function_source']
        self.query_data_page.reload_func_source()
        self.query_data_page.func_source_label.setText(self.sim_info_page.config['PATHS']['function_source'])

        # Set up the plot page
        self.plot_query_page = PlotQueryPage(self.query_data_dict, self.plot_data_dict)

        # Set up the main window stacked widget
        self.main_window_stack_widget.insertWidget(0, self.sim_info_page)
        self.main_window_stack_widget.insertWidget(1, self.query_data_page)
        self.main_window_stack_widget.insertWidget(2, self.plot_query_page)
        self.main_window_stack_widget.setCurrentIndex(0)

        # set up dropdown menus
        self.actionview_data.triggered.connect(self.loaded_data_window.show)
        self.actionrun_sim.triggered.connect(lambda: self.main_window_stack_widget.setCurrentIndex(0))
        self.actionquery.triggered.connect(lambda: self.main_window_stack_widget.setCurrentIndex(1))
        self.actionplot.triggered.connect(lambda: self.main_window_stack_widget.setCurrentIndex(2))
        self.actionmanual.triggered.connect(lambda: self.show_doc_window("index.html"))
        self.actionLoad_config.triggered.connect(self.select_and_load_config)

        # help buttons
        self.sim_info_page.sim_info_button.clicked.connect(
            lambda: self.show_doc_window("manual/simulation_script.html"))
        self.sim_info_page.sim_help_button.clicked.connect(
            lambda: self.show_doc_window("manual/gui_functionality.html", "simulation"))
        self.query_data_page.query_help_button.clicked.connect(
            lambda: self.show_doc_window("manual/gui_functionality.html", "query"))
        self.query_data_page.function_info_button.clicked.connect(
            lambda: self.show_doc_window("manual/function_definitions.html"))
        self.plot_query_page.plot_help_button.clicked.connect(
            lambda: self.show_doc_window("manual/gui_functionality.html", "plot"))

    def update_data_info(self, data_id, data):
        """
        Update data dropdowns over the whole gui
        :param data_id: id of data
        :param data: PsychSimRun object
        """
        self.sim_data_dict[data_id] = data
        # pgh.update_combo(self.query_data_page.data_combo, self.sim_data_dict.keys())
        self.update_data_table()
        self.query_data_page.function_combo.activated.emit(0)

    def select_and_load_config(self):
        """
        Select a config file to load. Load the config file once selected.
        """
        file_name, _ = QFileDialog.getOpenFileName(None, "Select Config File", "", filter="Config files (*.ini)")
        if file_name:
            self.sim_info_page.load_config(path=file_name)

    def update_data_table(self):
        """
        Populate the data window with rows including a button to rename and save
        """
        self.loaded_data_window.clear_table()
        for data_id, data in self.sim_data_dict.items():
            btn = self.create_data_table_button(data_id, "RENAME", self.show_rename_dialog)
            btn2 = self.create_data_table_button(data_id, "save", self.save_data_window)
            new_row = [data.run_date, data.id, data.sim_file, str(data.steps), btn, btn2]
            self.loaded_data_window.add_row_to_table(new_row)

    def create_data_table_button(self, data_id, button_label, button_function):
        """
        Create the button to save data in the data table
        :param data_id: id of data
        :button_label: text to be displayed on the button
        :button_function: function to connect to the button
        :return:
        """
        btn = QPushButton(self.loaded_data_window.loaded_data_table)
        btn.setText(button_label)
        btn.clicked.connect(partial(button_function, data_id))
        return btn

    def save_data_window(self, data_id):
        """
        Show the save data window (when save button in data table is clicked
        :param data_id: id of data to save
        """
        dt_string, _ = pgh.get_time_stamp()
        output_directory = 'sim_output'
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        output_path = os.path.join(output_directory, f"{data_id}_{dt_string}.pickle")
        output_name = QFileDialog.getSaveFileName(self,
                                                  self.tr('Save File'),
                                                  output_path,
                                                  self.tr("pickle (*.pickle)"))[0]
        if output_name:
            if not QFileInfo(output_name).suffix():
                output_name += ".pickle"
            pickle.dump(self.sim_data_dict[data_id], open(output_name, "wb"))
            self.sim_info_page.print_sim_output(f"{data_id} saved to: {output_name}", "black")
            self.update_data_table()

    def load_data_from_pickle(self):
        """
        load previously saved pickle data
        """
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self,
                                                   "Select data file",
                                                   "sim_output",
                                                   "psychsim data (*.pickle)",
                                                   options=options)
        if file_name:
            # load the psychsim libs to read the pickle objects
            self.sim_info_page.load_sim()
            with open(file_name, 'rb') as f:
                data = pickle.load(f)
                if type(data) == pgh.PsychSimRun:
                    self.sim_data_dict[data.id] = data
                    self.update_data_table()
                    # pgh.update_combo(self.query_data_page.data_combo, self.sim_data_dict.keys())
                else:
                    print(f"{file_name} is of type {type(data).__name__} and not a valid psychSim run.")

    def show_rename_dialog(self, old_key):
        """
        Show the rename dialog to rename data
        :param old_key: Old data id
        """
        new_key, accepted = RenameDataDialog.get_new_name(old_name=old_key)
        if accepted:
            self.rename_data_id(new_key, old_key)

    def rename_data_id(self, new_key, old_key):
        """
        Rename data
        :param new_key: new data id
        :param old_key: old data id
        """
        self.sim_data_dict[new_key] = self.sim_data_dict.pop(old_key)
        self.sim_data_dict[new_key].id = new_key
        self.update_data_table()
        self.update_query_dataid(old_key=old_key, new_key=new_key)

    def update_query_dataid(self, old_key, new_key):
        """
        update the data id in the query data dict to match the new key
        :param old_key: old data id
        :param new_key: new data id
        """
        for query_id, query in self.query_data_dict.items():
            if query.data_id == old_key:
                self.query_data_dict[query_id].data_id = new_key

    def rename_data_from_input(self, old_key, new_key):
        """
        Rename data from input on sim info page (just after a sim is run)
        :param old_key: old data id
        :param new_key: new data id
        :return:
        """
        if new_key in self.sim_data_dict.keys():
            self.sim_info_page.print_sim_output(f"{new_key} ALREADY EXISTS", "red")
        else:
            self.rename_data_id(new_key, old_key)
            self.sim_info_page.previous_run_id.setText(new_key)
            self.sim_info_page.print_sim_output(f"{old_key} renamed to {new_key}", "green")

    def show_doc_window(self, doc_file, doc_section=""):
        """
        Show the documentation window (to display the manual)
        :param doc_file:
        :param doc_section:
        :return:
        """
        file_path = os.path.abspath(os.path.join(os.getcwd(), "documentation", "static_html", f"{doc_file}"))
        local_url = QUrl.fromLocalFile(file_path)
        local_url.setFragment(f"{doc_section}")
        doc_window = DocWindow(parent=self)
        doc_window.web_widget.load(local_url)
        doc_window.show()


if __name__ == "__main__":
    sys.argv.append("--disable-web-security")
    app = QApplication(sys.argv)
    window = PsychSimGuiMainWindow()
    window.show()
    sys.exit(app.exec_())
