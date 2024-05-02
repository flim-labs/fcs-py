from functools import partial
import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QLabel, QPlainTextEdit
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QIcon, QColor
from components.gui_styles import GUIStyles
from components.logo_utilities import TitlebarIcon
from components.resource_path import resource_path
from components.top_bar_builder import TopBarBuilder
from components.settings import *
from export_data_scripts.script_files_utils import MatlabScriptUtils, PythonScriptUtils
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class ExportDataControl(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        self.info_link_widget, self.export_data_control = self.create_export_data_input()
        self.add_notes_button = self.create_add_notes_btn()
        self.file_size_info_layout = self.create_file_size_info_row()
        layout = QHBoxLayout()
        layout.addWidget(self.info_link_widget)
        layout.addWidget(self.add_notes_button)
        layout.addLayout(self.export_data_control)
        self.export_data_control.addSpacing(10)
        layout.addLayout(self.file_size_info_layout)

        self.setLayout(layout)

    def create_export_data_input(self):        
        info_link_widget, export_data_control, inp = TopBarBuilder.create_export_data_input(self.app.write_data, self.toggle_export_data)
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
            self.app.bin_file_size,
            self.app.bin_file_size_label,
            self.app.write_data,
           partial(DataExportActions.calc_exported_file_size, self.app))
        return file_size_info_layout 
    
    
    def show_add_notes_popup(self):
        notes_popup = AddNotesToExportedDataPopup(self.app)
        notes_popup.show()

    def toggle_export_data(self, state):        
        if state:
            self.app.write_data = True
            self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(self.app.write_data and self.app.acquisition_stopped)
            DataExportActions.set_download_button_icon(self.app)
            self.app.settings.setValue(SETTINGS_WRITE_DATA, True)
            self.app.bin_file_size_label.show()
            DataExportActions.calc_exported_file_size(self.app)
            self.app.control_inputs[ADD_NOTES_BUTTON].setVisible(True)
        else:
            self.app.write_data = False
            self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(self.app.write_data and self.app.acquisition_stopped)
            DataExportActions.set_download_button_icon(self.app)
            self.app.settings.setValue(SETTINGS_WRITE_DATA, False)
            self.app.bin_file_size_label.hide()
            self.app.control_inputs[ADD_NOTES_BUTTON].setVisible(False)          



class DownloadDataControl(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        self.download_button, self.download_menu = self.create_download_files_menu()
        layout = QHBoxLayout()
        layout.addWidget(self.download_button)

        self.setLayout(layout)

    def create_download_files_menu(self):    
        download_button, download_menu = TopBarBuilder.create_download_files_menu(
            self.app,
            self.app.write_data,
            self.app.acquisition_stopped,
            self.show_download_options,
            self.download_python,
            self.download_matlab
        )
        self.app.control_inputs[DOWNLOAD_BUTTON] = download_button
        self.app.control_inputs[DOWNLOAD_MENU] = download_menu
        DataExportActions.set_download_button_icon(self.app)
        return download_button, download_menu 

    def show_download_options(self):    
        self.app.control_inputs[DOWNLOAD_MENU].exec(self.app.control_inputs[DOWNLOAD_BUTTON].mapToGlobal(QPoint(0, self.app.control_inputs[DOWNLOAD_BUTTON].height())))

    def download_python(self):
        PythonScriptUtils.download_python(self)
        self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(False)
        self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(True) 
        
    def download_matlab(self):
        MatlabScriptUtils.download_matlab(self)
        self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(False)
        self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(True)     



class DataExportActions: 
    @staticmethod
    def calc_exported_file_size(app):
        filtered_corr = [(x, y) for x, y, boolean in app.ch_correlations if boolean]
        notes = app.notes
        if len(filtered_corr) ==0:
            app.bin_file_size_label.setText("")
            return
        file_dimension_kb = CORRELATIONS_FILE_DIMENSION_KB[len(filtered_corr)]
        if len(notes) == 0:
            app.bin_file_size_label.setText("File size: " + str(file_dimension_kb) + 'KB')
            return
        if(len(notes) <= 5000 and len(notes) > 4000):
           app.bin_file_size_label.setText("File size: " + str(file_dimension_kb + COMMENT_FILE_DIMENSION_KB[5000]) + 'KB') 
        if(len(notes) <= 4000 and len(notes) > 3000):
           app.bin_file_size_label.setText("File size: " + str(file_dimension_kb + COMMENT_FILE_DIMENSION_KB[4000]) + 'KB')    
        if(len(notes) <= 3000 and len(notes) > 2000):
           app.bin_file_size_label.setText("File size: " + str(file_dimension_kb + COMMENT_FILE_DIMENSION_KB[3000]) + 'KB')
        if(len(notes) <= 2000 and len(notes) > 500):
           app.bin_file_size_label.setText("File size: " + str(file_dimension_kb + COMMENT_FILE_DIMENSION_KB[2000]) + 'KB')
        if len(notes) <= 500:
           app.bin_file_size_label.setText("File size: " + str(file_dimension_kb + COMMENT_FILE_DIMENSION_KB[500]) + 'KB')         
    
    @staticmethod
    def set_download_button_icon(app):    
        if app.control_inputs[DOWNLOAD_BUTTON].isEnabled():
            icon = resource_path("assets/arrow-down-icon-white.png")
            app.control_inputs[DOWNLOAD_BUTTON].setIcon(QIcon(icon))
        else:
            icon = resource_path("assets/arrow-down-icon-grey.png")
            app.control_inputs[DOWNLOAD_BUTTON].setIcon(QIcon(icon))                    
            
            
 
 
class AddNotesToExportedDataPopup(QWidget):
    def __init__(self, window):
        super().__init__()
        self.app = window
        self.setWindowTitle("FCS - Add exported data notes")
        TitlebarIcon.setup(self)
        GUIStyles.customize_theme(self, bg= QColor(20, 20, 20))
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
        save_button.setStyleSheet(GUIStyles.button_style("#FB8C00", "#FB8C00", "#FB8C00", "#FB8C00", "100px"))
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
        

            