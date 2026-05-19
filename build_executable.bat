:: The pyinstaller command is provided by the pyinstaller Python module, so the command needs to be executed inside the conda environment
call conda activate Flow3R
pyinstaller^
 --add-data "flow3r/app/res/flow3r.png;./flow3r/app/res"^
 --add-data "flow3r/app/res/flow3r.ico;./flow3r/app/res"^
 --add-data "flow3r/app/res/style.qss;./flow3r/app/res"^
 --onedir^
 --noconsole^
 --name "Flow3Rb"^
 --icon "flow3r/app/res/flow3r.ico"^
 main.py -y