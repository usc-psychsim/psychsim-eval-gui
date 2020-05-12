from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
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

        self.set_type_dropdown()
        self.set_stat_dropdown()

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()
    sys.exit(app.exec_())
