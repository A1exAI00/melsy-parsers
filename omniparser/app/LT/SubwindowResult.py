from typing import List, Dict
from math import isnan
import re

from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMdiArea,
    QMdiSubWindow,
    QPushButton,
)
import clipboard as clip
import numpy as np

from backend.LTdata import LTdata
from app.MainController import MainController
from app.SubController import SubController
from app.SubwindowPlot import SubwindowPlot
from backend.misc import my_float_format


class SubwindowResult(QMdiSubWindow):
    def __init__(
        self, controller: "MainController", mdi: QMdiArea, index: int, _dict: Dict
    ):
        self.controller = controller
        self.sub_controller = SubController()
        self.mdi = mdi
        self.index = index
        self.datas: List[LTdata] = _dict["datas"]
        self.add_naming: bool = _dict["add_naming"]
        self.ndigits: int = _dict["ndigits"]

        self.power_plot_subwindows: List[SubwindowPlot] = []
        self.voltage_plot_subwindows: List[SubwindowPlot] = []
        self.temperature_plot_subwindows: List[SubwindowPlot] = []

        super().__init__()
        self.setup_ui(self.datas)
        return

    def setup_ui(self, datas: List[LTdata]) -> None:
        # Add new subwindow to Mdi Area
        self.setWindowTitle("LT table window")
        self.mdi.addSubWindow(self)

        # Define subwindow layout
        self.setGeometry(3, 3 + 500, 1500, 500)
        table_window_widget = QWidget()
        table_window_layout = QVBoxLayout()
        table_window_widget.setLayout(table_window_layout)
        self.setWidget(table_window_widget)

        # Create "Quick clipboard" and "Show plot" buttons
        box = QHBoxLayout()
        self.quick_clipboard_button = QPushButton("Quick clipboard")
        self.quick_clipboard_button.clicked.connect(self.quick_clipboard_slot)
        box.addWidget(self.quick_clipboard_button)

        self.show_plot_button = QPushButton("Open power(time) plot")
        self.show_plot_button.clicked.connect(
            lambda: self.create_power_plot_window_slot(datas)
        )
        box.addWidget(self.show_plot_button)

        self.show_plot_button = QPushButton("Open voltage(time) plot")
        self.show_plot_button.clicked.connect(
            lambda: self.create_voltage_plot_window_slot(datas)
        )
        box.addWidget(self.show_plot_button)

        self.show_plot_button = QPushButton("Open temperature(time) plot")
        self.show_plot_button.clicked.connect(
            lambda: self.create_temperature_plot_window_slot(datas)
        )
        box.addWidget(self.show_plot_button)

        table_window_layout.addLayout(box)

        N_cols = []
        for data in datas:
            LT = data.LT
            LT_rows = list(LT.values())
            for row in LT_rows:
                N_cols.append(len(row) + 1)
        max_cols = max(N_cols)

        # Create results table
        self.table = QTableWidget()
        self.table.setColumnCount(max_cols)
        self.table.setRowCount(0)
        self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        table_window_layout.addWidget(self.table)

        # Edit table
        for data_i, data in enumerate(datas):
            # Append naming
            if self.add_naming:
                self.append_to_results_table(("Name", data.other_data["Name"]))

            # Append other data
            for name, value in data.other_data.items():
                if name == "Name":
                    continue

                if re.search("frequency", name.lower()):
                    self.append_to_results_table((name, f"{value:.0f} Hz"))
                elif re.search("duration", name.lower()):
                    self.append_to_results_table((name, my_float_format(value, self.ndigits) + " ms"))
                else:
                    self.append_to_results_table((name, value))

            # Append LT data
            for i, (name, values) in enumerate(data.LT.items()):
                self.append_to_results_table(
                    [
                        name,
                    ]
                    + values
                )

            # Append empty row spacer
            if data_i != len(datas) - 1:
                self.add_row_to_results_table()

        self.table.resizeColumnsToContents()
        self.show()
        return

    def add_row_to_results_table(self) -> None:
        new_row_index = self.table.rowCount()
        self.table.setRowCount(self.table.rowCount() + 1)
        for i in range(self.table.columnCount()):
            self.table.setItem(new_row_index, i, QTableWidgetItem())
        return

    def quick_clipboard_slot(self) -> None:
        tmp = []
        for i in range(self.table.rowCount()):
            subtmp = []
            for j in range(self.table.columnCount()):
                value = self.table.item(i, j).text()
                subtmp.append(value)
            tmp.append("\t".join(subtmp))
        clip.copy("\n".join(tmp))
        return

    def append_to_results_table(self, array: List) -> None:
        self.add_row_to_results_table()
        for i, value in enumerate(array):

            # None
            if value is None:
                self.table.item(self.table.rowCount() - 1, i).setText("")
                continue

            # Float
            if isinstance(value, float):
                if np.isnan(value) or isnan(value):
                    self.table.item(self.table.rowCount() - 1, i).setText("NaN")
                else:
                    self.table.item(self.table.rowCount() - 1, i).setText(
                        my_float_format(value, self.ndigits)
                    )
                continue

            # String
            if isinstance(value, str):
                if "nan" == value.lower().strip():
                    self.table.item(self.table.rowCount() - 1, i).setText("NaN")
                else:
                    self.table.item(self.table.rowCount() - 1, i).setText(value)
                continue

        return

    def create_power_plot_window_slot(self, datas: List[LTdata]) -> None:
        new_window = SubwindowPlot(
            self.sub_controller, self.mdi, role="LTpower", datas=datas
        )
        self.power_plot_subwindows.append(new_window)
        return

    def create_voltage_plot_window_slot(self, datas: List[LTdata]) -> None:
        new_window = SubwindowPlot(
            self.sub_controller, self.mdi, role="LTvoltage", datas=datas
        )
        self.voltage_plot_subwindows.append(new_window)
        return

    def create_temperature_plot_window_slot(self, datas: List[LTdata]) -> None:
        new_window = SubwindowPlot(
            self.sub_controller, self.mdi, role="LTtemperature", datas=datas
        )
        self.temperature_plot_subwindows.append(new_window)
        return

    def closeEvent(self, closeEvent):
        all_windows = (
            self.power_plot_subwindows
            + self.voltage_plot_subwindows
            + self.temperature_plot_subwindows
        )
        for window in all_windows:
            window.close()
        self.controller.start_cooldown_release.emit()
        return super().closeEvent(closeEvent)
