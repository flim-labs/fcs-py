use std::fs;
use std::path::PathBuf;

pub fn get_flim_root() -> String {
    let user_firmwares_root = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    let flim_labs_folder = user_firmwares_root.join(".flim-labs");
    if !flim_labs_folder.exists() {
        fs::create_dir_all(&flim_labs_folder).unwrap();
    }
    return flim_labs_folder.to_str().unwrap().to_string();
}

pub fn get_flim_sub_folder(sub_folder: &str) -> String {
    let flim_root = get_flim_root();
    let sub_folder_path = std::path::Path::new(&flim_root).join(sub_folder);
    if !sub_folder_path.exists() {
        fs::create_dir_all(&sub_folder_path).unwrap();
    }
    return sub_folder_path.to_str().unwrap().to_string();
}

pub fn create_flim_file(prefix_file: &str, extension: &str) -> String {
    let date = chrono::Local::now().format("%Y-%m-%d_%H-%M-%S");
    let bin_name = format!("{}_{}.{}", prefix_file, date, extension);
    return bin_name.to_string();
}