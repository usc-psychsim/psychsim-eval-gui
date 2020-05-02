import sys
from PyQt5 import QtCore, QtGui, QtWidgets,   uic
from data_view import dataView

qtCreatorFile = "psychsim-gui-main.ui"
data_view_file = "data-view.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
ui_dataView, QtBaseClass = uic.loadUiType(qtCreatorFile)


class RawDataWindow(QtWidgets.QMainWindow, ui_dataView):
    #TODO: is this way better? https://www.codementor.io/@deepaksingh04/design-simple-dialog-using-pyqt5-designer-tool-ajskrd09n
    def __init__(self, parent=None):
        super(RawDataWindow, self).__init__(parent)


class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        #SET UP VARS
        self.sim_running = False

        #SET UP BUTTONS
        self.run_sim_button.setEnabled(False)
        self.run_sim_button.clicked.connect(self.run_simulation)
        self.actionSelect_simulation.triggered.connect(self.load_simulation)
        self.select_sim.clicked.connect(self.load_simulation)
        self.actionview_data.triggered.connect(self.show_data_window)

    def load_simulation(self):
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","Python Files (*.py)", options=options)
        if fileName:
            self.sim_path.setText(f"{str(fileName).split('/')[-1]}")
            self.run_sim_button.setEnabled(True)
            print(fileName)

    def run_simulation(self):
        #RUN SIM CODE FROM DASH GUI
        if self.sim_running:
            self.run_sim_button.setText("STOP")
            self.sim_running = False
            self.print_sim_output("SIM RUNNING")
        else:
            self.run_sim_button.setText("RUN")
            self.sim_running = True
            self.print_sim_output("SIM STOPPED")

    def print_sim_output(self, msg):
        self.simulation_output.setText(msg)

    def show_data_window(self):
        self.nd = RawDataWindow(self)
        self.nd.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
