from functools import partial
import json
import os
import re
import struct
from PyQt6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGridLayout,
    QWidget,
    QCheckBox,
    QApplication,
)
from PyQt6.QtCore import Qt, QRunnable, QThreadPool, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtGui import QColor, QIcon

from components.fcs_controller import FCSPostProcessingPlot
from components.gui_styles import GUIStyles
from components.input_text_control import InputTextControl
from components.layout_utilities import clear_layout
from components.logo_utilities import TitlebarIcon
from components.resource_path import resource_path
from components.settings import BIN_METADATA_BUTTON, COLLAPSE_BUTTON, EXPORT_PLOT_IMG_BUTTON, GT_WIDGET_WRAPPER, INTENSITY_WIDGET_WRAPPER, READ_FILE_BUTTON, READER_POPUP, RESET_BUTTON, SETTINGS_ACQUISITION_TIME_MILLIS, SETTINGS_BIN_WIDTH_MICROS, SETTINGS_CPS_THRESHOLD, SETTINGS_ENABLED_CHANNELS, SETTINGS_FREE_RUNNING_MODE, SETTINGS_INTENSITY_PLOTS_TO_SHOW, SETTINGS_TIME_SPAN, START_BUTTON, STOP_BUTTON, TOP_COLLAPSIBLE_WIDGET


current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class ReadData:
    @staticmethod
    def read_bin_data(window, app):
        result = ReadData.read_fcs_bin(window, app)
        if not result:
            return
        file_name, lag_index, g2_correlations, metadata = result
        app.reader_data["fcs"]["files"]["fcs"] = file_name
        app.reader_data["fcs"]["plots"] = []
        app.reader_data["fcs"]["metadata"] = metadata
        app.reader_data["fcs"]["data"]["lag_index"] = lag_index
        app.reader_data["fcs"]["data"]["g2_correlations"] = g2_correlations

    @staticmethod
    def read_fcs_bin(window, app):
        dialog = QFileDialog()
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        dialog.setNameFilter("Bin files (*.bin)")
        file_name, _ = dialog.getOpenFileName(
            window,
            f"Load FCS file",
            "",
            "Bin files (*.bin)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not file_name or not file_name.endswith(".bin"):
            ReadData.show_warning_message(
                "Invalid extension", "Invalid extension. File should be a .bin"
            )
            return None

        try:
            with open(file_name, "rb") as f:
                if f.read(4) != b"FCS1":
                    ReadData.show_warning_message(
                        "Invalid file",
                        f"Invalid file. The file is not a valid FCS file file.",
                    )
                    return None
                return ReadData.read_fcs_data(f, file_name)
        except Exception:
            ReadData.show_warning_message(
                "Error reading file", f"Error reading FCS file"
            )
            return None

    @staticmethod
    def read_fcs_data(file, file_name):
        try:
            json_length = struct.unpack("I", file.read(4))[0]
            metadata = json.loads(file.read(json_length).decode("utf-8"))
            (g2_correlations_json_length,) = struct.unpack("I", file.read(4))
            g2_correlations_json_string = file.read(g2_correlations_json_length).decode(
                "utf-8"
            )
            g2_correlations_json = eval(g2_correlations_json_string)
            lag_index = g2_correlations_json["lag_index"]
            g2_correlations = g2_correlations_json["g2_correlations"]
            return file_name, lag_index, g2_correlations, metadata
        except Exception as e:
            ReadData.show_warning_message(
                "Error reading file", "Error reading FCS file"
            )
            return None
        
        
    @staticmethod
    def plot_fcs_data(app):
        data = app.reader_data["fcs"]["data"]
        if not "lag_index" in data and not "g2_correlations" in data:
            return
        lag_index = data["lag_index"]
        g2_correlations = data["g2_correlations"]
        gt_plot_to_show = [
                    tuple(item) if isinstance(item, list) else item
                    for item in app.gt_plots_to_show
                ] 
        filtered_gt_results = [
            res for res in g2_correlations if res[0] in gt_plot_to_show
        ]
        for index, res in enumerate(filtered_gt_results):
                    correlation = res[0]
                    gt_values = res[1][0]
                    FCSPostProcessingPlot.generate_chart(
                        correlation, index, app, lag_index, gt_values
                    )                       
        


class ReadDataControls:
    @staticmethod
    def handle_widgets_visibility(app, read_mode):
        if INTENSITY_WIDGET_WRAPPER in app.widgets:
            app.widgets[INTENSITY_WIDGET_WRAPPER].setVisible(not read_mode)   
        app.controls_set_enabled(not read_mode)
        bin_metadata_btn_visible = ReadDataControls.read_bin_metadata_enabled(app)
        app.control_inputs[BIN_METADATA_BUTTON].setVisible(bin_metadata_btn_visible)
        app.control_inputs[START_BUTTON].setVisible(not read_mode)
        app.control_inputs[STOP_BUTTON].setVisible(not read_mode)
        app.control_inputs[RESET_BUTTON].setVisible(not read_mode)
        app.control_inputs[READ_FILE_BUTTON].setVisible(read_mode)
        app.control_inputs[EXPORT_PLOT_IMG_BUTTON].setVisible(bin_metadata_btn_visible)
        app.widgets[TOP_COLLAPSIBLE_WIDGET].setVisible(not read_mode)
        app.widgets[COLLAPSE_BUTTON].setVisible(not read_mode)
        app.control_inputs[SETTINGS_BIN_WIDTH_MICROS].setEnabled(not read_mode)
        app.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS].setEnabled(
            not read_mode and not app.free_running_acquisition_time
        )
        app.control_inputs[SETTINGS_FREE_RUNNING_MODE].setEnabled(not read_mode)
        app.control_inputs[SETTINGS_CPS_THRESHOLD].setEnabled(not read_mode)
        app.control_inputs[SETTINGS_TIME_SPAN].setEnabled(not read_mode)

    @staticmethod
    def read_bin_metadata_enabled(app):
        metadata = app.reader_data["fcs"]["metadata"]
        return not (metadata == {}) and app.acquire_read_mode == "read"


        
