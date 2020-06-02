from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView
import os
import plotly
import traceback
import copy
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go

import psychsim_gui_helpers as pgh

plot_window_file = os.path.join("ui", "plot_window.ui")
ui_plotWindow, QtBaseClass = uic.loadUiType(plot_window_file)

#TODO: REFACTOR
class PlotWindow(QMainWindow, ui_plotWindow):
    def __init__(self, query_data_dict, window_name="New Plot", parent=None):
        super(PlotWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(window_name)
        self.query_data_dict = query_data_dict
        self.setup_plot_widget()
        self.set_type_dropdown()
        self.set_stat_dropdown()
        self.add_plot_button.clicked.connect(self.plot_data)
        self.plot_undo_button.clicked.connect(self.undo)
        self.clear_plot_button.clicked.connect(self.clear_plot)

        self.plot_query.setToolTip('Select the query containing data you wish to plot')
        self.plot_x.setToolTip('Set the variable to be used for the x-axis')
        self.plot_y.setToolTip('Set the variable to be used for the y-axis')
        self.plot_type.setToolTip('Select the plot type')
        self.plot_group.setToolTip('Select the variable to group the data by')
        self.plot_stat.setToolTip('Select the statistic to apply')

        self.current_fig = go.Figure()
        self.current_plot = None
        self.plot_history = dict()

    def set_stat_dropdown(self):
        stats = ["none", "mean", "median"]
        pgh.update_toolbutton_list(list=stats, button=self.plot_stat, action_function=pgh.set_toolbutton_text,
                                   parent=self)

    def set_type_dropdown(self):
        stats = ["Line", "Scatter", "Histogram", "Bar", "Violin"]
        pgh.update_toolbutton_list(list=stats, button=self.plot_type, action_function=pgh.set_toolbutton_text,
                                   parent=self)

    def setup_plot_widget(self):
        # we create an instance of QWebEngineView and set the html code
        self.plot_widget = QWebEngineView()

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.plot_widget)
        self.plot_frame.setLayout(vbox_layout)

    def set_axis_dropdowns(self, action, button):
        # TODO: make sure these are the same types of queries (same function) - refactor with similar code
        selection = action.checkedAction().text()
        print(action.checkedAction().text())
        button.setText(action.checkedAction().text())

        # get the sample / data
        data_key = selection

        # set x and y axis dropdowns
        axis_values = sorted(self.query_data_dict[data_key].results.columns)
        pgh.update_toolbutton_list(list=axis_values, button=self.plot_y, action_function=pgh.set_toolbutton_text,
                                   parent=self)
        pgh.update_toolbutton_list(list=axis_values, button=self.plot_x, action_function=pgh.set_toolbutton_text,
                                   parent=self)
        axis_values.append("none")
        pgh.update_toolbutton_list(list=axis_values, button=self.plot_group, action_function=pgh.set_toolbutton_text,
                                   parent=self)

    def plot_data(self):
        try:
            # get the type of plot ["line", "scatter", "box", "violin"]
            plot_type = self.plot_type.text()

            if self.plot_query.text() in self.query_data_dict.keys():
                data = self.query_data_dict[self.plot_query.text()].results
                print(data.dtypes)

                trace_name = ""

                fig = self.current_fig
                print("adding new figure")

                stat = self.plot_stat.text()
                if self.plot_group.text() not in ["none", "..."]:
                    if stat in ["none", "..."]:
                        for group in data[self.plot_group.text()].unique().tolist():
                            group_data = data[data[self.plot_group.text()] == group]
                            x_data = group_data[self.plot_x.text()].tolist()
                            y_data = group_data[self.plot_y.text()].tolist()
                            name = f"{group}"
                            fig = self.add_trace_to_plot(fig, plot_type, x_data, y_data, name, data=data, x_name=self.plot_x.text(), y_name=self.plot_y.text())
                    else:
                        data = getattr(data.groupby(data[self.plot_x.text()]), stat)()
                        data[self.plot_x.text()] = data.index
                        x_data = data[self.plot_x.text()].to_numpy()
                        y_data = data[self.plot_y.text()].to_numpy()
                        name = f"{self.plot_y.text()}_{stat}"
                        fig = self.add_trace_to_plot(fig, plot_type, x_data, y_data, name, data=data, x_name=self.plot_x.text(), y_name=self.plot_y.text())
                else:
                    if stat not in ["none", "..."]:
                        data = getattr(data.groupby(data[self.plot_x.text()]), stat)()
                        data[self.plot_x.text()] = data.index
                    x_data = data[self.plot_x.text()].to_numpy()
                    y_data = data[self.plot_y.text()].to_numpy()
                    name = f"{self.plot_y.text()}"
                    fig = self.add_trace_to_plot(fig, plot_type, x_data, y_data, name, data=data, x_name=self.plot_x.text(), y_name=self.plot_y.text())

                self.current_fig = fig
                # set the current plot with the current details
                now = datetime.now()
                dt_string = now.strftime("%Y%m%d_%H%M%S")
                self.current_plot = pgh.PsySimPlot(id="current",
                                                   fig=copy.deepcopy(fig),
                                                   title="",
                                                   type=plot_type,
                                                   x_name=self.plot_x.text(),
                                                   y_name=self.plot_y.text())

                # append the plot to the history
                self.plot_history[dt_string] = self.current_plot
                self.add_new_plot(fig=fig, title="", x_name=self.plot_x.text(), y_name=self.plot_y.text())

        except:
            tb = traceback.format_exc()
            print(tb)
            # self.print_sim_output(tb, "red")

    def add_trace_to_plot(self, fig, plot_type, x_data, y_data, name, data=None, x_name="", y_name=""):
        # Group by the group variable
        if plot_type == "Scatter":
            fig.add_trace(getattr(go, plot_type)(x=x_data, y=y_data, mode='markers', name=name))
        elif plot_type == "Line":
            fig.add_trace(getattr(go, plot_type)(x=x_data, y=y_data, mode='lines+markers', name=name))
        elif plot_type == "Histogram":
            # fig.add_trace(getattr(go, plot_type)(x=x_data, y=y_data, name=name))
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


    def add_new_plot(self, fig, title="", x_name="", y_name=""):
        # remove y_axis name if there are more than one trace
        if len(self.plot_history.keys()) > 1:
            y_name=""
        if len(self.plot_history.keys()) >0:
            if list(self.plot_history.values())[-1].type == "Histogram":
                y_name="count"
        # set up layout
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
        # fig.update_yaxes(automargin=True)
        html = '<html><body>'
        html += plotly.offline.plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'
        self.plot_widget.setHtml(html)

        # self.current_fig = fig

    def undo(self):
        try:
            # pop the last key from the dict
            self.plot_history.popitem()

            # clear plot
            self.add_new_plot(fig=go.Figure(),
                              title="",
                              x_name="",
                              y_name="")

            # apply plots in history
            for plot_name, plot_data in self.plot_history.items():
                self.add_new_plot(fig=plot_data.fig,
                                  title=plot_data.title,
                                  x_name=plot_data.x_name,
                                  y_name=plot_data.y_name)

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

    def clear_plot(self):
        self.plot_history = dict()
        self.current_plot = None
        self.current_fig = go.Figure()
        self.add_new_plot(fig=self.current_fig,
                          title="",
                          x_name="",
                          y_name="")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()
    sys.exit(app.exec_())