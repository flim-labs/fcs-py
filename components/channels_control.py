import os
import json

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from components.controls_bar_builder import ControlsBarBuilder
from components.data_export_controls import DataExportActions
from components.plots_config_widget import PlotsConfigPopup
from components.correlations_matrix import ChCorrelationsPopup
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
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
        self.ch_checkboxes = []
        self.create_channel_type_control(self.channels_grid)
        self.correlations_btn = QPushButton("CORRELATIONS")
        self.correlations_btn.setIcon(
            QIcon(resource_path("assets/edit-matrix-icon.png"))
        )
        self.correlations_btn.setFixedWidth(180)
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
        self.plots_config_btn.setFixedWidth(180)
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
            checkbox = FancyCheckbox(text=f"Channel {i + 1}")
            checkbox.setStyleSheet(GUIStyles.set_checkbox_style())
            checked = i in self.app.enabled_channels
            checkbox.set_checked(checked)
            checkbox.toggled.connect(
                lambda state, index=i: self.on_ch_toggled(state, index)
            )
            row = QHBoxLayout()
            row.addWidget(checkbox)
            ch_checkbox_wrapper.setLayout(row)
            ch_checkbox_wrapper.setStyleSheet(GUIStyles.checkbox_wrapper_style())
            ch_checkbox_wrapper.setFixedHeight(40)
            self.ch_checkboxes.append(ch_checkbox_wrapper)
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
        DataExportActions.calc_exported_file_size(self.app)

    def open_ch_correlations_popup(self):
        self.popup = ChCorrelationsPopup(self.app)
        self.popup.show()

    def open_plots_config_popup(self):
        self.popup = PlotsConfigPopup(self.app, start_acquisition=False)
        self.popup.show()
