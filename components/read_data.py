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
from matplotlib import pyplot as plt

from components.box_message import BoxMessage
from components.fcs_controller import FCSPostProcessingPlot
from components.gui_styles import GUIStyles
from components.channel_name_utils import get_channel_name
from components.input_text_control import InputTextControl
from components.layout_utilities import (
    clear_layout,
    create_gt_layout,
    insert_widget,
    remove_widget,
)
from components.logo_utilities import TitlebarIcon
from components.messages_utilities import MessagesUtilities
from components.resource_path import resource_path
from components.settings import (
    ABORT_BUTTON,
    BIN_METADATA_BUTTON,
    CHECK_CARD_WIDGET,
    COLLAPSE_BUTTON,
    EXPORT_PLOT_IMG_BUTTON,
    GT_WIDGET_WRAPPER,
    INTENSITY_WIDGET_WRAPPER,
    PLOT_GRIDS_CONTAINER,
    READ_FILE_BUTTON,
    READER_METADATA_POPUP,
    READER_POPUP,
    RESET_BUTTON,
    SETTINGS_ACQUISITION_TIME_MILLIS,
    SETTINGS_BIN_WIDTH_MICROS,
    SETTINGS_CPS_THRESHOLD,
    SETTINGS_FREE_RUNNING_MODE,
    SETTINGS_GT_PLOTS_TO_SHOW,
    SETTINGS_TIME_SPAN,
    START_BUTTON,
    STOP_BUTTON,
    TOP_COLLAPSIBLE_WIDGET,
)


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
        app.reader_data["fcs"]["metadata"]["lag_index"] = lag_index
        app.reader_data["fcs"]["data"]["lag_index"] = lag_index
        app.reader_data["fcs"]["data"]["g2_correlations"] = g2_correlations
        
        # Extract channel_names from notes if present
        if "notes" in metadata and metadata["notes"]:
            try:
                notes_data = json.loads(metadata["notes"])
                if isinstance(notes_data, dict) and "channel_names" in notes_data:
                    app.reader_data["fcs"]["metadata"]["channel_names"] = notes_data["channel_names"]
                    app.reader_data["fcs"]["metadata"]["notes"] = notes_data.get("notes", "")
                else:
                    app.reader_data["fcs"]["metadata"]["channel_names"] = {}
            except:
                # If notes is not JSON, keep it as is
                app.reader_data["fcs"]["metadata"]["channel_names"] = {}
        else:
            app.reader_data["fcs"]["metadata"]["channel_names"] = {}

    @staticmethod
    def read_fcs_bin(window, app, filter_string = None):
        dialog = QFileDialog()
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if filter_string:
            filter_pattern = f"Bin files (*{filter_string}*.bin)"
        else:
            filter_pattern = "Bin files (*.bin)"
        dialog.setNameFilter(filter_pattern)         
        file_name, _ = dialog.getOpenFileName(
            window,
            f"Load FCS file",
            "",
            filter_pattern,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not file_name:
            return None
        if file_name is not None and not file_name.endswith(".bin"):   
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
        from components.intensity_tracing_controller import (
            IntensityTracingButtonsActions,
        )

        IntensityTracingButtonsActions.show_gt_widget(app, True)
        remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER])
        gt_widget = create_gt_layout(app)
        insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)
        app.widgets[GT_WIDGET_WRAPPER].setFixedWidth(app.width())
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
            res for res in g2_correlations if tuple(res[0]) in gt_plot_to_show
        ]
        
        # Get channel_names from file metadata for use in plot titles
        metadata = app.reader_data["fcs"]["metadata"]
        channel_names_from_file = metadata.get("channel_names", {})
        
        for index, res in enumerate(filtered_gt_results):
            correlation = res[0]
            gt_values = res[1][0]
            FCSPostProcessingPlot.generate_chart_with_custom_names(
                correlation, index, app, lag_index, gt_values, channel_names_from_file
            )

    @staticmethod
    def save_plot_image(plot):
        dialog = QFileDialog()
        base_path, _ = dialog.getSaveFileName(
            None,
            "Save plot image",
            "",
            "PNG Files (*.png);;EPS Files (*.eps)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )

        def show_success_message():
            info_title, info_msg = MessagesUtilities.info_handler("SavedPlotImage")
            BoxMessage.setup(
                info_title,
                info_msg,
                QMessageBox.Icon.Information,
                GUIStyles.set_msg_box_style(),
            )

        def show_error_message(error):
            ReadData.show_warning_message(
                "Error saving images", f"Error saving plot images: {error}"
            )

        if base_path:
            signals = WorkerSignals()
            signals.success.connect(show_success_message)
            signals.error.connect(show_error_message)
            task = SavePlotTask(plot, base_path, signals)
            QThreadPool.globalInstance().start(task)

    @staticmethod
    def prepare_fcs_data_for_export_img(app):
        lag_index = app.reader_data["fcs"]["data"]["lag_index"]
        g2_correlations = app.reader_data["fcs"]["data"]["g2_correlations"]
        return g2_correlations, lag_index

    @staticmethod
    def show_warning_message(title, message):
        BoxMessage.setup(
            title, message, QMessageBox.Icon.Warning, GUIStyles.set_msg_box_style()
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
        if ABORT_BUTTON in app.control_inputs:
            app.control_inputs[ABORT_BUTTON].setVisible(not read_mode)
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
        if CHECK_CARD_WIDGET in app.widgets:
            app.widgets[CHECK_CARD_WIDGET].setVisible(not read_mode)        

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
        if (
            "correlations" in file_metadata
            and file_metadata["correlations"] is not None
        ):
            ch_correlations = file_metadata["correlations"]
            # Get channel_names from file metadata
            channel_names_from_file = file_metadata.get("channel_names", {})
            
            self.app.gt_plots_to_show = []
            self.app.settings.setValue(
                SETTINGS_GT_PLOTS_TO_SHOW, json.dumps(self.app.gt_plots_to_show)
            )
            channels_layout = QVBoxLayout()
            desc = QLabel("CHOOSE MAX 4 PLOTS TO DISPLAY:")
            desc.setStyleSheet("font-size: 16px; font-family: 'Montserrat'")
            grid = QGridLayout()
            for ch in ch_correlations:
                ch1_name = get_channel_name(ch[0], channel_names_from_file, truncate_len=15)
                ch2_name = get_channel_name(ch[1], channel_names_from_file, truncate_len=15)
                checkbox, checkbox_wrapper = self.set_checkboxes(
                    f"{ch1_name} - {ch2_name}"
                )
                checkbox.setChecked(False)
                self.channels_checkboxes.append(checkbox)
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
        checkbox.setStyleSheet(GUIStyles.set_simple_checkbox_style(color="#ffff00"))
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
        gt_plot_to_show = [
            tuple(item) if isinstance(item, list) else item
            for item in self.app.gt_plots_to_show
        ]
        corr_tuple = self.extract_correlation_from_label(label_text)
        if state:
            if corr_tuple not in gt_plot_to_show:
                gt_plot_to_show.append(corr_tuple)
        else:
            if corr_tuple in gt_plot_to_show:
                gt_plot_to_show.remove(corr_tuple)
        self.app.gt_plots_to_show = gt_plot_to_show
        self.app.settings.setValue(
            SETTINGS_GT_PLOTS_TO_SHOW, json.dumps(gt_plot_to_show)
        )
        if len(gt_plot_to_show) >= 4:
            for checkbox in self.channels_checkboxes:
                if checkbox.text() != label_text and not checkbox.isChecked():
                    checkbox.setEnabled(False)
        else:
            for checkbox in self.channels_checkboxes:
                checkbox.setEnabled(True)
        if "plot_btn" in self.widgets:
            plot_btn_enabled = len(self.app.gt_plots_to_show) > 0
            self.widgets["plot_btn"].setEnabled(plot_btn_enabled)
        from components.intensity_tracing_controller import (
            IntensityTracingButtonsActions,
        )

        IntensityTracingButtonsActions.clear_plots(self.app)

    def on_loaded_file_change(self, text, file_type="fcs"):
        from components.intensity_tracing_controller import (
            IntensityTracingButtonsActions,
        )

        if text != self.app.reader_data["fcs"]["files"][file_type]:
            IntensityTracingButtonsActions.clear_plots(self.app)
        self.app.reader_data["fcs"]["files"][file_type] = text

    def on_load_file_btn_clicked(self):
        ReadData.read_bin_data(self, self.app)
        file_name = self.app.reader_data["fcs"]["files"]["fcs"]
        if file_name is not None and len(file_name) > 0:
            bin_metadata_btn_visible = ReadDataControls.read_bin_metadata_enabled(
                self.app
            )
            self.app.control_inputs[BIN_METADATA_BUTTON].setVisible(
                bin_metadata_btn_visible
            )
            self.app.control_inputs[EXPORT_PLOT_IMG_BUTTON].setVisible(
                bin_metadata_btn_visible
            )
            widget_key = "load_fcs_input"
            self.widgets[widget_key].setText(file_name)
            self.remove_channels_grid()
            channels_layout = self.init_channels_layout()
            if channels_layout is not None:
                self.layout.insertLayout(2, channels_layout)

    def on_plot_data_btn_clicked(self):
        ReadData.plot_fcs_data(self.app)
        self.close()

    def center_window(self):
        self.setMinimumWidth(500)
        window_geometry = self.frameGeometry()
        screen_geometry = QApplication.primaryScreen().availableGeometry().center()
        window_geometry.moveCenter(screen_geometry)
        self.move(window_geometry.topLeft())

    def extract_correlation_from_label(self, text):
        numbers = re.findall(r"\d+", text)
        corr_tuples = tuple(int(num) - 1 for num in numbers)
        return corr_tuples


class ReaderMetadataPopup(QWidget):
    def __init__(self, window):
        super().__init__()
        self.app = window
        self.setWindowTitle(f"FCS file metadata")
        TitlebarIcon.setup(self)
        GUIStyles.customize_theme(self, bg=QColor(20, 20, 20))
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # METADATA TABLE
        self.metadata_table = self.create_metadata_table()
        layout.addSpacing(10)
        layout.addLayout(self.metadata_table)
        layout.addSpacing(10)
        self.setLayout(layout)
        self.setStyleSheet(GUIStyles.plots_config_popup_style())
        self.app.widgets[READER_METADATA_POPUP] = self
        self.center_window()

    def get_metadata_keys_dict(self):
        return {
            "enabled_channels": "Enabled Channels",
            "bin_width": "Bin width (μs)",
            "acquisition_time": "Acquisition time (s)",
            "correlations": "Channels correlations",
            "num_acquisitions": "N. of acquisitions/channel",
            "lag_index": "Tau (lag index)",
            "notes": "Notes",
        }

    def create_metadata_table(self):
        metadata_keys = self.get_metadata_keys_dict()
        metadata = self.app.reader_data["fcs"]["metadata"]
        metadata["lag_index"][0] = 0
        file = self.app.reader_data["fcs"]["files"]["fcs"]
        v_box = QVBoxLayout()
        if metadata:
            title = QLabel(f"FCS FILE METADATA")
            title.setStyleSheet("font-size: 16px; font-family: 'Montserrat'")

            def get_key_label_style(bg_color):
                return f"width: 200px; font-size: 14px; border: 1px solid  {bg_color}; padding: 8px; color: white; background-color: {bg_color}"

            def get_value_label_style(bg_color):
                return f"width: 500px; font-size: 14px; border: 1px solid  {bg_color}; padding: 8px; color: white"

            v_box.addWidget(title)
            v_box.addSpacing(10)
            h_box = QHBoxLayout()
            h_box.setContentsMargins(0, 0, 0, 0)
            h_box.setSpacing(0)
            key_label = QLabel("File")
            key_label.setStyleSheet(get_key_label_style("#E65100"))
            value_label = QLabel(file)
            value_label.setStyleSheet(get_value_label_style("#E65100"))
            h_box.addWidget(key_label)
            h_box.addWidget(value_label)
            v_box.addLayout(h_box)
            for key, value in metadata_keys.items():
                metadata_value = ""
                if key in metadata:
                    metadata_value = str(metadata[key])
                    if key == "enabled_channels":
                        metadata_value = ", ".join(
                            ["Channel " + str(ch + 1) for ch in metadata[key]]
                        )
                    if key == "acquisition_time":
                        if metadata[key] is not None:
                            metadata_value = str(metadata[key] / 1000)
                    if key == "correlations":
                        correlated_channels = [
                            [channel + 1 for channel in pair] for pair in metadata[key]
                        ]
                        metadata_value = str(correlated_channels)
                    if key == "lag_index":
                        metadata_value = str(metadata[key])
                h_box = QHBoxLayout()
                h_box.setContentsMargins(0, 0, 0, 0)
                h_box.setSpacing(0)
                key_label = QLabel(value)
                key_label.setFixedWidth(300)
                value_label = QLabel(metadata_value)
                value_label.setWordWrap(True)
                key_label.setStyleSheet(get_key_label_style("#199401"))
                value_label.setStyleSheet(get_value_label_style("#199401"))
                h_box.addWidget(key_label)
                h_box.addWidget(value_label)
                v_box.addLayout(h_box)
        return v_box

    def center_window(self):
        self.setMinimumWidth(500)
        window_geometry = self.frameGeometry()
        screen_geometry = QApplication.primaryScreen().availableGeometry().center()
        window_geometry.moveCenter(screen_geometry)
        self.move(window_geometry.topLeft())


class WorkerSignals(QObject):
    success = pyqtSignal(str)
    error = pyqtSignal(str)


class SavePlotTask(QRunnable):
    def __init__(self, plot, base_path, signals):
        super().__init__()
        self.plot = plot
        self.base_path = base_path
        self.signals = signals

    @pyqtSlot()
    def run(self):
        try:
            # png
            png_path = (
                f"{self.base_path}.png"
                if not self.base_path.endswith(".png")
                else self.base_path
            )
            self.plot.savefig(png_path, format="png")
            # eps
            eps_path = (
                f"{self.base_path}.eps"
                if not self.base_path.endswith(".eps")
                else self.base_path
            )
            self.plot.savefig(eps_path, format="eps")
            plt.close(self.plot)
            self.signals.success.emit(
                f"Plot images saved successfully as {png_path} and {eps_path}"
            )
        except Exception as e:
            plt.close(self.plot)
            self.signals.error.emit(str(e))
