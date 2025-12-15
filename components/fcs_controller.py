from functools import partial
from components.box_message import BoxMessage
from components.gui_styles import GUIStyles
from components.layout_utilities import create_gt_layout, insert_widget, remove_widget
from components.settings import (
    GT_PLOTS_GRID,
    GT_PROGRESS_BAR_WIDGET,
    GT_WIDGET_WRAPPER,
    PLOT_GRIDS_CONTAINER,
    TIME_TAGGER_PROGRESS_BAR,
    UNICODE_SUP,
)
import numpy as np
import pyqtgraph as pg
import flim_labs 
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont

from components.time_tagger import TimeTaggerController


class FCSPostProcessingSingleCalcWorker(QThread):
    finished = pyqtSignal()
    single_step_finished = pyqtSignal(object)

    def __init__(
        self,
        active_correlations,
        num_acquisitions,
        enabled_channels,
        bin_width,
        acquisition_time,
        export_data,
        notes,
        tau_high_density
    ):
        super().__init__()
        self.active_correlations = active_correlations
        self.num_acquisitions = num_acquisitions
        self.enabled_channels = enabled_channels
        self.bin_width = bin_width
        self.tau_high_density = tau_high_density
        self.acquisition_time = acquisition_time
        self.export_data = export_data
        self.notes = notes
        self.is_running = True

    def run(self):
        self.single_step_finished.emit(0)
        for num in range(self.num_acquisitions):
            if not self.is_running:
                break
            flim_labs.fluorescence_correlation_spectroscopy(
                num_acquisitions=self.num_acquisitions,
                correlations=self.active_correlations,
                enabled_channels=self.enabled_channels,
                bin_width=self.bin_width,
                acquisition_time=self.acquisition_time,
                export_data=self.export_data,
                notes=self.notes,
                tau_high_density=self.tau_high_density
            )
            if not self.is_running:
                break
            self.single_step_finished.emit(num + 1)
        self.finished.emit()

    def stop(self):
        self.is_running = False


class FCSPostProcessingAverageCalcWorker(QThread):
    success = pyqtSignal(object)
    error = pyqtSignal(str) 

    def __init__(self, num_acquisitions):
        super().__init__()
        self.num_acquisitions = num_acquisitions
        self.is_running = True

    def run(self):
        try:
            result = flim_labs.average_fluorescence_correlation_spectroscopy(
                num_acquisitions=self.num_acquisitions,
            )
            if self.is_running:
                self.success.emit(result)
        except ValueError as e:  
            self.error.emit(str(e)) 

    def stop(self):
        self.is_running = False


