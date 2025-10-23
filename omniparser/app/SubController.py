from PySide6.QtCore import QObject, Signal


class SubController(QObject):
    draggable_line_position_changed = Signal()

    def __init__(self):
        super().__init__()
