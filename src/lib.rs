// File: src/lib.rs
mod models;
mod file_processing;
mod fcs_post_processing;
mod export_data;
mod utils;
use pyo3::prelude::*;
use pyo3::Bound;
use pyo3::wrap_pyfunction;
use fcs_post_processing::{
    fluorescence_correlation_spectroscopy,
    average_fluorescence_correlation_spectroscopy,
    IntensityData,
    PostProcessingFCSInput,
    GtCorrelationResult,
};

#[pymodule]
#[pyo3(name = "fcs_flim")]
fn fcs_flim(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fluorescence_correlation_spectroscopy, m)?)?;
    m.add_function(wrap_pyfunction!(average_fluorescence_correlation_spectroscopy, m)?)?;
    m.add_class::<IntensityData>()?;
    m.add_class::<PostProcessingFCSInput>()?;
    m.add_class::<GtCorrelationResult>()?;
    Ok(())
}
