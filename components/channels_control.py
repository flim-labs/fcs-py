import os
import json

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QIcon
from components.channels_detection import DetectChannelsButton
from components.controls_bar_builder import ControlsBarBuilder
from components.data_export_controls import DataExportActions
from components.plots_config_widget import PlotsConfigPopup
from components.correlations_matrix import ChCorrelationsPopup
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.channel_name_utils import get_channel_name_parts
from components.rename_channel_modal import RenameChannelModal
from components.settings import *

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class ChannelsControl(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.channels_grid = QHBoxLayout()
        layout.addLayout(self.channels_grid)
        self.setLayout(layout)
        
        # Detect channels button
        self.detect_channels_btn =  DetectChannelsButton(self.app)
        self.channels_grid.addWidget(self.detect_channels_btn)
             
        self.ch_checkboxes = []
        self.create_channel_type_control(self.channels_grid)
        self.correlations_btn = QPushButton("CORRELATIONS")
        self.correlations_btn.setIcon(
            QIcon(resource_path("assets/edit-matrix-icon.png"))
        )
        self.correlations_btn.setFixedWidth(160)
        self.correlations_btn.setStyleSheet(
            GUIStyles.channels_btn_style(
                base="#31c914", hover="#57D33D", pressed="#7FE777"
            )
        )
        self.correlations_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.correlations_btn.clicked.connect(self.open_ch_correlations_popup)
        (
            self.correlations_btn.setEnabled(False)
            if len(self.app.enabled_channels) == 0
            else self.correlations_btn.setEnabled(True)
        )
        self.plots_config_btn = QPushButton("PLOTS CONFIG")
        self.plots_config_btn.setIcon(QIcon(resource_path("assets/chart-icon.png")))
        self.plots_config_btn.setFixedWidth(160)
        self.plots_config_btn.setStyleSheet(
            GUIStyles.channels_btn_style(
                base="#FB8C00", hover="#FFA726", pressed="#FB8C00", text="white"
            )
        )
        self.plots_config_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.plots_config_btn.clicked.connect(self.open_plots_config_popup)

        self.widgets = self.ch_checkboxes + [
            self.correlations_btn,
            self.plots_config_btn,
        ]
        self.init_ch_grid()

    def create_channel_type_control(self, layout):
        inp = ControlsBarBuilder.create_channel_type_control(
            layout,
            self.app.selected_conn_channel,
            self.conn_channel_type_value_change,
            self.app.conn_channels,
        )
        inp.setFixedHeight(40)
        inp.setFixedWidth(90)
        self.app.control_inputs[SETTINGS_CONN_CHANNEL] = inp

    def conn_channel_type_value_change(self, index):
        self.app.selected_conn_channel = self.sender().currentText()
        if self.app.selected_conn_channel == "USB":
            self.app.selected_firmware = self.app.firmwares[0]
        else:
            self.app.selected_firmware = self.app.firmwares[1]
        self.app.settings.setValue(SETTINGS_FIRMWARE, self.app.selected_firmware)
        self.app.settings.setValue(
            SETTINGS_CONN_CHANNEL, self.app.selected_conn_channel
        )

    def init_ch_grid(self):
        self.update_ch_checkboxes()
        self.channels_grid.addWidget(self.correlations_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        self.channels_grid.addWidget(self.plots_config_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        return

    def update_ch_checkboxes(self):
        for i in range(MAX_CHANNELS):
            from components.fancy_checkbox import FancyCheckbox

            ch_checkbox_wrapper = QWidget()
            ch_checkbox_wrapper.setObjectName(f"ch_checkbox_wrapper")
            ch_checkbox_wrapper.setMinimumWidth(100)
            
            # Get custom and default parts of the channel name
            custom_part, default_part = get_channel_name_parts(i, self.app.channel_names)
            
            checkbox = FancyCheckbox(
                text=f"{custom_part} {default_part}" if default_part else custom_part,
                label_custom_part=custom_part if default_part else "",
                label_default_part=default_part
            )
            checkbox.setStyleSheet(GUIStyles.set_checkbox_style())
            checked = i in self.app.enabled_channels
            checkbox.set_checked(checked)
            checkbox.toggled.connect(
                lambda state, index=i: self.on_ch_toggled(state, index)
            )
            # Connect label click to open rename modal
            checkbox.labelClicked.connect(
                lambda index=i: self.open_rename_modal(index)
            )
            row = QHBoxLayout()
            row.addWidget(checkbox)
            ch_checkbox_wrapper.setLayout(row)
            ch_checkbox_wrapper.setStyleSheet(GUIStyles.checkbox_wrapper_style())
            ch_checkbox_wrapper.setFixedHeight(40)
            self.ch_checkboxes.append(ch_checkbox_wrapper)
            self.app.channel_checkboxes.append(checkbox)
            self.widgets = self.ch_checkboxes + [
                self.correlations_btn,
                self.plots_config_btn,
            ]
        for checkbox in self.ch_checkboxes:
            self.channels_grid.addWidget(checkbox, alignment=Qt.AlignmentFlag.AlignBottom)

    def on_ch_toggled(self, state, index):
        gt_plot_to_show = [
            tuple(item) if isinstance(item, list) else item
            for item in self.app.gt_plots_to_show
        ]
        intensity_plot_to_show = self.app.intensity_plots_to_show
        if state:
            if index not in self.app.enabled_channels:
                self.app.enabled_channels.append(index)
                if not(index in self.app.intensity_plots_to_show) and len(self.app.intensity_plots_to_show) < 4:
                    self.app.intensity_plots_to_show.append(index)
                    self.app.intensity_plots_to_show.sort()
                    self.app.settings.setValue(SETTINGS_INTENSITY_PLOTS_TO_SHOW, json.dumps(self.app.intensity_plots_to_show))                
        else:
            if index in self.app.enabled_channels:
                self.app.enabled_channels.remove(index)
                filtered_correlations = [
                    corr for corr in self.app.ch_correlations if index not in corr
                ]
                self.app.ch_correlations = filtered_correlations
                self.app.settings.setValue(
                    SETTINGS_CH_CORRELATIONS, json.dumps(filtered_correlations)
                )
                filtered_intensity_plot_to_show = list(
                    filter(lambda x: x != index, intensity_plot_to_show)
                )
                self.app.intensity_plots_to_show = filtered_intensity_plot_to_show
                self.app.settings.setValue(
                    SETTINGS_INTENSITY_PLOTS_TO_SHOW,
                    json.dumps(filtered_intensity_plot_to_show),
                )
                filtered_gt_plot_to_show = [
                    corr for corr in gt_plot_to_show if index not in corr
                ]
                self.app.gt_plots_to_show = filtered_gt_plot_to_show
                self.app.settings.setValue(
                    SETTINGS_GT_PLOTS_TO_SHOW, json.dumps(filtered_gt_plot_to_show)
                )
        (
            self.correlations_btn.setEnabled(False)
            if len(self.app.enabled_channels) == 0
            else self.correlations_btn.setEnabled(True)
        )
        self.app.settings.setValue(
            SETTINGS_ENABLED_CHANNELS, json.dumps(self.app.enabled_channels)
        )
        self.app.control_inputs[START_BUTTON].setEnabled(
            len(self.app.enabled_channels) > 0
        )
        # DataExportActions.calc_exported_file_size(self.app)

    def open_ch_correlations_popup(self):
        self.popup = ChCorrelationsPopup(self.app)
        self.popup.show()

    def open_plots_config_popup(self):
        self.popup = PlotsConfigPopup(self.app, start_acquisition=False)
        self.popup.show()
    
    def open_rename_modal(self, channel_id):
        """Open the rename channel modal"""
        current_name = self.app.channel_names.get(str(channel_id), "")
        modal = RenameChannelModal(channel_id, current_name, self.app)
        modal.channelRenamed.connect(self.on_channel_renamed)
        modal.exec()
    
    @pyqtSlot(int, str)
    def on_channel_renamed(self, channel_id, new_name):
        """Handle channel rename"""
        # Update the channel name in the app
        if new_name:
            self.app.channel_names[str(channel_id)] = new_name
        else:
            # Remove custom name if empty
            self.app.channel_names.pop(str(channel_id), None)
        
        # Save to settings
        self.app.settings.setValue(SETTINGS_CHANNEL_NAMES, json.dumps(self.app.channel_names))
        
        # Update the checkbox label
        custom_part, default_part = get_channel_name_parts(channel_id, self.app.channel_names)
        checkbox = self.app.channel_checkboxes[channel_id]
        checkbox.set_text_parts(custom_part, default_part)
