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
from app.LT.SubwindowSetup import SubwindowSetup
from app.LT.SubwindowResult import SubwindowResult


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

        self.create_menubar()

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.add_LT_tab()
        return
    
    def create_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&Click me!")
        new_action = QAction("&Open LT", self)
        new_action.triggered.connect(self.add_LT_tab)
        file_menu.addAction(new_action)
        return
    
    def add_LT_tab(self) -> None:
        mdi = QMdiArea()
        # mdi.setViewMode(QMdiArea.TabbedView)

        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.addWidget(mdi)
        
        self.tab_widget.addTab(tab_widget, "LT")
        self.subwindow_setup = SubwindowSetup(self.controller, mdi)

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

    def create_and_append_result_window(self, _dict) -> None:
        index = len(self.result_windows)
        current_widget = self.tab_widget.currentWidget()
        if current_widget:
            mdi_area = current_widget.findChild(QMdiArea)
            if mdi_area:
                new_window = SubwindowResult(self.controller, mdi_area, index, _dict)
                self.result_windows.append(new_window)
        return
