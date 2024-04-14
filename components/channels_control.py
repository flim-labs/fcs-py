import os
import json
import re
import functools
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHeaderView, QHBoxLayout, QPushButton, QTableWidget, QAbstractItemView, QTableWidgetItem, QGridLayout, QSizePolicy, QCheckBox, QLabel, QLineEdit,   QApplication
from PyQt6.QtCore import QPropertyAnimation, QSize, QRect, QEasingCurve, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QIntValidator, QPixmap
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.logo_utilities import LogoOverlay, TitlebarIcon
from components.settings import *

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class ChannelsControl(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        layout = QVBoxLayout()
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
        self.plots_config_btn.setStyleSheet(GUIStyles.channels_btn_style(base="#f5f538", hover="#d4d400", pressed="#c8b900", text="black"))
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
        self.popup = PlotsConfigPopup(self.app)
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



class PlotsConfigPopup(QWidget):
    def __init__(self, window):
        super().__init__()
        self.app = window
        self.setWindowTitle("FCS - Plots config")
        TitlebarIcon.setup(self)
        GUIStyles.customize_theme(self, bg= QColor(20, 20, 20))
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        desc = QLabel("To avoid cluttering the interface, only a maximum of 4 intensity tracing charts and 4 G(t) curves will be displayed. However, all charts can be reconstructed by exporting the acquired data. Please select the intensity tracing charts and G(t) curves you would like to be shown.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(20)
        intensity_prompt = QLabel("INTENSITY TRACING PLOTS (MAX 4):")
        intensity_prompt.setObjectName("prompt_text")
        gt_prompt = QLabel("G(T) PLOTS (MAX 4):")
        gt_prompt.setObjectName("prompt_text")
        self.intensity_ch_grid = QGridLayout()
        self.intensity_checkboxes = []
        self.intensity_checkboxes_wrappers = []
        self.gt_corr_grid = QGridLayout()
        self.gt_checkboxes = []
        self.gt_checkboxes_wrappers = []
        layout.addWidget(intensity_prompt)
        if len(self.app.enabled_channels) == 0:
            layout.addLayout(self.set_data_empty_row("No channels enabled."))
        else:
            self.init_intensity_grid()
            layout.addLayout(self.intensity_ch_grid) 
        layout.addSpacing(20)       
        layout.addWidget(gt_prompt)
        if all(any(value is False for value in sublist) for sublist in self.app.ch_correlations):
            layout.addLayout(self.set_data_empty_row("No channels correlations configured."))
        else:
            self.init_gt_grid() 
            layout.addLayout(self.gt_corr_grid)    
        self.setLayout(layout)
        self.setStyleSheet(GUIStyles.plots_config_popup_style())


    def init_gt_grid(self):
        corr_data = self.get_cleaned_correlations()
        for index, (ch1, ch2) in enumerate(corr_data):
            checkbox = self.set_checkboxes(f"Channel {ch1 + 1} - Channel {ch2 + 1}", "gt")
            gt_plot_to_show = [tuple(item) if isinstance(item, list) else item for item in self.app.gt_plots_to_show]
            isChecked = (ch1, ch2) in gt_plot_to_show
            checkbox.setChecked(isChecked)
        self.update_layout(self.gt_checkboxes_wrappers, self.gt_corr_grid, "gt")     


    def init_intensity_grid(self):
        for ch in self.app.enabled_channels:
            checkbox = self.set_checkboxes(f"Channel {ch + 1}", "intensity")
            isChecked = ch in self.app.intensity_plots_to_show
            checkbox.setChecked(isChecked)
        self.update_layout(self.intensity_checkboxes_wrappers, self.intensity_ch_grid, "intensity")        


    def set_checkboxes(self, text, typology):
        checkbox_wrapper = QWidget()
        checkbox_wrapper.setObjectName(f"tau_checkbox_wrapper")
        row = QHBoxLayout()
        checkbox = QCheckBox(text)
        checkbox.setStyleSheet(GUIStyles.set_tau_checkbox_style())
        checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        checkbox.toggled.connect(lambda state, checkbox=checkbox: self.on_ch_intensity_toggled(state, checkbox) if typology == 'intensity' else self.on_ch_gt_toggled(state, checkbox) )
        row.addWidget(checkbox)
        checkbox_wrapper.setLayout(row)
        checkbox_wrapper.setStyleSheet(GUIStyles.checkbox_wrapper_style())
        if typology == 'intensity':
            self.intensity_checkboxes_wrappers.append(checkbox_wrapper)
            self.intensity_checkboxes.append(checkbox)
        else:
            self.gt_checkboxes_wrappers.append(checkbox_wrapper)
            self.gt_checkboxes.append(checkbox)
        return checkbox  

    def set_data_empty_row(self, text):    
        row = QHBoxLayout()
        remove_icon_label = QLabel()
        remove_icon_label.setPixmap(QPixmap(resource_path("assets/close-icon-red.png")).scaledToWidth(15))
        label = QLabel(text)
        label.setStyleSheet("color: #c90404;")
        row.addWidget(remove_icon_label)
        row.addWidget(label)
        row.addStretch(1)
        return row

    def update_layout(self, widgets, grid, typology):       
        screen_width = self.width()
        if screen_width < 500:
            num_columns = 4 if typology == 'intensity' else 2
        elif 500 <= screen_width <= 1200:
            num_columns = 6 if typology == 'intensity' else 4
        elif 1201 <= screen_width <= 1450:
            num_columns = 8 if typology == 'intensity' else 6
        else:
            num_columns = 12 if typology == 'intensity' else 7
        for i, widget in enumerate(widgets):
            row, col = divmod(i, num_columns)
            grid.addWidget(widget, row, col)

    def on_ch_intensity_toggled(self, state, checkbox):
        label_text = checkbox.text() 
        ch_num_index = self.extract_channel_from_label(label_text) 
        if state:
            if ch_num_index not in self.app.intensity_plots_to_show:
                self.app.intensity_plots_to_show.append(ch_num_index)
        else:
            if ch_num_index in self.app.intensity_plots_to_show:
                self.app.intensity_plots_to_show.remove(ch_num_index) 
        self.app.settings.setValue(SETTINGS_INTENSITY_PLOTS_TO_SHOW, json.dumps(self.app.intensity_plots_to_show)) 
        if len(self.app.intensity_plots_to_show) >= 4:
            for checkbox in self.intensity_checkboxes:
                if checkbox.text() != label_text and not checkbox.isChecked():
                    checkbox.setEnabled(False)
        else:
            for checkbox in self.intensity_checkboxes:
                checkbox.setEnabled(True)


    def on_ch_gt_toggled(self, state, checkbox):    
        label_text = checkbox.text() 
        gt_plot_to_show = [tuple(item) if isinstance(item, list) else item for item in self.app.gt_plots_to_show]
        corr_tuple = self.extract_correlation_from_label(label_text) 
        if state:
            if corr_tuple not in gt_plot_to_show:
                gt_plot_to_show.append(corr_tuple)
        else:
            if corr_tuple in gt_plot_to_show:
                gt_plot_to_show.remove(corr_tuple) 
        self.app.gt_plots_to_show = gt_plot_to_show        
        self.app.settings.setValue(SETTINGS_GT_PLOTS_TO_SHOW, json.dumps(gt_plot_to_show)) 
        if len(gt_plot_to_show) >= 4:
            for checkbox in self.gt_checkboxes:
                if checkbox.text() != label_text and not checkbox.isChecked():
                    checkbox.setEnabled(False)
        else:
            for checkbox in self.gt_checkboxes:
                checkbox.setEnabled(True)            



    def extract_channel_from_label(self,text):
        ch = re.search(r'\d+', text).group()  
        ch_num = int(ch) 
        ch_num_index = ch_num - 1 
        return ch_num_index

    def extract_correlation_from_label(self, text):
        numbers = re.findall(r'\d+', text)
        corr_tuples = tuple(int(num) - 1 for num in numbers)
        return corr_tuples
    
    
    def get_cleaned_correlations(self):
        filtered_corr = sorted([(x, y) if x < y else (y, x) for x, y, boolean in self.app.ch_correlations if boolean])
        unique_filtered_data = []
        seen_pairs = set()
        for pair in filtered_corr:
            if pair not in seen_pairs:
                unique_filtered_data.append(pair)
                seen_pairs.add(pair)
        return unique_filtered_data      
        
