from components.layout_utilities import create_gt_layout, insert_widget, remove_widget
from components.settings import GT_PLOTS_GRID, GT_WIDGET_WRAPPER, PLOT_GRIDS_CONTAINER
import numpy as np
import pyqtgraph as pg
import matplotlib.pyplot as plt
from fcs_flim import fcs_flim


class FCSPostProcessing:
    
    @staticmethod
    def get_input(app):
        acquisition_time_us = int(app.last_acquisition_ns / 1000) if app.free_running_acquisition_time else int(app.acquisition_time_millis * 1000)
        intensities_data = app.intensities_data_processor.get_processed_data()
        correlations = [tuple(item) if isinstance(item, list) else item for item in app.ch_correlations]
        active_correlations = [(ch1, ch2) for ch1, ch2, active in correlations if active]
        bin_width_us = int(app.bin_width_micros)
        intensities_input = [
            fcs_flim.IntensityData(
                index=d['index'],
                data=d['data']
            ) 
            for d in intensities_data
        ]
        FCSPostProcessing.start_fcs_post_processing(app, intensities_input, active_correlations, bin_width_us, acquisition_time_us)  
       
        
  
            
    @staticmethod
    def start_fcs_post_processing(app, intensities_input, active_correlations, bin_width_us, acquisition_time_us):
        gt_results = fcs_flim.fluorescence_correlation_spectroscopy(
            intensities = intensities_input,
            correlations = active_correlations,
            bin_width_us = bin_width_us,
            acquisition_time_us = acquisition_time_us
        )  
        remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER])
        gt_widget = create_gt_layout(app)
        insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)
        gt_plot_to_show = [tuple(item) if isinstance(item, list) else item for item in app.gt_plots_to_show]
        lag_index = gt_results[0]
        print(lag_index)
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
