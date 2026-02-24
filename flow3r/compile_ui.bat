:: The pyside6-uic command is provided by the pyside6 Python module, so the command needs to be executed inside the conda environment
call conda activate GrimaceRecorder

echo Compiling Main Window...
:: pyside6-uic "app/ui/MainWindow.ui" -o "app/layout/main_window.py"

echo Compiling Widgets...
pyside6-uic "app/ui/RecordingControlsWidget.ui" -o "app/layout/recording_controls_widget.py"