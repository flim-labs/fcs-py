use crate::file_processing::{ get_intensity_tracing_bin_file, get_gt_serialized_calculation_files };
use crate::export_data::{ fcs_export_data, serialize_fcs_calculation };
use crate::models::{ FcsAverageCalculationInput };
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

#[pyclass]
#[derive(Clone)]
pub struct PostProcessingFCSOutput {
    #[pyo3(get)]
    pub export_data: bool,
    #[pyo3(get)]
    pub num_acquisitions: usize,
    #[pyo3(get)]
    pub correlations: Vec<(usize, usize)>,
    #[pyo3(get)]
    pub enabled_channels: Vec<usize>,
    #[pyo3(get)]
    pub bin_width: u32,
    #[pyo3(get)]
    pub acquisition_time: u32,
    #[pyo3(get)]
    pub lag_index: Vec<i64>,
    #[pyo3(get)]
    pub notes: String,
    #[pyo3(get)]
    pub intensities_length: u64,
    #[pyo3(get)]
    pub g2_correlations: Vec<((usize, usize), Vec<Vec<f64>>)>,
}

#[pymethods]
impl PostProcessingFCSOutput {
    #[new]
    pub fn new(
        export_data: bool,
        num_acquisitions: usize,
        correlations: Vec<(usize, usize)>,
        enabled_channels: Vec<usize>,
        bin_width: u32,
        acquisition_time: u32,
        lag_index: Vec<i64>,
        notes: String,
        intensities_length: u64,
        g2_correlations: Vec<((usize, usize), Vec<Vec<f64>>)>,
    ) -> Self {
        PostProcessingFCSOutput {
            export_data,
            num_acquisitions,
            correlations,
            enabled_channels,
            bin_width,
            acquisition_time,
            lag_index,
            notes,
            intensities_length,
            g2_correlations,
        }
    }
}

impl From<FcsAverageCalculationInput> for PostProcessingFCSOutput {
    fn from(input: FcsAverageCalculationInput) -> Self {
        PostProcessingFCSOutput {
            export_data: input.export_data,
            num_acquisitions: input.num_acquisitions,
            correlations: input.correlations,
            enabled_channels: input.enabled_channels,
            bin_width: input.bin_width,
            acquisition_time: input.acquisition_time,
            lag_index: input.lag_index,
            notes: input.notes,
            intensities_length: input.intensities_length,
            g2_correlations: input.g2_correlations,
        }
    }
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
    enabled_channels: Vec<usize>,
    bin_width: u32,
    acquisition_time: u32,
    export_data: bool,
    notes: &str,
    py: Python
) -> PyResult<()> {
    let _gt_correlations = py.allow_threads(move ||
        fluorescence_correlation_spectroscopy_calc(
            correlations,
            num_acquisitions,
            enabled_channels,
            bin_width,
            acquisition_time,
            export_data,
            notes
        )
    );
    Ok(())
}

#[pyfunction]
pub fn average_fluorescence_correlation_spectroscopy(
    num_acquisitions: usize,
    py: Python
) -> PyResult<PostProcessingFCSOutput> {
    let result = py.allow_threads(move || {
        fluorescence_average_correlation_spectroscopy_calc(num_acquisitions)
    })?;
    
    Ok(PostProcessingFCSOutput::from(result))
}

fn fluorescence_average_correlation_spectroscopy_calc(
    num_acquisitions: usize
) -> PyResult<FcsAverageCalculationInput> {
    let calc_input = match get_gt_serialized_calculation_files(num_acquisitions) {
        Ok(result) => result,
        Err(err) => {
            return Err(
                pyo3::exceptions::PyValueError::new_err(
                    format!("Error retrieving FCS calculations data: {}", err)
                )
            );
        }
    };
    let g2_correlations_with_averages: Vec<((usize, usize), Vec<Vec<f64>>)> = calc_input.g2_correlations
        .into_iter()
        .map(|(channels, repetitions)| {
            let (average, mut updated_repetitions) = calculate_average_correlation(repetitions);
            updated_repetitions.insert(0, average);
            (channels, updated_repetitions)
        })
        .collect();
    if calc_input.export_data {
        let lag_index_clone = calc_input.lag_index.clone();
        let notes_clone = calc_input.notes.clone();
        let correlations_clone = calc_input.correlations.clone();
        let enabled_channels_clone = calc_input.enabled_channels.clone();
        let g2_correlations_clone = g2_correlations_with_averages.clone(); 

        rayon::spawn(move || {
            if let Err(err) = fcs_export_data(
                correlations_clone,
                calc_input.num_acquisitions,
                enabled_channels_clone,
                calc_input.bin_width,
                calc_input.acquisition_time,
                notes_clone,
                lag_index_clone,
                g2_correlations_clone
            ) {
                println!("Error exporting data {:?}", err);
            }
        });
    }
    let output_with_average = FcsAverageCalculationInput {
        export_data: calc_input.export_data,
        num_acquisitions: calc_input.num_acquisitions,
        correlations: calc_input.correlations,
        enabled_channels: calc_input.enabled_channels,
        bin_width: calc_input.bin_width,
        acquisition_time: calc_input.acquisition_time,
        lag_index: calc_input.lag_index,
        notes: calc_input.notes,
        intensities_length: calc_input.intensities_length,
        g2_correlations: g2_correlations_with_averages,
    };
    Ok(output_with_average)
}

