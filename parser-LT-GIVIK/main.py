from typing import List, Dict
import sys
from os.path import join, dirname, basename, splitext
from glob import iglob
import re

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QHBoxLayout, QWidget, QMdiArea, QMdiSubWindow, QComboBox, QLineEdit,
    QPushButton, QFileDialog, QCheckBox, QLabel, QGridLayout
)
from PySide6.QtGui import QAction
import clipboard as clip
import matplotlib as mpl
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator, AutoMinorLocator, FixedLocator, AutoLocator
import mplcursors

from backend.Data import Data


mpl.rcParams['savefig.format'] = 'png'  # or 'png', 'svg', 'jpg', 'pdf' etc.


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


class ModifiedQMdiSubwindow(QMdiSubWindow):
    def __init__(self, mainwindow: "MainWindow"):
        self.mainwindow = mainwindow
        super().__init__()
        return

    def closeEvent(self, closeEvent):
        self.mainwindow.status = "Ready"
        self.mainwindow.plot_window.close()
        return super().closeEvent(closeEvent)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window_title = "melsytech LT parser"
        self.plot_windows: Dict[str, QMdiSubWindow] = {}
        self.status = "Ready"

    def setup_ui(self):
        self.setWindowTitle(self.window_title)
        self.setGeometry(100, 100, 1600, 800)

        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        self.create_menubar()
        self.create_setup_window()
        return

    def create_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&Click me!")

        new_action = QAction("&Open setup window", self)
        new_action.triggered.connect(self.create_setup_window)
        file_menu.addAction(new_action)

    def create_setup_window(self) -> None:
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
        self.setup_table.setHorizontalHeaderLabels(["Path", "", "Naming"])

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

        # Adjust column width
        self.setup_table.setColumnWidth(0, 1000)  # Name column

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

        self.status = "Ready"
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
        match self.status:
            case "Ready":
                pass
            case "Processing" | "Done":
                return

        self.status = "Processing"

        datas = self.parse()
        self.create_results_table(datas)
        self.create_power_plot_window(datas)
        try:
            pass
        except:
            print("error")
            self.status = "Ready"
            return

        self.status = "Done"
        return

    def parse(self) -> List[Data]:
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
        return datas

    def create_results_table(self, datas: List[Data]) -> None:

        # Add new subwindow to Mdi Area
        self.table_window = ModifiedQMdiSubwindow(self)
        self.table_window.setWindowTitle("LT table window")
        self.mdi.addSubWindow(self.table_window)

        # Define subwindow layout
        self.table_window.setGeometry(3, 3+500, 1500, 500)
        table_window_widget = QWidget()
        table_window_layout = QVBoxLayout()
        table_window_widget.setLayout(table_window_layout)
        self.table_window.setWidget(table_window_widget)

        # Create "Quick clipboard" and "Show plot" buttons
        box = QHBoxLayout()
        self.quick_clipboard_button = QPushButton("Quick clipboard")
        self.quick_clipboard_button.clicked.connect(self.quick_clipboard_slot)
        box.addWidget(self.quick_clipboard_button)

        self.show_plot_button = QPushButton("Open power(time) plot")
        self.show_plot_button.clicked.connect(
            lambda: self.create_power_plot_window(datas))
        box.addWidget(self.show_plot_button)

        self.show_plot_button = QPushButton("Open voltage(time) plot")
        self.show_plot_button.clicked.connect(
            lambda: self.create_voltage_plot_window(datas))
        box.addWidget(self.show_plot_button)

        self.show_plot_button = QPushButton("Open temperature(time) plot")
        self.show_plot_button.clicked.connect(
            lambda: self.create_temperature_plot_window(datas))
        box.addWidget(self.show_plot_button)

        table_window_layout.addLayout(box)

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
            if self.add_naming_checkbox.isChecked():
                self.append_to_results_table(data.get_naming())
            for (name, value) in zip(data.additional_data_names, data.additional_data_values):
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
        for i in range(self.result_table.rowCount()):
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

    def create_plot_window(self, tag: str, role: str, datas: List[Data]) -> None:
        match role:
            case "power":
                this_title = "LT power(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Power (avg), W"
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 600
            case "voltage":
                this_title = "LT voltage(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Voltage, V"
                datas = list(
                    filter(lambda each: each.GIVIK_version == 2, datas))
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 600
            case "temperature":
                this_title = "LT temperature(time) plot window"
                X_axis_label = "Reletive time, h"
                Y_axis_label = "Tank water temp., C"
                datas = list(
                    filter(lambda each: each.GIVIK_version == 2, datas))
                sub_x_position, sub_y_position = 1003, 3
                sub_w, sub_h = 500, 600

        # Add new subwindow to Mdi Area
        this_plot_window = QMdiSubWindow()
        self.plot_windows[tag] = this_plot_window
        this_plot_window.setWindowTitle(this_title)
        self.mdi.addSubWindow(this_plot_window)

        # Define subwindow layout
        this_plot_window.setGeometry(
            sub_x_position, sub_y_position, sub_w, sub_h)
        plot_window_widget = QWidget()
        plot_window_layout = QVBoxLayout()
        plot_window_widget.setLayout(plot_window_layout)
        this_plot_window.setWidget(plot_window_widget)

        # Manual tick locators setup
        grid_layout_edits = QGridLayout()
        x_multiple_locator_edit = QLineEdit(placeholderText="100")
        y_multiple_locator_edit = QLineEdit(placeholderText="5")
        grid_layout_edits.addWidget(QLabel("X Axis Multiple Locator"), 0, 0)
        grid_layout_edits.addWidget(QLabel("Y Axis Multiple Locator"), 1, 0)
        grid_layout_edits.addWidget(x_multiple_locator_edit, 0, 1)
        grid_layout_edits.addWidget(y_multiple_locator_edit, 1, 1)
        plot_window_layout.addLayout(grid_layout_edits)

        # Create canvas backend
        sc = MplCanvas(self, width=5, height=4, dpi=100)
        toolbar = ModifiedToolbar(sc, None, this_plot_window)
        plot_window_layout.addWidget(toolbar)
        plot_window_layout.addWidget(sc)

        # Add grid, axis lines, axis labels
        sc.axes.grid(True, linestyle='--', alpha=0.7)
        sc.axes.axhline(color="black")
        sc.axes.axvline(color="black")
        sc.axes.set_xlabel(X_axis_label)
        sc.axes.set_ylabel(Y_axis_label)

        # Add minor tick locators
        sc.axes.xaxis.set_minor_locator(AutoMinorLocator(10))
        sc.axes.yaxis.set_minor_locator(AutoMinorLocator(10))

        # Add plot lines
        lines = []
        for data in datas:
            X_data = data.LT[X_axis_label]
            Y_data = data.LT[Y_axis_label]
            label = data.naming_data["Name"]
            line = sc.axes.plot(X_data, Y_data, linewidth=1, label=label)
            lines.append(line)

        # Add legend
        sc.axes.legend()

        # Set tight layout
        sc.fig.tight_layout()

        # Create temporary slot function for manually changing tick locators
        def tmp_locator_changed_slot():
            X_Y_strings = (
                x_multiple_locator_edit.text().strip("\n"),
                y_multiple_locator_edit.text().strip("\n")
            )
            axes = sc.axes.xaxis, sc.axes.yaxis

            # Try to set multiple locators
            for (string, axis) in zip(X_Y_strings, axes):
                try:
                    integer = int(string)
                    axis.set_major_locator(MultipleLocator(integer))
                except:
                    axis.set_major_locator(AutoLocator())

            # Force redraw plot
            sc.draw()
            return

        # Connect tick locator signals and slots
        x_multiple_locator_edit.editingFinished.connect(
            tmp_locator_changed_slot)
        y_multiple_locator_edit.editingFinished.connect(
            tmp_locator_changed_slot)

        # Create cursor for plot
        cursor = mplcursors.cursor(sc.axes)
        cursor.connect("add", lambda sel: sel.annotation.set_text(
            "\n".join([
                sel.artist.get_label(),
                f"Time = {sel.target[0]:.3f} h",
                f"Power = {sel.target[1]:.3f} W",
            ])
        ))

        # Add checkboxes for each plot to show/hide plot
        grid_layout = QGridLayout()
        plot_window_layout.addLayout(grid_layout)

        # Generate checkboxes in a grid
        checkboxes = []
        columns, row, col = 3, 0, 0
        for (i, data) in enumerate(datas):
            checkbox = QCheckBox(data.naming_data["Name"])
            checkbox.setChecked(True)
            grid_layout.addWidget(checkbox, row, col)
            checkboxes.append(checkbox)

            # Iterate over columns
            col += 1
            if col >= columns:
                col = 0
                row += 1

        # Add slot function to update plot visibility
        def tmp_slot():
            for (i, (checkbox, line)) in enumerate(zip(checkboxes, lines)):
                line[0].set_linestyle(
                    "solid" if checkbox.isChecked() else "None")
                line[0].set_label(
                    datas[i].naming_data["Name"] if checkbox.isChecked() else "")
                sc.axes.legend()
            sc.draw()
            return

        # Connect visibility slots and signals
        for (i, data) in enumerate(datas):
            checkboxes[i].stateChanged.connect(tmp_slot)

        # Show plot window
        this_plot_window.show()
        return

    def create_power_plot_window(self, datas: List[Data]) -> None:
        self.create_plot_window(tag="1", role="power", datas=datas)
        return

    def create_voltage_plot_window(self, datas: List[Data]) -> None:
        self.create_plot_window(tag="2", role="voltage", datas=datas)
        return

    def create_temperature_plot_window(self, datas: List[Data]) -> None:
        self.create_plot_window(tag="3", role="temperature", datas=datas)
        return


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setup_ui()
    window.show()
    sys.exit(app.exec())
