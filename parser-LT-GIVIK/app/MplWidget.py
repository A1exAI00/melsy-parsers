from typing import List

import numpy as np
from PySide6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from app.DraggableLine import DraggableVerticalLine

from app.MainController import MainController


class MplWidget(QWidget):
    def __init__(
        self,
        controller: "MainController",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller

        self.dpi = 100
        self.figsize = (5, 4)

        # Create matplotlib figure and canvas
        self.fig = Figure(figsize=self.figsize)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)

        # Create draggable line
        self.draggable_lines: List[DraggableVerticalLine] = []

        # Connect the signal
        self.controller.draggable_line_position_changed.connect(self.on_line_moved)

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        return

    def plot(self, *args, **kwargs) -> None:
        return self.axes.plot(*args, **kwargs)

    def add_draggable_line(self, x: float, color: str, linewidth: int = 1):
        line = DraggableVerticalLine(self.axes, x=x, color=color, linewidth=linewidth)
        line.connect_controller(self.controller)
        self.draggable_lines.append(line)
        return
    
    def rm_draggable_lines(self) -> None:
        for line in self.draggable_lines:
            line.rm()
        return

    def on_line_moved(self):
        pass
