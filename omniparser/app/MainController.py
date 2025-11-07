from PySide6.QtCore import QObject, Signal


class MainController(QObject):
    after_LIV_start_pressed_signal = Signal(dict)
    after_LT_start_pressed_signal = Signal(dict)
    after_PULSE_start_pressed_signal = Signal(dict)
    start_cooldown_place = Signal()
    start_cooldown_release = Signal()

    def __init__(self):
        super().__init__()
