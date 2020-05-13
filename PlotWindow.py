from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from PyQt5.QtWebEngineWidgets import QWebEngineView
import sys
import numpy as np
import plotly
import plotly.graph_objects as go

import plotly.express as px
import pandas as pd
from functools import partial
import re
import pickle

plot_view_file = "plot_view.ui"
ui_plotView, QtBaseClass = uic.loadUiType(plot_view_file)

#TODO: get data appropriately
#todo: implement add to plot (to add more than one trace from different data)
    #todo:make sure the legent is meaningful
#TODO: implement clear plot function
#todo: implement stats functions


class PlotWindow(QMainWindow, ui_plotView):
    def __init__(self):
        super(PlotWindow, self).__init__()
        self.setupUi(self)

        self.plot_button.clicked.connect(self.plot_data)

        self.set_type_dropdown()
        self.set_stat_dropdown()

        self.setup_plot()

        #TEST DATA
        data_id = "test_data"
        data = px.data.iris()
        self.data_dict = {data_id: data}
        self.set_data_dropdown()

    def set_data_dropdown(self):
        self.update_toolbutton_list(list=self.data_dict.keys(), button=self.plot_query, action_function=self.set_axis_dropdowns)

    def set_axis_dropdowns(self, action, button):
        #TODO: make sure these are the same types of queries (same function)
        selection = action.checkedAction().text()
        print(action.checkedAction().text())
        button.setText(action.checkedAction().text())

        #get the sample / data
        data_key = selection

        #set x and y axis dropdowns
        axis_values = sorted(self.data_dict[data_key])
        self.update_toolbutton_list(list=axis_values, button=self.plot_y, action_function=self.set_toolbutton_text)
        self.update_toolbutton_list(list=axis_values, button=self.plot_x, action_function=self.set_toolbutton_text)

    def set_stat_dropdown(self):
        stats = ["none", "mean", "median", "count"]
        self.update_toolbutton_list(list=stats, button=self.plot_stat, action_function=self.set_toolbutton_text)

    def set_type_dropdown(self):
        stats = ["line", "scatter", "histogram", "violin"]
        self.update_toolbutton_list(list=stats, button=self.plot_type, action_function=self.set_toolbutton_text)

    def update_toolbutton_list(self, button, list, action_function):
        #TODO: refactor this with other versinos of it and put in helper file somewhere
        toolmenu = QMenu(self)
        alignmentGroup = QActionGroup(self)
        actions = list
        for act in actions:
            a = alignmentGroup.addAction(act)
            a.setCheckable(True)
            toolmenu.addAction(a)
        alignmentGroup.triggered.connect(lambda: action_function(alignmentGroup, button))
        button.setMenu(toolmenu)
        button.setPopupMode(QToolButton.InstantPopup)

    def set_toolbutton_text(self, action, button):
        #TODO: make sure these are the same types of queries (same function)
        selection = action.checkedAction().text()
        print(action.checkedAction().text())
        button.setText(action.checkedAction().text())

    def setup_plot(self):
        # we create an instance of QWebEngineView and set the html code
        self.plot_widget = QWebEngineView()

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.plot_widget)
        self.plot_frame.setLayout(vbox_layout)

    def plot_data(self):
        data = self.data_dict[self.plot_query.text()]
        x_axis = self.plot_x.text()
        y_axis = self.plot_y.text()

        #get the stat and do the operation on the data
        stat = self.plot_stat.text()
        if stat == "mean":
            data.groupby(x_axis).mean()
        elif stat == "median":
            pass
        elif stat == "count":
            pass
        elif stat == "none":
            pass

        #get the type of plot ["line", "scatter", "box", "violin"]
        plot_type = self.plot_type.text()
        if plot_type == "scatter":
            self.add_scatter_plot(data=data, x=x_axis, y=y_axis)
        elif plot_type == "line":
            self.add_line_plot(data=data, x=x_axis, y=y_axis)
        elif plot_type == "histogram":
            self.add_histogram_plot(data=data, x=x_axis, y=y_axis)
        elif plot_type == "violin":
            pass

    def add_scatter_plot(self, data, x, y):
        fig = px.scatter(data, x=x, y=y, trendline="ols", color=data.index)
        fig.update_layout(
            margin=dict(
                l=1,
                r=1,
                b=1,
                t=1,
                pad=4
            ),
        )
        # fig.update_yaxes(automargin=True)
        # we create html code of the figure
        html = '<html><body>'
        html += plotly.offline.plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'
        self.plot_widget.setHtml(html)

    def add_line_plot(self, data, x, y):
        fig = px.line(data, x=x, y=y)
        #                       # line_group="country", hover_name="country"))
        # x_axis = data[x].to_numpy()
        # y_axis = data[y].to_numpy()
        # fig = go.Figure(data=go.Scatter(x=x_axis, y=y_axis))
        fig.update_layout(
            margin=dict(
                l=1,
                r=1,
                b=1,
                t=1,
                pad=4
            ),
        )
        html = '<html><body>'
        html += plotly.offline.plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'
        self.plot_widget.setHtml(html)

    def add_histogram_plot(self, data, x, y):
        fig = px.histogram(data, x=x, y=y)
        fig.update_layout(
            margin=dict(
                l=1,
                r=1,
                b=1,
                t=1,
                pad=4
            ),
        )
        html = '<html><body>'
        html += plotly.offline.plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'
        self.plot_widget.setHtml(html)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()
    sys.exit(app.exec_())
