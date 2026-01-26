python -m venv .venv-fcs
.\.venv-fcs\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m pip install -r .\requirements.txt
python -m pip install PyQt6 --force-reinstall
pyinstaller --onefile --icon .\assets\fcs-logo.ico --add-data "assets/*:assets" --add-data "export_data_scripts/*:export_data_scripts" --hidden-import=matplotlib.backends.backend_ps --hidden-import=matplotlib.backends.backend_agg .\fcs.py
deactivate