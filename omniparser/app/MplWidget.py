from typing import List, Tuple, Callable
import re

import numpy as np
from PySide6.QtWidgets import QVBoxLayout, QWidget, QLineEdit
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import (
    MultipleLocator,
    AutoMinorLocator,
    AutoLocator,
)
from matplotlib import pyplot as plt
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
        self.show_legend = True
        self.approx_function = self.approx_two_point
        # self.approx_function = self.approx_linear_regression
        self.legend_position_outside = False

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

        self.setup_ui()
        self.connect_controller()
        return

    def setup_ui(self) -> None:
        # Create matplotlib figure and canvas
        # self.fig = Figure(figsize=self.figsize, dpi=self.dpi)
        # self.canvas = FigureCanvas(self.fig)
        # self.axes = self.fig.add_subplot(111)
        self.fig, self.axes = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.initial_box = self.axes.get_position()

        self.axes.grid(True, linestyle="--", alpha=0.7)
        self.axes.set_xlabel(self.xlabel)
        self.axes.set_ylabel(self.ylabel)
        self.axes.xaxis.set_minor_locator(AutoMinorLocator(10))
        self.axes.yaxis.set_minor_locator(AutoMinorLocator(10))

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        return

    def connect_mplcursor(self):
        cursor = mplcursors.cursor(self.axes.lines)
        cursor.connect("add", self.mplcursor_connect_function)
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
        self.controller.touch_legend.connect(self.touch_legend_slot)
        self.controller.update_ticks.connect(self.update_tick_slot)
        self.controller.show_legend.connect(self.show_legend_slot)
        self.controller.hide_legend.connect(self.hide_legend_slot)
        self.controller.approx_mode_changed.connect(self.approx_mode_changed_slot)
        self.controller.cold_wavelength_changed.connect(
            self.cold_wavelength_changed_slot
        )
        self.controller.legend_position_changed.connect(
            self.legend_position_changed_slot
        )

        return

    ############################################################################
    # DATA PLOTS ###############################################################
    ############################################################################

    def plot(self, X_data, Y_data, label, linewidth) -> None:
        line = self.axes.plot(X_data, Y_data, label=label, linewidth=linewidth)
        self.lines.append(line)
        self.labels.append(label)
        self.lines_visibility.append(True)

        self.draggable_lines.append(None)
        self.draggable_lines_visibibity.append(False)

        self.approx_lines.append(None)
        self.approx_lines_visibility.append(False)
        self.controller.touch_legend.emit()
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
        self.controller.touch_plot.emit()
        self.controller.touch_legend.emit()
        return

    ############################################################################
    # PAIRS OF DRAGGABLE LINES #################################################
    ############################################################################

    def add_draggable_lines(self, index: int):
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
        self.draggable_lines[index] = [line1, line2]
        self.draggable_lines_visibibity[index] = True
        return

    def delete_draggable_lines(self, index: int) -> None:
        self.draggable_lines_visibibity[index] = False
        lines = self.draggable_lines[index]
        for line in lines:
            line.delete()
        self.draggable_lines[index] = None
        return

    def show_draggable_lines(self, index: int) -> None:
        self.add_draggable_lines(index)
        return

    def draggable_visibility_toggled_slot(self, index: int) -> None:
        prev_visible = self.draggable_lines_visibibity[index]
        if prev_visible:
            self.delete_draggable_lines(index)
        else:
            self.show_draggable_lines(index)
        self.controller.touch_legend.emit()
        self.controller.touch_plot.emit()
        return

    ############################################################################
    # APPROXIMATION LINES ######################################################
    ############################################################################

    def add_approx_line(self, index: int) -> None:
        color = self.lines[index][0].get_color()
        self.approx_lines_visibility[index] = True
        try:
            slope, intersept, _, _ = self.approx_function(index)
        except:
            slope = 0.0
            ylim = self.axes.get_ylim()
            intersept = (ylim[0] + ylim[1]) / 2
        line = LinearApproxLine(
            self.axes,
            intercept_point=(0.0, intersept),
            slope=slope,
            color=color,
            linewidth=1,
        )
        self.approx_lines[index] = line
        line.connect_controller(self.controller)
        self.approx_line_update_position_slot(index)
        return

    def delete_approx_line(self, index: int) -> None:
        line = self.approx_lines[index]
        self.approx_lines_visibility[index] = False
        line.delete()
        self.approx_lines[index] = None
        return

    def approx_line_visibility_toggled_slot(self, index: int) -> None:
        prev_visible = self.approx_lines_visibility[index]
        if prev_visible:
            self.delete_approx_line(index)
        else:
            self.add_approx_line(index)
            # TODO find best linear section
        self.controller.touch_legend.emit()
        self.controller.touch_plot.emit()
        return

    def approx_linear_regression(self, index: int) -> Tuple[float, float]:
        # Do nothing if approx line is hidden
        if not self.approx_lines_visibility[index]:
            raise Exception("Plot is not visible")

        # Get data from the plot
        x_data_all = self.lines[index][0].get_xdata(orig=True)
        y_data_all = self.lines[index][0].get_ydata(orig=True)
        draggable_line1, draggable_line2 = self.draggable_lines[index]
        x1, x2 = draggable_line1.x, draggable_line2.x

        # Swap if out of order
        if x1 > x2:
            x1, x2 = x2, x1

        # Get points between draggable lines
        indexes_window = []
        for i, x in enumerate(x_data_all):
            if x1 <= x and x < x2:
                indexes_window.append(i)

        # Ignore of there are no points between draggable lines
        if not indexes_window:
            raise Exception("Not enough points to approximate plot")

        x_data_window = []
        y_data_window = []
        for i in indexes_window:
            tmpx = x_data_all[i]
            tmpy = y_data_all[i]
            if np.isnan(tmpx) or np.isnan(tmpy):
                continue
            x_data_window.append(tmpx)
            y_data_window.append(tmpy)

        _, slope, intersept = create_linear_approximation(x_data_window, y_data_window)
        return slope, intersept, x_data_window, y_data_window

    def approx_two_point(
        self, index: int
    ) -> Tuple[float, float, List[float], List[float]]:
        if not self.approx_lines_visibility[index]:
            raise Exception("Plot is not visible")

        # Get data from the plot
        x_data_all = self.lines[index][0].get_xdata(orig=True)
        y_data_all = self.lines[index][0].get_ydata(orig=True)
        draggable_line1, draggable_line2 = self.draggable_lines[index]
        x1, x2 = draggable_line1.x, draggable_line2.x

        # Swap if out of order
        if x1 > x2:
            x1, x2 = x2, x1

        # Get points between draggable lines
        indexes_window = []
        for i, x in enumerate(x_data_all):
            if x1 <= x and x < x2:
                indexes_window.append(i)

        # Ignore of there are no points between draggable lines
        if not indexes_window:
            raise Exception("Not enough points to approximate plot")

        x_data_window = []
        y_data_window = []
        for i in indexes_window:
            tmpx = x_data_all[i]
            tmpy = y_data_all[i]
            if np.isnan(tmpx) or np.isnan(tmpy):
                continue
            x_data_window.append(tmpx)
            y_data_window.append(tmpy)

        if len(x_data_window) == 1:
            return (0.0, y_data_window[0], x_data_window, y_data_window)

        slope = (y_data_window[-1] - y_data_window[0]) / (
            x_data_window[-1] - x_data_window[0]
        )
        intersept = y_data_window[0] - slope * x_data_window[0]
        return (slope, intersept, x_data_window, y_data_window)

    def approx_line_update_position_slot(self, index: int) -> None:
        slope, intersept, _, y_data_window = self.approx_function(index)

        # Update approx line position and display parameters on the legend
        line = self.approx_lines[index]
        line.set_position(intercept_point=(0.0, intersept), slope=slope)
        _min, _max, _mean = [func(y_data_window) for func in [np.min, np.max, np.mean]]
        first, last = y_data_window[0], y_data_window[-1]

        # Create annotation text
        annotation_texts = []
        match self.role:
            case "LIVpower":
                annotation_texts.append(f"k={slope:.3E}")
                annotation_texts.append(f"I₀={(-intersept/slope):.3f}")
            case "LIVvoltage":
                annotation_texts.append(f"k={slope:.3E}")
                annotation_texts.append(f"V₀={intersept:.3E}")
            case "LIVspectrummean":
                annotation_texts.append(f"W₀={intersept:.3E}")
            case "LTpower":
                annotation_texts.append(f"k={slope:.3E}")
                annotation_texts.append(f"Δ={(last-first):.3f}")
            case "LTvoltage":
                annotation_texts.append(f"Δ={(last-first):.3f}")
                annotation_texts.append(f"mean={_mean:.3f}")
                annotation_texts.append(f"min={_min:.3f}")
                annotation_texts.append(f"max={_max:.3f}")
            case "LTtemperature":
                annotation_texts.append(f"mean={_mean:.3f}")
                annotation_texts.append(f"min={_min:.3f}")
                annotation_texts.append(f"max={_max:.3f}")
            case "PULSEpower":
                annotation_texts.append(f"k={slope:.3E}")
                annotation_texts.append(f"I₀={(-intersept/slope):.3f}")
            case "PULSEvoltage":
                annotation_texts.append(f"k={slope:.3E}")
                annotation_texts.append(f"v0={intersept:.3E}")
            case "PULSEintensity":
                pass
            case _:
                raise Exception(f"{self.role}: unknown role")
        line.set_label("\n".join(annotation_texts))
        self.controller.touch_legend.emit()
        self.controller.touch_plot.emit()
        return

    def touch_plot_slot(self) -> None:
        self.canvas.draw()
        return

    def touch_legend_slot(self) -> None:
        try:
            if self.legend:
                self.legend.remove()
        except:
            pass

        if not self.show_legend:
            self.axes.set_position(
                [
                    self.initial_box.x0,
                    self.initial_box.y0,
                    self.initial_box.width,
                    self.initial_box.height,
                ]
            )
            return

        if self.legend_position_outside:
            
            self.legend = self.axes.legend(
                loc="center left",
                bbox_to_anchor=(1.0, 0.5),
                frameon=True,
                fancybox=True,
                shadow=True,
                fontsize=10,
            )
            legend_bbox = self.legend.get_window_extent()
            legend_width_pixels = legend_bbox.width
            fig_width = self.fig.get_figwidth() * self.dpi
            legend_width_fig = legend_width_pixels / fig_width

            self.axes.set_position(
                [
                    self.initial_box.x0,
                    self.initial_box.y0,
                    self.initial_box.width - legend_width_fig,
                    self.initial_box.height,
                ]
            )

        if not self.legend_position_outside:
            self.axes.set_position(
                [
                    self.initial_box.x0,
                    self.initial_box.y0,
                    self.initial_box.width,
                    self.initial_box.height,
                ]
            )
            self.legend = self.axes.legend(
                loc="best", frameon=True, fancybox=True, shadow=True, fontsize=10
            )

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
        self.controller.touch_legend.emit()
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

        if self.role == "LIVspectrummean":
            selection.annotation.set_text(
                "\n".join(
                    [
                        selection.artist.get_label(),
                        f"{self.xlabel} = {selection.target[0]:.3f}",
                        f"{self.ylabel} = {selection.target[1]:.3f}",
                        f"ΔT, °C = {(selection.target[1]-self.cold_wavelength)/0.27:.3f}",
                    ]
                )
            )
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

    def show_legend_slot(self) -> None:
        self.show_legend = True
        self.controller.touch_legend.emit()
        self.controller.touch_plot.emit()
        return

    def hide_legend_slot(self) -> None:
        self.show_legend = False
        self.controller.touch_legend.emit()
        self.controller.touch_plot.emit()
        return

    def legend_position_changed_slot(self, is_outside) -> None:
        self.legend_position_outside = is_outside
        self.controller.touch_legend.emit()
        self.controller.touch_plot.emit()
        return

    def approx_mode_changed_slot(self, mode_index: int) -> None:
        if mode_index == 0:
            self.approx_function = self.approx_two_point
        if mode_index == 1:
            self.approx_function = self.approx_linear_regression
        for i in range(len(self.lines)):
            if self.approx_lines_visibility[i]:
                self.controller.draggable_changed_position.emit(i)
        return

    def cold_wavelength_changed_slot(self, edit: QLineEdit) -> None:
        try:
            value = float(edit.text())
        except:
            return

        self.cold_wavelength = value
        if self.secxaxis:
            self.secxaxis.remove()
        self.add_secondary_yaxis(
            "T, °C",
            "right",
            functions=(lambda x: (x - value) / 0.27, lambda x: x * 0.27 + value),
        )
        return

    def add_secondary_yaxis(
        self, label: str, posidion: str, functions: List[Callable]
    ) -> None:
        self.secxaxis = self.axes.secondary_yaxis(posidion, functions=functions)
        self.secxaxis.set_xlabel(label)
        self.controller.touch_plot.emit()
        return
