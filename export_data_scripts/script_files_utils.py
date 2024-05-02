import os
import shutil

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from components.box_message import BoxMessage
from components.gui_styles import GUIStyles
from components.messages_utilities import MessagesUtilities

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, '..'))



class FileUtils:
    @classmethod
    def export_script_file(cls, file_extension, content_modifier, window):
        file_name, _ = QFileDialog.getSaveFileName(None, "Save File", "", f"All Files (*.{file_extension})")
        if not file_name:
            return
        try:
            bin_file_path = cls.get_recent_fcs_file()
            bin_file_name = os.path.join(os.path.dirname(file_name),
                                         f"{os.path.splitext(os.path.basename(file_name))[0]}.bin").replace('\\', '/')

            shutil.copy(bin_file_path, bin_file_name) if bin_file_path else None

            # write script file
            content = content_modifier['source_file']
            new_content = cls.manipulate_file_content(content, bin_file_name)
            cls.write_file(file_name, new_content)

            # write requirements file only for python export
            if len(content_modifier['requirements']) > 0:
                requirement_path, requirements_content = cls.create_requirements_file(file_name,
                                                                                      content_modifier['requirements'])
                cls.write_file(requirement_path, requirements_content)

            cls.show_success_message(file_name)
        except Exception as e:
            cls.show_error_message(str(e))

    @classmethod
    def write_file(cls, file_name, content):
        with open(file_name, 'w') as file:
            file.writelines(content)

    @classmethod
    def create_requirements_file(cls, script_file_name, requirements):
        directory = os.path.dirname(script_file_name)
        requirements_path = os.path.join(directory, 'requirements.txt')
        requirements_content = []

        for requirement in requirements:
            requirements_content.append(f"{requirement}\n")
        return [requirements_path, requirements_content]

    @classmethod
    def read_file_content(cls, file_path):
        with open(file_path, 'r') as file:
            return file.readlines()

    @classmethod
    def manipulate_file_content(cls, content, file_name):
        return content.replace("<FILE-PATH>", file_name.replace('\\', '/'))

    @classmethod
    def show_success_message(cls, file_name):
        info_title, info_msg = MessagesUtilities.info_handler("SavedScriptFile", file_name)
        BoxMessage.setup(
            info_title,
            info_msg,
            QMessageBox.Icon.Information,
            GUIStyles.set_msg_box_style(),
        )

    @classmethod
    def show_error_message(cls, error_message):
        error_title, error_msg = MessagesUtilities.error_handler("ErrorSavingScriptFile", error_message)
        BoxMessage.setup(
            error_title,
            error_msg,
            QMessageBox.Icon.Critical,
            GUIStyles.set_msg_box_style(),
        )

    @classmethod
    def get_recent_fcs_file(cls):
        data_folder = os.path.join(os.environ["USERPROFILE"], ".flim-labs", "data")
        files = [f for f in os.listdir(data_folder) if f.startswith("fcs")]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(data_folder, x)), reverse=True)
        return os.path.join(data_folder, files[0])
    
    
    


