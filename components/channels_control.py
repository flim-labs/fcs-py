import os
import json
import functools
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHeaderView, QHBoxLayout, QPushButton, QTableWidget, QAbstractItemView, QTableWidgetItem, QCheckBox, QApplication
from PyQt6.QtCore import  QSize, Qt
from PyQt6.QtGui import QIcon, QColor
from components.buttons import PlotsConfigPopup
from components.data_export_controls import DataExportActions
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.logo_utilities import TitlebarIcon
from components.settings import *
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class ChannelsControl(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        self.channels_grid = QHBoxLayout()
        layout.addLayout(self.channels_grid)

        self.setLayout(layout)
        self.ch_checkboxes = []
        self.correlations_btn = QPushButton("CORRELATIONS")
        self.correlations_btn.setIcon(QIcon(resource_path("assets/edit-matrix-icon.png")))
        self.correlations_btn.setFixedWidth(150) 
        self.correlations_btn.setStyleSheet(GUIStyles.channels_btn_style(base = "#31c914", hover="#57D33D", pressed = "#7FE777"))
        self.correlations_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.correlations_btn.clicked.connect(self.open_ch_correlations_popup)
        self.correlations_btn.setEnabled(False) if len(self.app.enabled_channels) == 0 else self.correlations_btn.setEnabled(True)
        self.plots_config_btn = QPushButton("PLOTS CONFIG")
        self.plots_config_btn.setIcon(QIcon(resource_path("assets/chart-icon.png")))
        self.plots_config_btn.setFixedWidth(150)
        self.plots_config_btn.setStyleSheet(GUIStyles.channels_btn_style(base="#FB8C00", hover="#FFA726", pressed="#FB8C00", text="white"))
        self.plots_config_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.plots_config_btn.clicked.connect(self.open_plots_config_popup) 

        self.widgets = self.ch_checkboxes + [self.correlations_btn, self.plots_config_btn] 
        self.init_ch_grid()
 

    def init_ch_grid(self):
        self.update_ch_checkboxes()
        self.channels_grid.addWidget(self.correlations_btn)
        self.channels_grid.addWidget(self.plots_config_btn)
        return 

    def update_ch_checkboxes(self):
        for i in range(MAX_CHANNELS):
            from components.fancy_checkbox import FancyCheckbox
            ch_checkbox_wrapper = QWidget() 
            ch_checkbox_wrapper.setObjectName(f"ch_checkbox_wrapper")
            checkbox = FancyCheckbox(text=f"Channel {i + 1}")
            checkbox.setStyleSheet(GUIStyles.set_checkbox_style())
            checked = i in self.app.enabled_channels
            checkbox.set_checked(checked)
            checkbox.toggled.connect(lambda state, index=i: self.on_ch_toggled(state, index))
            row = QHBoxLayout()
            row.addWidget(checkbox)
            ch_checkbox_wrapper.setLayout(row)
            ch_checkbox_wrapper.setStyleSheet(GUIStyles.checkbox_wrapper_style())
            self.ch_checkboxes.append(ch_checkbox_wrapper)
            self.widgets = self.ch_checkboxes + [self.correlations_btn, self.plots_config_btn]
        for checkbox in  self.ch_checkboxes:
            self.channels_grid.addWidget(checkbox)    
    

    def on_ch_toggled(self, state, index):
        gt_plot_to_show = [tuple(item) if isinstance(item, list) else item for item in self.app.gt_plots_to_show]
        intensity_plot_to_show = self.app.intensity_plots_to_show
        if state:
            if index not in self.app.enabled_channels:
                self.app.enabled_channels.append(index)
        else:
            if index in self.app.enabled_channels:
                self.app.enabled_channels.remove(index)
                filtered_correlations = [corr for corr in self.app.ch_correlations if index not in corr]
                self.app.ch_correlations = filtered_correlations
                self.app.settings.setValue(SETTINGS_CH_CORRELATIONS, json.dumps(filtered_correlations))
                filtered_intensity_plot_to_show = list(filter(lambda x: x != index, intensity_plot_to_show))
                self.app.intensity_plots_to_show = filtered_intensity_plot_to_show
                self.app.settings.setValue(SETTINGS_INTENSITY_PLOTS_TO_SHOW, json.dumps(filtered_intensity_plot_to_show))
                filtered_gt_plot_to_show = [corr for corr in gt_plot_to_show if index not in corr]
                self.app.gt_plots_to_show = filtered_gt_plot_to_show
                self.app.settings.setValue(SETTINGS_GT_PLOTS_TO_SHOW, json.dumps(filtered_gt_plot_to_show))
        self.correlations_btn.setEnabled(False) if len(self.app.enabled_channels) == 0 else self.correlations_btn.setEnabled(True)                       
        self.app.settings.setValue(SETTINGS_ENABLED_CHANNELS, json.dumps(self.app.enabled_channels))
 

    def open_ch_correlations_popup(self):
        self.popup = ChCorrelationsPopup(self.app)
        self.popup.show()


    def open_plots_config_popup(self):
        self.popup = PlotsConfigPopup(self.app, start_acquisition=False)
        self.popup.show()


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

        self.check_icon = QIcon(resource_path("assets/checkmark-icon.png"))
        self.close_icon = QIcon(resource_path("assets/close-icon.png"))

        self.matrix = QTableWidget()
        self.matrix.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.matrix.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.matrix.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.matrix.verticalHeader().setDefaultSectionSize(50)

        self.matrix.setStyleSheet(GUIStyles.set_correlation_table_style())
        self.matrix.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.matrix.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
      

        matrix_row = QHBoxLayout()
        matrix_row.addWidget(self.matrix)
        layout.setSpacing(20)
        layout.addLayout(matrix_row)
      
        self.setLayout(layout)
        self.app.widgets[CH_CORRELATIONS_POPUP] = self
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

    def set_matrix_labels(self, num_channels, enabled_channels):
        for i in range(num_channels):
            self.matrix.setHorizontalHeaderItem(i, QTableWidgetItem(f"Ch {enabled_channels[i] + 1}"))
            self.matrix.setVerticalHeaderItem(i, QTableWidgetItem(f"Ch {enabled_channels[i] + 1}"))
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

    def save_correlations(self):
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
        DataExportActions.calc_exported_file_size(self.app)

    def filter_gt_plot_to_show_on_correlations_change(self):
        correlations_tuples = [tuple(item) if isinstance(item, list) else item for item in self.app.ch_correlations]
        gt_to_show_tuples =  [tuple(item) if isinstance(item, list) else item for item in self.app.gt_plots_to_show]
        filtered_corr = set()
        for tpl in correlations_tuples:
            filtered_corr.update(tpl[:-1]) 
        return [tpl for tpl in gt_to_show_tuples if all(num in filtered_corr for num in tpl)]    

    def closeEvent(self, event):    
        self.save_correlations()
        event.accept()


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



