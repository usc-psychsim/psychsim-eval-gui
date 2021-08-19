from PyQt5.QtWidgets import *
from PyQt5 import uic

import os
import sys
import copy
import plotly.express as px
import pandas as pd

from ui.PlotWindow import PlotWindow
from ui.SavePlotDialog import SavePlotDialog

import psychsim_gui_helpers as pgh

plot_query_page_file = os.path.join("ui", "plot_query_page.ui")
ui_plotQueryPage, QtBaseClass = uic.loadUiType(plot_query_page_file)


class PlotQueryPage(QWidget, ui_plotQueryPage):
    """
    This class is for all functions relating to the plot page of the GUI
    This includes:
    """

    def __init__(self, query_data_dict, plot_data_dict, parent=None):
        super().__init__(parent)
        self.test_data_dict = dict(iris=px.data.iris().T, wind=px.data.wind().T, gapminder=px.data.gapminder().T)
        self.setupUi(self)
        self.query_data_dict = query_data_dict
        self.plot_data_dict = plot_data_dict

        self.current_plot = None
        self.current_fig = None

        self.create_new_plot_button.clicked.connect(lambda: self.create_new_plot())
        self.test_check.stateChanged.connect(self.setup_test_plot)
        self.plot_listwidget.itemDoubleClicked.connect(self.add_plot_from_list)
        self.remove_plot_button.clicked.connect(self.remove_plot)

    def create_new_plot(self, plot_name="New plot"):
        """
        Create and display a new plot window
        :param plot_name: name to display on the plot window
        :return: the newly created plot window
        """
        plot_window = PlotWindow(query_data_dict=self.query_data_dict, window_name=plot_name, parent=self)
        plot_window.save_plot_button.clicked.connect(lambda: self.save_plot(plot_window.current_plot))
        pgh.update_combo(plot_window.query_combo, self.query_data_dict.keys())
        # emit the query_combo activated signal to populate the other dropdowns when this window opens
        plot_window.query_combo.activated.emit(0)
        plot_window.show()
        return plot_window

    def save_plot(self, plot=None):
        """
        Save the plot and populate the saved plot list
        :param plot: plot to save
        """
        sending_window = self.sender().window()
        if plot:
            new_key, accepted = SavePlotDialog.get_new_name(self.plot_data_dict.keys())
            if accepted:
                self.plot_data_dict[new_key] = copy.deepcopy(plot)
                item = QListWidgetItem(f"{new_key}")
                self.plot_listwidget.addItem(item)
                sending_window.close()

    def setup_test_plot(self):
        """
        Create queries from test data sets to enable test plotting
        """
        # Create test data for testing the plot stat functions
        v1 = "v1"
        v2 = "v2"
        stat_test_data = pd.DataFrame(dict(
            step=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            variable=[v1, v1, v1, v1, v1, v1, v1, v1, v1, v1, v2, v2, v2, v2, v2, v2, v2, v2, v2, v2],
            value=[1, 2, 3, 5, 5, 0, -5, -5, 2, 0, 5, 8, 10, 6, 5, 1, -10, 10, -4, -5]
        )).T
        self.test_data_dict["stat_test"] = stat_test_data

        if self.test_check.isChecked():
            for key, data in self.test_data_dict.items():
                self.query_data_dict[key] = pgh.PsySimQuery(id=key,
                                                            params=[],
                                                            function="test",
                                                            result_type="table",
                                                            results=data)
        elif not self.test_check.isChecked():
            try:
                for key, data in self.test_data_dict.items():
                    self.query_data_dict.pop(key)
            except:
                print("test data not in dict")

    def add_plot_from_list(self, item):
        """
        Create a new plot window and show the saved plot from the list
        :param item: name of plot to open
        """
        if item.text() in self.plot_data_dict.keys():
            selected_plot = self.plot_data_dict[item.text()]
            if selected_plot:
                new_plot = self.create_new_plot(plot_name=item.text())
                new_plot.render_plot_to_gui(fig=selected_plot.fig,
                                            title=selected_plot.title,
                                            x_name=selected_plot.x_name,
                                            y_name=selected_plot.y_name)

    def remove_plot(self):
        """
        Remove a plot from the saved lists and from the plot_data_dict
        """
        try:
            list_items = self.plot_listwidget.selectedItems()
            if not list_items:
                return
            for item in list_items:
                self.plot_listwidget.takeItem(self.plot_listwidget.row(item))
                self.plot_data_dict.pop(item.text())
        except:
            print("plot not in dict")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotQueryPage()