class ReaderPopup(QWidget):
    def __init__(self, window):
        super().__init__()
        self.app = window
        self.widgets = {}
        self.layouts = {}
        self.channels_checkboxes = []
        self.channels_checkbox_first_toggle = True
        self.setWindowTitle("Read data")
        TitlebarIcon.setup(self)
        GUIStyles.customize_theme(self, bg=QColor(20, 20, 20))
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # PLOT BUTTON ROW
        plot_btn_row = self.create_plot_btn_layout()
        # LOAD FILE ROW
        load_file_row = self.init_file_load_ui()
        self.layout.addSpacing(10)
        self.layout.insertLayout(1, load_file_row)
        # LOAD CHANNELS GRID
        self.layout.addSpacing(20)
        channels_layout = self.init_channels_layout()
        if channels_layout is not None:
            self.layout.insertLayout(2, channels_layout)
        self.layout.addSpacing(20)
        self.layout.insertLayout(3, plot_btn_row)
        self.setLayout(self.layout)
        self.setStyleSheet(GUIStyles.plots_config_popup_style())
        self.app.widgets[READER_POPUP] = self
        self.center_window()

    def init_file_load_ui(self):
        v_box = QVBoxLayout()
        files = self.app.reader_data["fcs"]["files"]
        for file_type, file_path in files.items():
            input_desc = QLabel(f"LOAD FCS FILE:")
            input_desc.setStyleSheet("font-size: 16px; font-family: 'Montserrat'")
            control_row = QHBoxLayout()
            file_extension = ".bin"

            def on_change(file_type=file_type):
                def callback(text):
                    self.on_loaded_file_change(text, file_type)

                return callback

            _, input = InputTextControl.setup(
                label="",
                placeholder=f"Load {file_extension} file",
                event_callback=on_change(),
                text=file_path,
            )
            input.setStyleSheet(GUIStyles.set_input_text_style())
            widget_key = f"load_{file_type}_input"
            self.widgets[widget_key] = input
            load_file_btn = QPushButton()
            load_file_btn.setIcon(QIcon(resource_path("assets/folder-white.png")))
            load_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            GUIStyles.set_start_btn_style(load_file_btn)
            load_file_btn.setFixedHeight(36)
            load_file_btn.clicked.connect(partial(self.on_load_file_btn_clicked))
            control_row.addWidget(input)
            control_row.addWidget(load_file_btn)
            v_box.addWidget(input_desc)
            v_box.addSpacing(10)
            v_box.addLayout(control_row)
            v_box.addSpacing(10)
        return v_box

    def init_channels_layout(self):
        self.channels_checkboxes.clear()
        file_metadata = self.app.reader_data["fcs"]["metadata"]
        plots_to_show = self.app.reader_data["fcs"]["plots"]
        if "channels" in file_metadata and file_metadata["channels"] is not None:
            selected_channels = file_metadata["channels"]
            selected_channels.sort()
            self.app.enabled_channels = selected_channels
            for i, ch in enumerate(self.app.channels_checkboxes):
                ch.set_checked(i in self.app.enabled_channels)
            self.app.settings.setValue(
                SETTINGS_ENABLED_CHANNELS, json.dumps(self.app.enabled_channels)
            )
            if len(plots_to_show) == 0:
                plots_to_show = selected_channels[:2]
            self.app.intensity_plots_to_show = plots_to_show
            self.app.settings.setValue(
                SETTINGS_INTENSITY_PLOTS_TO_SHOW, json.dumps(plots_to_show)
            )
            channels_layout = QVBoxLayout()
            desc = QLabel("CHOOSE MAX 4 PLOTS TO DISPLAY:")
            desc.setStyleSheet("font-size: 16px; font-family: 'Montserrat'")
            grid = QGridLayout()
            for ch in selected_channels:
                checkbox, checkbox_wrapper = self.set_checkboxes(f"Channel {ch + 1}")
                isChecked = ch in plots_to_show
                checkbox.setChecked(isChecked)
                if len(plots_to_show) >= 4 and ch not in plots_to_show:
                    checkbox.setEnabled(False)
                grid.addWidget(checkbox_wrapper)
            channels_layout.addWidget(desc)
            channels_layout.addSpacing(10)
            channels_layout.addLayout(grid)
            self.layouts["ch_layout"] = channels_layout
            return channels_layout
        else:
            return None

    def create_plot_btn_layout(self):
        row_btn = QHBoxLayout()
        # PLOT BTN
        plot_btn = QPushButton("")
        plot_btn.setText("PLOT DATA")
        plot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        plot_btn.setObjectName("btn")
        GUIStyles.set_stop_btn_style(plot_btn)
        plot_btn.setFixedHeight(40)
        plot_btn.setFixedWidth(150)
        plots_to_show = self.app.reader_data["fcs"]["plots"]
        plot_btn.setEnabled(len(plots_to_show) > 0)
        plot_btn.clicked.connect(self.on_plot_data_btn_clicked)
        self.widgets["plot_btn"] = plot_btn
        row_btn.addStretch(1)
        row_btn.addWidget(plot_btn)
        return row_btn

    def remove_channels_grid(self):
        if "ch_layout" in self.layouts:
            clear_layout(self.layouts["ch_layout"])
            del self.layouts["ch_layout"]

    def set_checkboxes(self, text):
        checkbox_wrapper = QWidget()
        checkbox_wrapper.setObjectName(f"simple_checkbox_wrapper")
        row = QHBoxLayout()
        checkbox = QCheckBox(text)
        checkbox.setStyleSheet(GUIStyles.set_simple_checkbox_style(color="#8d4ef2"))
        checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        checkbox.toggled.connect(
            lambda state, checkbox=checkbox: self.on_channel_toggled(state, checkbox)
        )
        row.addWidget(checkbox)
        checkbox_wrapper.setLayout(row)
        checkbox_wrapper.setStyleSheet(GUIStyles.checkbox_wrapper_style())
        return checkbox, checkbox_wrapper

    def on_channel_toggled(self, state, checkbox):
        label_text = checkbox.text()
        ch_index = self.extract_channel_from_label(label_text)
        if state:
            if ch_index not in self.app.intensity_plots_to_show:
                self.app.intensity_plots_to_show.append(ch_index)
        else:
            if ch_index in self.app.intensity_plots_to_show:
                self.app.intensity_plots_to_show.remove(ch_index)
        self.app.intensity_plots_to_show.sort()
        self.app.settings.setValue(
            SETTINGS_INTENSITY_PLOTS_TO_SHOW,
            json.dumps(self.app.intensity_plots_to_show),
        )
        self.app.reader_data["fcs"]["plots"] = self.app.intensity_plots_to_show
        if len(self.app.intensity_plots_to_show) >= 4:
            for checkbox in self.channels_checkboxes:
                if checkbox.text() != label_text and not checkbox.isChecked():
                    checkbox.setEnabled(False)
        else:
            for checkbox in self.channels_checkboxes:
                checkbox.setEnabled(True)
        if "plot_btn" in self.widgets:
            plot_btn_enabled = len(self.app.intensity_plots_to_show) > 0
            self.widgets["plot_btn"].setEnabled(plot_btn_enabled)
        from components.intensity_tracing_controller import IntensityTracingButtonsActions    
        IntensityTracingButtonsActions.clear_plots(self.app)

    def on_loaded_file_change(self, text, file_type="fcs"):
        from components.intensity_tracing_controller import IntensityTracingButtonsActions    
        if text != self.app.reader_data["fcs"]["files"][file_type]:
            IntensityTracingButtonsActions.clear_plots(self.app) 
        self.app.reader_data["fcs"]["files"][file_type] = text

    @classmethod
    def handle_bin_file_result_ui(cls, instance):
        app = instance.app
        app.loading_overlay.toggle_overlay()
        file_name = app.reader_data["intensity"]["files"]["intensity"]
        if file_name is not None and len(file_name) > 0:
            bin_metadata_btn_visible = ReadDataControls.read_bin_metadata_enabled(app)
            app.control_inputs[BIN_METADATA_BUTTON].setVisible(bin_metadata_btn_visible)
            app.control_inputs[EXPORT_PLOT_IMG_BUTTON].setVisible(
                bin_metadata_btn_visible
            )
            widget_key = "load_fcs_input"
            instance.widgets[widget_key].setText(file_name)
            instance.remove_channels_grid()
            channels_layout = instance.init_channels_layout()
            if channels_layout is not None:
                instance.layout.insertLayout(2, channels_layout)

    def on_load_file_btn_clicked(self):
        ReadData.read_bin_data(self, self.app)

    def on_plot_data_btn_clicked(self):
        ReadData.plot_fcs_data(self.app)
        self.close()

    def center_window(self):
        self.setMinimumWidth(500)
        window_geometry = self.frameGeometry()
        screen_geometry = QApplication.primaryScreen().availableGeometry().center()
        window_geometry.moveCenter(screen_geometry)
        self.move(window_geometry.topLeft())

    def extract_channel_from_label(self, text):
        ch = re.search(r"\d+", text).group()
        ch_num = int(ch)
        ch_num_index = ch_num - 1
        return ch_num_index
    
    
    
class ReaderMetadataPopup(QWidget):
        pass    