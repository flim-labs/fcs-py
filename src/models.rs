use serde_derive::{Serialize, Deserialize};


#[derive(Debug, Serialize, Deserialize)]
pub struct FcsCalculationData {
    pub intensities_length: u64,
    pub correlations: Vec<(usize, usize)>,
    pub num_acquisitions: usize,
    pub enabled_channels: Vec<usize>,
    pub bin_width: u32,
    pub acquisition_time: u32,
    pub notes: String,
    pub export_data: bool,
    pub lag_index: Vec<i64>,
    pub g2_correlations: Vec<((usize, usize), Vec<Vec<f64>>)>,
}


#[derive(Debug)]
pub struct FcsAverageCalculationInput {
    pub export_data: bool,
    pub num_acquisitions: usize,
    pub correlations: Vec<(usize, usize)>,
    pub enabled_channels: Vec<usize>,
    pub bin_width: u32,
    pub acquisition_time: u32,
    pub lag_index: Vec<i64>,
    pub notes: String,
    pub intensities_length: u64,
    pub g2_correlations: Vec<((usize, usize), Vec<Vec<f64>>)>,
}