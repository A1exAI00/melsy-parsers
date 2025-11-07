from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ModifiedToolbar(NavigationToolbar):
    def __init__(self, canvas: FigureCanvas, fig: Figure, parent):
        self.canvas = canvas
        self.fig = fig
        super().__init__(self.canvas, parent)
        return

    def save_figure(self, *args):
        """Modify this function to always save figure with the same resolution"""
        prev_width, prev_height = self.fig.get_size_inches()
        self.fig.set_size_inches(10, 8)
        try:
            super().save_figure(*args)
        except: pass
        self.fig.set_size_inches(prev_width, prev_height)
        return
