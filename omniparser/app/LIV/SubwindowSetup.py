from typing import List
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
    QFormLayout,
    QSpinBox,
)

from backend.misc import get_3_parents_dirs
from backend.LIVdata import LIVdata, LIVparser
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

        form = QFormLayout()
        window_layout.addLayout(form)

        self.work_mode_combo = QComboBox()
        self.work_mode_combo.setToolTip(
            "Combo box to choose working mode. Working mode will define a behaviour of 'Edit path' button.\nFor more infornation open manual."
        )
        self.work_mode_combo.addItems(["File mode", "Folder mode", "Recursive mode"])
        form.addRow("Working mode", self.work_mode_combo)

        self.filename_filter = QLineEdit("LIV|SPEC")
        self.filename_filter.setToolTip(
            "Here you can enter a pattern (python regex) to filter files by their filenames.\nFilename here is a basename of a file without it's extention."
        )
        form.addRow("Filename filter", self.filename_filter)

        self.extention_edit = QLineEdit("txt")
        self.extention_edit.setToolTip(
            "Here you can enter a pattern (python regex) to filter files by their extentions."
        )
        form.addRow("File extention filter", self.extention_edit)

        # Create "add source" and "clear" buttons
        box = QHBoxLayout()
        self.add_source_button = QPushButton("Add source")
        self.add_source_button.setToolTip(
            "This button will add an empty row at the end of setup table."
        )
        self.add_source_button.clicked.connect(self.add_row_slot)
        box.addWidget(self.add_source_button)
        self.clear_table_button = QPushButton("Clear")
        self.clear_table_button.setToolTip(
            "This button will clear all input fields of setup table."
        )
        self.clear_table_button.clicked.connect(self.clear_table_slot)
        box.addWidget(self.clear_table_button)
        window_layout.addLayout(box)

        # Create table widget
        self.table = QTableWidget()
        self.table.setRowCount(1)
        self.table.setColumnCount(5)
        self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setHorizontalHeaderLabels(["Path", "", "Type prod", "Date", "№ Rad"])

        type_prod_overwrite_widget = QWidget()
        type_prod_overwrite_box = QHBoxLayout()
        type_prod_overwrite_box.setContentsMargins(0, 0, 0, 0)
        self.type_prod_overwrite_edit = QLineEdit()
        self.type_prod_overwrite_edit.setPlaceholderText("2525")
        type_prod_overwrite_button = QPushButton("Replace")
        type_prod_overwrite_button.setToolTip(
            "This button will replace all values in this column with a value placed in an input field to the left of this button.\n Note that gray text is an example (placeholder text), it is considered an empty input field."
        )
        type_prod_overwrite_button.clicked.connect(self.type_prod_overwrite_slot)
        type_prod_overwrite_box.addWidget(self.type_prod_overwrite_edit)
        type_prod_overwrite_box.addWidget(type_prod_overwrite_button)
        type_prod_overwrite_widget.setLayout(type_prod_overwrite_box)
        self.table.setCellWidget(0, 2, type_prod_overwrite_widget)

        date_overwrite_widget = QWidget()
        date_overwrite_box = QHBoxLayout()
        date_overwrite_box.setContentsMargins(0, 0, 0, 0)
        self.date_overwrite_edit = QLineEdit()
        self.date_overwrite_edit.setPlaceholderText("9999")
        date_overwrite_button = QPushButton("Replace")
        date_overwrite_button.setToolTip(
            "This button will replace all values in this column with a value placed in an input field to the left of this button.\n Note that gray text is an example (placeholder text), it is considered an empty input field."
        )
        date_overwrite_button.clicked.connect(self.date_overwrite_slot)
        date_overwrite_box.addWidget(self.date_overwrite_edit)
        date_overwrite_box.addWidget(date_overwrite_button)
        date_overwrite_widget.setLayout(date_overwrite_box)
        self.table.setCellWidget(0, 3, date_overwrite_widget)

        n_rad_overwrite_widget = QWidget()
        n_rad_overwrite_box = QHBoxLayout()
        n_rad_overwrite_box.setContentsMargins(0, 0, 0, 0)
        self.n_rad_overwrite_edit = QLineEdit()
        self.n_rad_overwrite_edit.setPlaceholderText("01")
        n_rad_overwrite_button = QPushButton("Replace")
        n_rad_overwrite_button.setToolTip(
            "This button will replace all values in this column with a value placed in an input field to the left of this button.\n Note that gray text is an example (placeholder text), it is considered an empty input field."
        )
        n_rad_overwrite_button.clicked.connect(self.n_rad_overwrite_slot)
        n_rad_overwrite_box.addWidget(self.n_rad_overwrite_edit)
        n_rad_overwrite_box.addWidget(n_rad_overwrite_button)
        n_rad_overwrite_widget.setLayout(n_rad_overwrite_box)
        self.table.setCellWidget(0, 4, n_rad_overwrite_widget)

        self.add_row_slot()
        window_layout.addWidget(self.table)

        # Adjust column width
        self.table.setColumnWidth(0, 1000)  # Name column

        self.add_naming_checkbox = QCheckBox("Add naming")
        self.add_naming_checkbox.setToolTip(
            "If this checkbox is checked, naming from 'Type prod', 'Date' and '№ Rad' will appear in result table.\nIf not, naming will not appear in result table."
        )
        self.add_naming_checkbox.setChecked(True)
        window_layout.addWidget(self.add_naming_checkbox)

        form2 = QFormLayout()
        window_layout.addLayout(form2)
        self.ndigits_spinbox = QSpinBox()
        self.ndigits_spinbox.setMaximum(10)
        self.ndigits_spinbox.setMinimum(0)
        self.ndigits_spinbox.setValue(2)
        form2.addRow("# of digits after point", self.ndigits_spinbox)

        self.start_button = QPushButton("Start")
        self.start_button.setToolTip(
            "This button will start parsing process and open result subwindow after successful parsing."
        )
        self.start_button.clicked.connect(self.start_slot)
        window_layout.addWidget(self.start_button)

        self.show()
        return

    def connect_controller(self) -> None:
        return

    def type_prod_overwrite_slot(self) -> None:
        value = self.type_prod_overwrite_edit.text()
        for i in range(1, self.table.rowCount()):
            self.table.item(i, 2).setText(value)
        return

    def date_overwrite_slot(self) -> None:
        value = self.date_overwrite_edit.text()
        for i in range(1, self.table.rowCount()):
            self.table.item(i, 3).setText(value)
        return

    def n_rad_overwrite_slot(self) -> None:
        value = self.n_rad_overwrite_edit.text()
        for i in range(1, self.table.rowCount()):
            self.table.item(i, 4).setText(value)
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
        edit_path_button.setToolTip(
            "This button will open OS dialog window, where you will need to choose files or folder.\nSelected files will appear in this row's and subsequent rows' 'Path' fields."
        )
        edit_path_button.clicked.connect(lambda: self.edit_path_slot(row_index))
        self.table.setCellWidget(row_index, 1, edit_path_button)
        self.table.setItem(row_index, 2, QTableWidgetItem())
        self.table.setItem(row_index, 3, QTableWidgetItem())
        self.table.setItem(row_index, 4, QTableWidgetItem())
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

        # Filter basename for name and extention
        filepaths_filtered = []
        for i, filepath in enumerate(filepaths):
            file_basename = basename(filepath)
            pattern_for_basename = self.filename_filter.text()

            if pattern_for_basename and not re.search(
                pattern_for_basename, file_basename
            ):
                continue

            pattern_for_extention = self.extention_edit.text()
            extention = splitext(file_basename)[1]
            if pattern_for_extention and not re.search(
                pattern_for_extention, extention
            ):
                continue
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
            parents_basenames = list(map(basename, get_3_parents_dirs(filepath)))
            for i in range(len(parents_basenames)):
                item = self.table.item(current_row, 2 + i)
                item.setText(list(reversed(parents_basenames))[i])
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
            parents_basenames = list(map(basename, get_3_parents_dirs(filepath)))
            for i in range(len(parents_basenames)):
                item = self.table.item(current_row, 2 + i)
                item.setText(list(reversed(parents_basenames))[i])
        return

    def parse(self) -> List[LIVdata]:
        parser = LIVparser()
        datas: List[LIVdata] = []
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
            name_strs = [self.table.item(i, 2 + j).text() for j in range(3)]
            name_str = "-".join([each for each in name_strs if each])
            data.add_other_data("Name", name_str)

            datas.append(data)
        return datas

    def start_slot(self) -> None:
        datas = self.parse()
        _dict = {
            "datas": datas,
            "add_naming": self.add_naming_checkbox.isChecked(),
            "ndigits": self.ndigits_spinbox.value(),
        }
        self.controller.after_LIV_start_pressed_signal.emit(_dict)
        return
