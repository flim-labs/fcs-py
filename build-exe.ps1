py -3.9 -m venv .venv-fcs
.venv-fcs\Scripts\Activate.ps1
pip install pyinstaller
pip install -r .\requirements.txt
maturin develop --release
pip install PyQt6 --force-reinstall
pyinstaller --noconsole --onefile --icon .\assets\fcs-logo.png --add-data "assets/*:assets"  .\fcs.py
deactivate