:: The pyside6-uic command is provided by the pyside6 Python module, so the command needs to be executed inside the conda environment
call conda activate GrimaceRecorder
echo Compiling Main Window...
pyside6-uic "ui/WelfareRecorder.ui" -o "app/layout/welfare_recorder.py"
echo Compiling Widgets...
pyside6-uic "ui/CameraWidget.ui" -o "app/layout/camera_widget.py"
pyside6-uic "ui/HeatmapWidget.ui" -o "app/layout/heatmap_widget.py"
pyside6-uic "ui/WelfareAnalysisWidget.ui" -o "app/layout/welfare_analysis_widget.py"
echo Compiling Dialogs...
pyside6-uic "ui/CameraConfigurationDialog.ui" -o "app/layout/camera_configuration_dialog.py"
pyside6-uic "ui/RecordingConfigurationDialog.ui" -o "app/layout/recording_configuration_dialog.py"
