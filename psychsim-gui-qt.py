import sys
from PyQt5 import QtCore, QtGui, QtWidgets,   uic

qtCreatorFile = "psychsim-gui-main.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


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

    def load_simulation(self):
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","Python Files (*.py)", options=options)
        if fileName:
            self.loaded_sim_label.setText(f"Loaded Sim: {str(fileName).split('/')[-1]}")
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
