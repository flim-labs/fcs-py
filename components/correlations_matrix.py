import os
import json
import functools
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHeaderView, QHBoxLayout, QTableWidget, QAbstractItemView, QTableWidgetItem, QCheckBox, QApplication
from PyQt6.QtCore import  QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.logo_utilities import TitlebarIcon
from components.channel_name_utils import get_channel_name
from components.settings import *
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))




class ChCorrelationsPopup(QWidget):
    def __init__(self, window):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #141414;
            }
        """)
        self.app = window
        self.resize(self.app.settings.value("size", QSize(CORR_POPUP_WIDTH, CORR_POPUP_HEIGHT)))
        self.move(self.app.settings.value("pos", QApplication.primaryScreen().geometry().center() - self.frameGeometry().center()))
        
        self.setWindowTitle("FCS - Channels correlations")
        TitlebarIcon.setup(self)
        GUIStyles.customize_theme(self, bg= QColor(20, 20, 20))
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.correlations_matrix = ChCorrelationsMatrix(self.app)
        layout.addWidget(self.correlations_matrix)
        self.app.widgets[CH_CORRELATIONS_POPUP] = self
        self.setLayout(layout)
        

    def closeEvent(self, event):    
        self.correlations_matrix.save_correlations()
        event.accept()






class ChCorrelationsMatrix(QWidget):
    correlations_saved = pyqtSignal()
    def __init__(self, window):
        super().__init__()
        self.app = window
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
       

        self.check_icon = QIcon(resource_path("assets/checkmark-icon.png"))
        self.close_icon = QIcon(resource_path("assets/close-icon.png"))

        self.matrix = QTableWidget()
        self.matrix.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.matrix.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.matrix.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.matrix.verticalHeader().setDefaultSectionSize(50)
        self.matrix.setStyleSheet(GUIStyles.set_correlation_table_style())
    

        matrix_row = QHBoxLayout()
        matrix_row.addWidget(self.matrix)
        layout.addLayout(matrix_row)
      
        self.setLayout(layout)
        self.adjustSize()
        self.app.widgets[CH_CORRELATIONS_MATRIX] = self
        self.populate_matrix()

    def populate_matrix(self):
        enabled_channels = self.app.enabled_channels
        enabled_channels.sort()
        num_channels = len(enabled_channels)
        self.matrix.setRowCount(num_channels)
        self.matrix.setColumnCount(num_channels)
        self.set_matrix_labels(num_channels, enabled_channels)
        header = self.matrix.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        total_height = 0
        row_count = self.matrix.rowCount()
        for row in range(row_count):
            if row_count < 3:
               total_height += self.matrix.rowHeight(row) + 60
            if row_count < 6 and row_count >= 3:
               total_height += self.matrix.rowHeight(row) + 20  
            if row_count >= 6:
                total_height += self.matrix.rowHeight(row) + 10  
        self.matrix.setFixedHeight(total_height)

    def set_matrix_labels(self, num_channels, enabled_channels):
        for i in range(num_channels):
            ch_name = get_channel_name(enabled_channels[i], self.app.channel_names, truncate_len=15)
            self.matrix.setHorizontalHeaderItem(i, QTableWidgetItem(ch_name))
            self.matrix.setVerticalHeaderItem(i, QTableWidgetItem(ch_name))
            self.build_matrix_checkboxes(num_channels, enabled_channels)

      
    def build_matrix_checkboxes(self, num_channels, enabled_channels):    
        correlations = self.app.ch_correlations
        for i, row_index in enumerate(enabled_channels):
            for j, column_index in enumerate(enabled_channels):
                cell_widget = CheckboxCellWidget()
                checkbox = cell_widget.checkbox
                if [row_index, column_index, True] in correlations or [column_index, row_index, True] in correlations:
                    checkbox.setCheckState(Qt.CheckState.Checked)
                    checkbox.setIcon(self.check_icon)
                else:
                    checkbox.setCheckState(Qt.CheckState.Unchecked)
                    checkbox.setIcon(self.close_icon)
                checkbox.clicked.connect(functools.partial(self.handle_inverse_check, row=i, column=j))    
                self.matrix.setCellWidget(i, j, cell_widget)
            

    def handle_inverse_check(self, row, column):    
        inverse_checkbox = self.matrix.cellWidget(column, row).checkbox
        if self.matrix.cellWidget(row, column).checkbox.isChecked():
            self.matrix.cellWidget(row, column).checkbox.setIcon(self.check_icon)
            inverse_checkbox.setChecked(True)
            inverse_checkbox.setIcon(self.check_icon)
        else:
            self.matrix.cellWidget(row, column).checkbox.setIcon(self.close_icon)
            inverse_checkbox.setChecked(False)
            inverse_checkbox.setIcon(self.close_icon)
        self.save_correlations()    
            

    def save_correlations(self):
        from components.data_export_controls import DataExportActions
        correlations = []
        enabled_channels = self.app.enabled_channels
        enabled_channels.sort()
        for i, row_index in enumerate(enabled_channels):
            for j, column_index in enumerate(enabled_channels):
                cell_widget = self.matrix.cellWidget(i, j)
                checkbox = cell_widget.checkbox
                if checkbox.isChecked():
                    correlations.append([row_index, column_index, True])
                else:
                    correlations.append([row_index, column_index, False])
        self.app.ch_correlations = correlations
        self.app.settings.setValue(SETTINGS_CH_CORRELATIONS, json.dumps(correlations))
        filtered_gt_to_show = self.filter_gt_plot_to_show_on_correlations_change()
        self.app.gt_plots_to_show = filtered_gt_to_show
        self.app.settings.setValue(SETTINGS_GT_PLOTS_TO_SHOW, json.dumps(filtered_gt_to_show))
        # DataExportActions.calc_exported_file_size(self.app)
        self.correlations_saved.emit()
        

    def filter_gt_plot_to_show_on_correlations_change(self):
        correlations_tuples = [tuple(item) if isinstance(item, list) else item for item in self.app.ch_correlations]
        gt_to_show_tuples =  [tuple(item) if isinstance(item, list) else item for item in self.app.gt_plots_to_show]
        filtered_corr = set()
        for tpl in correlations_tuples:
            filtered_corr.update(tpl[:-1]) 
        return [tpl for tpl in gt_to_show_tuples if all(num in filtered_corr for num in tpl)]   
    
    
    

class CheckboxCellWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.checkbox = QCheckBox(self)
        self.checkbox.setStyleSheet(GUIStyles.set_correlations_checkbox_style())
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.checkbox)
        self.setLayout(layout)  

    def sizeHint(self):
        return self.checkbox.sizeHint()    