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


pub struct FcsSerializedCalculationData {
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
