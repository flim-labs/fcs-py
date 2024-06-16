use crate::utils::{ get_flim_sub_folder, create_flim_file };
use crate::models::{ FcsCalculationData };
use std::fs::{ File };
use std::io::{ self, Write };
use std::path::{ PathBuf };
use serde_json::json;
use serde_derive::Serialize;
use byteorder::{ LittleEndian, WriteBytesExt };
use rand::prelude::*;
use uuid::Uuid;

pub fn fcs_export_data(
    correlations: Vec<(usize, usize)>,
    num_acquisitions: usize,
    enabled_channels: Vec<usize>,
    bin_width: u32,
    acquisition_time: u32,
    notes: String,
    lag_index: Vec<i64>,
    g2_correlations: Vec<((usize, usize), Vec<Vec<f64>>)>
) -> Result<(), io::Error> {
    static HEADER_FCS: [u8; 4] = *b"FCS1";
    let flim_data_folder = PathBuf::from(get_flim_sub_folder("data"));
    let file_name = create_flim_file("fcs", "bin");
    let metadata =
        json!({
        "correlations": correlations,
        "num_acquisitions": num_acquisitions,
        "enabled_channels": enabled_channels,
        "bin_width": bin_width,
        "acquisition_time": acquisition_time,
        "notes": notes,
    });
    let metadata_json_string = serde_json::to_string(&metadata)?;
    let metadata_json_length = metadata_json_string.len();
    let g2_correlations_json =
        json!({
        "lag_index": lag_index,
        "g2_correlations": g2_correlations,
    });
    let g2_correlations_json_string = serde_json::to_string(&g2_correlations_json)?;
    let g2_correlations_json_length = g2_correlations_json_string.len();
    let mut file = File::create(flim_data_folder.join(&file_name))?;
    file.write_all(&HEADER_FCS)?;
    file.write_u32::<LittleEndian>(metadata_json_length as u32)?;
    file.write_all(metadata_json_string.as_bytes())?;
    file.write_u32::<LittleEndian>(g2_correlations_json_length as u32)?;
    file.write_all(g2_correlations_json_string.as_bytes())?;

    Ok(())
}

pub fn serialize_fcs_calculation(
    intensities_length: u64,
    correlations: Vec<(usize, usize)>,
    num_acquisitions: usize,
    enabled_channels: Vec<usize>,
    bin_width: u32,
    acquisition_time: u32,
    notes: String,
    export_data: bool,
    lag_index: Vec<i64>,
    g2_correlations: Vec<((usize, usize), Vec<Vec<f64>>)>
) -> Result<(), io::Error> {
    let flim_data_folder = PathBuf::from(get_flim_sub_folder("data"));
    let mut rng = rand::thread_rng();
    let uuid = Uuid::from_u128(rng.gen::<u128>());
    let uuid_string = uuid.to_string();
    let filename = format!("fcs_calc_{}", &uuid_string);
    let file_name = create_flim_file(&filename, "json");
    let file_path = flim_data_folder.join(file_name);

    let fcs_data = FcsCalculationData {
        intensities_length,
        correlations,
        num_acquisitions,
        enabled_channels,
        bin_width,
        acquisition_time,
        notes,
        export_data,
        lag_index,
        g2_correlations,
        
    };

    let json_data = serde_json::to_string(&fcs_data)?;
    let mut file = File::create(&file_path)?;
    file.write_all(json_data.as_bytes())?;

    Ok(())
}