class FCSPostProcessing:
    @staticmethod
    def get_input(app):
        notes = app.notes
        free_running_mode = app.free_running_acquisition_time
        enabled_channels = app.enabled_channels
        bin_width = int(app.bin_width_micros)
        acquisition_time = (
            app.acquisition_time_millis
            if not free_running_mode
            else int(app.last_acquisition_ns / 1000000)
        )
        export_data = app.write_data
        correlations = [
            tuple(item) if isinstance(item, list) else item
            for item in app.ch_correlations
        ]
        active_correlations = [
            (ch1, ch2) for ch1, ch2, active in correlations if active
        ]
        num_acquisitions = app.selected_average if free_running_mode == False else 1
        tau_high_density = app.tau_axis_scale == "High density"
        
        if hasattr(flim_labs, "reset_fcs_stop"):
            flim_labs.reset_fcs_stop()
        worker = FCSPostProcessingSingleCalcWorker(
            active_correlations,
            num_acquisitions,
            enabled_channels,
            bin_width,
            acquisition_time,
            export_data,
            notes,
            tau_high_density
        )
        QApplication.processEvents()
        app.fcs_single_worker = worker
        worker.single_step_finished.connect(
            lambda iteration: FCSPostProcessing.update_gt_progress_bar(
                iteration, app, worker
            )
        )
        worker.finished.connect(lambda: FCSPostProcessing.gt_averages_calc(app, worker))
        worker.start()

    @staticmethod
    def update_gt_progress_bar(iteration, app, worker):
        if iteration == 0:
            app.widgets[GT_PROGRESS_BAR_WIDGET].setVisible(True)
        app.widgets[GT_PROGRESS_BAR_WIDGET].update_calculation_count(iteration)

    @staticmethod
    def gt_averages_calc(app, worker):
        worker.stop()
        num_acquisitions = app.selected_average if app.free_running_acquisition_time == False else 1
        worker = FCSPostProcessingAverageCalcWorker(num_acquisitions)
        app.fcs_avg_worker = worker
        worker.success.connect(lambda result: FCSPostProcessing.handle_fcs_post_processing_result(result, app, worker))
        worker.error.connect(lambda error_message: display_error_message(error_message))
        def display_error_message(error_message):
            BoxMessage.setup(
            "FCS Processing Error",
            error_message,
            QMessageBox.Icon.Critical,
            GUIStyles.set_msg_box_style(),
        )
        worker.start()  
    
    @staticmethod
    def abort(app):
        if hasattr(flim_labs, "request_fcs_stop"):
            try:
                flim_labs.request_fcs_stop()
            except Exception:
                pass
        if hasattr(app, "fcs_single_worker") and app.fcs_single_worker is not None:
            app.fcs_single_worker.stop()
        if hasattr(app, "fcs_avg_worker") and app.fcs_avg_worker is not None:
            app.fcs_avg_worker.stop()
        if GT_PROGRESS_BAR_WIDGET in app.widgets:
            app.widgets[GT_PROGRESS_BAR_WIDGET].setVisible(False)

    @staticmethod
    def handle_fcs_post_processing_result(gt_results, app, worker):
        from components.data_export_controls import ExportData
        worker.stop()
        app.acquisition_stopped = True
        remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER])
        gt_widget = create_gt_layout(app)
        insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)
        gt_plot_to_show = [
            tuple(item) if isinstance(item, list) else item
            for item in app.gt_plots_to_show
        ]
        lag_index = gt_results.lag_index
        filtered_gt_results = [
            res for res in gt_results.g2_correlations if res[0] in gt_plot_to_show
        ]
        for index, res in enumerate(filtered_gt_results):
            correlation = res[0]
            gt_values = res[1][0]
            FCSPostProcessingPlot.generate_chart(
                correlation, index, app, lag_index, gt_values
            )
        if app.write_data:    
            QTimer.singleShot(
                300,
                partial(ExportData.save_fcs_data, app),
            )
              
        # if app.write_data and app.time_tagger:
            # app.widgets[TIME_TAGGER_PROGRESS_BAR].set_visible(True)
            #TimeTaggerController.init_time_tagger_processing(app)            
            

class FCSPostProcessingPlot:
    @staticmethod
    def generate_chart(correlation, index, app, lag_index, gt_values):
        values = np.array(lag_index)
        values = np.where(values <= 0, 1e-9, values)
        log_values = np.log10(values)
        log_values = np.where(log_values < 0, -0.1, log_values)
        exponents_int = log_values.astype(int)
        exponents_lin_space_int = np.linspace(
            0, max(exponents_int), len(exponents_int)
        ).astype(int)        
        gt_widget = pg.PlotWidget()
        gt_widget.setLabel("left", "G(τ)", units="")
        gt_widget.setLabel("bottom", "τ (μs)", units="")
        q_font = QFont("Times New Roman")
        gt_widget.getAxis("bottom").label.setFont(q_font)
        gt_widget.getAxis("left").label.setFont(q_font)
        gt_widget.setTitle(
            f"Channel {correlation[0] + 1} - Channel {correlation[1] + 1}; G(0) = {{:.6f}}".format(gt_values[0])
        )
        gt_widget.plotItem.layout.setContentsMargins(10, 10, 10, 10)
        fcs_plot = gt_widget.plot(
            log_values, gt_values, pen=pg.mkPen(color="#31c914", width=2)
        )
        gt_widget.plotItem.getAxis("left").enableAutoSIPrefix(False)
        gt_widget.plotItem.getAxis("bottom").enableAutoSIPrefix(False)
        def format_power_of_ten(i):
            if i < 0:
                return "0"
            else:
                return "10" + "".join([UNICODE_SUP[c] for c in str(i)])
        ticks = [(i, format_power_of_ten(i)) for i in exponents_lin_space_int]
        axis = gt_widget.getAxis("bottom")
        axis.setTicks([ticks])
        gt_widget.setBackground("#141414")
        app.gt_lines.append(fcs_plot)
        row, col = divmod(index, 2)
        app.layouts[GT_PLOTS_GRID].addWidget(gt_widget, row, col)
