import os
import shutil

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from components.box_message import BoxMessage
from components.gui_styles import GUIStyles
from components.messages_utilities import MessagesUtilities
from components.resource_path import resource_path

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, ".."))

fcs_py_script_path = resource_path("export_data_scripts/fcs_script.py")
fcs_m_script_path = resource_path("export_data_scripts/fcs_script.m")
time_tagger_py_script_path = resource_path("export_data_scripts/time_tagger_script.py")


class ScriptFileUtils:

    @classmethod
    def export_scripts(cls, bin_file_paths, file_name, directory, script_type, time_tagger=False, time_tagger_file_path=""):
        try:
            if time_tagger:
                python_modifier = cls.get_time_tagger_content_modifiers()
                cls.write_new_scripts_content(python_modifier, {"time_tagger": time_tagger_file_path}, file_name, directory, "py", "time_tagger_fcs")  
            
            if script_type == "fcs":
                python_modifier, matlab_modifier = cls.get_fcs_content_modifiers(time_tagger)
                cls.write_new_scripts_content(
                    python_modifier,
                    bin_file_paths,
                    file_name,
                    directory,
                    "py",
                    script_type,
                )
                cls.write_new_scripts_content(
                    matlab_modifier,
                    bin_file_paths,
                    file_name,
                    directory,
                    "m",
                    script_type,
                )
            cls.show_success_message(file_name)
        except Exception as e:
            cls.show_error_message(str(e))

    @classmethod
    def write_new_scripts_content(
        cls,
        content_modifier,
        bin_file_paths,
        file_name,
        directory,
        file_extension,
        script_type,
    ):
        content = cls.read_file_content(content_modifier["source_file"])
        new_content = cls.manipulate_file_content(content, bin_file_paths)
        script_file_name = f"{file_name}_{script_type}_script.{file_extension}"
        script_file_path = os.path.join(directory, script_file_name)
        cls.write_file(script_file_path, new_content)
        if content_modifier["requirements"]:
            requirements_file_name = "requirements.txt"
            requirements_file_path = os.path.join(directory, requirements_file_name)
            requirements_content = cls.create_requirements_content(
                content_modifier["requirements"]
            )
            cls.write_file(requirements_file_path, requirements_content)

    @classmethod
    def get_fcs_content_modifiers(cls, time_tagger=False):
        python_modifier = {
            "source_file": fcs_py_script_path,
            "skip_pattern": "def get_recent_spectroscopy_file():",
            "end_pattern": "# Read bin data",
            "replace_pattern": "# Read bin data",
            "requirements": (
                ["matplotlib", "numpy"]
                if not time_tagger
                else ["matplotlib", "numpy", "pandas", "tqdm", "pyarrow", "colorama"]
            ),
        }
        matlab_modifier = {
            "source_file": fcs_m_script_path,
            "skip_pattern": "% Get the recent spectroscopy file",
            "end_pattern": "% Open the file",
            "replace_pattern": "% Open the file",
            "requirements": [],
        }
        return python_modifier, matlab_modifier

    @classmethod
    def get_time_tagger_content_modifiers(cls):
        python_modifier = {
            "source_file": time_tagger_py_script_path,
            "skip_pattern": "def get_recent_time_tagger_file():",
            "end_pattern": "init(autoreset=True)",
            "replace_pattern": "init(autoreset=True)",
            "requirements": [],
        }
        return python_modifier

    @classmethod
    def write_file(cls, file_name, content):
        with open(file_name, "w") as file:
            file.writelines(content)

    @classmethod
    def create_requirements_content(cls, requirements):
        requirements_content = [f"{requirement}\n" for requirement in requirements]
        return requirements_content

    @classmethod
    def read_file_content(cls, file_path):
        with open(file_path, "r") as file:
            return file.readlines()

    @classmethod
    def manipulate_file_content(cls, content, file_paths):
        manipulated_lines = []
        for line in content:
            if "fcs" in file_paths:
                line = line.replace("<FILE-PATH>", file_paths["fcs"].replace("\\", "/"))
            else:
                line = line.replace(
                    "<FILE-PATH>", file_paths["time_tagger"].replace("\\", "/")
                )
            manipulated_lines.append(line)
        return manipulated_lines

    @classmethod
    def show_success_message(cls, file_name):
        info_title, info_msg = MessagesUtilities.info_handler(
            "SavedDataFiles", file_name
        )
        BoxMessage.setup(
            info_title,
            info_msg,
            QMessageBox.Icon.Information,
            GUIStyles.set_msg_box_style(),
        )

    @classmethod
    def show_error_message(cls, error_message):
        error_title, error_msg = MessagesUtilities.error_handler(
            "ErrorSavingDataFiles", error_message
        )
        BoxMessage.setup(
            error_title,
            error_msg,
            QMessageBox.Icon.Critical,
            GUIStyles.set_msg_box_style(),
        )
