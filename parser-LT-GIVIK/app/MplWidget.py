from typing import List

import numpy as np
from PySide6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from backend.misc import create_linear_approximation
from app.DraggableLine import DraggableVerticalLine
from app.PlotController import PlotController
from app.LinearApproxLine import LinearApproxLine


class MplWidget(QWidget):
    def __init__(
        self,
        controller: "PlotController",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller

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

        self.setup_ui()
        self.connect_controller()
        return

    def setup_ui(self) -> None:
        # Create matplotlib figure and canvas
        self.fig = Figure(figsize=self.figsize, dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)

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
            self.draggable_changed_position_slot
        )
        self.controller.draggable_changed_position.connect(
            self.approx_line_visibility_toggled_slot
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
        self.controller.touch_plot.emit()
        return

    ############################################################################
    # PAIRS OF DRAGGABLE LINES #################################################
    ############################################################################

    def add_draggable_lines(self):
        index = len(self.draggable_lines)
        color = self.lines[index][0].get_color()
        line1 = DraggableVerticalLine(self.axes, index, x=100, color=color, linewidth=1)
        line1.connect_controller(self.controller)
        line2 = DraggableVerticalLine(self.axes, index, x=200, color=color, linewidth=1)
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

    def draggable_changed_position_slot(self, index: int) -> None:
        if not self.approx_lines_visibility[index]:
            return
        
        x_data_all = self.lines[index][0].get_xdata(orig=True)
        y_data_all = self.lines[index][0].get_ydata(orig=True)
        draggable_line1, draggable_line2 = self.draggable_lines[index]
        x1, x2 = draggable_line1.x, draggable_line2.x

        x_indexes_window = []
        for i, x in enumerate(x_data_all):
            if x1 <= x and x < x2:
                x_indexes_window.append(i)

        x_data_window = [x_data_all[i] for i in x_indexes_window]
        y_data_window = [y_data_all[i] for i in x_indexes_window]

        _, slope, intersept = create_linear_approximation(x_data_window, y_data_window)

        line = self.approx_lines[index]
        line.set_position(intercept_point=(0.0, intersept), slope=slope)

        return
