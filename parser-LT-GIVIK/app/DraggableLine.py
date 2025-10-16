from matplotlib.axes import Axes

from app.MainController import MainController


class DraggableVerticalLine:
    def __init__(self, ax: Axes, x: float, color: str = "red", linewidth=2) -> None:
        self.ax = ax
        self.x = x
        self.color = color
        self.linewidth = linewidth
        self.canvas = ax.figure.canvas

        # Create the vertical line
        self.line = ax.axvline(
            x=self.x,
            color=self.color,
            linewidth=self.linewidth,
            picker=True,
            pickradius=10,
        )

        # Add text annotation
        ylim = self.ax.get_ylim()
        self.text = ax.text(
            x,
            0.1 * (ylim[1] - ylim[0]),
            f"x={x:.2f}",
            ha="center",
            va="bottom",
            color=color,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        )

        # Connect event handlers
        self.cid_press = self.canvas.mpl_connect("button_press_event", self.on_press)
        self.cid_release = self.canvas.mpl_connect(
            "button_release_event", self.on_release
        )
        self.cid_motion = self.canvas.mpl_connect("motion_notify_event", self.on_motion)

        self.pressed = False
        return

    def connect_controller(self, controller: "MainController") -> None:
        self.controller = controller
        return

    def on_press(self, event):
        if event.inaxes != self.ax:
            return

        contains, attrd = self.line.contains(event)
        if contains:
            self.pressed = True
            self.offset = event.xdata - self.x
        return

    def on_motion(self, event):
        if not self.pressed:
            return
        if event.inaxes != self.ax:
            return

        # Update line position
        new_x = event.xdata - self.offset
        self.set_position(new_x)

        # Emit signal
        self.controller.draggable_line_position_changed.emit()
        return

    def on_release(self, event):
        if self.pressed:
            self.pressed = False
        return

    def set_position(self, x):
        """Set the line position and update display"""
        self.x = x
        self.line.set_xdata([x, x])

        # Update text position
        ylim = self.ax.get_ylim()
        self.text.set_position((x, 0.1 * (ylim[1] - ylim[0])))
        self.text.set_text(f"x={x:.2f}")

        self.canvas.draw()
        return

    def disconnect(self):
        """Disconnect all the stored connection ids"""
        self.canvas.mpl_disconnect(self.cid_press)
        self.canvas.mpl_disconnect(self.cid_release)
        self.canvas.mpl_disconnect(self.cid_motion)
        return
