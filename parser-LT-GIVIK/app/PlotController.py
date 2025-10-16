from PySide6.QtCore import QObject, Signal


class PlotController(QObject):
    plot_visibility_toggled = Signal(int)
    draggable_visibility_toggled = Signal(int)
    draggable_changed_position = Signal(int)
    touch_plot = Signal()

    def __init__(self):
        super().__init__()
