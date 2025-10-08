from typing import List
import sys
from os.path import join, dirname, basename
from glob import iglob
import re


from PySide6.QtWidgets import (QApplication, QMainWindow,
                               QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QHBoxLayout, QWidget, QMdiArea, QMdiSubWindow, QComboBox, QLineEdit, QPushButton, QFileDialog, QCheckBox, QLabel)
import clipboard as clip

from backend.Data import Data


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window_title = "melsytech LIV parser"

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
        self.filename_filter = QLineEdit("LIV|SPEC")
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
        self.setup_table.setColumnCount(5)
        self.setup_table.setHorizontalHeaderLabels(
            ["Path", "", "Type prod", "Date", "№ Rad"])
        
        type_prod_overwrite_widget = QWidget()
        type_prod_overwrite_box = QHBoxLayout()
        type_prod_overwrite_box.setContentsMargins(0, 0, 0, 0)
        self.type_prod_overwrite_edit = QLineEdit()
        self.type_prod_overwrite_edit.setPlaceholderText("2525")
        type_prod_overwrite_button = QPushButton("Replace")
        type_prod_overwrite_button.clicked.connect(self.type_prod_overwrite_slot)
        type_prod_overwrite_box.addWidget(self.type_prod_overwrite_edit)
        type_prod_overwrite_box.addWidget(type_prod_overwrite_button)
        type_prod_overwrite_widget.setLayout(type_prod_overwrite_box)
        self.setup_table.setCellWidget(0, 2, type_prod_overwrite_widget)

        date_overwrite_widget = QWidget()
        date_overwrite_box = QHBoxLayout()
        date_overwrite_box.setContentsMargins(0, 0, 0, 0)
        self.date_overwrite_edit = QLineEdit()
        self.date_overwrite_edit.setPlaceholderText("9999")
        date_overwrite_button = QPushButton("Replace")
        date_overwrite_button.clicked.connect(self.date_overwrite_slot)
        date_overwrite_box.addWidget(self.date_overwrite_edit)
        date_overwrite_box.addWidget(date_overwrite_button)
        date_overwrite_widget.setLayout(date_overwrite_box)
        self.setup_table.setCellWidget(0, 3, date_overwrite_widget)

        n_rad_overwrite_widget = QWidget()
        n_rad_overwrite_box = QHBoxLayout()
        n_rad_overwrite_box.setContentsMargins(0, 0, 0, 0)
        self.n_rad_overwrite_edit = QLineEdit()
        self.n_rad_overwrite_edit.setPlaceholderText("01")
        n_rad_overwrite_button = QPushButton("Replace")
        n_rad_overwrite_button.clicked.connect(self.n_rad_overwrite_slot)
        n_rad_overwrite_box.addWidget(self.n_rad_overwrite_edit)
        n_rad_overwrite_box.addWidget(n_rad_overwrite_button)
        n_rad_overwrite_widget.setLayout(n_rad_overwrite_box)
        self.setup_table.setCellWidget(0, 4, n_rad_overwrite_widget)

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
        self.setup_table.setItem(row_index, 3, QTableWidgetItem())
        self.setup_table.setItem(row_index, 4, QTableWidgetItem())
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

            # Parse filepath and save parent directories basenames
            parents_basenames = list(
                map(basename, get_3_parents_dirs(filepath)))
            for i in range(len(parents_basenames)):
                item = self.setup_table.item(current_row, 2+i)
                item.setText(list(reversed(parents_basenames))[i])
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
            parents_basenames = list(
                map(basename, get_3_parents_dirs(filepath)))
            for i in range(len(parents_basenames)):
                item = self.setup_table.item(current_row, 2+i)
                item.setText(list(reversed(parents_basenames))[i])
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
            data.parse()

            # Get part name from GUI, add to data
            name_strs = [self.setup_table.item(
                i, 2+j).text() for j in range(3)]
            name_strs = [each for each in name_strs if each]
            name_str = "-".join(name_strs)
            data.add_nameing(name_str)

            datas.append(data)

        self.create_results_table(datas)
        return

    def create_results_table(self, datas: List[Data]) -> None:
        N_cols = []
        for data in datas:
            LIV = data.LIV
            LIV_rows = list(LIV.values())
            for row in LIV_rows:
                N_cols.append(len(row)+1)
        max_cols = max(N_cols)

        # Add new subwindow to Mdi Area
        self.table_window = QMdiSubWindow()
        self.table_window.setWindowTitle("LIV table window")
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

        # Create results table
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(max_cols)
        self.result_table.setRowCount(0)
        table_window_layout.addWidget(self.result_table)

        # Edit table
        for (data_i, data) in enumerate(datas):
            # Append additional data
            self.append_to_results_table((data.naming_data_name, data.naming_data_value))
            for (name, value) in zip(data.additional_data_names, data.additional_data_values):
                # Skip naming if inchecked
                if (name == "Name") and (not self.add_naming_checkbox.isChecked()):
                    continue
                self.append_to_results_table((name, value))

            # Append LIV data
            for (i, (name, values)) in enumerate(data.LIV.items()):
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
            if "nan" in value.lower():
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


def get_3_parents_dirs(filepath: str) -> List[str]:
    parent1 = dirname(filepath)
    parent2 = dirname(parent1)
    parent3 = dirname(parent2)
    return (parent1, parent2, parent3)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setup_ui()
    window.show()
    sys.exit(app.exec())
