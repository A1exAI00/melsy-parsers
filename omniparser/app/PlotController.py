from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QLineEdit


class PlotController(QObject):
    plot_visibility_toggled = Signal(int)
    draggable_visibility_toggled = Signal(int)
    draggable_changed_position = Signal(int)
    touch_plot = Signal()
    touch_legend = Signal()
    update_ticks = Signal(tuple)
    show_legend = Signal()
    hide_legend = Signal()
    approx_mode_changed = Signal(int)
    cold_wavelength_changed = Signal(QLineEdit)
    legend_position_changed = Signal(bool)

    def __init__(self):
        super().__init__()
