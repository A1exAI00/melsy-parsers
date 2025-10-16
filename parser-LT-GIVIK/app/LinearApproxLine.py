from typing import Tuple, List
from time import time

from matplotlib.axes import Axes

from backend.misc import find_best_linear_subset
from app.PlotController import PlotController


class LinearApproxLine:
    def __init__(
        self,
        ax: Axes,
        intercept_point: Tuple[float, float],
        slope: float,
        color: str = "green",
        linewidth=2,
    ) -> None:

        self.ax = ax
        self.intercept_point = intercept_point
        self.slope = slope
        self.color = color
        self.linewidth = linewidth
        self.canvas = ax.figure.canvas

        self.line = self.ax.axline(
            xy1=self.intercept_point,
            slope=self.slope,
            color=self.color,
            linewidth=self.linewidth,
        )
        return

    def connect_controller(self, controller: "PlotController") -> None:
        self.controller = controller
        return

    def set_position(self, intercept_point, slope):
        """Set the line position and update display"""
        self.intercept_point = intercept_point
        self.slope = slope
        self.line.set_xy1(self.intercept_point)
        self.line.set_slope(self.slope)
        return

    def hide(self) -> None:
        self.line.set_linestyle("None")
        self.line.set_label("")
        return

    def show(self) -> None:
        self.line.set_linestyle("--")
        # self.line.set_label("")
        return

    def set_label(self, label: str) -> None:
        self.line.set_label(label)
        return
