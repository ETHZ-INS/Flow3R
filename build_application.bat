:: The pyinstaller command is provided by the pyinstaller Python module, so the command needs to be executed inside the conda environment
call conda activate Flow3R
pyinstaller^
 --add-data "res/logo.png;./res"^
 --add-data "res/logo.ico;./res"^
 --add-data "res/flow3r.png;./res"^
 --add-data "res/flow3r.ico;./res"^
 --onedir^
 --noconsole^
 --name "Flow3R"^
 --icon "res/flow3r.ico"^
 main.py -y