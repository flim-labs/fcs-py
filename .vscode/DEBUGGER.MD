
# Debugging Python + Rust (PyO3)

### For the FCS (`fcs-py`) + FLIM Processing (`flim-processing`) Workspace

The debugger is currently working only for the python part but NOT for the rust lib.
    
----------

# 1. Project Structure
I ve created a workspace config file to have both the projects in the same root

`workspace/
├── fcs-py/
│   ├── venv/
└── flim-processing/
    ├── flim-lib/ 

The Python gui in fcs in .vscode is the one that works better and requires no cofnigurations.

----------

**Install** the extension **CodeLLDB** in VSCode
# 2. Preparing the Environment

## 2.1 Activate Python virtual environment
- in FCS project, delete the flim_labs dependency from the requirements.txt 
- If you already have a Venv created, go in the folder: C:\Users\{{your user}}\1\flim-labs\fcs-py\venv\Lib\site-packages and delete boththe flim_labs dependencies
- then type `cd fcs-py
- venv\Scripts\activate`
- `cd ..\flim-processing\flim-pyo3-wrapper` 
-  `$env:MATURIN_PROFILE="dev"`
- `$env:VIRTUAL_ENV = "C:\Users\Daguanno\1\flim-labs\fcs-py\venv"`
- `maturin develop`: This builds a **debug-mode** `.pyd` file and installs it into the venv.

Verify:
- `python -c "import flim_labs; print('Using:', flim_labs.__file__)"` 
Expected output:
`Using: C:\...\fcs-py\venv\Lib\site-packages\flim_labs\__init__.py` 

Check if inside that folder, the `.pyd` file must exist.

This pyd file will be used as flim_lab library from the fcs code so that it can be mapped to the rust code




----------

# 3. Debugging Python in VSCode

Run the :
`Python: Run fcs.py (wait for Rust debugger)`
This will start the FCS GUI and process, here you will be already able to enable breakpoints in the python code.




# 4. Debugging Rust Called Through PyO3
Only once you started the fcs process,  you can now start the 
`Rust: Attach with CodeLLDB` that will **attach** the code with the running instance of FCS, providing the correct PID. 

You have a helper script:

### `find-python-process.ps1`

Run it:

`./find-python-process.ps1` 

It wil list all the python processes containing the **fcs.py** string. However, the debugger will start 3 processes out of a running instance, therefore we need to carefully select the proper one to get attached to the debugger: usually the correct PID is the one the highlihts the "fcs.py" filename, typically with a longer name

Debugging Rust requires **attaching CodeLLDB** to the Python interpreter that loads `flim_labs.pyd`.

Install VSCode extension:

-   **CodeLLDB** (Vadim Chugunov)
    

----------

# 5. Finding the Correct Python PID

You have a helper script:

### `find-python-process.ps1`

Run it:

`./find-python-process.ps1` 

It lists all running Python processes, including the one running your GUI:

`c:\...\venv\Scripts\python.exe fcs.py  PID: 12345` 

That PID must be used when attaching the Rust debugger.

----------

# Summarization  Debug Workflow

## Step 1 — Activate venv

- `cd fcs-py`
- `venv\Scripts\activate`
- remove flim_labs libraries from Venv and from requirements.txt 

## Step 2 — Build the Rust extension

- `cd ..\flim-processing\flim-pyo3-wrapper`
- `$env:MATURIN_PROFILE="dev"`
- `$env:VIRTUAL_ENV = "C:\Users\{{user}}\1\flim-labs\fcs-py\venv"`
- `maturin develop` 

## Step 3 — Start the Python debugger in VSCode

Run:

**Python: Run fcs.py (wait for Rust debugger)**


## Step 4 — Find the correct Python PID

`./find-python-process.ps1` 

Example output:

`PID: 21216  -  debugger etc... python.exe fcs.py` 

## Step 5 — Attach Rust debugger

In VSCode run:

**Rust: Attach with CodeLLDB**

Select the PID from Step 4.

## Step 6 — Trigger Rust code

Apply brekapoints in either python and rust code

----------

# 8. Requirements

### Rust toolchain must be MSVC

`rustup show` 

Should display:

`stable-x86_64-pc-windows-msvc` 

### The `.pyd` must have debug symbols

The venv folder should contain:

`flim_labs.cp312-win_amd64.pyd
flim_labs.cp312-win_amd64.pdb`// i don t have this 

Both required for debugging.

