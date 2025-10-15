from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from app.MplCanvas import MplCanvas


class ModifiedToolbar(NavigationToolbar):
    def __init__(self, canvas: MplCanvas, parent):
        self.canvas = canvas
        super().__init__(self.canvas, parent)
        return

    def save_figure(self, *args):
        """Modify this function to always save figure with the same resolution"""
        self.canvas.fig.tight_layout()
        prev_width, prev_height = self.canvas.fig.get_size_inches()
        self.canvas.fig.set_size_inches(10, 8)
        super().save_figure(*args)
        self.canvas.fig.set_size_inches(prev_width, prev_height)
        self.canvas.fig.tight_layout()
        return
