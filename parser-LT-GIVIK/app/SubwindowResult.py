from typing import List, Dict

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

from backend.Data import Data
from app.MainController import MainController
from app.SubController import SubController
from app.SubwindowPlot import SubwindowPlot


class SubwindowResult(QMdiSubWindow):
    def __init__(
        self, controller: "MainController", mdi: QMdiArea, index: int, _dict: Dict
    ):
        self.controller = controller
        self.sub_controller = SubController()
        self.mdi = mdi
        self.index = index
        self.datas = _dict["datas"]
        self.add_naming = _dict["add_naming"]

        self.power_plot_subwindows: List[SubwindowPlot] = []
        self.voltage_plot_subwindows: List[SubwindowPlot] = []
        self.temperature_plot_subwindows: List[SubwindowPlot] = []

        super().__init__()
        self.setup_ui(self.datas)
        return

    def setup_ui(self, datas: List[Data]) -> None:
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
        table_window_layout.addWidget(self.table)

        # Edit table
        for data_i, data in enumerate(datas):
            # Append additional data
            if self.add_naming:
                self.append_to_results_table(data.get_naming())
            for name, value in zip(
                data.additional_data_names, data.additional_data_values
            ):
                self.append_to_results_table((name, value))

            # Append LT data
            for i, (name, values) in enumerate(data.LT.items()):
                curr_line = [
                    name,
                ] + list(map(str, values))
                self.append_to_results_table(curr_line)

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

    def append_to_results_table(self, array: List[str]) -> None:
        self.add_row_to_results_table()
        for i, value in enumerate(array):
            if value is None:
                value = ""
            elif "nan" in value.lower():
                value = "NaN"
            self.table.item(self.table.rowCount() - 1, i).setText(value)
        return

    def create_power_plot_window_slot(self, datas: List[Data]) -> None:
        new_window = SubwindowPlot(self.sub_controller, self.mdi, role="power", datas=datas)
        self.power_plot_subwindows.append(new_window)
        return

    def create_voltage_plot_window_slot(self, datas: List[Data]) -> None:
        new_window = SubwindowPlot(
            self.sub_controller, self.mdi, role="voltage", datas=datas
        )
        self.voltage_plot_subwindows.append(new_window)
        return

    def create_temperature_plot_window_slot(self, datas: List[Data]) -> None:
        new_window = SubwindowPlot(
            self.sub_controller, self.mdi, role="temperature", datas=datas
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
