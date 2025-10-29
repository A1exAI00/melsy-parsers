from typing import List, Dict, Tuple

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

        self.labels: List[str] = []
        self.xss: List[List[float]] = []
        self.yss: List[List[float]] = []

        super().__init__()
        self.parse_role()
        self.setup_ui()
        self.connect_controller()
        return

    def connect_controller(self) -> None:
        return
    
    def parse_role(self) -> None:
        role_to_title: Dict[str, str] = {}
        role_to_title["LIVpower"] = "LIV power(set current) plot window"
        role_to_title["LIVvoltage"] = "LIV vontage(set current) plot window"
        role_to_title["LIVspectrummean"] = "LIV WLmean(set current) plot window"
        role_to_title["LIVintensity"] = "LIV intensity(WL) plot window"
        role_to_title["LTpower"] = "LT power(time) plot window"
        role_to_title["LTvoltage"] = "LT voltage(time) plot window"
        role_to_title["LTtemperature"] = "LT temperature(time) plot window"
        role_to_title["PULSEpower"] = "PULSE power(set current) plot window"
        role_to_title["PULSEvoltage"] = "PULSE voltage(set current) plot window"
        role_to_title["PULSEintensity"] = "PULSE intensity(WL) plot window"
        self.role_to_title = role_to_title

        role_to_axes: Dict[str, List[str | None]] = {}
        role_to_axes["LIVpower"] = ["Set, A", None, "Power, W", None]
        role_to_axes["LIVvoltage"] = ["Set, A", None, "Voltage, V", None]
        role_to_axes["LIVspectrummean"] = ["Set, A", None, "WLmean, nm", None]
        role_to_axes["LIVintensity"] = ["Wavelength, nm", None, "Intensity", None]
        role_to_axes["LTpower"] = ["Time, h", None, "Power (avg), W", None]
        role_to_axes["LTvoltage"] = ["Time, h", None, "Voltage, V", None]
        role_to_axes["LTtemperature"] = ["Time, h", None, "Tank water temp., C", None]
        role_to_axes["PULSEpower"] = ["Current, A", None, "Power, W", None]
        role_to_axes["PULSEvoltage"] = ["Current, A", None, "Voltage, V", None]
        role_to_axes["PULSEintensity"] = ["Wavelength, nm", None, "Intensity", None]
        self.role_to_axes = role_to_axes

        role_to_window_pos: Dict[str, Tuple[float, float, float, float]] = {}
        role_to_window_pos["LIVpower"] = (1003, 3, 500, 800)
        role_to_window_pos["LIVvoltage"] = (1003, 3, 500, 800)
        role_to_window_pos["LIVspectrummean"] = (1003, 3, 500, 800)
        role_to_window_pos["LIVintensity"] = (1003, 3, 500, 800)
        role_to_window_pos["LTpower"] = (1003, 3, 500, 800)
        role_to_window_pos["LTvoltage"] = (1003, 3, 500, 800)
        role_to_window_pos["LTtemperature"] = (1003, 3, 500, 800)
        role_to_window_pos["PULSEpower"] = (1003, 3, 500, 800)
        role_to_window_pos["PULSEvoltage"] = (1003, 3, 500, 800)
        role_to_window_pos["PULSEintensity"] = (1003, 3, 500, 800)
        self.role_to_window_pos = role_to_window_pos

        role_to_hvlines: Dict[str, Tuple[bool, bool]] = {}
        role_to_hvlines["LIVpower"] = (True, True)
        role_to_hvlines["LIVvoltage"] = (True, True)
        role_to_hvlines["LIVspectrummean"] = (False, True)
        role_to_hvlines["LIVintensity"] = (True, False)
        role_to_hvlines["LTpower"] = (True, True)
        role_to_hvlines["LTvoltage"] = (False, True)
        role_to_hvlines["LTtemperature"] = (False, True)
        role_to_hvlines["PULSEpower"] = (True, True)
        role_to_hvlines["PULSEvoltage"] = (True, True)
        role_to_hvlines["PULSEintensity"] = (True, False)
        self.role_to_hvlines = role_to_hvlines

        match self.role:
            case "LIVpower":
                keys_filter = ["Power, W", "OPM"]
                for data in self.datas:
                    for key in keys_filter:
                        if key in data.LIV.keys():
                            self.labels.append(data.other_data["Name"])
                            self.xss.append(data.LIV["Set, A"])
                            self.yss.append(data.LIV[key])
            case "LIVvoltage":
                keys_filter = ["Voltage, V", "AI_Voltage"]
                for data in self.datas:
                    for key in keys_filter:
                        if key in data.LIV.keys():
                            self.labels.append(data.other_data["Name"])
                            self.xss.append(data.LIV["Set, A"])
                            self.yss.append(data.LIV[key])
            case "LIVspectrummean":
                for data in self.datas:
                    keys = data.LIV.keys()
                    this_name = data.other_data["Name"]
                    for key in keys:
                        if "WLmean, nm" in key:
                            self.labels.append(
                                this_name + str(key)[len("WLmean, nm") :]
                            )
                            self.xss.append(data.LIV["Set, A"])
                            self.yss.append(data.LIV[key])
            case "LIVintensity":
                datas: List[LTdata] = list(
                    filter(
                        lambda each: isinstance(each, LIVdata),
                        self.datas,
                    )
                )
                for data in datas:
                    keys = data.LIV.keys()
                    this_name = data.other_data["Name"]
                    for key in keys:
                        if "Intensity" in key:
                            self.labels.append(str(key)[len("Intensity") :])
                            self.xss.append(data.LIV["Wavelength1, nm"])
                            self.yss.append(data.LIV[key])
            case "LTpower":
                self.labels = [data.other_data["Name"] for data in self.datas]
                self.xss = [data.LT["Reletive time, h"] for data in self.datas]
                self.yss = [data.LT["Power (avg), W"] for data in self.datas]
            case "LTvoltage":
                datas: List[LTdata] = list(
                    filter(lambda each: each.GIVIK_version == 2, self.datas)
                )
                self.labels = [data.other_data["Name"] for data in datas]
                self.xss = [data.LT["Reletive time, h"] for data in datas]
                self.yss = [data.LT["Voltage, V"] for data in datas]
            case "LTtemperature":
                datas: List[LTdata] = list(
                    filter(lambda each: each.GIVIK_version == 2, self.datas)
                )
                self.labels = [data.other_data["Name"] for data in datas]
                self.xss = [data.LT["Reletive time, h"] for data in datas]
                self.yss = [data.LT["Tank water temp., C"] for data in datas]
            case "PULSEpower":
                datas: List[LTdata] = list(
                    filter(lambda each: "LIV" in each.mode, self.datas)
                )
                self.labels = [data.other_data["Name"] for data in datas]
                self.xss = [data.LIV["Current, A"] for data in datas]
                self.yss = [data.LIV["Power, W"] for data in datas]
            case "PULSEvoltage":
                datas: List[LTdata] = list(
                    filter(lambda each: "LIV" in each.mode, self.datas)
                )
                self.labels = [data.other_data["Name"] for data in datas]
                self.xss = [data.LIV["Current, A"] for data in datas]
                self.yss = [data.LIV["Voltage, V"] for data in datas]
            case "PULSEintensity":
                datas: List[LTdata] = list(
                    filter(lambda each: "Spectrum" in each.mode, self.datas)
                )
                for data in datas:
                    keys = data.LIV.keys()
                    this_name = data.other_data["Name"]
                    for key in keys:
                        if "Intensity" in key:
                            self.labels.append(str(key)[len("Intensity") :])
                            self.xss.append(data.LIV["Wavelength, nm"])
                            self.yss.append(data.LIV[key])
            case _:
                raise Exception("Unknown role of plot window")
        return

    def setup_ui(self) -> None:
        
        # Add new subwindow to Mdi Area
        self.setWindowTitle(self.role_to_title[self.role])
        self.mdi.addSubWindow(self)

        # Define subwindow layout
        
        self.setGeometry(*self.role_to_window_pos[self.role])
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

        # Legend configuration
        legend_config_box = QHBoxLayout()
        plot_window_layout.addLayout(legend_config_box)

        show_legend_checkbox = QCheckBox("Show legend")
        show_legend_checkbox.setChecked(True)
        show_legend_checkbox.stateChanged.connect(self.show_legend_checkbox_slot)
        legend_config_box.addWidget(show_legend_checkbox)

        put_legend_outside_checkbox = QCheckBox("Put legend outside")
        put_legend_outside_checkbox.stateChanged.connect(self.put_legend_outside_slot)
        legend_config_box.addWidget(put_legend_outside_checkbox)

        # Approximatiom mode configuration
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
            xlabel=self.role_to_axes[self.role][0],
            ylabel=self.role_to_axes[self.role][2],
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
        for i, (label, xs, ys) in enumerate(zip(self.labels, self.xss, self.yss)):
            self.mplwidget.plot(xs, ys, label=label, linewidth=1)

        self.mplwidget.connect_mplcursor()

        axhline_needed, axvline_needed = self.role_to_hvlines[self.role]
        if axhline_needed:
            self.mplwidget.axes.axhline(0.0, color="black")
        if axvline_needed:
            self.mplwidget.axes.axvline(0.0, color="black")

        self.plot_controller.touch_legend.emit()

        table = QTableWidget()
        table.setColumnCount(3)
        table.setRowCount(len(self.labels))
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
        for i, label in enumerate(self.labels):
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
        for i, label in enumerate(self.labels):
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

    def put_legend_outside_slot(self, state) -> None:
        self.plot_controller.legend_position_changed.emit(
            Qt.CheckState(state) == Qt.Checked
        )
        return