fn fluorescence_correlation_spectroscopy_calc(
    correlations: Vec<(usize, usize)>,
    num_acquisitions: usize,
    enabled_channels: Vec<usize>,
    bin_width: u32,
    acquisition_time: u32,
    export_data: bool,
    notes: &str
) -> PyResult<()> {
    let bin_width_clone = bin_width.clone();
    let acquisition_time_clone = acquisition_time.clone();
    let intensities_data = get_intensity_tracing_bin_file(bin_width_clone, acquisition_time_clone);
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
    let lag_index = calculate_lag_index(&intensity_data_length);
    let g2_correlations: Arc<Mutex<Vec<_>>> = Arc::new(Mutex::new(Vec::new()));

    correlations.par_iter().for_each(|(channel1, channel2)| {
        let total_channels_couple_correlations: Arc<Mutex<Vec<Vec<f64>>>> = Arc::new(
            Mutex::new(Vec::new())
        );
        let data_channel_1 = intensities.get(&(*channel1 as u8)).unwrap();
        let data_channel_2 = intensities.get(&(*channel2 as u8)).unwrap();
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
        let mut g2_correlations = g2_correlations.lock().unwrap();
        g2_correlations.push(((*channel1, *channel2), total_channels_couple_correlations));
    });
    let g2_correlations_unwrapped = g2_correlations.lock().unwrap().clone();
    let lag_index_clone = lag_index.clone();
    let notes_clone = notes.to_string();
    let intensities_length = intensity_data_length.clone();
    let g2_correlations_for_serialization = g2_correlations_unwrapped.clone();
    rayon::spawn(move || (
        if
            let Err(err) = serialize_fcs_calculation(
                intensities_length,
                correlations,
                num_acquisitions,
                enabled_channels,
                bin_width,
                acquisition_time,
                notes_clone,
                export_data,
                lag_index_clone,
                g2_correlations_for_serialization
            )
        {
            println!("Error saving fcs json calculation {:?}", err);
        }
    ));
    Ok(())
}

fn calculate_average_correlation(repetitions: Vec<Vec<f64>>) -> (Vec<f64>, Vec<Vec<f64>>) {
    let repetitions_res = repetitions;
    let repetitions_num = repetitions_res.len();
    let g2_values_num = repetitions_res[0].len();
    let mut averages = vec![0.0; g2_values_num];
    for i in 0..repetitions_num {
        for j in 0..g2_values_num {
            averages[j] += repetitions_res[i][j];
        }
    }
    for average in &mut averages {
        *average /= repetitions_num as f64;
    }

    (averages, repetitions_res)
}

fn calculate_lag_index(data_length: &u64) -> Vec<i64> {
    let max_tau = (data_length - 1) as i64;
    let scale_factor = (max_tau as f64) / (3.0f64).powf(8.0 - 2.0);
    let mut lag_index: Vec<i64> = Vec::new();
    let mut exponent = 2.0;
    while exponent < 8.0 {
        let result = (scale_factor * (3.0f64).powf(exponent)).round() as i64;
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
    lag_index: &[i64]
) -> Vec<f64> {
    let mut g2_values = vec![0.0; lag_index.len()];
    let epsilon = 1e-10;
    let mean_intensity1: f64 =
        (intensity1.iter().sum::<usize>() as f64) / (intensity1.len() as f64);
    let mean_intensity2: f64 =
        (intensity2.iter().sum::<usize>() as f64) / (intensity2.len() as f64);

    for (i, &tau) in lag_index.iter().enumerate() {
        let mean1 = if mean_intensity1 == 0.0 { epsilon } else { mean_intensity1 };
        let mean2 = if mean_intensity2 == 0.0 { epsilon } else { mean_intensity2 };
        if tau == 0 {
            let correlation_sum: f64 = intensity1
                .iter()
                .zip(intensity2)
                .map(|(&x1, &x2)| ((x1 as f64) - mean1) * ((x2 as f64) - mean2))
                .sum();
            g2_values[i] = correlation_sum / (mean1 * mean2 * (intensity2.len() as f64));
        } else if tau < (intensity2.len() as i64) {
            let correlation_sum: f64 = intensity1
                .iter()
                .take(intensity1.len() - (tau as usize))
                .zip(&intensity2[tau as usize..])
                .map(|(&x1, &x2)| ((x1 as f64) - mean1) * ((x2 as f64) - mean2))
                .sum();
            g2_values[i] =
                correlation_sum / (mean1 * mean2 * ((intensity2.len() - (tau as usize)) as f64));
        }
    }
    g2_values
}
