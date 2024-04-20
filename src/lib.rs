// File: src/lib.rs

mod fcs_post_processing;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use fcs_post_processing::{fluorescence_correlation_spectroscopy, 
    IntensityData, PostProcessingFCSInput, GtCorrelationResult};

#[pymodule]
#[pyo3(name = "fcs_flim")]
fn fcs_flim(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fluorescence_correlation_spectroscopy, m)?)?;
    m.add_class::<IntensityData>()?;
    m.add_class::<PostProcessingFCSInput>()?;
    m.add_class::<GtCorrelationResult>()?;
    Ok(())
}
