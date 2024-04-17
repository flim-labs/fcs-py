class FCSPostProcessing:
    
    @staticmethod
    def get_input(app):
        intensities_data = app.intensities_data_processor.get_processed_data() 
        correlations = [tuple(item) if isinstance(item, list) else item for item in app.ch_correlations]
        active_correlations = [(ch1, ch2) for ch1, ch2, active in correlations if active]
        bin_width_us = int(app.bin_width_micros)
        taus_number = int(app.selected_tau)
        acquisition_time_us = int(app.last_acquisition_ns / 1000) if app.free_running_acquisition_time else int(app.acquisition_time_millis * 1000)
        input = {
            "intensities": intensities_data, 
            "correlations": active_correlations, 
            "bin_width_us" : bin_width_us, 
            "taus_number": taus_number, 
            "acquisition_time_us": acquisition_time_us
            }
        FCSPostProcessing.start_fcs_post_processing(app, input)    
            
    @staticmethod
    def start_fcs_post_processing(app, input):
        print(input)
                