from typing import List, Dict

from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QMdiArea,
    QMdiSubWindow,
    QLineEdit,
    QCheckBox,
    QLabel,
    QGridLayout,
    QTableWidget,
)

from backend.LTdata import LTdata
from app.SubController import SubController
from app.PlotController import PlotController
from app.ModifiedToolbar import ModifiedToolbar
from app.MplWidget import MplWidget
from app.LinearApproxLine import LinearApproxLine


class SubwindowPlot(QMdiSubWindow):
    def __init__(
        self, controller: "SubController", mdi: QMdiArea, role: str, datas: List[LTdata]
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
            case "power":
                this_title = "LT power(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Power (avg), W"
                datas = self.datas
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 800
            case "voltage":
                this_title = "LT voltage(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Voltage, V"
                datas = list(filter(lambda each: each.GIVIK_version == 2, self.datas))
                sub_x_position, sub_y_position = 1103, 3
                sub_w, sub_h = 500, 800
            case "temperature":
                this_title = "LT temperature(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Tank water temp., C"
                datas = list(filter(lambda each: each.GIVIK_version == 2, self.datas))
                sub_x_position, sub_y_position = 1203, 3
                sub_w, sub_h = 500, 800

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
        grid_layout_edits.addWidget(QLabel("X Axis Multiple Locator"), 0, 0)
        grid_layout_edits.addWidget(QLabel("Y Axis Multiple Locator"), 1, 0)
        grid_layout_edits.addWidget(x_multiple_locator_edit, 0, 1)
        grid_layout_edits.addWidget(y_multiple_locator_edit, 1, 1)
        plot_window_layout.addLayout(grid_layout_edits)

        # Create canvas backend
        self.mplwidget = MplWidget(
            self.plot_controller,
            xlabel=X_axis_label,
            ylabel=Y_axis_label,
            role=self.role,
        )
        self.mplwidget.setMinimumHeight(500)
        self.mplwidget.setMinimumWidth(500)
        toolbar = ModifiedToolbar(self.mplwidget.canvas, self.mplwidget.fig, None)
        plot_window_layout.addWidget(toolbar)
        plot_window_layout.addWidget(self.mplwidget)

        # Add plot lines
        for data in datas:
            X_data = data.LT[X_axis_label]
            Y_data = data.LT[Y_axis_label]
            label = data.other_data["Name"]
            self.mplwidget.plot(X_data, Y_data, label=label, linewidth=1)

        self.plot_controller.touch_legend.emit()

        # Connect tick locator signals and slots
        tmp_slot = lambda edits=(
            x_multiple_locator_edit,
            y_multiple_locator_edit,
        ): self.plot_controller.update_ticks.emit(edits)
        x_multiple_locator_edit.editingFinished.connect(tmp_slot)
        y_multiple_locator_edit.editingFinished.connect(tmp_slot)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setRowCount(len(datas))
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
        checkboxes_show = []
        checkboxes_approx = []
        checkbox_style = """
                QCheckBox::indicator {
                    width: 25px;
                    height: 25px;
                }
            """
        for data_i, data in enumerate(datas):
            table.setCellWidget(data_i, 0, QLabel(data.other_data["Name"]))

            checkbox_show = QCheckBox()
            checkbox_show.setChecked(True)
            checkbox_show.setStyleSheet(checkbox_style)
            table.setCellWidget(data_i, 1, checkbox_show)
            checkboxes_show.append(checkbox_show)

            checkbox_approx = QCheckBox()
            # checkbox_approx.setChecked(False)
            checkbox_approx.setStyleSheet(checkbox_style)
            table.setCellWidget(data_i, 2, checkbox_approx)
            checkboxes_approx.append(checkbox_approx)

        # Connect visibility slots and signals
        for i, data in enumerate(datas):
            checkboxes_show[i].stateChanged.connect(
                lambda _, i=i: self.plot_controller.plot_visibility_toggled.emit(i)
            )
            checkboxes_approx[i].stateChanged.connect(
                lambda _, i=i: self.plot_controller.draggable_visibility_toggled.emit(i)
            )

        self.show()
        return
