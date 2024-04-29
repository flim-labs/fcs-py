from components.layout_utilities import create_gt_layout, insert_widget, remove_widget
from components.settings import GT_PLOTS_GRID, GT_WIDGET_WRAPPER, PLOT_GRIDS_CONTAINER
import numpy as np
import pyqtgraph as pg
from fcs_flim import fcs_flim
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication


class FCSPostProcessingWorker(QThread):
    finished = pyqtSignal(object)

    def __init__(self, active_correlations, num_acquisitions):
        super().__init__()
        self.active_correlations = active_correlations
        self.num_acquisitions = num_acquisitions
        self.is_running = True

    def run(self):
        gt_results = fcs_flim.fluorescence_correlation_spectroscopy(
            num_acquisitions=self.num_acquisitions,
            correlations=self.active_correlations,
        )  
        self.finished.emit(gt_results)    

    def stop(self):
        self.is_running = False


class FCSPostProcessing:
    @staticmethod
    def get_input(app):
        free_running_mode = app.free_running_acquisition_time
        correlations = [tuple(item) if isinstance(item, list) else item for item in app.ch_correlations]
        active_correlations = [(ch1, ch2) for ch1, ch2, active in correlations if active]
        num_acquisitions = app.selected_average if free_running_mode == False else 1
        worker = FCSPostProcessingWorker(active_correlations, num_acquisitions)
        QApplication.processEvents()
        worker.finished.connect(lambda result: FCSPostProcessing.handle_fcs_post_processing_result(app, result, worker))
        worker.start()
        

    @staticmethod
    def handle_fcs_post_processing_result(app, gt_results, worker):
        worker.stop()
        remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER])
        gt_widget = create_gt_layout(app)
        insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)
        gt_plot_to_show = [tuple(item) if isinstance(item, list) else item for item in app.gt_plots_to_show]
        lag_index = gt_results[0]
        filtered_gt_results = [res for res in gt_results[1] if res[0] in gt_plot_to_show]
        for index, res in enumerate(filtered_gt_results):
            correlation = res[0]
            gt_values = res[1]
            FCSPostProcessingPlot.generate_chart(correlation, index, app, lag_index, gt_values)
        
        

class FCSPostProcessingPlot:
    @staticmethod
    def generate_chart(correlation, index, app, lag_index, gt_values):
        lag_index[0] = lag_index[0] + 0.000000001
        gt_widget = pg.PlotWidget()
        gt_widget.setLabel('left', 'G(τ)', units='')
        gt_widget.setLabel('bottom', 'τ', units='')
        gt_widget.setTitle(f'Channel {correlation[0] + 1} - Channel {correlation[1] + 1}')
        gt_widget.plotItem.setRange(yRange=[min(gt_values), max(gt_values)])
        gt_widget.plotItem.setRange(xRange=[min(lag_index), max(lag_index)])
        gt_widget.plotItem.layout.setContentsMargins(10, 10, 10, 10) 
        y_range = max(gt_values) - min(gt_values)
        y_num_ticks = 5 
        y_step = y_range / (y_num_ticks - 1)
        y_tick_values = np.arange(min(gt_values), max(gt_values) + y_step, y_step)
        gt_widget.plotItem.getAxis('left').setTicks([[(tick, f'{tick:.5f}') for tick in y_tick_values]])
        intensity_plot = gt_widget.plot(lag_index, gt_values, pen='#31c914')
        gt_widget.plotItem.getAxis('left').enableAutoSIPrefix(False)
        gt_widget.setBackground("#141414")
        app.gt_lines.append(intensity_plot)
        row, col = divmod(index, 2)
        app.layouts[GT_PLOTS_GRID].addWidget(gt_widget, row, col)
