use pyo3::prelude::*;
use rayon::prelude::*;
use nalgebra::DVector;

#[pyclass]
#[derive(Clone)]
pub struct IntensityData {
    #[pyo3(get)]
    pub index: usize,
    #[pyo3(get)]
    pub data: Vec<usize>,
}

#[pymethods]
impl IntensityData {
    #[new]
    fn new(index: usize, data: Vec<usize>) -> Self {
        IntensityData { index, data }
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Correlation {
    #[pyo3(get)]
    intensity1_index: usize,
    #[pyo3(get)]
    intensity2_index: usize,
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
#[derive(Clone)]
pub struct GtCorrelationResult {
    #[pyo3(get)]
    lag_index: Vec<i32>,
    #[pyo3(get)]
    g2_correlations: Vec<(Correlation, Vec<f64>)>,
}

#[pymethods]
impl GtCorrelationResult {
    #[new]
    pub fn new(lag_index: Vec<i32>, g2_correlations: Vec<(Correlation, Vec<f64>)>) -> Self {
        GtCorrelationResult { lag_index, g2_correlations }
    }
}

#[pyfunction]
pub fn fluorescence_correlation_spectroscopy(
    correlations: Vec<(usize, usize)>,
    #[allow(unused_variables)]
    bin_width_us: usize,
    taus_number: usize,
    #[allow(unused_variables)]
    acquisition_time_us: usize,
    intensities: Vec<IntensityData>,
) -> PyResult<(Vec<i32>, Vec<((usize, usize), Vec<f64>)>)> {
    let lag_index = calculate_lag_index(taus_number);
    let g2_correlations: Vec<_> = correlations
        .par_iter()
        .filter_map(|&correlation| {
            let intensity1_index = correlation.0;
            let intensity2_index = correlation.1;
            let intensity1_data = intensities
                .iter()
                .find(|&intensity_data| intensity_data.index == intensity1_index)?;
            let intensity2_data = intensities
                .iter()
                .find(|&intensity_data| intensity_data.index == intensity2_index)?;
            let g2_values = calculate_correlation(&intensity1_data.data, &intensity2_data.data, &lag_index);
            Some(((intensity1_index, intensity2_index), g2_values))
        })
        .collect();

    Ok((lag_index, g2_correlations))
}

fn linspace(start: f64, end: f64, num_points: usize) -> DVector<f64> {
    let step = (end - start) / (num_points - 1) as f64;
    let mut result = DVector::zeros(num_points);
    for i in 0..num_points {
        result[i] = start + i as f64 * step;
    }
    result
}

fn calculate_lag_index(taus_number: usize) -> Vec<i32> {
    let mut steps = Vec::with_capacity(taus_number);
    let mut value = 2.0;
    let end = 8.0;
    let step_size = 0.05;
    while value < end {
        steps.push((3.0_f64).powf(value).round());
        value += step_size;
    }
    let tau_ind = linspace(steps[0], *steps.last().unwrap(), taus_number - 1);
    let mut lag_index: Vec<i32> = tau_ind.iter().map(|&x| x as i32).collect();
    lag_index.insert(0, 0);
    lag_index
}

fn calculate_correlation(intensity1: &[usize], intensity2: &[usize], lag_index: &[i32]) -> Vec<f64> {
    let mut g2_values = vec![0.0; lag_index.len()];
    let mean_intensity1: f64 = intensity1.iter().sum::<usize>() as f64 / intensity1.len() as f64;
    let mean_intensity2: f64 = intensity2.iter().sum::<usize>() as f64 / intensity2.len() as f64;

    for (i, &tau) in lag_index.iter().enumerate() {
        if tau == 0 {
            let correlation_sum: f64 = intensity1.iter().zip(intensity2).map(|(&x1, &x2)| (x1 as f64 - mean_intensity1) * (x2 as f64 - mean_intensity2)).sum();
            g2_values[i] = correlation_sum / (mean_intensity1 * mean_intensity2 * intensity2.len() as f64);
        } else if tau < intensity2.len() as i32 {
            let correlation_sum: f64 = intensity1.iter().take(intensity1.len() - tau as usize).zip(&intensity2[tau as usize..]).map(|(&x1, &x2)| (x1 as f64 - mean_intensity1) * (x2 as f64 - mean_intensity2)).sum();
            g2_values[i] = correlation_sum / (mean_intensity1 * mean_intensity2 * (intensity2.len() - tau as usize) as f64);
        }
    }
    g2_values
}

