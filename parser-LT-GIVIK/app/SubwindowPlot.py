from typing import List

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMdiArea,
    QMdiSubWindow,
    QLineEdit,
    QCheckBox,
    QLabel,
    QGridLayout,
    QTableWidget,
    QComboBox,
)
from PySide6.QtCore import Qt

from backend.LTdata import LTdata
from backend.LIVdata import LIVdata
from app.SubController import SubController
from app.PlotController import PlotController
from app.ModifiedToolbar import ModifiedToolbar
from app.MplWidget import MplWidget


class SubwindowPlot(QMdiSubWindow):
    def __init__(
        self,
        controller: "SubController",
        mdi: QMdiArea,
        role: str,
        datas: List[LIVdata | LTdata],
    ) -> None:
        self.controller = controller
        self.plot_controller = PlotController()
        self.mdi = mdi
        self.role = role
        self.datas = datas
        super().__init__()
        self.setup_ui()
        self.connect_controller()
        return

    def connect_controller(self) -> None:
        return

    def setup_ui(self) -> None:
        datas = None
        match self.role:
            case "LIVpower":
                this_title = "LIV power(set current) plot window"
                X_axis_label = "Set, A"
                Y_axis_label = "Power, W"
                labels = []
                X_arrays = []
                Y_arrays = []
                keys_filter = ["Power, W", "OPM"]
                for data in self.datas:
                    for key in keys_filter:
                        if key in data.LIV.keys():
                            labels.append(data.other_data["Name"])
                            X_arrays.append(data.LIV["Set, A"])
                            Y_arrays.append(data.LIV[key])
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 800
                axhline_needed, axvline_needed = True, True
            case "LIVvoltage":
                this_title = "LIV vontage(set current) plot window"
                X_axis_label = "Set, A"
                Y_axis_label = "Voltage, V"
                labels = []
                X_arrays = []
                Y_arrays = []
                keys_filter = ["Voltage, V", "AI_Voltage"]
                for data in self.datas:
                    for key in keys_filter:
                        if key in data.LIV.keys():
                            labels.append(data.other_data["Name"])
                            X_arrays.append(data.LIV["Set, A"])
                            Y_arrays.append(data.LIV[key])
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 800
                axhline_needed, axvline_needed = True, True
            case "LIVspectrummean":
                this_title = "LIV WLmean(set current) plot window"
                X_axis_label = "Set, A"
                Y_axis_label = "WLmean, nm"
                labels = []
                X_arrays = []
                Y_arrays = []
                for data in self.datas:
                    keys = data.LIV.keys()
                    this_name = data.other_data["Name"]
                    for key in keys:
                        if "WLmean, nm" in key:
                            labels.append(this_name + str(key)[len("WLmean, nm") :])
                            X_arrays.append(data.LIV["Set, A"])
                            Y_arrays.append(data.LIV[key])
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 800
                axhline_needed, axvline_needed = False, True
            case "LTpower":
                this_title = "LT power(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Power (avg), W"
                labels = [data.other_data["Name"] for data in self.datas]
                X_arrays = [data.LT["Reletive time, h"] for data in self.datas]
                Y_arrays = [data.LT["Power (avg), W"] for data in self.datas]
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 800
                axhline_needed, axvline_needed = True, True
            case "LTvoltage":
                this_title = "LT voltage(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Voltage, V"
                datas: List[LTdata] = list(
                    filter(lambda each: each.GIVIK_version == 2, self.datas)
                )
                labels = [data.other_data["Name"] for data in datas]
                X_arrays = [data.LT["Reletive time, h"] for data in datas]
                Y_arrays = [data.LT["Voltage, V"] for data in datas]
                sub_x_position, sub_y_position = 1103, 3
                sub_w, sub_h = 500, 800
                axhline_needed, axvline_needed = False, True
            case "LTtemperature":
                this_title = "LT temperature(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Tank water temp., C"
                datas: List[LTdata] = list(
                    filter(lambda each: each.GIVIK_version == 2, self.datas)
                )
                labels = [data.other_data["Name"] for data in datas]
                X_arrays = [data.LT["Reletive time, h"] for data in datas]
                Y_arrays = [data.LT["Tank water temp., C"] for data in datas]
                sub_x_position, sub_y_position = 1203, 3
                sub_w, sub_h = 500, 800
                axhline_needed, axvline_needed = False, True
            case "PULSEpower":
                this_title = "PULSE power(set current) plot window"
                X_axis_label = "Current, A"
                Y_axis_label = "Power, W"
                datas: List[LTdata] = list(
                    filter(lambda each: "LIV" in each.mode, self.datas)
                )
                labels = [data.other_data["Name"] for data in datas]
                X_arrays = [data.LIV["Current, A"] for data in datas]
                Y_arrays = [data.LIV["Power, W"] for data in datas]
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 800
                axhline_needed, axvline_needed = True, True
            case "PULSEvoltage":
                this_title = "PULSE voltage(set current) plot window"
                X_axis_label = "Current, A"
                Y_axis_label = "Voltage, V"
                datas: List[LTdata] = list(
                    filter(lambda each: "LIV" in each.mode, self.datas)
                )
                labels = [data.other_data["Name"] for data in datas]
                X_arrays = [data.LIV["Current, A"] for data in datas]
                Y_arrays = [data.LIV["Voltage, V"] for data in datas]
                sub_x_position, sub_y_position = 1203, 3
                sub_w, sub_h = 500, 800
                axhline_needed, axvline_needed = True, True
            case "PULSEintensity":
                this_title = "PULSE intensity(WL) plot window"
                X_axis_label = "Wavelength, nm"
                Y_axis_label = "Intensity, ??"
                datas: List[LTdata] = list(
                    filter(lambda each: "Spectrum" in each.mode, self.datas)
                )
                labels = []
                X_arrays = []
                Y_arrays = []
                for data in datas:
                    keys = data.LIV.keys()
                    this_name = data.other_data["Name"]
                    for key in keys:
                        if "Intensity" in key:
                            labels.append(str(key)[len("Intensity") :])
                            X_arrays.append(data.LIV["Wavelength, nm"])
                            Y_arrays.append(data.LIV[key])
                sub_x_position, sub_y_position = 1203, 3
                sub_w, sub_h = 500, 800
                axhline_needed, axvline_needed = True, False
            case _:
                raise Exception("Unknown role of plot window")

        # Add new subwindow to Mdi Area
        self.setWindowTitle(this_title)
        self.mdi.addSubWindow(self)

        # Define subwindow layout
        self.setGeometry(sub_x_position, sub_y_position, sub_w, sub_h)
        plot_window_widget = QWidget()
        plot_window_layout = QVBoxLayout()
        plot_window_widget.setLayout(plot_window_layout)
        self.setWidget(plot_window_widget)

        # Manual tick locators setup
        grid_layout_edits = QGridLayout()
        x_multiple_locator_edit = QLineEdit(placeholderText="100")
        y_multiple_locator_edit = QLineEdit(placeholderText="5")
        grid_layout_edits.addWidget(QLabel("X Axis Tick Size"), 0, 0)
        grid_layout_edits.addWidget(x_multiple_locator_edit, 0, 1)
        grid_layout_edits.addWidget(QLabel("Y Axis Tick Size"), 0, 2)
        grid_layout_edits.addWidget(y_multiple_locator_edit, 0, 3)
        plot_window_layout.addLayout(grid_layout_edits)

        # Connect tick locator signals and slots
        tmp_slot = lambda edits=(
            x_multiple_locator_edit,
            y_multiple_locator_edit,
        ): self.plot_controller.update_ticks.emit(edits)
        x_multiple_locator_edit.editingFinished.connect(tmp_slot)
        y_multiple_locator_edit.editingFinished.connect(tmp_slot)

        show_legend_checkbox = QCheckBox("Show legend")
        show_legend_checkbox.setChecked(True)
        show_legend_checkbox.stateChanged.connect(self.show_legend_checkbox_slot)
        plot_window_layout.addWidget(show_legend_checkbox)

        approx_mode_box = QHBoxLayout()
        approx_mode_label = QLabel("Approximation mode")
        approx_mode_combobox = QComboBox()
        approx_mode_combobox.addItem("Two Point fit")
        approx_mode_combobox.addItem("Linear Regression fit")
        approx_mode_box.addWidget(approx_mode_label)
        approx_mode_box.addWidget(approx_mode_combobox)
        plot_window_layout.addLayout(approx_mode_box)
        approx_mode_combobox.currentIndexChanged.connect(self.approx_mode_changed_slot)

        if self.role == "LIVspectrummean":
            cold_wavelength_box = QHBoxLayout()
            cold_wavelength_label = QLabel("Cold wavelength, nm")
            cold_wavelength_edit = QLineEdit(text="805")
            cold_wavelength_box.addWidget(cold_wavelength_label)
            cold_wavelength_box.addWidget(cold_wavelength_edit)
            cold_wavelength_edit.editingFinished.connect(
                lambda edit=cold_wavelength_edit: self.plot_controller.cold_wavelength_changed.emit(
                    edit
                )
            )
            plot_window_layout.addLayout(cold_wavelength_box)

        # Create canvas backend
        self.mplwidget = MplWidget(
            self.plot_controller,
            xlabel=X_axis_label,
            ylabel=Y_axis_label,
            role=self.role,
        )
        if self.role == "LIVspectrummean":
            self.mplwidget.secxaxis = None
            self.plot_controller.cold_wavelength_changed.emit(cold_wavelength_edit)

        self.mplwidget.setMinimumHeight(500)
        self.mplwidget.setMinimumWidth(500)
        toolbar = ModifiedToolbar(self.mplwidget.canvas, self.mplwidget.fig, None)
        plot_window_layout.addWidget(toolbar)
        plot_window_layout.addWidget(self.mplwidget)

        # Add plot lines
        for i, label in enumerate(labels):
            X_data = X_arrays[i]
            Y_data = Y_arrays[i]
            self.mplwidget.plot(X_data, Y_data, label=label, linewidth=1)

        self.mplwidget.connect_mplcursor()

        if axhline_needed:
            self.mplwidget.axes.axhline(0.0, color="black")
        if axvline_needed:
            self.mplwidget.axes.axvline(0.0, color="black")

        self.plot_controller.touch_legend.emit()

        table = QTableWidget()
        table.setColumnCount(3)
        table.setRowCount(len(labels))
        table.setHorizontalHeaderLabels(["Naming", "Show", "Approx."])
        table.setColumnWidth(0, 250)
        table.resizeColumnToContents(1)
        table.resizeColumnToContents(2)
        table.setMinimumHeight(50)
        table.setMaximumHeight(150)
        # table.setFixedHeight(150)
        table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)

        plot_window_layout.addWidget(table)

        # Generate checkboxes in a grid
        checkboxes_show: List[QCheckBox] = []
        checkboxes_approx: List[QCheckBox] = []
        checkbox_style = """
                QCheckBox::indicator {
                    width: 25px;
                    height: 25px;
                }
            """
        for i, label in enumerate(labels):
            table.setCellWidget(i, 0, QLabel(label))

            checkbox_show = QCheckBox()
            checkbox_show.setChecked(True)
            checkbox_show.setStyleSheet(checkbox_style)
            table.setCellWidget(i, 1, checkbox_show)
            checkboxes_show.append(checkbox_show)

            checkbox_approx = QCheckBox()
            # checkbox_approx.setChecked(False)
            checkbox_approx.setStyleSheet(checkbox_style)
            table.setCellWidget(i, 2, checkbox_approx)
            checkboxes_approx.append(checkbox_approx)

        # Connect visibility slots and signals
        for i, label in enumerate(labels):
            checkboxes_show[i].stateChanged.connect(
                lambda _, i=i: self.plot_controller.plot_visibility_toggled.emit(i)
            )
            checkboxes_approx[i].stateChanged.connect(
                lambda _, i=i: self.plot_controller.draggable_visibility_toggled.emit(i)
            )

        self.show()
        return

    def show_legend_checkbox_slot(self, state) -> None:
        if Qt.CheckState(state) == Qt.Checked:
            self.plot_controller.show_legend.emit()
        else:
            self.plot_controller.hide_legend.emit()
        return

    def approx_mode_changed_slot(self, index: int) -> None:
        self.plot_controller.approx_mode_changed.emit(index)
        return
