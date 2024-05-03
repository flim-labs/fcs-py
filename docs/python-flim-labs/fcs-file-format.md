<a name="readme-top"></a>

<div align="center">
  <h1>FCS - File Format </h1>
</div>
<div align="center">
  <a href="https://www.flimlabs.com/">
    <img src="../assets/images/fcs-logo.png" alt="Logo" width="120" height="120">
  </a>
</div>
<br>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#introduction">Introduction</a>
    </li>
    <li><a href="#file-format">File Format</a></li>
    <li><a href="#data-visualization">Data Visualization</a>
    <ul
    ><li><a href="#export-data-with-download">Export data with download</a></li>
    <li><a href="#export-data-without-download">Export data without download</a>
    <ul>
    <li><a href="#project-cloned-from-github">Project cloned from GitHub</a></li>
    <li><a href="#executable">Executable</a></li>
    </ul>
    </li>
    </ul>
    </li>
    <li><a href="#download-example-files">Download Example Files </a></li>
    <li><a href="#useful-links">Useful links</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

## Introduction


The [FCS (Fluorescence Correlation Spectroscopy)](https://github.com/flim-labs/fcs-py) tool allows export of photons intensity vectors correlations (**G(<span style="font-family: Times New Roman ">τ</span>)**), outputted during post-processing, to binary files, with convenient plotting and visualization capabilities. This guide provides an in-depth exploration of the **binary file structure**, offering a comprehensive understanding of how exported data is formatted and can be leveraged.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## File Format

<div align="center">
    <img src="../assets/images/export_data.png" width="100%"> 
</div>

Here a detailed explanation of the exported binary data file structure:

##### Header (4 bytes):

The first 4 bytes of the file must be `FCS1`. This serves as a validation check to ensure the correct format of the file. If the check fails, the script prints "Invalid data file" and exits.

##### Metadata Section (Variable length):

Following the header, metadata is stored in the file. This includes:

- `JSON length (4 bytes)`: an unsigned integer representing the length of the JSON metadata.
- `JSON metadata`: this is a variable-length string that contains information about the data, including _enabled channels_, _channels correlations_, _number of acquisitions_, _bin width_, _acquisition time_, and _additional notes written by the user_. This information is printed to the console.

##### G(τ) data section (Variable length):

After the metadata, the subsequent section, of variable length, contains essential data regarding **G(<span style="font-family: Times New Roman ">τ</span>) correlations** for each pair of correlated channels and the **lag index** (a vector of tau values used in correlation calculations). The length of this section depends on the number of correlations analyzed, which can range from 1 to 8 channels, resulting in a potential maximum of _64_ correlations.

- **Lag index**: this is a vector of unsigned integers, spanning from _0 to the length of the intensity vectors - 1_. The lag index (tau) denotes the time lags in microseconds (μs) utilized in computing correlation functions.
- **G(<span style="font-family: Times New Roman ">τ</span>) correlations**: This section comprises essential data concerning correlations, organized as a vector of tuples with the following components:
    - A tuple of 2 unsigned integers indicating the `pair of correlated channels` (e.g., (4,8)).
    - A G(τ) vector representing the `mean of all G(τ)` values calculated for the correlated channel pair.
    - A vector of `G(τ) vectors` computed for the correlated channel pair (the number of G(τ) vectors corresponds to the number of acquisitions performed. For instance, if 5 acquisitions were conducted, the resulting vector will contain 5 G(τ) vectors, with each vector derived from a separate acquisition).
<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Data Visualization

Depending on whether you have chosen to download the script files (Python and/or Matlab) for data analysis on the [FCS GUI](../fcs/v1.0/index.md) or not, follow one of the these guides to visualize the saved data:

#### Export data with download

If you have chosen to download the script files along with the exported .bin data file, follow these steps:

- **Python script**:

  - Open the terminal and navigate to the directory where the saved files are located (it is advisable to save and group them in a folder):

    ```sh
    cd YOUR_DOWNLOADED_DATA_ROOT_FOLDER
    ```

  - Create a virtual environment using the command:
    ```sh
    python -m venv venv
    ```
  - Activate the virtual environment with the command:
    ```sh
    venv\Scripts\activate
    ```
  - Install the necessary dependencies listed in the automatically downloaded _requirements.txt_ with:
    ```sh
    pip install -r requirements.txt
    ```
  - Run your script with:
    ```sh
    python YOUR_SCRIPT_NAME.py
    ```
    <br>

- **Matlab script**:  
   Simply open your MATLAB command window prompt and, after navigating to the folder containing the script, type the name of the script to launch it.

#### Export data without download

If you have chosen to export the data without also downloading the scripts for manipulation, follow one of the these guides depending on whether you are running the _compiled executable_ of FCS or have downloaded the _project locally_ from the GitHub repository:

##### Project cloned from GitHub:

If you are testing FCS locally after cloning the [GitHub repository](https://github.com/flim-labs/fcs-py.git), follow these steps:

- **Python script**:
  <br>

  - Navigate to the root directory of the project:

  ```sh
  cd YOUR_PROJECT_ROOT_FOLDER
  ```

  - Ensure you have created a virtual environment with:
    ```sh
    python -m venv venv
    ```
  - Make sure the virtual environment is activated with:
    ```sh
    venv\Scripts\activate
    ```
  - Ensure you have installed the required dependencies with:
    ```sh
    pip install -r requirements.txt
    ```
  - Ensure you ran this command to make Pyo3 libraries work:
     ```sh
    maturin develop --release
    ```
  - In your code editor, modify the `file_path ` variable in the `exported_data_script.py ` file within the _export_data_scripts_ folder, inserting the path of the _.bin file_ you want to analyze. You can find the .bin file exported at the path `C:\\Users\\YOUR_USER\\.flim-labs\\data `. Note: if you do not modify the path, the most recently saved file will be automatically selected.

  - From the terminal, make sure you have moved to the _export_data_scripts_ folder with:
    ```sh
    cd export_data_scripts
    ```
  - Run the script using the command:
    ```sh
    python exported_data_script.py
    ```

- **Matlab script**:
  - With your code editor, navigate to the `exported_data_script.m ` file within the _export_data_scripts_ folder and modify the `file_path ` variable by inserting the path of the .bin file you want to analyze. You can find the _.bin file_ exported at the path `C:\\Users\\YOUR_USER\\.flim-labs\\data `. Note: if you do not modify the path, the most recently saved file will be automatically selected.

  - From your MATLAB command window prompt, navigate to the _export_data_scripts_ folder of the project and run the MATLAB script by typing `exported_data_script`.

<hr>

##### Executable:

If you are using the FCS executable after installing the software via the [installer](https://github.com/flim-labs/fcs-py/releases), you can download the compressed folder available in the [Download Example Files](#download-example-files) section and follow the steps described. Instead of the example binary file you can use your preferred exported data file.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Download Example Files

By clicking on this [link](../assets/data/fcs-export-data-example.zip) you can download a compressed folder containing an example _Python script_, _Matlab script_, a _binary file of exported data_ and a _requirements.txt_ file with the python needed libraries.

Here the steps to make your tests:

1. Move **fcs-export-data-example.bin** file to this path:
   ```sh
   C:\Users\YOUR_USER\.flim-labs\data
   ```
2. If you are testing **Python** script, follow these steps:
   <br>

   - In the **fcs_plot_data_file_example.py** file, comment out this line of code:
     ```python
     file_path = get_recent_fcs_file()
     ```
   - Uncomment this line of code:

     ```python
     # file_path = "INSERT DATA FILE PATH HERE" # You can also manually insert the path to the data file here
     ```

     and set the correct file path pointing to the .bin file:

     ```python
     file_path = "C:\\Users\\YOUR_USER\\.flim-labs\\data\\fcs-export-data-example.bin"
     ```

   - Set the virtual environment in the root downloaded unzipped folder:
     ```sh
     python -m venv venv
     ```
   - Activate the virtual environment:
     ```sh
     venv\Scripts\activate
     ```
   - Install the dependencies

   ```sh
   pip install -r requirements.txt
   ```

   - Run the example Python script:

   ```sh
   python fcs_plot_data_file_example.py
   ```

      <hr>

3. If you are testing **Matlab** script, follow these steps:  
   <br>
   - In the **fcs_plot_data_file_example.m** file replace this line of code:
     ```sh
     file_path = fullfile(data_folder, most_recent_file);
     ```
     with the correct file path pointing to the .bin file:
     ```sh
     file_path = "C:\\Users\\YOUR_USER\\.flim-labs\\data\\fcs-export-data-example.bin"
     ```
   - From your MATLAB command window prompt, navigate to the _fcs_export_data_example_ folder and run the MATLAB script by typing `fcs_plot_data_file_example`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Useful Links

For more details about the project follow these links:

- [FCS introduction](../index.md)
- [FCS GUI guide](../v1.0/index.md)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

Distributed under the MIT License.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

FLIM LABS: info@flimlabs.com


Project Link: [FCS (Fluorescence Correlation Spectroscopy)](https://github.com/flim-labs/fcs-py)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
