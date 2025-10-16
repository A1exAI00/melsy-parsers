from typing import List

import numpy as np
from PySide6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from app.DraggableLine import DraggableVerticalLine

from app.PlotController import PlotController


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

        self.lines_visibility: List[bool] = []
        self.lines: List[List[Line2D]] = []
        self.labels: List[str] = []

        # Create draggable line
        self.draggable_lines: List[List[DraggableVerticalLine]] = []
        self.draggable_lines_visibibity: List[bool] = []

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
        self.controller.draggable_changed_position.connect(self.on_line_moved)
        self.controller.plot_visibility_toggled.connect(
            self.plot_visibility_toggled_slot
        )
        self.controller.draggable_visibility_toggled.connect(
            self.draggable_visibility_toggled_slot
        )
        self.controller.draggable_changed_position.connect(
            self.draggable_changed_position_slot
        )
        return

    def plot(self, X_data, Y_data, label, linewidth) -> None:
        line = self.axes.plot(X_data, Y_data, label=label, linewidth=linewidth)
        self.lines.append(line)
        self.labels.append(label)
        self.lines_visibility.append(True)

        index = len(self.draggable_lines)
        self.add_draggable_lines()
        self.hide_draggable_lines(index)
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

    def on_line_moved(self) -> None:
        pass

    def plot_visibility_toggled_slot(self, index: int) -> None:
        prev_visible = self.lines_visibility[index]
        if prev_visible:
            self.hide_plot(index)
        else: 
            self.show_plot(index)
        self.controller.touch_plot.emit()
        return

    def draggable_visibility_toggled_slot(self, index: int) -> None:
        prev_visible = self.draggable_lines_visibibity[index]
        if prev_visible:
            self.hide_draggable_lines(index)
        else:
            self.show_draggable_lines(index)
            # TODO find best linear section 
        self.controller.touch_plot.emit()
        return

    def draggable_changed_position_slot(self, index: int) -> None:
        return