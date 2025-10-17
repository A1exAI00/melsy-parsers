from typing import List, Dict
from os.path import join, basename, splitext
from glob import iglob
import re

from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMdiArea,
    QMdiSubWindow,
    QComboBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QLabel,
)

from backend.LTdata import LTdata, LTparser
from app.MainController import MainController


class SubwindowSetup(QMdiSubWindow):
    def __init__(self, controller: "MainController", mdi: QMdiArea):
        self.controller = controller
        self.mdi = mdi
        super().__init__()
        self.setup_ui()
        pass

    def setup_ui(self) -> None:
        self.setWindowTitle("Setup window")
        self.mdi.addSubWindow(self)

        # Define subwindow layout
        self.setGeometry(3, 3, 1500, 500)
        window_widget = QWidget()
        window_layout = QVBoxLayout()
        window_widget.setLayout(window_layout)
        self.setWidget(window_widget)

        # Create combo box with work mode
        self.work_mode_combo = QComboBox()
        self.work_mode_combo.addItem("File mode")
        self.work_mode_combo.addItem("Folder mode")
        self.work_mode_combo.addItem("Recursive mode")
        window_layout.addWidget(self.work_mode_combo)

        box = QHBoxLayout()
        filename_filter_label = QLabel(text="Filename filter")
        box.addWidget(filename_filter_label)
        self.filename_filter = QLineEdit("")
        box.addWidget(self.filename_filter)
        window_layout.addLayout(box)

        # Create extention edit field
        box = QHBoxLayout()
        extention_label = QLabel(text="File extention filter")
        box.addWidget(extention_label)
        self.extention_edit = QLineEdit(".txt")
        box.addWidget(self.extention_edit)
        window_layout.addLayout(box)

        # Create "add source" and "clear" buttons
        box = QHBoxLayout()
        self.add_source_button = QPushButton("Add source")
        self.add_source_button.clicked.connect(self.add_row_slot)
        box.addWidget(self.add_source_button)
        self.clear_table_button = QPushButton("Clear")
        self.clear_table_button.clicked.connect(self.clear_table_slot)
        box.addWidget(self.clear_table_button)
        window_layout.addLayout(box)

        # Create table widget
        self.table = QTableWidget()
        self.table.setRowCount(1)
        self.table.setColumnCount(3)
        self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)

        self.table.setHorizontalHeaderLabels(["Path", "", "Naming"])

        naming_overwrite_widget = QWidget()
        naming_overwrite_box = QHBoxLayout()
        naming_overwrite_box.setContentsMargins(0, 0, 0, 0)
        self.naming_overwrite_edit = QLineEdit()
        self.naming_overwrite_edit.setPlaceholderText("2525_9999_01")
        naming_overwrite_button = QPushButton("Replace")
        naming_overwrite_button.clicked.connect(self.naming_overwrite_slot)
        naming_overwrite_box.addWidget(self.naming_overwrite_edit)
        naming_overwrite_box.addWidget(naming_overwrite_button)
        naming_overwrite_widget.setLayout(naming_overwrite_box)
        self.table.setCellWidget(0, 2, naming_overwrite_widget)

        self.add_row_slot()
        window_layout.addWidget(self.table)

        # Adjust column width
        self.table.setColumnWidth(0, 1000)  # Name column

        self.add_naming_checkbox = QCheckBox("Add naming")
        self.add_naming_checkbox.setChecked(True)
        window_layout.addWidget(self.add_naming_checkbox)

        # Create "add source" button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_slot)
        window_layout.addWidget(self.start_button)

        self.show()
        return

    def connect_controller(self) -> None:
        return

    def naming_overwrite_slot(self) -> None:
        value = self.naming_overwrite_edit.text()
        for i in range(1, self.table.rowCount()):
            self.table.item(i, 2).setText(value)
        return

    def clear_table_slot(self) -> None:
        for i in range(1, self.table.rowCount()):
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if isinstance(item, QTableWidgetItem):
                    item.setText("")
        return

    def add_row_slot(self) -> None:
        row_index = self.table.rowCount()
        self.table.setRowCount(row_index + 1)
        self.table.setItem(row_index, 0, QTableWidgetItem())
        edit_path_button = QPushButton("Edit path")
        edit_path_button.clicked.connect(lambda: self.edit_path_slot(row_index))
        self.table.setCellWidget(row_index, 1, edit_path_button)
        self.table.setItem(row_index, 2, QTableWidgetItem())
        return

    def edit_path_slot(self, row_index: int) -> None:
        self.controller.start_cooldown_release.emit()
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
        for i, filepath in enumerate(filepaths):

            # Current row to edit
            current_row = row_index + i

            # Add needed number of rows to fit all sources
            while current_row >= self.table.rowCount():
                self.add_row_slot()

            # Set filepaths
            item = self.table.item(current_row, 0)
            item.setText(filepath)

            file_basename = splitext(basename(filepath))[0]
            self.table.item(current_row, 2).setText(file_basename)
        return

    def edit_path_other_modes(self, row_index: int, recursive: bool = False) -> None:
        folderpath = QFileDialog.getExistingDirectory(self, "Select folder")

        file_extention = self.extention_edit.text()
        if recursive:
            pattern = join(folderpath, "**", "*" + file_extention)
        else:
            pattern = join(folderpath, "*" + file_extention)
        filepaths = list(iglob(pattern, recursive=recursive))

        if not filepaths:
            return
        filepaths = sorted(filepaths)

        filepaths_filtered = []
        for i, filepath in enumerate(filepaths):
            file_basename = basename(filepath)
            pattern = self.filename_filter.text()
            if re.search(pattern, file_basename):
                filepaths_filtered.append(filepath)

        # Parse filepaths and edit setup table
        for i, filepath in enumerate(filepaths_filtered):
            # Current row to edit
            current_row = row_index + i

            # Add needed number of rows to fit all sources
            while current_row >= self.table.rowCount():
                self.add_row_slot()

            # Set filepaths
            item = self.table.item(current_row, 0)
            item.setText(filepath)

            # Parse filepath and save parent directories basenames
            file_basename = splitext(basename(filepath))[0]
            self.table.item(current_row, 2).setText(file_basename)
        return

    def parse(self) -> List[LTdata]:
        parser = LTparser()
        datas: List[LTdata] = []
        for i in range(1, self.table.rowCount()):
            # Get filepath from GUI
            item = self.table.item(i, 0)
            filepath = item.text()

            # Check it is not empty
            if not filepath:
                continue

            # Parse file to data
            data = parser.parse(filepath)

            # Get part name from GUI, add to data
            data.add_other_data("Name", self.table.item(i, 2).text())

            datas.append(data)
        return datas

    def start_slot(self) -> None:
        datas = self.parse()
        _dict = {"datas": datas, "add_naming": self.add_naming_checkbox.isChecked()}
        self.controller.after_start_pressed_signal.emit(_dict)
        return
