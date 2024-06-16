use std::io::{self, BufReader, Read};
use std::path::{PathBuf};
use std::error::Error;
use std::collections::{HashMap, VecDeque};
use serde_json::Value;
use serde_json::json;
use std::fs::{self, File};
use crate::models::{ FcsCalculationData, FcsSerializedCalculationData};



/*

pub fn get_gt_serialized_calculation_files(num_acquisitions: usize) -> Result<FcsSerializedCalculationData, Box<dyn Error>> {
    let user_profile_path = get_user_profile_path()?;
    let data_folder_path = user_profile_path.join(".flim-labs/data");
    let files = read_data_folder(data_folder_path)?;
    let fcs_calc_files: Vec<PathBuf> = files
        .iter()
        .filter(|file| {
            if let Some(file_name) = file.file_name() {
                if let Some(name) = file_name.to_str() {
                    return name.starts_with("fcs_calc");
                }
            }
            false
        })
        .cloned()
        .collect();

    let sorted_files = sort_files_by_modified_time(&fcs_calc_files);
    let parsed_data = get_gt_serializes_calculation_data(&num_acquisitions, sorted_files);

}


 fn get_gt_serializes_calculation_data(num_acquisitions: &usize, files: Vec<PathBuf>) -> Result<FcsSerializedCalculationData, Box<dyn Error>> {
    let shared_data =  read_json_file(files[0])?;
    let acquisitions_number = num_acquisitions.clone();
    let export_data = shared_data.export_data;
    let correlations =  shared_data.correlations;
    let enabled_channels = shared_data.enabled_channels;
    let bin_width = shared_data.bin_width;
    let acquisition_time = shared_data.acquisition_time;
    let notes = shared_data.notes;
    let mut lags_vectors: Vec<Vec<i64>> = Vec::with_capacity(*num_acquisitions);
    let intensities_lengths = Vec<u64> = Vec::with_capacity(*num_acquisitions);
    for file in files.iter().take(num_acquisitions) {
        let data = read_json_file(file)?;
        lags_vectors.push(*data.lag_index);
        intensities_lengths.push(*data.intensities_length);
        
    }
    let min_intensity_length = *intensities_lengths.iter().min().unwrap();

}


fn read_json_file(file_path: &PathBuf) -> Result<FcsCalculationData, Box<dyn Error>> {
    let mut file = File::open(file_path)?;
    let mut json_string = String::new();
    file.read_to_string(&mut json_string)?;
    let data: FcsCalculationData = serde_json::from_str(&json_string)?;
    Ok(data)
}


*/


pub fn get_intensity_tracing_bin_file() -> Result<(HashMap<u8, Vec<Vec<usize>>>, u64), Box<dyn Error>> {
    let user_profile_path = get_user_profile_path()?;

    let mut channel_data = HashMap::new();
    let data_folder_path = user_profile_path.join(".flim-labs/data");
    let files = read_data_folder(data_folder_path)?;
    let intensity_tracing_files: Vec<PathBuf> = files
        .iter()
        .filter(|file| {
            if let Some(file_name) = file.file_name() {
                if let Some(name) = file_name.to_str() {
                    return name.starts_with("intensity-tracing");
                }
            }
            false
        })
        .cloned()
        .collect();

    let sorted_files = sort_files_by_modified_time(&intensity_tracing_files);

    if let Some(last_file) = sorted_files.first() {
        process_bin_file(last_file, &mut channel_data)?;
        if let Err(err) = delete_file(last_file) {
            eprintln!("Error during intensity tracing bin file removal: {}", err);
        }
    }

    let max_length = calculate_first_vector_length(&channel_data);
    let length = max_length.unwrap_or(0);
    Ok((channel_data, length))
}

fn process_bin_file(
    file_path: &PathBuf,
    channel_data: &mut HashMap<u8, Vec<Vec<usize>>>
) -> Result<(), Box<dyn Error>> {
    let mut reader = BufReader::new(File::open(file_path)?);
    let metadata = read_bin_metadata(&mut reader)?;
    let channel_lines = read_channels_data(&mut reader, metadata.clone())?;
    let data_to_insert = prepare_data_to_insert(metadata, channel_lines)?;
    insert_data_into_channel_data(channel_data, data_to_insert)?;
    Ok(())
}

