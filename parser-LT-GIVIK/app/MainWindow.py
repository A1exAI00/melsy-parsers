from typing import List, Dict

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QMdiArea,
    QMdiSubWindow,
    QTabWidget,
    QVBoxLayout,
)
from PySide6.QtGui import QAction

from app.MainController import MainController
from app.LT.SubwindowSetup import SubwindowSetup as LTsubwindowSetup
from app.LT.SubwindowResult import SubwindowResult as LTsubwindowResult
from app.LIV.SubwindowSetup import SubwindowSetup as LIVsubwindowSetup
from app.LIV.SubwindowResult import SubwindowResult as LIVsubwindowResult


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
        self.setGeometry(20, 20, 1600, 800)

        self.create_menubar()

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabBar::tab {
                height: 25px;
                width: 120px;
            }
            """
        )
        self.setCentralWidget(self.tab_widget)

        self.add_LIV_tab()
        self.add_LT_tab()
        return

    def create_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Click me!")

        open_LIV_action = QAction("Open LIV tab", self)
        open_LIV_action.triggered.connect(self.add_LIV_tab)
        file_menu.addAction(open_LIV_action)

        open_LT_action = QAction("Open LT tab", self)
        open_LT_action.triggered.connect(self.add_LT_tab)
        file_menu.addAction(open_LT_action)
        return

    def add_LIV_tab(self) -> None:
        mdi = QMdiArea()

        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.addWidget(mdi)

        self.tab_widget.addTab(tab_widget, "LIV")
        self.subwindow_setup = LIVsubwindowSetup(self.controller, mdi)
        return

    def add_LT_tab(self) -> None:
        mdi = QMdiArea()

        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.addWidget(mdi)

        self.tab_widget.addTab(tab_widget, "LT")
        self.subwindow_setup = LTsubwindowSetup(self.controller, mdi)
        return

    def connect_controller(self) -> None:
        self.controller.after_LIV_start_pressed_signal.connect(
            self.after_LIV_start_pressed_slot
        )
        self.controller.after_LT_start_pressed_signal.connect(
            self.after_LT_start_pressed_slot
        )
        self.controller.start_cooldown_release.connect(self.start_cooldown_release_slot)
        return

    def after_LIV_start_pressed_slot(self, _dict) -> None:
        if not self.start_cooldown_active:
            self.start_cooldown_active = True
            self.create_and_append_LIV_result_window(_dict)
        return

    def after_LT_start_pressed_slot(self, _dict) -> None:
        if not self.start_cooldown_active:
            self.start_cooldown_active = True
            self.create_and_append_LT_result_window(_dict)
        return

    def start_cooldown_release_slot(self) -> None:
        self.start_cooldown_active = False

    def create_and_append_LIV_result_window(self, _dict) -> None:
        index = len(self.result_windows)
        current_widget = self.tab_widget.currentWidget()
        if current_widget:
            mdi_area = current_widget.findChild(QMdiArea)
            if mdi_area:
                new_window = LIVsubwindowResult(self.controller, mdi_area, index, _dict)
                self.result_windows.append(new_window)
        return

    def create_and_append_LT_result_window(self, _dict) -> None:
        index = len(self.result_windows)
        current_widget = self.tab_widget.currentWidget()
        if current_widget:
            mdi_area = current_widget.findChild(QMdiArea)
            if mdi_area:
                new_window = LTsubwindowResult(self.controller, mdi_area, index, _dict)
                self.result_windows.append(new_window)
        return
