from typing import List, Dict
import re

from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QMdiArea,
    QMdiSubWindow,
    QLineEdit,
    QCheckBox,
    QLabel,
    QGridLayout,
)
from matplotlib.ticker import (
    MultipleLocator,
    AutoMinorLocator,
    AutoLocator,
)
import mplcursors

from backend.Data import Data
from app.SubController import SubController
from app.PlotController import PlotController
from app.ModifiedToolbar import ModifiedToolbar
from app.MplWidget import MplWidget
from app.LinearApproxLine import LinearApproxLine


class SubwindowPlot(QMdiSubWindow):
    def __init__(
        self, controller: "SubController", mdi: QMdiArea, role: str, datas: List[Data]
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
        self.plot_controller.draggable_changed_position.connect(
            self.draggable_changed_position_slot
        )
        self.plot_controller.touch_plot.connect(self.touch_plot_slot)
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
                sub_w, sub_h = 500, 600
            case "voltage":
                this_title = "LT voltage(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Voltage, V"
                datas = list(filter(lambda each: each.GIVIK_version == 2, self.datas))
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 600
            case "temperature":
                this_title = "LT temperature(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Tank water temp., C"
                datas = list(filter(lambda each: each.GIVIK_version == 2, self.datas))
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 600

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
        self.mplwidget = MplWidget(self.plot_controller)
        toolbar = ModifiedToolbar(self.mplwidget.canvas, None)
        plot_window_layout.addWidget(toolbar)
        plot_window_layout.addWidget(self.mplwidget)

        # Add grid, axis lines, axis labels
        self.mplwidget.axes.grid(True, linestyle="--", alpha=0.7)
        self.mplwidget.axes.axhline(color="black")
        self.mplwidget.axes.axvline(color="black")
        self.mplwidget.axes.set_xlabel(X_axis_label)
        self.mplwidget.axes.set_ylabel(Y_axis_label)

        # Add minor tick locators
        self.mplwidget.axes.xaxis.set_minor_locator(AutoMinorLocator(10))
        self.mplwidget.axes.yaxis.set_minor_locator(AutoMinorLocator(10))

        # Add plot lines
        for data in datas:
            X_data = data.LT[X_axis_label]
            Y_data = data.LT[Y_axis_label]
            label = data.naming_data["Name"]
            self.mplwidget.plot(X_data, Y_data, label=label, linewidth=1)

        # Add legend
        self.mplwidget.axes.legend()

        # Set tight layout
        self.mplwidget.fig.tight_layout()

        # Create temporary slot function for manually changing tick locators
        def tmp_locator_changed_slot():
            X_Y_strings = (
                x_multiple_locator_edit.text().strip("\n"),
                y_multiple_locator_edit.text().strip("\n"),
            )
            axes = self.mplwidget.axes.xaxis, self.mplwidget.axes.yaxis

            # Try to set multiple locators
            for string, axis in zip(X_Y_strings, axes):
                try:
                    integer = int(string)
                    axis.set_major_locator(MultipleLocator(integer))
                except:
                    axis.set_major_locator(AutoLocator())

            # Force redraw plot
            self.mplwidget.canvas.draw()
            return

        # Connect tick locator signals and slots
        x_multiple_locator_edit.editingFinished.connect(tmp_locator_changed_slot)
        y_multiple_locator_edit.editingFinished.connect(tmp_locator_changed_slot)

        # Create cursor for plot
        cursor = mplcursors.cursor(self.mplwidget.axes.lines)
        cursor.connect(
            "add",
            lambda sel: self.mplcursor_connect_function(
                sel, X_axis_label, Y_axis_label
            ),
        )

        # Add checkboxes for each plot to show/hide plot
        grid_layout = QGridLayout()
        plot_window_layout.addLayout(grid_layout)

        # Generate checkboxes in a grid
        checkboxes_show = []
        checkboxes_approx = []
        for i, data in enumerate(datas):
            checkbox_show = QCheckBox(data.naming_data["Name"])
            checkbox_show.setChecked(True)
            grid_layout.addWidget(checkbox_show, i, 0)
            checkboxes_show.append(checkbox_show)

            checkbox_approx = QCheckBox("Approx.")
            # checkbox_approx.setChecked(False)
            grid_layout.addWidget(checkbox_approx, i, 1)
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

    def mplcursor_connect_function(
        self, selection, X_axis_label: str, Y_axis_label: str
    ):  
        if re.findall(r"_child\d+", selection.artist.get_label()):
            selection.annotation.set_visible(False)
        else:
            selection.annotation.set_text(
                "\n".join(
                    [
                        selection.artist.get_label(),
                        f"{X_axis_label} = {selection.target[0]:.3f}",
                        f"{Y_axis_label} = {selection.target[1]:.3f}",
                    ]
                )
            )
        return

    def draggable_changed_position_slot(self, index: int) -> None:
        return

    def touch_plot_slot(self) -> None:
        self.mplwidget.axes.legend()
        self.mplwidget.canvas.draw()
        return
