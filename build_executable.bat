call conda activate Flow3R

pyinstaller ^
 --paths src ^
 --add-data "src/flow3r/app/res/flow3r.png;flow3r/app/res" ^
 --add-data "src/flow3r/app/res/flow3r.ico;flow3r/app/res" ^
 --add-data "src/flow3r/app/res/style.qss;flow3r/app/res" ^
 --onedir ^
 --noconsole ^
 --name "Flow3R" ^
 --icon "src/flow3r/app/res/flow3r.ico" ^
 src/main.py -y