fn read_bin_metadata(reader: &mut BufReader<File>) -> Result<Value, Box<dyn Error>> {
    let mut magic = [0u8; 4];
    reader.read_exact(&mut magic)?;
    if magic.as_ref() != b"IT02" {
        println!("Invalid data file");
        return Ok(json!({}));
    }
    let mut json_length_bytes = [0u8; 4];
    reader.read_exact(&mut json_length_bytes)?;
    let json_length = u32::from_le_bytes(json_length_bytes) as usize;

    let mut metadata_bytes = vec![0u8; json_length];
    reader.read_exact(&mut metadata_bytes)?;
    Ok(serde_json::from_slice(&metadata_bytes)?)
}

fn read_channels_data(
    reader: &mut BufReader<File>,
    metadata: Value
) -> Result<Vec<Vec<usize>>, Box<dyn Error>> {
    let number_of_channels = metadata
        .get("channels")
        .and_then(Value::as_array)
        .map_or(0, |channels| channels.len());

    let mut channel_lines: Vec<_> = (0..number_of_channels).map(|_| Vec::new()).collect();
    let mut buffer = vec![0u8; 8 + 4 * number_of_channels];
    while reader.read_exact(&mut buffer).is_ok() {
        let channel_values: Vec<u32> = buffer[8..]
            .chunks_exact(4)
            .map(|bytes| u32::from_le_bytes(bytes.try_into().unwrap()))
            .collect();

        for (i, value) in channel_values.into_iter().enumerate() {
            channel_lines[i].push(value as usize);
        }
    }

    Ok(channel_lines)
}

fn prepare_data_to_insert(
    metadata: Value,
    channel_lines: Vec<Vec<usize>>
) -> Result<HashMap<u8, VecDeque<Vec<usize>>>, Box<dyn Error>> {
    let mut data_to_insert: HashMap<u8, VecDeque<Vec<usize>>> = HashMap::new();
    if let Some(channels) = metadata.get("channels").and_then(Value::as_array) {
        let enabled_channels: Vec<u8> = channels
            .iter()
            .filter_map(|ch| ch.as_u64().map(|ch| ch as u8))
            .collect();

        for (i, channel_line) in channel_lines.into_iter().enumerate() {
            if let Some(enabled_channel) = enabled_channels.get(i).cloned() {
                data_to_insert
                    .entry(enabled_channel)
                    .or_insert_with(VecDeque::new)
                    .push_back(channel_line);
            }
        }
    }
    Ok(data_to_insert)
}

fn insert_data_into_channel_data(
    channel_data: &mut HashMap<u8, Vec<Vec<usize>>>,
    data_to_insert: HashMap<u8, VecDeque<Vec<usize>>>
) -> Result<(), Box<dyn Error>> {
    for (enabled_channel, data) in data_to_insert {
        channel_data.entry(enabled_channel).or_insert_with(Vec::new).extend(data);
    }
    Ok(())
}

fn get_user_profile_path() -> Result<PathBuf, io::Error> {
    dirs::home_dir().ok_or(
        io::Error::new(io::ErrorKind::NotFound, "User profile directory not found")
    )
}

fn read_data_folder(data_folder_path: PathBuf) -> Result<Vec<PathBuf>, io::Error> {
    let mut files = Vec::new();

    for entry in fs::read_dir(data_folder_path)? {
        let entry = entry?;
        files.push(entry.path());
    }

    Ok(files)
}

fn sort_files_by_modified_time(files: &Vec<PathBuf>) -> Vec<PathBuf> {
    let mut sorted_files = files.clone();
    sorted_files.sort_by(|a, b|
        b.metadata().unwrap().modified().unwrap().cmp(&a.metadata().unwrap().modified().unwrap())
    );
    sorted_files
}

fn calculate_first_vector_length(channel_data: &HashMap<u8, Vec<Vec<usize>>>) -> Option<u64> {
    if let Some((_key, vectors)) = channel_data.iter().next() {
        if let Some(first_vector) = vectors.first() {
            return Some(first_vector.len() as u64);
        }
    }
    None
}

fn delete_file(file_path: &PathBuf) -> Result<(), Box<dyn Error>> {
    fs::remove_file(file_path)?;
    Ok(())
}