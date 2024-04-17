
use std::fmt;


#[derive(Clone, Debug)] 
pub struct IntensityData {
    pub index: usize,
    pub data: Vec<usize>,
}

#[derive(Clone, Debug)] 
pub struct PostProcessingFCSInput {
    pub correlations: Vec<(usize, usize)>,
    pub bin_width_us: usize,
    pub taus_number: usize,
    pub acquisition_time_us: usize,
    pub intensities: Vec<IntensityData>,
}

impl From<Vec<(usize, Vec<usize>)>> for PostProcessingFCSInput {
    fn from(intensities: Vec<(usize, Vec<usize>)>) -> Self {
        let mut intensity_data = Vec::new();
        for (index, data) in intensities {
            intensity_data.push(IntensityData { index, data });
        }
        Self {
            correlations: Vec::new(),
            bin_width_us: 0,
            taus_number: 0,
            acquisition_time_us: 0,
            intensities: intensity_data,
        }
    }
}

#[derive(Clone, Debug)] 
pub struct GtCorrelationResult {
    pub correlation: (usize, usize),
    pub g2_values: Vec<f64>,
    pub lag_index: Vec<usize>,
}

impl GtCorrelationResult {
    fn new(correlation: (usize, usize), g2_values: Vec<f64>, lag_index: Vec<usize>) -> Self {
        GtCorrelationResult { correlation, g2_values, lag_index }
    }
}

impl fmt::Display for GtCorrelationResult {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        writeln!(f, "Channels: {:?}", self.correlation)?;
        writeln!(f, "G(t):")?;
        for (i, g2) in self.g2_values.iter().enumerate() {
            writeln!(f, "  {}: {}", self.lag_index[i], g2)?;
        }
        Ok(())
    }
}

pub fn fluorescence_correlation_spectroscopy(
    input_data: PostProcessingFCSInput,
) -> Vec<GtCorrelationResult> {
    let PostProcessingFCSInput { correlations, bin_width_us, taus_number, acquisition_time_us, intensities } = input_data;

    let mut results = Vec::new();
    for correlation in correlations {
        let (intensity1_index, intensity2_index) = correlation;
        let intensity1_data = intensities.iter().find(|&intensity| intensity.index == intensity1_index).unwrap();
        let intensity2_data = intensities.iter().find(|&intensity| intensity.index == intensity2_index).unwrap();
        let tau: Vec<f64> = (0..taus_number).map(|i| (i as f64) * (acquisition_time_us as f64) / (taus_number as f64)).collect();
        let tau_int: Vec<f64> = tau.iter().map(|&t| ((t / (bin_width_us as f64)).floor()) * (bin_width_us as f64)).collect();
        let (g2_values, lag_index) = calculate_correlation(&intensity1_data.data, &intensity2_data.data, &tau_int);
        results.push(GtCorrelationResult::new(correlation, g2_values, lag_index));
    }
    results
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