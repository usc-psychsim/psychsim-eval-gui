import sys
from PyQt5.QtWidgets import *
from ui.PsychSimGuiMainWindow import PsychSimGuiMainWindow

if __name__ == "__main__":
    sys.argv.append("--disable-web-security")
    app = QApplication(sys.argv)
    window = PsychSimGuiMainWindow()
    window.show()
    sys.exit(app.exec_())
