from typing import List
from time import time
import re
from statistics import mean

# import numpy as np
from PySide6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import (
    MultipleLocator,
    AutoMinorLocator,
    AutoLocator,
)
import mplcursors

from backend.misc import create_linear_approximation
from app.DraggableLine import DraggableVerticalLine
from app.PlotController import PlotController
from app.LinearApproxLine import LinearApproxLine


class MplWidget(QWidget):
    def __init__(
        self,
        controller: "PlotController",
        parent=None,
        xlabel: str = "",
        ylabel: str = "",
        role: str = "",
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.role = role

        self.dpi = 100
        self.figsize = (5, 4)

        # Data plots
        self.lines_visibility: List[bool] = []
        self.lines: List[List[Line2D]] = []
        self.labels: List[str] = []

        # Pairs of raggable lines
        self.draggable_lines: List[List[DraggableVerticalLine]] = []
        self.draggable_lines_visibibity: List[bool] = []

        # Approx lines
        self.approx_lines: List[LinearApproxLine] = []
        self.approx_lines_visibility: List[bool] = []
        self.approx_lines_last_update_time = time()
        self.approx_lines_update_cooldown = 0.0

        self.setup_ui()
        self.connect_controller()
        return

    def setup_ui(self) -> None:
        # Create matplotlib figure and canvas
        self.fig = Figure(figsize=self.figsize, dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)

        self.axes.grid(True, linestyle="--", alpha=0.7)
        self.axes.axhline(color="black")
        self.axes.axvline(color="black")
        self.axes.set_xlabel(self.xlabel)
        self.axes.set_ylabel(self.ylabel)
        self.axes.xaxis.set_minor_locator(AutoMinorLocator(10))
        self.axes.yaxis.set_minor_locator(AutoMinorLocator(10))
        self.axes.legend()

        # Create cursor for plot
        cursor = mplcursors.cursor(self.axes.lines)
        cursor.connect("add", self.mplcursor_connect_function)

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        return

    def connect_controller(self):
        self.controller.plot_visibility_toggled.connect(
            self.plot_visibility_toggled_slot
        )
        self.controller.draggable_visibility_toggled.connect(
            self.draggable_visibility_toggled_slot
        )
        self.controller.draggable_changed_position.connect(
            self.approx_line_update_position_slot
        )
        self.controller.draggable_visibility_toggled.connect(
            self.approx_line_visibility_toggled_slot
        )
        self.controller.touch_plot.connect(self.touch_plot_slot)
        self.controller.update_ticks.connect(self.update_tick_slot)

        return

    ############################################################################
    # DATA PLOTS ###############################################################
    ############################################################################

    def plot(self, X_data, Y_data, label, linewidth) -> None:
        line = self.axes.plot(X_data, Y_data, label=label, linewidth=linewidth)
        self.lines.append(line)
        self.labels.append(label)
        self.lines_visibility.append(True)

        index = len(self.draggable_lines)

        # Add and hide a pair of draggable lines
        self.add_draggable_lines()
        self.hide_draggable_lines(index)

        # Add and hide approximation line
        self.add_approx_line()
        self.hide_approx_line(index)
        return

    def hide_plot(self, index: int) -> None:
        self.lines_visibility[index] = False
        self.lines[index][0].set_linestyle("None")
        self.lines[index][0].set_label("")
        return

    def show_plot(self, index: int) -> None:
        self.lines_visibility[index] = True
        self.lines[index][0].set_linestyle("solid")
        self.lines[index][0].set_label(self.labels[index])
        return

    def plot_visibility_toggled_slot(self, index: int) -> None:
        prev_visible = self.lines_visibility[index]
        if prev_visible:
            self.hide_plot(index)
        else:
            self.show_plot(index)
        self.axes.legend()
        self.controller.touch_plot.emit()
        return

    ############################################################################
    # PAIRS OF DRAGGABLE LINES #################################################
    ############################################################################

    def add_draggable_lines(self):
        index = len(self.draggable_lines)
        color = self.lines[index][0].get_color()
        xlim = self.axes.get_xlim()
        line1 = DraggableVerticalLine(
            self.axes,
            index,
            x=xlim[0] + 0.2 * (xlim[1] - xlim[0]),
            color=color,
            linewidth=1,
        )
        line1.connect_controller(self.controller)
        line2 = DraggableVerticalLine(
            self.axes,
            index,
            x=xlim[0] + 0.8 * (xlim[1] - xlim[0]),
            color=color,
            linewidth=1,
        )
        line2.connect_controller(self.controller)
        self.draggable_lines.append([line1, line2])
        self.draggable_lines_visibibity.append(True)
        return

    def hide_draggable_lines(self, index: int) -> None:
        self.draggable_lines_visibibity[index] = False
        lines = self.draggable_lines[index]
        for line in lines:
            line.hide()
        return

    def show_draggable_lines(self, index: int) -> None:
        self.draggable_lines_visibibity[index] = True
        lines = self.draggable_lines[index]
        for line in lines:
            line.show()
        return

    def draggable_visibility_toggled_slot(self, index: int) -> None:
        prev_visible = self.draggable_lines_visibibity[index]
        if prev_visible:
            self.hide_draggable_lines(index)
        else:
            self.show_draggable_lines(index)
        self.controller.touch_plot.emit()
        self.controller.draggable_changed_position.emit(index)
        return

    ############################################################################
    # APPROXIMATION LINES ######################################################
    ############################################################################

    def add_approx_line(self) -> None:
        index = len(self.approx_lines)
        color = self.lines[index][0].get_color()
        line = LinearApproxLine(self.axes, (0.0, 0.0), 0.0, color=color, linewidth=1)
        line.connect_controller(self.controller)
        self.approx_lines.append(line)
        self.approx_lines_visibility.append(True)
        return

    def hide_approx_line(self, index: int) -> None:
        line = self.approx_lines[index]
        self.approx_lines_visibility[index] = False
        line.hide()
        return

    def show_approx_line(self, index: int) -> None:
        line = self.approx_lines[index]
        self.approx_lines_visibility[index] = True
        line.show()
        self.controller.draggable_changed_position.emit(index)
        return

    def approx_line_visibility_toggled_slot(self, index: int) -> None:
        prev_visible = self.approx_lines_visibility[index]
        if prev_visible:
            self.hide_approx_line(index)
        else:
            self.show_approx_line(index)
            # TODO find best linear section
        self.controller.touch_plot.emit()
        return

    def approx_line_update_position_slot(self, index: int) -> None:
        # Do nothing if approx line is hidden
        if not self.approx_lines_visibility[index]:
            return

        # Save compute by waiting for cooldown
        if (
            time() - self.approx_lines_last_update_time
            < self.approx_lines_update_cooldown
        ):
            return
        self.approx_lines_last_update_time = time()

        # Get data from the plot
        x_data_all = self.lines[index][0].get_xdata(orig=True)
        y_data_all = self.lines[index][0].get_ydata(orig=True)
        draggable_line1, draggable_line2 = self.draggable_lines[index]
        x1, x2 = draggable_line1.x, draggable_line2.x

        # Swap if out of order
        if x1 > x2:
            x1, x2 = x2, x1

        # Get points between draggable lines
        x_indexes_window = []
        for i, x in enumerate(x_data_all):
            if x1 <= x and x < x2:
                x_indexes_window.append(i)

        # Ignore of there are no points between draggable lines
        if not x_indexes_window:
            return

        x_data_window = [x_data_all[i] for i in x_indexes_window]
        y_data_window = [y_data_all[i] for i in x_indexes_window]
        _, slope, intersept = create_linear_approximation(x_data_window, y_data_window)

        # Update approx line position and display parameters on the legend
        line = self.approx_lines[index]
        line.set_position(intercept_point=(0.0, intersept), slope=slope)
        # _min, _max, _mean = min(y_data_window), max(y_data_window), mean(y_data_window)
        _min, _max, _mean = [func(y_data_window) for func in [min, max, mean]]
        first, last = y_data_window[0], y_data_window[-1]
        texts = []
        match self.role:
            case "LIVpower":
                texts.append(f"k={slope:.3E}")
                texts.append(f"Δ={(last-first):.3f}")
            case "LIVvoltage":
                texts.append(f"k={slope:.3E}")
            case "LIVspectrummean":
                texts.append(f"k={slope:.3E}")
            case "LTpower":
                texts.append(f"k={slope:.3E}")
                texts.append(f"Δ={(last-first):.3f}")
            case "LTvoltage":
                texts.append(f"Δ={(last-first):.3f}")
                texts.append(f"mean={_mean:.3f}")
                texts.append(f"min={_min:.3f}")
                texts.append(f"max={_max:.3f}")
            case "LTtemperature":
                texts.append(f"mean={_mean:.3f}")
                texts.append(f"min={_min:.3f}")
                texts.append(f"max={_max:.3f}")
        line.set_label("\n".join(texts))
        self.axes.legend()
        return

    def touch_plot_slot(self) -> None:
        self.axes.legend()
        self.canvas.draw()
        return

    def update_tick_slot(self, edits):
        strings = [edit.text().strip("\n") for edit in edits]
        axes = self.axes.xaxis, self.axes.yaxis

        # Try to set multiple locators
        for string, axis in zip(strings, axes):
            try:
                integer = int(string)
                axis.set_major_locator(MultipleLocator(integer))
            except:
                axis.set_major_locator(AutoLocator())

        # Force redraw plot
        self.controller.touch_plot.emit()
        return

    def mplcursor_connect_function(self, selection):
        label = selection.artist.get_label()
        if re.findall(r"_child\d+", label):
            selection.annotation.set_visible(False)
            return
        if re.findall(r"k=[+-]?\d*\.\d+E[+-]\d+", label):
            selection.annotation.set_visible(False)
            return

        selection.annotation.set_text(
            "\n".join(
                [
                    selection.artist.get_label(),
                    f"{self.xlabel} = {selection.target[0]:.3f}",
                    f"{self.ylabel} = {selection.target[1]:.3f}",
                ]
            )
        )
        return
