
from PySide6.QtWidgets import (
    QMdiSubWindow,
)
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from app.MplCanvas import MplCanvas

class ModifiedToolbar(NavigationToolbar):
    def __init__(self, canvas: MplCanvas, parent, plot_window: QMdiSubWindow):
        self.plot_window = plot_window
        self.canvas = canvas
        super().__init__(self.canvas, parent)
        return

    def save_figure_1(self, *args):
        W, H = 1000, 800
        prev_geomerty = self.plot_window.geometry()
        prev_width, prev_height = prev_geomerty.width(), prev_geomerty.height()
        self.plot_window.resize(W, H)
        self.tight()
        super().save_figure(*args)
        self.plot_window.resize(prev_width, prev_height)
        self.tight()
        return

    def save_figure_2(self, *args):
        self.tight()
        prev_width, prev_height = self.canvas.fig.get_size_inches()
        self.canvas.fig.set_size_inches(10, 8)
        super().save_figure(*args)
        self.canvas.fig.set_size_inches(prev_width, prev_height)
        self.tight()
        return

    def save_figure(self, *args):
        self.save_figure_2(*args)

    def tight(self):
        self.canvas.fig.tight_layout()
        return
