use std::io::{ self, BufReader, Read };
use std::path::{ Path, PathBuf };
use std::error::Error;
use std::sync::{ Arc, RwLock };
use std::collections::{ HashMap, VecDeque };
use serde_json::Value;
use serde_json::json;
use std::fs::{self, File};
use rayon::prelude::*;

pub fn get_intensity_tracing_bin_files(
    num_files: usize
) -> Result<(Arc<RwLock<HashMap<u8, Vec<Vec<usize>>>>>, usize), Box<dyn Error>> {
    let user_profile_path = get_user_profile_path()?;

    let channel_data = Arc::new(RwLock::new(HashMap::new()));

    let data_folder_path = user_profile_path.join(".flim-labs/data");
    let files = read_data_folder(data_folder_path)?;
    let sorted_files = sort_files_by_modified_time(files);

    process_files_in_parallel(&channel_data, &sorted_files, num_files)?;

    if let Err(err) = delete_files(&sorted_files) {
        eprintln!("Error during intensity tracing bin files removal: {}", err);
    }

    let max_length = adjust_channel_data_lengths(&channel_data);

    Ok((channel_data, max_length))
}

fn process_bin_file(
    file_path: &Path,
    channel_data: &Arc<RwLock<HashMap<u8, Vec<Vec<usize>>>>>
) -> Result<(), Box<dyn Error>> {
    let mut reader = BufReader::new(File::open(file_path)?);
    let metadata = read_bin_metadata(&mut reader)?;
    let channel_lines = read_channels_data(&mut reader, metadata.clone())?; 
    let data_to_insert = prepare_data_to_insert(metadata, channel_lines)?;
    insert_data_into_channel_data(channel_data, data_to_insert)?;
    Ok(())
}

fn read_bin_metadata(reader: &mut BufReader<File>) -> Result<Arc<Value>, Box<dyn Error>> {
    let mut magic = [0u8; 4];
    reader.read_exact(&mut magic)?;
    if magic.as_ref() != b"IT02" {
        println!("Invalid data file");
        return Ok(Arc::new(json!({})));
    }
    let mut json_length_bytes = [0u8; 4];
    reader.read_exact(&mut json_length_bytes)?;
    let json_length = u32::from_le_bytes(json_length_bytes) as usize;

    let mut metadata_bytes = vec![0u8; json_length];
    reader.read_exact(&mut metadata_bytes)?;
    Ok(Arc::new(serde_json::from_slice(&metadata_bytes)?))
}

fn read_channels_data(
    reader: &mut BufReader<File>,
    metadata: Arc<Value>
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
    metadata: Arc<Value>,
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
    channel_data: &Arc<RwLock<HashMap<u8, Vec<Vec<usize>>>>>,
    data_to_insert: HashMap<u8, VecDeque<Vec<usize>>>
) -> Result<(), Box<dyn Error>> {
    let mut channel_data = channel_data.write().unwrap();
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
fn sort_files_by_modified_time(files: Vec<PathBuf>) -> Vec<PathBuf> {
    let mut sorted_files = files;
    sorted_files.sort_by(|a, b|
        b.metadata().unwrap().modified().unwrap().cmp(&a.metadata().unwrap().modified().unwrap())
    );
    sorted_files
}

fn process_files_in_parallel(
    channel_data: &Arc<RwLock<HashMap<u8, Vec<Vec<usize>>>>>,
    files: &Vec<PathBuf>,
    num_files: usize
) -> Result<(), Box<dyn Error>> {
    files
        .into_par_iter()
        .take(num_files)
        .for_each(|file_path| {
            if let Err(err) = process_bin_file(&file_path, channel_data) {
                eprintln!("Error processing file {:?}: {}", file_path, err);
            }
        });
    Ok(())
}

#[allow(unused_assignments)]
fn adjust_channel_data_lengths(channel_data: &Arc<RwLock<HashMap<u8, Vec<Vec<usize>>>>>) -> usize {
    let mut max_length = 0;
    {
        let mut data = channel_data.write().unwrap();
        max_length = calculate_intensities_vector_max_length(&data);
        for vectors in data.values_mut() {
            for vector in vectors.iter_mut() {
                vector.resize(max_length, 0);
            }
        }
    }
    max_length
}

fn calculate_intensities_vector_max_length(data: &HashMap<u8, Vec<Vec<usize>>>) -> usize {
    data.values()
        .flat_map(|v| v.iter())
        .map(Vec::len)
        .max()
        .unwrap_or(0)
}


fn delete_files(files:  &Vec<PathBuf>) -> Result<(), Box<dyn Error>> {
    files.par_iter().for_each(|file_path| {
        if let Err(err) = fs::remove_file(&file_path) {
            eprintln!("Error during intensity tracing bin files removal {}: {}", file_path.display(), err);
        }
    });
    Ok(())
}