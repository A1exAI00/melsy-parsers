from typing import List, Dict
from time import time

from PySide6.QtWidgets import (
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMdiArea,
    QMdiSubWindow,
    QComboBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QLabel,
    QGridLayout,
)
from PySide6.QtGui import QAction

from backend.Data import Data
from app.MainController import MainController
from app.SubwindowSetup import SubwindowSetup
from app.SubwindowResult import SubwindowResult


class MainWindow(QMainWindow):
    def __init__(self, controller: "MainController"):
        super().__init__()
        self.controller = controller
        self.window_title = "melsytech LT parser"
        self.plot_windows: Dict[str, QMdiSubWindow] = {}

        self.start_cooldown_active = False

        self.result_windows = []
        self.setup_ui()
        self.connect_controller()
        return

    def setup_ui(self):
        self.setWindowTitle(self.window_title)
        self.setGeometry(100, 100, 1600, 800)

        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        self.create_menubar()
        return

    def create_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&Click me!")

        new_action = QAction("&Open setup window", self)
        new_action.triggered.connect(self.create_setup_window)
        file_menu.addAction(new_action)
        return

    def connect_controller(self) -> None:
        self.controller.after_start_pressed_signal.connect(
            self.after_start_pressed_slot
        )
        self.controller.start_cooldown_release.connect(
            self.start_cooldown_release_slot
        )
        return

    def after_start_pressed_slot(self, _dict) -> None:
        if not self.start_cooldown_active:
            self.start_cooldown_active = True
            self.create_and_append_result_window(_dict)
        return
    
    def start_cooldown_release_slot(self) -> None:
        self.start_cooldown_active = False

    def create_setup_window(self) -> None:
        self.subwindow_setup = SubwindowSetup(self.controller, self.mdi)
        return

    def create_and_append_result_window(self, _dict) -> None:
        index = len(self.result_windows)
        new_window = SubwindowResult(self.controller, self.mdi, index, _dict)
        self.result_windows.append(new_window)
        return
