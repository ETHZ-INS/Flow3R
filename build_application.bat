:: The pyinstaller command is provided by the pyinstaller Python module, so the command needs to be executed inside the conda environment
call conda activate Welfar3Recorder
pyinstaller^
 --add-data "res/logo.png;./res"^
 --add-data "res/logo.ico;./res"^
 --onedir^
 --noconsole^
 --name "Welfar3Recorder"^
 --icon "res/logo.ico"^
 main.py -y