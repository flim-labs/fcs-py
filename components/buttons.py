import json
import os
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QCheckBox, QLabel
from PyQt6.QtCore import QPropertyAnimation, Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap
from components.intensity_tracing_controller import IntensityTracingButtonsActions
from components.plots_config_widget import PlotsConfigPopup
from components.read_data import ReadData, ReadDataControls, ReaderMetadataPopup, ReaderPopup
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.controls_bar_builder import ControlsBarBuilder
from components.settings import *
from load_data import plot_fcs_data

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class CollapseButton(QWidget):
    def __init__(self, collapsible_widget, parent=None):
        super().__init__(parent)
        self.collapsible_widget = collapsible_widget
        self.collapsed = True
        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(
            QIcon(resource_path("assets/arrow-up-dark-grey.png"))
        )
        self.toggle_button.setFixedSize(30, 30)
        self.toggle_button.setStyleSheet(GUIStyles.toggle_collapse_button())
        self.toggle_button.clicked.connect(self.toggle_collapsible)
        self.toggle_button.move(self.toggle_button.x(), self.toggle_button.y() - 100)
        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addWidget(self.toggle_button)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.animation = QPropertyAnimation(self.collapsible_widget, b"maximumHeight")
        self.animation.setDuration(300)

    def toggle_collapsible(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.animation.setStartValue(0)
            self.animation.setEndValue(self.collapsible_widget.sizeHint().height())
            self.toggle_button.setIcon(
                QIcon(resource_path("assets/arrow-up-dark-grey.png"))
            )
        else:
            self.animation.setStartValue(self.collapsible_widget.sizeHint().height())
            self.animation.setEndValue(0)
            self.toggle_button.setIcon(
                QIcon(resource_path("assets/arrow-down-dark-grey.png"))
            )
        self.animation.start()


class ActionButtons(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window

        layout = self.create_buttons()
        self.setLayout(layout)

    def create_buttons(self):
        (
            buttons_row_layout,
            start_button,
            stop_button,
            reset_button,
            read_bin_data_button,
            bin_metadata_button,
            export_plot_img_button,
            abort_button,
        ) = ControlsBarBuilder.create_buttons(
            self.start_button_pressed,
            self.stop_button_pressed,
            self.reset_button_pressed,
            self.plot_read_data_button_pressed,
            self.read_bin_metadata_button_pressed,
            self.app.enabled_channels,
            self.app,
            self.abort_button_pressed,
        )
        self.app.control_inputs[START_BUTTON] = start_button
        self.app.control_inputs[STOP_BUTTON] = stop_button
        self.app.control_inputs[RESET_BUTTON] = reset_button
        self.app.control_inputs[ABORT_BUTTON] = abort_button
        read_bin_data_button.setVisible(self.app.acquire_read_mode == "read")
        bin_metadata_btn_visible = ReadDataControls.read_bin_metadata_enabled(self.app)
        bin_metadata_button.setVisible(bin_metadata_btn_visible)
        self.app.control_inputs[BIN_METADATA_BUTTON] = bin_metadata_button
        self.app.control_inputs[READ_FILE_BUTTON] = read_bin_data_button
        return buttons_row_layout

    def start_button_pressed(self):
        open_popup = len(self.app.gt_plots_to_show) == 0
        if open_popup:
            popup = PlotsConfigPopup(self.app, start_acquisition=True)
            popup.show()
        else:
            IntensityTracingButtonsActions.start_button_pressed(self.app)

    def stop_button_pressed(self):
        IntensityTracingButtonsActions.stop_button_pressed(self.app)

    def abort_button_pressed(self):
        IntensityTracingButtonsActions.abort_button_pressed(self.app)

    def reset_button_pressed(self):
        IntensityTracingButtonsActions.reset_button_pressed(self.app)

    def plot_read_data_button_pressed(self):
        popup = ReaderPopup(self.app)
        popup.show()
        
    
    def read_bin_metadata_button_pressed(self):
        popup = ReaderMetadataPopup(self.app)
        popup.show()
            


class GTModeButtons(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window

        layout = self.create_buttons()
        self.setLayout(layout)

    def create_buttons(self):
        buttons_row_layout, realtime_button, post_processing_button = (
            ControlsBarBuilder.create_gt_calc_mode_buttons(
                self.realtime_button_pressed,
                self.post_processing_button_pressed,
                self.app.selected_gt_calc_mode,
            )
        )
        self.app.control_inputs[REALTIME_BUTTON] = realtime_button
        self.app.control_inputs[POST_PROCESSING_BUTTON] = post_processing_button
        return buttons_row_layout

    def realtime_button_pressed(self, checked):
        self.app.control_inputs[REALTIME_BUTTON].setChecked(checked)
        self.app.control_inputs[POST_PROCESSING_BUTTON].setChecked(not checked)
        self.app.settings.setValue(
            SETTINGS_GT_CALC_MODE, "realtime" if checked else "post-processing"
        )

    def post_processing_button_pressed(self, checked):
        self.app.control_inputs[REALTIME_BUTTON].setChecked(not checked)
        self.app.control_inputs[POST_PROCESSING_BUTTON].setChecked(checked)
        self.app.settings.setValue(
            SETTINGS_GT_CALC_MODE, "post-processing" if checked else "realtime"
        )


class ReadAcquireModeButton(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        layout = QVBoxLayout()
        buttons_row = self.create_buttons()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(buttons_row)
        self.setLayout(layout)

    def create_buttons(self):
        buttons_row_layout = QHBoxLayout()
        buttons_row_layout.setSpacing(0)
        # Acquire button
        acquire_button = QPushButton("ACQUIRE")
        acquire_button.setCursor(Qt.CursorShape.PointingHandCursor)
        acquire_button.setCheckable(True)
        acquire_button.setObjectName("acquire_btn")  # Set objectName
        acquire_button.setChecked(self.app.acquire_read_mode == "acquire")
        acquire_button.clicked.connect(self.on_acquire_btn_pressed)
        buttons_row_layout.addWidget(acquire_button)
        # Read button
        read_button = QPushButton("READ")
        read_button.setCheckable(True)
        read_button.setCursor(Qt.CursorShape.PointingHandCursor)
        read_button.setObjectName("read_btn")  # Set objectName
        read_button.setChecked(self.app.acquire_read_mode != "acquire")
        read_button.clicked.connect(self.on_read_btn_pressed)
        buttons_row_layout.addWidget(read_button)
        self.app.control_inputs[ACQUIRE_BUTTON] = acquire_button
        self.app.control_inputs[READ_BUTTON] = read_button
        self.apply_base_styles()
        self.set_buttons_styles()
        return buttons_row_layout

    def apply_base_styles(self):
        base_style = GUIStyles.acquire_read_btn_style()
        self.app.control_inputs[ACQUIRE_BUTTON].setStyleSheet(base_style)
        self.app.control_inputs[READ_BUTTON].setStyleSheet(base_style)

    def set_buttons_styles(self):
        def get_buttons_style(color_acquire, color_read, bg_acquire, bg_read):
            return f"""
            QPushButton {{
                font-family: "Montserrat";
                letter-spacing: 0.1em;
                padding: 10px 12px;
                font-size: 14px;
                font-weight: bold;
                min-width: 60px;
            }}
            QPushButton#acquire_btn {{
                border-top-left-radius: 3px;
                border-bottom-left-radius: 3px;
                color: {color_acquire};
                background-color: {bg_acquire};
            }}
            QPushButton#read_btn {{
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                color: {color_read};
                background-color: {bg_read};
            }}
        """

        read_mode = self.app.acquire_read_mode == "read"
        if read_mode:
            style = get_buttons_style(
                color_acquire="#8c8b8b",
                color_read="#222222",
                bg_acquire="#cecece",
                bg_read="#ffff00",
            )
        else:
            style = get_buttons_style(
                color_acquire="#222222",
                color_read="#8c8b8b",
                bg_acquire="#ffff00",
                bg_read="#cecece",
            )
        self.app.control_inputs[ACQUIRE_BUTTON].setStyleSheet(style)
        self.app.control_inputs[READ_BUTTON].setStyleSheet(style)

    def on_acquire_btn_pressed(self, checked):
        from components.intensity_tracing_controller import IntensityTracingButtonsActions 
        IntensityTracingButtonsActions.clear_plots(self.app)
        self.app.control_inputs[ACQUIRE_BUTTON].setChecked(checked)
        self.app.control_inputs[READ_BUTTON].setChecked(not checked)
        self.app.acquire_read_mode = "acquire" if checked else "read"
        self.app.settings.setValue(
            SETTINGS_ACQUIRE_READ_MODE, self.app.acquire_read_mode
        )
        self.set_buttons_styles()
        self.app.reader_data = deepcopy(DEFAULT_READER_DATA)
        ReadDataControls.handle_widgets_visibility(
            self.app, self.app.acquire_read_mode == "read"
        )
        self.app.gt_plots_to_show = []        
        self.app.settings.setValue(SETTINGS_GT_PLOTS_TO_SHOW, json.dumps(self.app.gt_plots_to_show))         

    def on_read_btn_pressed(self, checked):
        from components.intensity_tracing_controller import IntensityTracingButtonsActions 
        IntensityTracingButtonsActions.clear_plots(self.app)
        self.app.control_inputs[ACQUIRE_BUTTON].setChecked(not checked)
        self.app.control_inputs[READ_BUTTON].setChecked(checked)
        self.app.acquire_read_mode = "read" if checked else "acquire"
        self.app.settings.setValue(
            SETTINGS_ACQUIRE_READ_MODE, self.app.acquire_read_mode
        )
        self.set_buttons_styles()
        ReadDataControls.handle_widgets_visibility(
            self.app, self.app.acquire_read_mode == "read"
        )

class ExportPlotImageButton(QWidget):
    def __init__(self, app, show = True, parent=None):
        super().__init__(parent)
        self.app = app
        self.show = show
        self.data = None
        self.export_img_button = self.create_button()
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.export_img_button)
        self.setLayout(layout)
        
    def create_button(self):
        export_img_button = QPushButton()
        export_img_button.setIcon(
            QIcon(resource_path("assets/save-img-icon.png"))
        )
        export_img_button.setIconSize(QSize(30, 30))
        export_img_button.setStyleSheet("background-color: #FB8C00; padding: 0 14px;")
        export_img_button.setFixedHeight(55)
        export_img_button.setCursor(Qt.CursorShape.PointingHandCursor)
        export_img_button.clicked.connect(self.on_export_plot_image)
        button_visible = ReadDataControls.read_bin_metadata_enabled(self.app) and self.show
        export_img_button.setVisible(button_visible)
        self.app.control_inputs[EXPORT_PLOT_IMG_BUTTON] = export_img_button
        return export_img_button
    
    
    def on_export_plot_image(self):
        g2_correlations, lag_index = ReadData.prepare_fcs_data_for_export_img(self.app)
        plot = plot_fcs_data(g2_correlations, lag_index, show_plot=False)
        ReadData.save_plot_image(plot)        
  
   

class TimeTaggerWidget(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        write_data = self.app.write_data
        time_tagger_container = QWidget()
        time_tagger_container.setObjectName("container")
        time_tagger_container.setStyleSheet(GUIStyles.time_tagger_style())
        time_tagger_container.setFixedHeight(48)
        time_tagger_container.setContentsMargins(0, 0, 0, 0)
        time_tagget_layout = QHBoxLayout()
        time_tagget_layout.setSpacing(0)
        # time tagger icon
        pixmap = QPixmap(resource_path("assets/time-tagger-icon.png")).scaledToWidth(25)
        icon = QLabel(pixmap=pixmap)
        # time tagger checkbox
        time_tagger_checkbox = QCheckBox("TIME TAGGER")
        time_tagger_checkbox.setChecked(self.app.time_tagger)
        time_tagger_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        time_tagger_checkbox.toggled.connect(
            lambda checked: self.on_time_tagger_state_changed(
                checked
            )
        )        
        time_tagget_layout.addWidget(time_tagger_checkbox)
        time_tagget_layout.addWidget(icon)
        time_tagger_container.setLayout(time_tagget_layout)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(time_tagger_container)
        self.app.widgets[TIME_TAGGER_WIDGET] = self
        self.setLayout(main_layout)
        self.setVisible(write_data)
        
    def on_time_tagger_state_changed(self, checked):
        self.app.time_tagger = checked        
        