from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView
import os
import plotly
import traceback
import copy
import plotly.graph_objects as go

import psychsim_gui_helpers as pgh

plot_window_file = os.path.join("ui", "plot_window.ui")
ui_plotWindow, QtBaseClass = uic.loadUiType(plot_window_file)


class PlotWindow(QMainWindow, ui_plotWindow):
    """
    Window to setup, display, and save plots. Contains all functions for plotting including applying plot stats
    """

    def __init__(self, query_data_dict, window_name="New Plot", parent=None):
        super(PlotWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(window_name)
        self.query_data_dict = query_data_dict

        self.setup_plot_widget()
        self.setup_fixed_dropdowns()

        self.add_plot_button.clicked.connect(self.plot_data)
        self.plot_undo_button.clicked.connect(self.undo)
        self.clear_plot_button.clicked.connect(self.reset_plot)
        self.query_combo.activated.connect(self.set_axis_dropdowns)

        self.query_combo.setToolTip('Select the query containing data you wish to plot')
        self.x_combo.setToolTip('Set the variable to be used for the x-axis')
        self.y_combo.setToolTip('Set the variable to be used for the y-axis')
        self.type_combo.setToolTip('Select the plot type')
        self.group_combo.setToolTip('Select the variable to group the data by')
        self.stat_combo.setToolTip('Select the statistic to apply')

        self.current_fig = go.Figure()
        self.current_plot = None
        self.plot_history = dict()

    def setup_plot_widget(self):
        """
        create an instance of QWebEngineView and place it in the window
        """
        self.plot_widget = QWebEngineView()
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.plot_widget)
        self.plot_frame.setLayout(vbox_layout)

    def setup_fixed_dropdowns(self):
        """
        Set the type and stat combo box with fixed options
        """
        pgh.update_combo(self.stat_combo, ["none", "mean", "median"])
        pgh.update_combo(self.type_combo, ["Line", "Scatter", "Histogram", "Bar", "Violin"])

    def set_axis_dropdowns(self):
        """
        Update the relevent dropdowns based on the selected query
        """
        data_key = self.query_combo.currentText()
        axis_values = sorted(self.query_data_dict[data_key].results.index.values)
        pgh.update_combo(self.y_combo, axis_values)
        pgh.update_combo(self.x_combo, axis_values)
        axis_values.insert(0, "none")
        pgh.update_combo(self.group_combo, axis_values)

    def plot_data(self):
        """
        Add the plot to the widget using the user-defined parameters
        """
        try:
            plot_type = self.type_combo.currentText()

            if self.query_combo.currentText() in self.query_data_dict.keys():
                data = self.query_data_dict[self.query_combo.currentText()].results
                fig = self.current_fig
                stat = self.stat_combo.currentText()

                if self.group_combo.currentText() not in ["none"]:
                    if stat in ["none"]:
                        # if there is a group and no stat, loop over the unique elements in the group and add a new trace for each
                        for group in data[self.group_combo.currentText()].unique().tolist():
                            name = f"{group}"
                            group_data = data[data[self.group_combo.currentText()] == group]
                            fig = self.set_figure(data=group_data, fig=fig, plot_type=plot_type, name=name)
                    else:
                        # if there is a group and also a stat groupby the x-axis and apply the stat to that data
                        data = getattr(data.groupby(data[self.x_combo.currentText()]), stat)()
                        data[self.x_combo.currentText()] = data.index
                        name = f"{self.y_combo.currentText()}_{stat}_{self.query_combo.currentText()}"
                        fig = self.set_figure(data, fig, plot_type, name)
                else:
                    if stat not in ["none"]:
                        # if there is no group but a stat
                        data = getattr(data.groupby(data[self.x_combo.currentText()]), stat)()
                        data[self.x_combo.currentText()] = data.index
                    name = f"{self.y_combo.currentText()}_{self.query_combo.currentText()}"
                    fig = self.set_figure(data, fig, plot_type, name)

                self.update_class_plot_info(fig, plot_type)
                self.render_plot_to_gui(fig=fig, title="", x_name=self.x_combo.currentText(),
                                        y_name=self.y_combo.currentText())
        except:
            tb = traceback.format_exc()
            print(tb)

    def set_figure(self, data, fig, plot_type, name):
        """
        Set a new figure based on selections and add it to the plot
        :param data: data to create plot from
        :param fig: current figure to add to
        :param plot_type: type of plot to create (line, bar, histogram, scatter, violin)
        :param name: name of the axis (to be added to the legend)
        :return: newly created figure
        """
        x_data = data.loc[self.x_combo.currentText(), :].tolist()
        y_data = data.loc[self.y_combo.currentText(), :].tolist()
        return self.add_trace_to_plot(fig, plot_type, x_data, y_data, name, data=data,
                                      x_name=self.x_combo.currentText(),
                                      y_name=self.y_combo.currentText())

    def update_class_plot_info(self, fig, plot_type):
        """
        Update the class plot details.
        This includes the dictionary holding current plot history
        Also includes the dictionary holding PsySimPlot objects
        :param fig: current figure to add to
        :param plot_type: type of plot to create (line, bar, histogram, scatter, violin)
        """
        # update current_fig
        self.current_fig = fig

        # set the current plot with the current details
        dt_string, _ = pgh.get_time_stamp()
        self.current_plot = pgh.PsySimPlot(id="current",
                                           fig=copy.deepcopy(fig),
                                           title="",
                                           type=plot_type,
                                           x_name=self.x_combo.currentText(),
                                           y_name=self.y_combo.currentText())

        # append the plot to the history
        self.plot_history[dt_string] = self.current_plot

    def add_trace_to_plot(self, fig, plot_type, x_data, y_data, name, data=None, x_name="", y_name=""):
        """
        Add a plotly trace based on the user selected type
        This uses the plotly graph_object library
        :param fig: current figure to add to
        :param plot_type: type of plot to create (line, bar, histogram, scatter, violin)
        :param x_data: Data to plot on x-axis
        :param y_data: Data to plot on y-axis
        :param name: plot name (to add to plot legend)
        :param data: Data to create pot from (used in violin plot)
        :param x_name: x-axis name
        :param y_name: y-axis name
        :return: figure with added traces
        """
        if plot_type == "Scatter":
            fig.add_trace(getattr(go, plot_type)(x=x_data, y=y_data, mode='markers', name=name))
        elif plot_type == "Line":
            fig.add_trace(getattr(go, plot_type)(x=x_data, y=y_data, mode='lines+markers', name=name))
        elif plot_type == "Histogram":
            fig.add_trace(getattr(go, plot_type)(histfunc="count", y=y_data, x=x_data, name=name))
        elif plot_type == "Bar":
            fig.add_trace(getattr(go, plot_type)(x=x_data, y=y_data, name=name))
        elif plot_type == "Violin":
            for x_unique in data[x_name].unique():
                fig.add_trace(go.Violin(x=data[x_name][data[x_name] == x_unique],
                                        y=data[y_name][data[x_name] == x_unique],
                                        name=f"{x_unique}-{y_name}",
                                        box_visible=True,
                                        meanline_visible=True))
        return fig

    def render_plot_to_gui(self, fig, title="", x_name="", y_name=""):
        """
        Create the html code for the plot to disply on the qwebengine widget
        :param fig: plotly plot to display
        :param title: title of the plot
        :param x_name: x_axis name
        :param y_name: y_axis name
        """
        self.update_y_axis_name(y_name)
        self.setup_plot_layout(fig, title, x_name, y_name)
        html = self.get_fig_as_html(fig)
        self.plot_widget.setHtml(html)

    def update_y_axis_name(self, y_name):
        """
        remove y_axis name if there is more than one trace (in this case the y-axis name is meaningless)
        If the last plot is a histogram, name the y_axis as 'count'
        :return: updated y_name
        """
        if len(self.plot_history.keys()) > 1:
            y_name = ""
        if len(self.plot_history.keys()) > 0:
            if list(self.plot_history.values())[-1].type == "Histogram":
                y_name = "count"
        return y_name

    def setup_plot_layout(self, fig, title, x_name, y_name):
        """
        Update the layout of the figure. This is how the plot is formatted for visualisation
        plotly layout reference: https://plotly.com/python/reference/#layout
        :param fig: plotly plot to display
        :param title: title of the plot
        :param x_name: x_axis name
        :param y_name: y_axis name
        :return: figure with updated layout
        """
        layout = dict(
            margin=dict(
                l=1,
                r=1,
                b=1,
                t=25,
                pad=4
            ),
            showlegend=True,
            title=title,
            xaxis_title=x_name,
            yaxis_title=y_name,
        )
        fig.update_layout(layout)
        return fig

    def get_fig_as_html(self, fig):
        """
        Convert the figure to html
        :param fig: figure containng plot
        :return: figure as html (string)
        """
        html = '<html><body>'
        html += plotly.offline.plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'
        return html

    def undo(self):
        """
        Undo an add trace added by the user.
        """
        try:
            self.plot_history.popitem()  # pop the last key from the dict
            self.clear_plot()
            self.render_plot_history()

            if len(self.plot_history.keys()) > 0:
                self.current_plot = copy.deepcopy(list(self.plot_history.values())[-1])
                self.current_plot.id = "current"
                self.current_fig = self.current_plot.fig
            else:
                self.current_plot = None
                self.current_fig = go.Figure()
        except:
            tb = traceback.format_exc()
            print(tb)

    def render_plot_history(self):
        """
        Cycle through the plot history and apply all plots.
        """
        for plot_name, plot_data in self.plot_history.items():
            self.render_plot_to_gui(fig=plot_data.fig,
                                    title=plot_data.title,
                                    x_name=plot_data.x_name,
                                    y_name=plot_data.y_name)

    def reset_plot(self):
        """
        completely clear the plot and erase the history.
        """
        self.plot_history = dict()
        self.current_plot = None
        self.current_fig = go.Figure()
        self.clear_plot()

    def clear_plot(self):
        """
        Clear the current plot. This will generate an empty figure so the displayed plot is empty.
        """
        self.render_plot_to_gui(fig=go.Figure(),
                                title="",
                                x_name="",
                                y_name="")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()
    sys.exit(app.exec_())
