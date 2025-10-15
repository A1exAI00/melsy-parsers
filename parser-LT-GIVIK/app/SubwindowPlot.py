from typing import List, Dict
from os.path import join, dirname, basename, splitext
from glob import iglob
import re

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
import matplotlib as mpl
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import (
    MultipleLocator,
    AutoMinorLocator,
    FixedLocator,
    AutoLocator,
)
import mplcursors

from backend.Data import Data
from app.MainController import MainController
from app.MplCanvas import MplCanvas
from app.ModifiedToolbar import ModifiedToolbar


class SubwindowPlot(QMdiSubWindow):
    def __init__(self, controller: "MainController", mdi: QMdiArea, role: str, datas: List[Data]) -> None:
        self.controller = controller
        self.mdi = mdi
        self.role = role
        self.datas = datas
        super().__init__()
        self.setup_ui()
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
        sc = MplCanvas(self, width=5, height=4, dpi=100)
        toolbar = ModifiedToolbar(sc, None, self)
        plot_window_layout.addWidget(toolbar)
        plot_window_layout.addWidget(sc)

        # Add grid, axis lines, axis labels
        sc.axes.grid(True, linestyle="--", alpha=0.7)
        sc.axes.axhline(color="black")
        sc.axes.axvline(color="black")
        sc.axes.set_xlabel(X_axis_label)
        sc.axes.set_ylabel(Y_axis_label)

        # Add minor tick locators
        sc.axes.xaxis.set_minor_locator(AutoMinorLocator(10))
        sc.axes.yaxis.set_minor_locator(AutoMinorLocator(10))

        # Add plot lines
        lines = []
        for data in datas:
            X_data = data.LT[X_axis_label]
            Y_data = data.LT[Y_axis_label]
            label = data.naming_data["Name"]
            line = sc.axes.plot(X_data, Y_data, linewidth=1, label=label)
            lines.append(line)

        # Add legend
        sc.axes.legend()

        # Set tight layout
        sc.fig.tight_layout()

        # Create temporary slot function for manually changing tick locators
        def tmp_locator_changed_slot():
            X_Y_strings = (
                x_multiple_locator_edit.text().strip("\n"),
                y_multiple_locator_edit.text().strip("\n"),
            )
            axes = sc.axes.xaxis, sc.axes.yaxis

            # Try to set multiple locators
            for string, axis in zip(X_Y_strings, axes):
                try:
                    integer = int(string)
                    axis.set_major_locator(MultipleLocator(integer))
                except:
                    axis.set_major_locator(AutoLocator())

            # Force redraw plot
            sc.draw()
            return

        # Connect tick locator signals and slots
        x_multiple_locator_edit.editingFinished.connect(tmp_locator_changed_slot)
        y_multiple_locator_edit.editingFinished.connect(tmp_locator_changed_slot)

        # Create cursor for plot
        cursor = mplcursors.cursor(sc.axes)
        cursor.connect(
            "add",
            lambda sel: sel.annotation.set_text(
                "\n".join(
                    [
                        sel.artist.get_label(),
                        f"{X_axis_label} = {sel.target[0]:.3f}",
                        f"{Y_axis_label} = {sel.target[1]:.3f}",
                    ]
                )
            ),
        )

        # Add checkboxes for each plot to show/hide plot
        grid_layout = QGridLayout()
        plot_window_layout.addLayout(grid_layout)

        # Generate checkboxes in a grid
        checkboxes = []
        columns, row, col = 3, 0, 0
        for i, data in enumerate(datas):
            checkbox = QCheckBox(data.naming_data["Name"])
            checkbox.setChecked(True)
            grid_layout.addWidget(checkbox, row, col)
            checkboxes.append(checkbox)

            # Iterate over columns
            col += 1
            if col >= columns:
                col = 0
                row += 1
        
        # Add slot function to update plot visibility
        def tmp_slot():
            for i, (checkbox, line) in enumerate(zip(checkboxes, lines)):
                line[0].set_linestyle("solid" if checkbox.isChecked() else "None")
                line[0].set_label(
                    datas[i].naming_data["Name"] if checkbox.isChecked() else ""
                )
                sc.axes.legend()
            sc.draw()
            return

        # Connect visibility slots and signals
        for i, data in enumerate(datas):
            checkboxes[i].stateChanged.connect(tmp_slot)

        # Show plot window
        self.show()
        return
