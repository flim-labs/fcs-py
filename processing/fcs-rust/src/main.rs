extern crate rand;
use rand::*;

mod fcs_post_processing;
use fcs_post_processing::{PostProcessingFCSInput, IntensityData, fluorescence_correlation_spectroscopy};

fn main() {
    // test with random data
    let input_data = PostProcessingFCSInput {
        correlations: vec![(0, 1), (1, 1), (0, 8), (8, 0)],
        bin_width_us: 100,
        taus_number: 100,
        acquisition_time_us: 400000,
        intensities: vec![
            IntensityData{index: 0, data: (0..400000).map(|_| rand::random::<usize>() % 101).collect()},
            IntensityData{index: 1, data: (0..400000).map(|_| rand::random::<usize>() % 101).collect()},
            IntensityData{index: 8, data: (0..400000).map(|_| rand::random::<usize>() % 101).collect()}
        ]
    };
    let results = fluorescence_correlation_spectroscopy(input_data);
    for gt in &results {
        println!("{}", gt);
    }
}