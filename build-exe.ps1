py -3.9 -m venv .venv-fcs
.venv-fcs\Scripts\Activate.ps1
pip install pyinstaller
pip install -r .\requirements.txt
pip install flim_labs-1.0.64-cp312-none-win_amd64.whl --force reinstall
pip install PyQt6 --force-reinstall
pyinstaller --onefile --icon .\assets\fcs-logo.png --add-data "assets/*:assets" --add-data "export_data_scripts/*:export_data_scripts" --hidden-import=matplotlib.backends.backend_ps --hidden-import=matplotlib.backends.backend_agg .\fcs.py
deactivate