use crate::bin_processing::get_intensity_tracing_bin_files;
use pyo3::prelude::*;
use rayon::prelude::*;
use std::sync::{ Arc, Mutex };
use std::vec::Vec;

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
    num_acquisitions: usize,
    py: Python
) -> PyResult<(Vec<i32>, Vec<((usize, usize), Vec<f64>)>)> {
    let gt_correlations = py.allow_threads(move ||
        fluorescence_correlation_spectroscopy_calc(correlations, num_acquisitions)
    );
    Ok(gt_correlations?)
}

fn fluorescence_correlation_spectroscopy_calc(
    correlations: Vec<(usize, usize)>,
    num_acquisitions: usize
) -> PyResult<(Vec<i32>, Vec<((usize, usize), Vec<f64>)>)> {
    let intensities_data = get_intensity_tracing_bin_files(num_acquisitions);
    let (intensities, intensity_data_length) = match intensities_data {
        Ok(result) => result,
        Err(err) => {
            return Err(
                pyo3::exceptions::PyValueError::new_err(
                    format!("Error retrieving intensities data: {}", err)
                )
            );
        }
    };
    let lag_index = calculate_lag_index(intensity_data_length);
    let g2_correlations: Arc<Mutex<Vec<_>>> = Arc::new(Mutex::new(Vec::new()));

    correlations.par_iter().for_each(|(channel1, channel2)| {
        let total_channels_couple_correlations: Arc<Mutex<Vec<Vec<f64>>>> = Arc::new(
            Mutex::new(Vec::new())
        );
        let intensities_lock = intensities.read().unwrap();
        let data_channel_1 = intensities_lock.get(&(*channel1 as u8)).unwrap();
        let data_channel_2 = intensities_lock.get(&(*channel2 as u8)).unwrap();
        data_channel_1
            .par_iter()
            .enumerate()
            .for_each(|(index, data_repetition)| {
                let correlations = calculate_correlation(
                    data_repetition,
                    &data_channel_2[index],
                    &lag_index
                );
                let mut locked_correlations = total_channels_couple_correlations.lock().unwrap();
                locked_correlations.push(correlations);
            });
        let total_channels_couple_correlations = total_channels_couple_correlations.lock().unwrap();
        let total_channels_couple_correlations = total_channels_couple_correlations.to_owned();
        let correlations_average_vec = calculate_average_correlation(
            total_channels_couple_correlations
        );
        let mut g2_correlations = g2_correlations.lock().unwrap();
        g2_correlations.push(((*channel1, *channel2), correlations_average_vec));
    });
    let g2_correlations_unwrapped = g2_correlations.lock().unwrap().clone();
    println!("RESULT: {:?}", (&lag_index, &g2_correlations_unwrapped));
    Ok((lag_index, g2_correlations_unwrapped))
}

fn calculate_average_correlation(repetitions: Vec<Vec<f64>>) -> Vec<f64> {
    let repetitions_num = repetitions.len();
    let g2_values_num = repetitions[0].len();
    let mut averages = vec![0.0; g2_values_num];
    for i in 0..repetitions_num {
        for j in 0..g2_values_num {
            averages[j] += repetitions[i][j];
        }
    }
    for average in &mut averages {
        *average /= repetitions_num as f64;
    }

    averages
}

fn calculate_lag_index(data_length: usize) -> Vec<i32> {
    let max_tau = (data_length - 1) as i32;
    let scale_factor = (max_tau as f64) / (3.0f64).powf(8.0 - 2.0);
    let mut lag_index: Vec<i32> = Vec::new();
    let mut exponent = 2.0;
    while exponent < 8.0 {
        let result = (scale_factor * (3.0f64).powf(exponent)).round() as i32;
        lag_index.push(result);
        exponent += 0.05;
    }
    lag_index.sort();
    lag_index.dedup();
    if let Some(last_value) = lag_index.last().cloned() {
        if last_value > max_tau {
            lag_index.retain(|&x| x <= max_tau);
        }
    }
    if lag_index.is_empty() || lag_index[0] != 0 {
        lag_index.insert(0, 0);
    }

    lag_index
}

fn calculate_correlation(
    intensity1: &[usize],
    intensity2: &[usize],
    lag_index: &[i32]
) -> Vec<f64> {
    let mut g2_values = vec![0.0; lag_index.len()];
    let mean_intensity1: f64 =
        (intensity1.iter().sum::<usize>() as f64) / (intensity1.len() as f64);
    let mean_intensity2: f64 =
        (intensity2.iter().sum::<usize>() as f64) / (intensity2.len() as f64);

    for (i, &tau) in lag_index.iter().enumerate() {
        if tau == 0 {
            let correlation_sum: f64 = intensity1
                .iter()
                .zip(intensity2)
                .map(|(&x1, &x2)| ((x1 as f64) - mean_intensity1) * ((x2 as f64) - mean_intensity2))
                .sum();
            g2_values[i] =
                correlation_sum / (mean_intensity1 * mean_intensity2 * (intensity2.len() as f64));
        } else if tau < (intensity2.len() as i32) {
            let correlation_sum: f64 = intensity1
                .iter()
                .take(intensity1.len() - (tau as usize))
                .zip(&intensity2[tau as usize..])
                .map(|(&x1, &x2)| ((x1 as f64) - mean_intensity1) * ((x2 as f64) - mean_intensity2))
                .sum();
            g2_values[i] =
                correlation_sum /
                (mean_intensity1 * mean_intensity2 * ((intensity2.len() - (tau as usize)) as f64));
        }
    }
    g2_values
}
