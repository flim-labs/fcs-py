py -3.9 -m venv .venv-fcs
.venv-fcs\Scripts\Activate.ps1
pip install pyinstaller
pip install -r .\requirements.txt
pyinstaller --noconsole --onefile --icon .\assets\fcs-logo.png --add-data "assets/*:assets"  .\fcs.py
deactivate