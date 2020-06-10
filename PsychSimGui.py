"""
Run this script to execute the GUI
"""
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from ui.PsychSimGuiMainWindow import PsychSimGuiMainWindow

if __name__ == "__main__":
    sys.argv.append("--disable-web-security")
    app = QApplication(sys.argv)
    window = PsychSimGuiMainWindow()
    window.setWindowIcon(QIcon('icon.png'))
    window.show()
    sys.exit(app.exec_())
