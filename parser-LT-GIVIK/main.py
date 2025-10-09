from typing import List
import sys
from os.path import join, dirname, basename, splitext
from glob import iglob
import re

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QHBoxLayout, QWidget, QMdiArea, QMdiSubWindow, QComboBox, QLineEdit,
    QPushButton, QFileDialog, QCheckBox, QLabel
)
import clipboard as clip
import matplotlib as mpl
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator, AutoMinorLocator

from backend.Data import Data


mpl.rcParams['savefig.format'] = 'pdf'  # or 'png', 'svg', 'jpg', etc.


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        return


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window_title = "melsytech LT parser"

    def setup_ui(self):
        self.setWindowTitle("Simple Table Example")
        self.setGeometry(100, 100, 1600, 800)

        # Create Mdi Area
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        # Add subwindow to mdi area
        self.setup_window = QMdiSubWindow()
        self.setup_window.setWindowTitle("Setup window")
        self.mdi.addSubWindow(self.setup_window)

        # Define subwindow layout
        self.setup_window.setGeometry(3, 3, 1500, 500)
        setup_window_widget = QWidget()
        setup_window_layout = QVBoxLayout()
        setup_window_widget.setLayout(setup_window_layout)
        self.setup_window.setWidget(setup_window_widget)

        # Create combo box with work mode
        self.work_mode_combo = QComboBox()
        self.work_mode_combo.addItem("File mode")
        self.work_mode_combo.addItem("Folder mode")
        self.work_mode_combo.addItem("Recursive mode")
        setup_window_layout.addWidget(self.work_mode_combo)

        box = QHBoxLayout()
        filename_filter_label = QLabel(text="Filename filter")
        box.addWidget(filename_filter_label)
        self.filename_filter = QLineEdit("")
        box.addWidget(self.filename_filter)
        setup_window_layout.addLayout(box)

        # Create extention edit field
        box = QHBoxLayout()
        extention_label = QLabel(text="File extention filter")
        box.addWidget(extention_label)
        self.extention_edit = QLineEdit(".txt")
        box.addWidget(self.extention_edit)
        setup_window_layout.addLayout(box)

        # Create "add source" and "clear" buttons
        box = QHBoxLayout()
        self.add_source_button = QPushButton("Add source")
        self.add_source_button.clicked.connect(self.add_row_slot)
        box.addWidget(self.add_source_button)
        self.clear_setup_table_button = QPushButton("Clear")
        self.clear_setup_table_button.clicked.connect(
            self.clear_setup_table_slot)
        box.addWidget(self.clear_setup_table_button)
        setup_window_layout.addLayout(box)

        # Create table widget
        self.setup_table = QTableWidget()
        self.setup_table.setRowCount(1)
        self.setup_table.setColumnCount(3)
        self.setup_table.setHorizontalHeaderLabels(
            ["Path", "", "Naming"])

        type_prod_overwrite_widget = QWidget()
        type_prod_overwrite_box = QHBoxLayout()
        type_prod_overwrite_box.setContentsMargins(0, 0, 0, 0)
        self.type_prod_overwrite_edit = QLineEdit()
        self.type_prod_overwrite_edit.setPlaceholderText("2525_9999_01")
        type_prod_overwrite_button = QPushButton("Replace")
        type_prod_overwrite_button.clicked.connect(
            self.type_prod_overwrite_slot)
        type_prod_overwrite_box.addWidget(self.type_prod_overwrite_edit)
        type_prod_overwrite_box.addWidget(type_prod_overwrite_button)
        type_prod_overwrite_widget.setLayout(type_prod_overwrite_box)
        self.setup_table.setCellWidget(0, 2, type_prod_overwrite_widget)

        self.add_row_slot()
        setup_window_layout.addWidget(self.setup_table)

        # Optional: Adjust column widths
        self.setup_table.setColumnWidth(0, 1000)  # Name column
        # self.table.setColumnWidth(1, 80)   # Age column
        # self.table.setColumnWidth(2, 150)  # City column

        self.add_naming_checkbox = QCheckBox("Add naming")
        self.add_naming_checkbox.setChecked(True)
        setup_window_layout.addWidget(self.add_naming_checkbox)

        # Create "add source" button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_slot)
        setup_window_layout.addWidget(self.start_button)

        self.setup_window.show()
        return

    def add_row_slot(self) -> None:
        row_index = self.setup_table.rowCount()
        self.setup_table.setRowCount(row_index+1)
        self.setup_table.setItem(row_index, 0, QTableWidgetItem())
        edit_path_button = QPushButton("Edit path")
        edit_path_button.clicked.connect(
            lambda: self.edit_path_slot(row_index))
        self.setup_table.setCellWidget(row_index, 1, edit_path_button)
        self.setup_table.setItem(row_index, 2, QTableWidgetItem())
        return

    def edit_path_slot(self, row_index: int) -> None:
        match self.work_mode_combo.currentIndex():
            case 0:  # File mode
                self.edit_path_file_mode(row_index)
            case 1:  # Folder mode
                self.edit_path_other_modes(row_index, recursive=False)
            case 2:  # Recursive mode
                self.edit_path_other_modes(row_index, recursive=True)
        return

    def edit_path_file_mode(self, row_index: int) -> None:
        # Get paths of selected files
        filepaths = QFileDialog.getOpenFileNames(self, "Select file/files")[0]

        if not filepaths:
            return
        filepaths = sorted(filepaths)

        # Parse filepaths and edit setup table
        for (i, filepath) in enumerate(filepaths):

            # Current row to edit
            current_row = row_index + i

            # Add needed number of rows to fit all sources
            while current_row >= self.setup_table.rowCount():
                self.add_row_slot()

            # Set filepaths
            item = self.setup_table.item(current_row, 0)
            item.setText(filepath)

            file_basename = splitext(basename(filepath))[0]
            self.setup_table.item(current_row, 2).setText(file_basename)
        return

    def edit_path_other_modes(self, row_index: int, recursive: bool = False) -> None:
        folderpath = QFileDialog.getExistingDirectory(self, "Select folder")

        file_extention = self.extention_edit.text()
        if recursive:
            pattern = join(folderpath, "**", "*"+file_extention)
        else:
            pattern = join(folderpath, "*"+file_extention)
        filepaths = list(iglob(pattern, recursive=recursive))

        if not filepaths:
            return
        filepaths = sorted(filepaths)

        filepaths_filtered = []
        for (i, filepath) in enumerate(filepaths):
            file_basename = basename(filepath)
            pattern = self.filename_filter.text()
            if re.search(pattern, file_basename):
                filepaths_filtered.append(filepath)

        # Parse filepaths and edit setup table
        for (i, filepath) in enumerate(filepaths_filtered):
            # Current row to edit
            current_row = row_index + i

            # Add needed number of rows to fit all sources
            while current_row >= self.setup_table.rowCount():
                self.add_row_slot()

            # Set filepaths
            item = self.setup_table.item(current_row, 0)
            item.setText(filepath)

            # Parse filepath and save parent directories basenames
            file_basename = splitext(basename(filepath))[0]
            self.setup_table.item(current_row, 2).setText(file_basename)
        return

    def start_slot(self) -> None:
        datas: List[Data] = []
        for i in range(1, self.setup_table.rowCount()):
            # Get filepath from GUI
            item = self.setup_table.item(i, 0)
            filepath = item.text()

            # Check it is not empty
            if not filepath:
                continue

            # Parse file to data
            data = Data(filepath)
            data.read_lines_from_file()
            data.parse_GIVIK_version()
            data.parse_LT()
            data.parse_additional_data()

            # Get part name from GUI, add to data
            name_str = self.setup_table.item(i, 2).text()
            data.add_naming(name_str)

            datas.append(data)

        self.create_results_table(datas)
        self.create_results_plot(datas)
        return

    def create_results_table(self, datas: List[Data]) -> None:

        # Add new subwindow to Mdi Area
        self.table_window = QMdiSubWindow()
        self.table_window.setWindowTitle("LT table window")
        self.mdi.addSubWindow(self.table_window)

        # Define subwindow layout
        self.table_window.setGeometry(3, 3+500, 1500, 500)
        table_window_widget = QWidget()
        table_window_layout = QVBoxLayout()
        table_window_widget.setLayout(table_window_layout)
        self.table_window.setWidget(table_window_widget)

        # Create Quick clipboard button
        self.quick_clipboard_button = QPushButton("Quick clipboard")
        self.quick_clipboard_button.clicked.connect(self.quick_clipboard_slot)
        table_window_layout.addWidget(self.quick_clipboard_button)

        N_cols = []
        for data in datas:
            LT = data.LT
            LT_rows = list(LT.values())
            for row in LT_rows:
                N_cols.append(len(row)+1)
        max_cols = max(N_cols)

        # Create results table
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(max_cols)
        self.result_table.setRowCount(0)
        table_window_layout.addWidget(self.result_table)

        # Edit table
        for (data_i, data) in enumerate(datas):
            # Append additional data
            self.append_to_results_table(
                (data.naming_data_name, data.naming_data_value))
            for (name, value) in zip(data.additional_data_names, data.additional_data_values):
                # Skip naming if inchecked
                if (name == "Name") and (not self.add_naming_checkbox.isChecked()):
                    continue
                self.append_to_results_table((name, value))

            # Append LT data
            for (i, (name, values)) in enumerate(data.LT.items()):
                curr_line = [name,] + list(map(str, values))
                self.append_to_results_table(curr_line)

            # Append empty row spacer
            if (data_i != len(datas)-1):
                self.add_row_to_results_table()

        self.result_table.resizeColumnsToContents()
        self.table_window.show()
        return

    def add_row_to_results_table(self) -> None:
        new_row_index = self.result_table.rowCount()
        self.result_table.setRowCount(self.result_table.rowCount()+1)
        for i in range(self.result_table.columnCount()):
            self.result_table.setItem(new_row_index, i, QTableWidgetItem())
        return

    def quick_clipboard_slot(self) -> None:
        tmp = []
        for i in range(1, self.result_table.rowCount()):
            subtmp = []
            for j in range(self.result_table.columnCount()):
                value = self.result_table.item(i, j).text()
                subtmp.append(value)
            tmp.append("\t".join(subtmp))
        clip.copy("\n".join(tmp))
        return

    def append_to_results_table(self, array: List[str]) -> None:
        self.add_row_to_results_table()
        for (i, value) in enumerate(array):
            if value is None:
                value = ""
            elif "nan" in value.lower():
                value = "NaN"
            self.result_table.item(
                self.result_table.rowCount()-1, i).setText(value)
        return

    def clear_setup_table_slot(self) -> None:
        for i in range(1, self.setup_table.rowCount()):
            for j in range(self.setup_table.columnCount()):
                item = self.setup_table.item(i, j)
                if isinstance(item, QTableWidgetItem):
                    item.setText("")
        return

    def type_prod_overwrite_slot(self) -> None:
        value = self.type_prod_overwrite_edit.text()
        for i in range(1, self.setup_table.rowCount()):
            self.setup_table.item(i, 2).setText(value)
        return

    def date_overwrite_slot(self) -> None:
        value = self.date_overwrite_edit.text()
        for i in range(1, self.setup_table.rowCount()):
            self.setup_table.item(i, 3).setText(value)
        return

    def n_rad_overwrite_slot(self) -> None:
        value = self.n_rad_overwrite_edit.text()
        for i in range(1, self.setup_table.rowCount()):
            self.setup_table.item(i, 4).setText(value)
        return

    def create_results_plot(self, datas: List[Data]) -> None:
        # Add new subwindow to Mdi Area
        self.plot_window = QMdiSubWindow()
        # self.plot_window.
        self.plot_window.setWindowTitle("LT plot window")
        self.mdi.addSubWindow(self.plot_window)

        # Define subwindow layout
        self.plot_window.setGeometry(3+1000, 3, 500, 500)
        plot_window_widget = QWidget()
        plot_window_layout = QVBoxLayout()
        plot_window_widget.setLayout(plot_window_layout)
        self.plot_window.setWidget(plot_window_widget)

        sc = MplCanvas(self, width=5, height=4, dpi=100)
        toolbar = ModifiedToolbar(sc, None, self.plot_window)
        plot_window_layout.addWidget(toolbar)
        plot_window_layout.addWidget(sc)

        sc.axes.grid(True, linestyle='--', alpha=0.7)
        sc.axes.axhline(color="black")
        sc.axes.axvline(color="black")
        sc.axes.set_xlabel("Reletive time, h")
        sc.axes.set_ylabel("Power (avg), W")

        for data in datas:
            X_data = data.LT["Reletive time, h"]
            Y_data = data.LT["Power (avg), W"]
            label = data.naming_data_value
            sc.axes.plot(X_data, Y_data, linewidth=1, label=label)

        sc.axes.legend()
        sc.axes.xaxis.set_minor_locator(AutoMinorLocator(10))
        sc.axes.yaxis.set_minor_locator(AutoMinorLocator(10))
        sc.fig.tight_layout()

        self.plot_window.show()
        return


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setup_ui()
    window.show()
    sys.exit(app.exec())
