import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from components.progress_bar import ProgressBar
from components.resource_path import resource_path
from components.settings import TIME_TAGGER_PROGRESS_BAR

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, ".."))
from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
)
from components.gui_styles import GUIStyles
from components.switch_control import SwitchControl
from components.select_control import SelectControl
from components.input_number_control import InputNumberControl
from components.layout_utilities import draw_layout_separator


class ControlsBarBuilder:

    @staticmethod
    def init_gui_controls_layout(controls_row, buttons_row, app):
        layout_container = QVBoxLayout()
        layout_container.setSpacing(0)
        layout_container.setContentsMargins(0, 0, 0, 0)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        blank_space = QWidget()
        blank_space.setMinimumHeight(1)
        blank_space.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        buttons_qv_box = QVBoxLayout()
        buttons_qv_box.setSpacing(0)
        buttons_qv_box.setContentsMargins(0, 0, 0, 0)
        buttons_qv_box.addLayout(buttons_row)
        controls_layout.addWidget(controls_row, alignment=Qt.AlignmentFlag.AlignTop)
        controls_layout.addLayout(buttons_qv_box)
        controls_layout.addSpacing(10)
        layout_container.addLayout(controls_layout)
        layout_container.addWidget(draw_layout_separator())
        # Time tagger progress bar
        time_tagger_progress_bar = ProgressBar(
            visible=False, indeterminate=True, label_text="Time tagger processing..."
        )
        app.widgets[TIME_TAGGER_PROGRESS_BAR] = time_tagger_progress_bar
        layout_container.addWidget(time_tagger_progress_bar)
        layout_container.addSpacing(5)     
        return blank_space, layout_container

    @staticmethod
    def create_buttons(
        start_btn_pressed_cb,
        stop_btn_pressed_cb,
        reset_btn_pressed_cb,
        plot_read_data_btn_pressed_cb,
        read_bin_metadata_btn_pressed_cb,
        enabled_channels,
        app,
    ):
        # ACTION BUTTONS
        buttons_row_layout = QHBoxLayout()
        buttons_row_layout.addStretch(1)
        # start button
        start_button = QPushButton("START")
        start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        GUIStyles.set_start_btn_style(start_button)
        start_button.setFlat(True)
        start_button.setFixedHeight(55)
        start_button.setFixedWidth(110)
        start_button.clicked.connect(start_btn_pressed_cb)
        start_button.setEnabled(len(enabled_channels) > 0)
        buttons_row_layout.addWidget(start_button)
        # stop button
        stop_button = QPushButton("STOP")
        stop_button.setCursor(Qt.CursorShape.PointingHandCursor)
        GUIStyles.set_stop_btn_style(stop_button)
        stop_button.setFlat(True)
        stop_button.setFixedHeight(55)
        stop_button.setFixedWidth(110)
        stop_button.setEnabled(False)

        stop_button.clicked.connect(stop_btn_pressed_cb)
        buttons_row_layout.addWidget(stop_button)
        # reset button
        reset_button = QPushButton("RESET")
        reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        GUIStyles.set_reset_btn_style(reset_button)
        reset_button.setFlat(True)
        reset_button.setFixedHeight(55)
        reset_button.setFixedWidth(110)
        reset_button.clicked.connect(reset_btn_pressed_cb)
        buttons_row_layout.addWidget(reset_button)
        # read/plot bin data button
        read_bin_data_button = QPushButton("READ/PLOT")
        read_bin_data_button.setFlat(True)
        read_bin_data_button.setFixedHeight(55)
        read_bin_data_button.setFixedWidth(120)
        read_bin_data_button.setCursor(Qt.CursorShape.PointingHandCursor)
        GUIStyles.set_start_btn_style(read_bin_data_button)
        read_bin_data_button.clicked.connect(plot_read_data_btn_pressed_cb)
        # read bin metadata button
        bin_metadata_button = QPushButton()
        bin_metadata_button.setIcon(QIcon(resource_path("assets/metadata-icon.png")))
        bin_metadata_button.setIconSize(QSize(30, 30))
        bin_metadata_button.setStyleSheet("background-color: white; padding: 0 14px;")
        bin_metadata_button.setFixedHeight(55)
        bin_metadata_button.setCursor(Qt.CursorShape.PointingHandCursor)
        bin_metadata_button.clicked.connect(read_bin_metadata_btn_pressed_cb)
        # # export plot image button
        from components.buttons import ExportPlotImageButton
        export_plot_img_button = ExportPlotImageButton(app)
        buttons_row_layout.addWidget(bin_metadata_button)
        buttons_row_layout.addWidget(export_plot_img_button)
        buttons_row_layout.addWidget(read_bin_data_button)
        buttons_row_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        return (
            buttons_row_layout,
            start_button,
            stop_button,
            reset_button,
            read_bin_data_button,
            bin_metadata_button,
            export_plot_img_button,
        )

    @staticmethod
    def create_channel_type_control(controls_row, value, change_cb, options):
        # Channels type control (USB/SMA)
        _, inp = SelectControl.setup(
            "Channel type:", value, controls_row, options, change_cb, spacing=None
        )
        inp.setStyleSheet(GUIStyles.set_input_select_style())
        inp.setFixedWidth(100)
        return inp

    @staticmethod
    def create_tau_control(controls_row, value, change_cb, options):
        # Channels type control (USB/SMA)
        _, inp = SelectControl.setup(
            "#τ:",
            value,
            controls_row,
            options,
            change_cb,
            "vertical",
            "font-family: Times New Roman; color: #f8f8f8; font-size: 18px;",
        )
        inp.setStyleSheet(GUIStyles.set_input_select_style())
        return inp

    @staticmethod
    def create_averages_control(controls_row, value, change_cb, options, free_running):
        # Averages control
        _, inp = SelectControl.setup(
            "#averages:",
            value,
            controls_row,
            options,
            change_cb,
        )
        inp.setEnabled(not free_running.isChecked())
        inp.setStyleSheet(GUIStyles.set_input_select_style())
        return inp

    @staticmethod
    def create_bin_width_control(controls_row, value, change_cb, options):
        # Bin width micros control
        _, inp = SelectControl.setup(
            "Bin width (µs):",
            value,
            controls_row,
            options,
            change_cb,
        )
        inp.setStyleSheet(GUIStyles.set_input_select_style())
        return inp

    @staticmethod
    def create_running_mode_control(value, change_cb):
        # Acquisition time mode switch control (Free Running/Fixed)
        running_mode_control = QVBoxLayout()
        inp = SwitchControl(active_color="#31c914", height=30, checked=value)
        inp.stateChanged.connect((lambda state: change_cb(state)))
        running_mode_control.addWidget(QLabel("Free running:"))
        running_mode_control.addSpacing(8)
        running_mode_control.addWidget(inp)

        return running_mode_control, inp

    @staticmethod
    def create_time_span_control(controls_row, value, change_cb):
        # Time span control
        _, inp = InputNumberControl.setup(
            "Time span (s):",
            1,
            300,
            value,
            controls_row,
            change_cb,
        )
        inp.setStyleSheet(GUIStyles.set_input_number_style())
        return inp

    @staticmethod
    def create_cps_threshold_control(controls_row, value, change_cb, show_cps):
        # CPS threshold control
        _, inp = InputNumberControl.setup(
            "Pile-up threshold (CPS):",
            0,
            100000000,
            value,
            controls_row,
            change_cb,
        )
        inp.setStyleSheet(GUIStyles.set_input_number_style())
        inp.setEnabled(show_cps)
        return inp

    @staticmethod
    def create_acquisition_time_control(controls_row, value, change_cb, free_running):
        # Acquisition time millis input number control
        # # (configurable when in acquisition time fixed mode)
        _, inp = InputNumberControl.setup(
            "Acquisition time (s):",
            0,
            1800,
            int(value / 1000) if value is not None else None,
            controls_row,
            change_cb,
        )
        inp.setEnabled(not free_running.isChecked())
        inp.setStyleSheet(GUIStyles.set_input_number_style())
        return inp

    @staticmethod
    def create_gt_calc_mode_buttons(
        realtime_btn_pressed_cb, post_processing_btn_pressed_cb, selected_calc_mode
    ):
        # G(T) CALC MODE TOGGLE BUTTONS
        buttons_row_layout = QHBoxLayout()
        buttons_row_layout.setSpacing(0)
        # realtime button
        realtime_button = QPushButton("REALTIME")
        realtime_button.setCursor(Qt.CursorShape.PointingHandCursor)
        realtime_button.setCheckable(True)

        realtime_button.clicked.connect(realtime_btn_pressed_cb)
        realtime_button.setChecked(selected_calc_mode == "realtime")
        realtime_button.setObjectName("realtime_btn")
        realtime_button.setStyleSheet(GUIStyles.gt_calc_mode_btn_style())
        # buttons_row_layout.addWidget(realtime_button)

        # post-processing button
        post_processing_button = QPushButton("POST-PROCESSING")
        # post_processing_button.setCheckable(True)
        # post_processing_button.setCursor(Qt.CursorShape.PointingHandCursor)

        # post_processing_button.clicked.connect(post_processing_btn_pressed_cb)
        # post_processing_button.setChecked(selected_calc_mode != "realtime")
        post_processing_button.setObjectName("post_processing_btn")
        post_processing_button.setStyleSheet(GUIStyles.gt_calc_mode_btn_style())
        buttons_row_layout.addWidget(post_processing_button)

        return buttons_row_layout, realtime_button, post_processing_button

    @staticmethod
    def create_tau_scale_control(controls_row, value, change_cb, options):
        # Tau scale control
        _, inp = SelectControl.setup(
            "Tau scale:",
            value,
            controls_row,
            options,
            change_cb,
        )
        inp.setStyleSheet(GUIStyles.set_input_select_style())
        return inp
