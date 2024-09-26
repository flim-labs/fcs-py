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

The script files are automatically downloaded along with the intensity and fcs .bin files once the acquisition and fcs post-processing is complete and a file name has been chosen. Follow one of the guides below if you wish to use the Python or Matlab script:

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

## Useful Links

For more details about the project follow these links:

- [FCS introduction](../index.md)
- [FCS GUI guide](../v1.2/index.md)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

Distributed under the MIT License.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

FLIM LABS: info@flimlabs.com


Project Link: [FCS (Fluorescence Correlation Spectroscopy)](https://github.com/flim-labs/fcs-py)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
