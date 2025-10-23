import sys

from PySide6.QtWidgets import QApplication
import matplotlib as mpl

from app.MainController import MainController
from app.MainWindow import MainWindow

mpl.rcParams["savefig.format"] = "png"  # or 'png', 'svg', 'jpg', 'pdf' etc.


if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = MainController()
    window = MainWindow(controller)
    window.showMaximized()
    sys.exit(app.exec())
