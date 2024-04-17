use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple, PyDict};
use rand::Rng;

#[pyclass]
#[derive(Clone)]
pub struct IntensityData {
    #[pyo3(get)]
    pub index: usize,
    #[pyo3(get)]
    pub data: Vec<usize>,
}

#[pyclass]
#[derive(Clone)]
pub struct PostProcessingFCSInput {
    #[pyo3(get)]
    pub correlations: Vec<(usize, usize)>,
    #[pyo3(get)]
    pub bin_width_us: usize,
    #[pyo3(get)]
    pub taus_number: usize,
    #[pyo3(get)]
    pub acquisition_time_us: usize,
    #[pyo3(get)]
    pub intensities: Vec<IntensityData>,
}


#[pyclass]
pub struct GtCorrelationResult {
    #[pyo3(get)]
    pub correlation: (usize, usize),
    #[pyo3(get)]
    pub g2_values: Vec<f64>,
    #[pyo3(get)]
    pub lag_index: Vec<usize>,
}


impl ToPyObject for GtCorrelationResult {
    fn to_object(&self, py: Python) -> PyObject {
        let g2_values_obj = PyList::new_bound(py, self.g2_values.clone()).to_object(py);
        let lag_index_obj = PyList::new_bound(py, self.lag_index.clone()).to_object(py);
        let correlation_obj = PyTuple::new_bound(py, &[self.correlation.0, self.correlation.1]).to_object(py);
        let result_dict = PyDict::new_bound(py);
        result_dict.set_item("correlation", correlation_obj).unwrap();
        result_dict.set_item("g2_values", g2_values_obj).unwrap();
        result_dict.set_item("lag_index", lag_index_obj).unwrap();
        result_dict.to_object(py)
    }
}


#[pyfunction]
pub fn fluorescence_correlation_spectroscopy(
    _py: Python,
    input_data: PostProcessingFCSInput,
) -> PyResult<PyObject> {
    let PostProcessingFCSInput { correlations, bin_width_us, taus_number, acquisition_time_us, intensities } = input_data;
    
    let mut results = Vec::new();
    for correlation in correlations {
        let (intensity1_index, intensity2_index) = correlation;
        let intensity1_data = intensities.iter().find(|&intensity| intensity.index == intensity1_index).unwrap();
        let intensity2_data = intensities.iter().find(|&intensity| intensity.index == intensity2_index).unwrap();
        
        let tau: Vec<f64> = (0..taus_number).map(|i| (i as f64) * (acquisition_time_us as f64) / (taus_number as f64)).collect();
        let tau_int: Vec<f64> = tau.iter().map(|&t| ((t / (bin_width_us as f64)).floor()) * (bin_width_us as f64)).collect();
        
        let (g2_values, lag_index) = calculate_correlation(&intensity1_data.data, &intensity2_data.data, &tau_int);
        results.push(GtCorrelationResult { correlation, g2_values, lag_index });
    }
    Ok(PyList::new_bound(_py, results).to_object(_py))
}


fn calculate_correlation(intensity1: &[usize], intensity2: &[usize], tau: &[f64]) -> (Vec<f64>, Vec<usize>) {
    let mut g2_values = Vec::new();
    let mut lag_index = Vec::new();
    let mean_intensity1: f64 = intensity1.iter().map(|&x| x as f64).sum::<f64>() / (intensity1.len() as f64);
    let mean_intensity2: f64 = intensity2.iter().map(|&x| x as f64).sum::<f64>() / (intensity2.len() as f64);
    for &t in tau {
        let t_int = t as usize;
        let correlation_sum = if t_int == 0 {
            intensity1.iter().zip(intensity2.iter()).map(|(&x, &y)| (x as f64 - mean_intensity1) * (y as f64 - mean_intensity2)).sum::<f64>()
        } else {
            intensity1.iter().take(intensity1.len() - t_int).zip(intensity2.iter().skip(t_int)).map(|(&x, &y)| (x as f64 - mean_intensity1) * (y as f64 - mean_intensity2)).sum::<f64>()
        };
        let g2 = correlation_sum / (mean_intensity1 * mean_intensity2 * (intensity1.len() - t_int) as f64);
        g2_values.push(g2);
        lag_index.push(t_int);
    }
    (g2_values, lag_index)
}