class PythonScriptUtils(FileUtils):
    @staticmethod
    def download_python(window):
        content_modifier = {
            'source_file': """import struct
from matplotlib.gridspec import GridSpec            
import matplotlib.pyplot as plt

file_path = "<FILE-PATH>"

# calc G(t) correlations mean
def calc_g2_correlations_mean(g2):
    g2_with_mean = []
    for corr in g2:
        g2_vector = corr[1]
        g2_vector_length = len(g2_vector)
        correlations_length = len(g2_vector[0])
        average = [0.0] * correlations_length  
        for i in range(g2_vector_length):
            for j in range(correlations_length):
                    average[j] += g2_vector[i][j]
            for k in range(correlations_length):        
                average[k] /= g2_vector_length 
            g2_with_mean.append((corr[0], average, g2_vector))        
    return g2_with_mean            

with open(file_path, "rb") as f:               
    # first 4 bytes must be FCS1
    # 'FCS1' is an identifier for fcs bin files
    if f.read(4) != b"FCS1":
        print("Invalid data file")
        exit(0)
        
    # read metadata from file    
    (json_length,) = struct.unpack("I", f.read(4))
    null = None
    metadata = eval(f.read(json_length).decode("utf-8"))
    
    # Read g2_correlations JSON length
    (g2_correlations_json_length,) = struct.unpack("I", f.read(4))
    g2_correlations_json_string = f.read(g2_correlations_json_length).decode("utf-8")
    g2_correlations_json = eval(g2_correlations_json_string)
    
    # Extract lag_index and g2_correlations from JSON
    lag_index = g2_correlations_json["lag_index"]
    g2_correlations = g2_correlations_json["g2_correlations"]
    
    # ENABLED CHANNELS
    if "enabled_channels" in metadata and metadata["enabled_channels"]:
        print( "Enabled channels: " + ( ", ".join( ["Channel " + str(ch + 1) for ch in metadata["enabled_channels"]])))
        
    # CORRELATIONS (info about correlated channels)    
    if "correlations" in metadata and metadata["correlations"] is not None:
        correlated_channels = [[channel + 1 for channel in pair] for pair in metadata["correlations"]]
        print("Channels correlations: " + str(correlated_channels))
    
    # NUMBER OF ACQUISITIONS
    if "num_acquisitions" in metadata and metadata["num_acquisitions"] is not None:
        print("Number of acquisitions: " + str(metadata["num_acquisitions"]))

    # ACQUISITION TIME (duration of the acquisition)            
    if "acquisition_time" in metadata and metadata["acquisition_time"] is not None:
        num_acquisition = (
            int(metadata["num_acquisition"])
            if "num_acquisition" in metadata and metadata["num_acquisition"] is not None
            else 1
        )
        print(
            "Acquisition time: "
            + "{:.2f}".format(
                round(metadata["acquisition_time"] / 1000 / num_acquisition, 2)
            )
            + "s"
        )

    # BIN WIDTH            
    if "bin_width" in metadata and metadata["bin_width"] is not None:
        print("Bin width: " + str(metadata["bin_width"]) + "us")

    # TAU            
    print("Tau (lag index):", lag_index)
    
    # NOTES
    if "notes" in metadata and metadata["notes"] is not None:
        print("Notes: " + str(metadata["notes"]))
                    
    # Plot G(t) correlations    
    num_plots = len(g2_correlations)
    num_plots_per_row = 1
    if num_plots < 2:
        num_plots_per_row = 1
    if num_plots > 1 and num_plots < 4:            
        num_plots_per_row = 2
    if num_plots >=4:            
        num_plots_per_row = 4
    if num_plots >= 12:            
        num_plots_per_row = 6             
                    
    num_rows = (num_plots + num_plots_per_row - 1) // num_plots_per_row                
    g2_with_means = calc_g2_correlations_mean(g2_correlations)
    
    fig = plt.figure(figsize=(12, 3*num_rows))
    fig.suptitle("Fluorescence Spectroscopy Correlations")
    gs = GridSpec(num_rows, num_plots_per_row, figure=fig)
    
    for i, ((channel1, channel2), average, data_list) in enumerate(g2_with_means):
        row = i // num_plots_per_row
        col = i % num_plots_per_row
        ax = fig.add_subplot(gs[row, col])
        for data_index, data in enumerate(data_list):
            ax.plot(lag_index, data, label=f"G(t) {data_index + 1}")
        if len(data_list) > 1:    
            ax.plot(lag_index, average, label=f"G(t) mean")  
        ax.set_xlabel("t" + "(" + "us" + ")")            
        ax.set_ylabel("G(" + "t" + ")")
        ax.set_title(f"Channel {channel1 + 1}- Channel {channel2 + 1}")
        ax.set_xscale('log')
        ax.grid(True)
        ax.legend() 
               
    plt.tight_layout()     
    plt.show()                         
                              
            """,
            'skip_pattern': 'def get_recent_fcs_file():',
            'end_pattern': 'def calc_g2_correlations_mean(g2):',
            'replace_pattern': 'def calc_g2_correlations_mean(g2):',
            'requirements': ['matplotlib']         
        }            
        FileUtils.export_script_file('py', content_modifier, window)             
    
    