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


class PlotWindow(QMainWindow, ui_plotView):
    def __init__(self):
        super(PlotWindow, self).__init__()
        self.setupUi(self)

        self.plot_button.clicked.connect(self.add_plot)

        self.set_type_dropdown()
        self.set_stat_dropdown()

        self.setup_plot()

    def set_axis_dropdowns(self):
        pass

    def set_stat_dropdown(self):
        stats = ["none", "mean", "median", "count"]
        self.update_toolbutton_list(list=stats, button=self.plot_stat, action_function=self.set_toolbutton_text)

    def set_type_dropdown(self):
        stats = ["line", "scatter", "box", "violin"]
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

    def add_plot(self):
        # some example data
        x = np.arange(1000)
        y = x**2

        # create the plotly figure
        # fig = go.Figure(go.Scatter(x=x, y=y))
        fig = go.Figure(data=go.Bar(y=[2, 3, 1]))

#-----
        df = px.data.iris()
        fig = px.scatter(df, x="sepal_width", y="sepal_length")

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

        # html = plotly.io.to_html(fig)

        # we create an instance of QWebEngineView and set the html code
        # self.plot_widget = QWebEngineView()
        self.plot_widget.setHtml(html)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()
    sys.exit(app.exec_())
