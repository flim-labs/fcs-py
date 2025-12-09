from functools import partial
import os
import shutil
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
    QFileDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor
from components.file_utilities import FileUtils
from components.format_utilities import FormatUtils
from components.general_utilities import (
    calculate_expected_intensity_entries,
    calculate_lag_index_length,
)
from components.gui_styles import GUIStyles
from components.helpers import calc_timestamp
from components.logo_utilities import TitlebarIcon
from components.resource_path import resource_path
from components.top_bar_builder import TopBarBuilder
from components.settings import *
from export_data_scripts.script_files_utils import ScriptFileUtils

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class ExportDataControl(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        self.info_link_widget, self.export_data_control = (
            self.create_export_data_input()
        )
        self.add_notes_button = self.create_add_notes_btn()
        self.file_size_info_layout = self.create_file_size_info_row()
        layout = QHBoxLayout()
        layout.addWidget(self.info_link_widget)
        layout.addWidget(self.add_notes_button)
        layout.addLayout(self.export_data_control)
        self.export_data_control.addSpacing(10)
        layout.addLayout(self.file_size_info_layout)
        layout.addSpacing(5)


        # Export options widget
        self.export_options_widget = self.create_export_options_widget()
        layout.addWidget(self.export_options_widget)
        # Time Tagger
        # Deprecated, now time tagger is included in the export options widget
        # time_tagger = self.create_time_tagger_widget()
        # layout.addWidget(time_tagger)

        self.setLayout(layout)
    
    def create_export_options_widget(self):
        from components.buttons import MultiSelectDropdown
        export_options_widget = MultiSelectDropdown(self.app)
        self.app.widgets[EXPORT_OPTIONS_WIDGET] = export_options_widget
        export_options_widget.setVisible(self.app.write_data)
        return export_options_widget

    def create_time_tagger_widget(self):
        from components.buttons import TimeTaggerWidget

        time_tagger = TimeTaggerWidget(self.app)
        return time_tagger

    def create_export_data_input(self):
        info_link_widget, export_data_control, inp = (
            TopBarBuilder.create_export_data_input(
                self.app.write_data, self.toggle_export_data
            )
        )
        self.app.control_inputs[SETTINGS_WRITE_DATA] = inp
        return info_link_widget, export_data_control

    def create_add_notes_btn(self):
        button = QPushButton()
        button.setIcon(QIcon(resource_path("assets/notes.png")))
        button.setFixedSize(30, 30)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(GUIStyles.add_notes_button())
        button.setVisible(self.app.write_data)
        button.clicked.connect(self.show_add_notes_popup)
        self.app.control_inputs[ADD_NOTES_BUTTON] = button
        return button

    def create_file_size_info_row(self):
        file_size_info_layout = TopBarBuilder.create_file_size_info_row(
            self.app,
            self.app.bin_file_size,
            self.app.bin_file_size_label,
            self.app.write_data,
            partial(DataExportActions.calc_exported_file_size, self.app),
        )
        return file_size_info_layout

    def show_add_notes_popup(self):
        notes_popup = AddNotesToExportedDataPopup(self.app)
        notes_popup.show()

    def toggle_export_data(self, state):
        if state:
            self.app.write_data = True
            self.app.settings.setValue(SETTINGS_WRITE_DATA, True)
            self.app.bin_file_size_label.show()
            DataExportActions.calc_exported_file_size(self.app)
            self.app.control_inputs[ADD_NOTES_BUTTON].setVisible(True)
            self.app.widgets[EXPORT_OPTIONS_WIDGET].setVisible(True)
        else:
            self.app.write_data = False
            self.app.settings.setValue(SETTINGS_WRITE_DATA, False)
            self.app.bin_file_size_label.hide()
            self.app.control_inputs[ADD_NOTES_BUTTON].setVisible(False)
            self.app.widgets[EXPORT_OPTIONS_WIDGET].setVisible(False)

        if TIME_TAGGER_WIDGET in self.app.widgets:
            self.app.widgets[TIME_TAGGER_WIDGET].setVisible(state)


class DataExportActions:
    @staticmethod
    def calc_exported_file_size(app):
        if len(app.enabled_channels) == 0:
            app.bin_file_size_label.setText("")
            return
        filtered_corr = [(x, y) for x, y, boolean in app.ch_correlations if boolean]
        if len(filtered_corr) == 0:
            fcs_file_size = 0
        else:
            fcs_file_size = DataExportActions.calc_fcs_file_size(app, filtered_corr)
        fcs_file_size_str = f";\n{fcs_file_size} KB (fcs)" if fcs_file_size > 0 else ""
        intensity_tracing_files_size, type = (
            DataExportActions.calc_intensity_files_size(app)
        )
        if type == "per_second":
            app.bin_file_size_label.setText(
                f"{intensity_tracing_files_size}/s (intensity){fcs_file_size_str}"
            )
        else:
            app.bin_file_size_label.setText(
                f"{intensity_tracing_files_size} (intensity){fcs_file_size_str}"
            )

    @staticmethod
    def calc_intensity_files_size(app):
        free_running = app.free_running_acquisition_time
        num_acquisition = app.selected_average if not free_running else 1
        chunk_bytes = 8 + (4 * len(app.enabled_channels))
        chunk_bytes_in_us = (1000 * (chunk_bytes * 1000)) / app.bin_width_micros
        acquisition_time = (
            0 if app.acquisition_time_millis is None else app.acquisition_time_millis
        )
        if free_running is True:
            file_size_bytes = int(chunk_bytes_in_us)
            bin_file_size = FormatUtils.format_size(file_size_bytes * num_acquisition)
            return bin_file_size, "per_second"
        else:
            file_size_bytes = int(chunk_bytes_in_us * (acquisition_time / 1000))
            bin_file_size = FormatUtils.format_size(file_size_bytes * num_acquisition)
            return bin_file_size, "total"

    @staticmethod
    def calc_fcs_file_size(app, filtered_corr):
        bin_width = app.bin_width_micros
        acquisition_time = (
            0 if app.acquisition_time_millis is None else app.acquisition_time_millis
        )
        free_running = app.free_running_acquisition_time
        num_acquisition = app.selected_average if not free_running else 1
        expected_intensity_entries = (
            calculate_expected_intensity_entries(acquisition_time, bin_width)
            if not free_running
            else None
        )
        n_correlations = len(filtered_corr)
        n_channels = len(app.enabled_channels)
        notes_length = len(app.notes.encode("utf-8"))
        
        # Get tau_high_density from app settings
        tau_high_density = app.tau_axis_scale == "High density"
        
        n_lag_index = calculate_lag_index_length(bin_width, tau_high_density) 
      
        header_size = 4
        u32_size = 4
        usize_size = 8
        f64_size = 8
        correlations_size = n_correlations * (2 * usize_size)
        channels_size = n_channels * usize_size
        metadata_json_size = correlations_size + channels_size + notes_length
        lag_index_size = n_lag_index * usize_size
        g2_correlations_size = n_correlations * (
            2 * usize_size + (num_acquisition + 1) * n_lag_index * f64_size
        )
        g2_json_size = lag_index_size + g2_correlations_size
        total_estimated_size_bytes = (
            header_size + 2 * u32_size + metadata_json_size + g2_json_size
        )
        total_estimated_size_kb = round(total_estimated_size_bytes / 1024, 2)
        return int(round(total_estimated_size_kb, 2))


class AddNotesToExportedDataPopup(QWidget):
    def __init__(self, window):
        super().__init__()
        self.app = window
        self.setWindowTitle("FCS - Add exported data notes")
        TitlebarIcon.setup(self)
        GUIStyles.customize_theme(self, bg=QColor(20, 20, 20))
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        desc = QLabel("Add notes to your exported data bin file (max 5000 characters):")
        desc.setStyleSheet("font-family: Montserrat; color: #6e6b6b")
        self.textarea = QPlainTextEdit(self)
        self.textarea.setPlainText(self.app.notes)
        self.textarea.textChanged.connect(self.limit_characters)
        self.textarea.setStyleSheet(GUIStyles.add_notes_textarea())
        button_row = QHBoxLayout()
        save_button = QPushButton("SAVE")
        save_button.setStyleSheet(
            GUIStyles.button_style("#FB8C00", "#FB8C00", "#FB8C00", "#FB8C00", "100px")
        )
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.clicked.connect(self.save_notes)
        button_row.addStretch(1)
        button_row.addWidget(save_button)
        layout.addWidget(desc)
        layout.addSpacing(10)
        layout.addWidget(self.textarea)
        layout.addSpacing(20)
        layout.addLayout(button_row)
        self.setLayout(layout)
        self.app.widgets[ADD_NOTES_POPUP] = self

    def save_notes(self):
        self.app.notes = self.textarea.toPlainText()
        DataExportActions.calc_exported_file_size(self.app)
        self.close()

    def limit_characters(self):
        self.textarea.textChanged.disconnect(self.limit_characters)
        max_char = 5000
        if len(self.textarea.toPlainText()) > max_char:
            text = self.textarea.toPlainText()
            cursor_pos = self.textarea.textCursor().position()
            truncated_text = text[:max_char]
            selected_text = text[cursor_pos:]
            truncated_text += selected_text
            self.textarea.setPlainText(truncated_text)
            cursor = self.textarea.textCursor()
            cursor.setPosition(len(truncated_text))
            self.textarea.setTextCursor(cursor)
        self.textarea.textChanged.connect(self.limit_characters)


class ExportData:

    @staticmethod
    def save_fcs_data(app):
        try:
            timestamp = calc_timestamp()
            time_tagger = app.time_tagger
            num_acquisitions = (
                app.selected_average
                if app.free_running_acquisition_time == False
                else 1
            )
            fcs_file = FileUtils.get_recent_fcs_file()
            txt_fcs_file = FileUtils.get_recent_fcs_file(extension=".txt")
            intensity_files = FileUtils.get_recent_n_intensity_tracing_files(
                num_acquisitions
            )
            new_fcs_file_path, save_dir, save_name = ExportData.rename_and_move_file(
                fcs_file, "fcs", "Save FCS files", timestamp, app
            )
            if not new_fcs_file_path:
                return
            ExportData.copy_file(
                txt_fcs_file, save_name, save_dir, "fcs", timestamp, "txt"
            )
       
            for index, file in enumerate(intensity_files):
                file_name = FileUtils.clean_filename(save_name)
                new_intensity_file_name = (
                    f"{file_name}_{timestamp}_intensity_tracing_{index + 1}.bin"
                )
                new_intensity_ref_path = os.path.join(save_dir, new_intensity_file_name)
                shutil.copyfile(file, new_intensity_ref_path)

            if time_tagger:
                time_tagger_file = FileUtils.get_recent_time_tagger_file()
                new_time_tagger_path = ExportData.copy_file(
                    time_tagger_file,
                    save_name,
                    save_dir,
                    "time_tagger_fcs",
                    timestamp,
                )
            new_time_tagger_path = (
                ""
                if not time_tagger or not new_time_tagger_path
                else new_time_tagger_path
            )
            file_paths = {
                "fcs": new_fcs_file_path,
            }
            ExportData.download_scripts(
                file_paths,
                save_name,
                save_dir,
                "fcs",
                timestamp,
                time_tagger=time_tagger,
                time_tagger_file_path=new_time_tagger_path,
            )
        except Exception as e:
            ScriptFileUtils.show_error_message(e)

    @staticmethod
    def download_scripts(
        bin_file_paths,
        file_name,
        directory,
        script_type,
        timestamp,
        time_tagger=False,
        time_tagger_file_path="",
    ):
        file_name = FileUtils.clean_filename(file_name)
        file_name = f"{file_name}_{timestamp}"
        ScriptFileUtils.export_scripts(
            bin_file_paths,
            file_name,
            directory,
            script_type,
            time_tagger,
            time_tagger_file_path,
        )

    @staticmethod
    def copy_file(
        origin_file_path,
        save_name,
        save_dir,
        file_type,
        timestamp,
        file_extension="bin",
    ):
        new_filename = f"{save_name}_{timestamp}_{file_type}"
        new_filename = f"{FileUtils.clean_filename(new_filename)}.{file_extension}"
        new_file_path = os.path.join(save_dir, new_filename)
        shutil.copyfile(origin_file_path, new_file_path)
        return new_file_path

    @staticmethod
    def rename_and_move_file(
        original_file_path,
        file_type,
        file_dialog_prompt,
        timestamp,
        app,
        file_extension="bin",
    ):
        dialog = QFileDialog()
        save_path, _ = dialog.getSaveFileName(
            app,
            file_dialog_prompt,
            "",
            "All Files (*);;Binary Files (*.bin)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if save_path:
            save_dir = os.path.dirname(save_path)
            save_name = os.path.basename(save_path)
            new_filename = f"{save_name}_{timestamp}_{file_type}"
            new_filename = f"{FileUtils.clean_filename(new_filename)}.{file_extension}"
            new_file_path = os.path.join(save_dir, new_filename)
            shutil.copyfile(original_file_path, new_file_path)
            return new_file_path, save_dir, save_name
        else:
            return None, None, None
