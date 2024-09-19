import os
import re
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, '..'))

class FileUtils:
    @staticmethod
    def get_recent_n_intensity_tracing_files(num):
        data_folder = os.path.join(os.environ["USERPROFILE"], ".flim-labs", "data", "fcs-intensity")
        files = [f for f in os.listdir(data_folder) if f.startswith("intensity-tracing")]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(data_folder, x)), reverse=True)
        return [os.path.join(data_folder, f) for f in files[:num]]
    
    @staticmethod
    def get_recent_fcs_file():
        data_folder = os.path.join(os.environ["USERPROFILE"], ".flim-labs", "data")
        files = [
            f
            for f in os.listdir(data_folder)
            if f.startswith("fcs") and not ("calc" in f) and not ("intensity" in f)
        ]
        files.sort(
            key=lambda x: os.path.getmtime(os.path.join(data_folder, x)), reverse=True
        )
        return os.path.join(data_folder, files[0])
    
    @staticmethod
    def clean_filename(filename):
        # Keep only letters, numbers and underscores
        return re.sub(r'[^a-zA-Z0-9_]', '', filename)      
    