from typing import Tuple, List

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
            # # Add text annotation  # TODO
            # ylim = self.ax.get_ylim()
            # self.text = ax.text(
            #     x,
            #     ylim[1],
            #     f"x={x:.2f}",
            #     ha="center",
            #     va="bottom",
            #     color=color,
            #     bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
            # )
        )

        return

    def connect_controller(self, controller: "PlotController") -> None:
        self.controller = controller
        return

    def set_position(self, intercept_point, slope):
        """Set the line position and update display"""
        self.intercept_point = intercept_point
        self.slope = slope
        # self.line.set_xdata([x, x]) # TODO

        # # Update text position # TODO
        # ylim = self.ax.get_ylim()
        # self.text.set_position((x, ylim[1] - 0.1 * (ylim[1] - ylim[0])))
        # self.text.set_text(f"x={x:.2f}")

        self.canvas.draw()
        return
