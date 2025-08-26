:: The pyside6-uic command is provided by the pyside6 Python module, so the command needs to be executed inside the conda environment
call conda activate GrimaceRecorder
echo Compiling Main Window...
pyside6-uic "ui/MainWindow.ui" -o "app/layout/main_window.py"
echo Compiling Widgets...
pyside6-uic "ui/CameraWidget.ui" -o "app/layout/camera_widget.py"
pyside6-uic "ui/HeatmapWidget.ui" -o "app/layout/heatmap_widget.py"
pyside6-uic "ui/WelfareAnalysisWidget.ui" -o "app/layout/welfare_analysis_widget.py"
pyside6-uic "ui/RecordingControlsWidget.ui" -o "app/layout/recording_controls_widget.py"
echo Compiling Dialogs...
pyside6-uic "ui/CameraPreviewDialog.ui" -o "app/layout/camera_preview_dialog.py"
pyside6-uic "ui/PipelineConfigurationDialog.ui" -o "app/layout/pipeline_configuration_dialog.py"
pyside6-uic "ui/VideoFileConfigurationDialog.ui" -o "app/layout/video_file_configuration_dialog.py"
pyside6-uic "ui/PoseEstimationConfigurationDialog.ui" -o "app/layout/pose_estimation_configuration_dialog.py"
pyside6-uic "ui/CameraListDialog.ui" -o "app/layout/camera_list_dialog.py"
pyside6-uic "ui/CameraEditDialog.ui" -o "app/layout/camera_edit_dialog.py"
pyside6-uic "ui/CameraGroupListDialog.ui" -o "app/layout/camera_group_list_dialog.py"
pyside6-uic "ui/CameraGroupEditDialog.ui" -o "app/layout/camera_group_edit_dialog.py"
pyside6-uic "ui/VariablePreparationDialog.ui" -o "app/layout/variable_preparation_dialog.py"
pyside6-uic "ui/TextEditorDialog.ui" -o "app/layout/text_editor_dialog.py"
pyside6-uic "ui/VariableListDialog.ui" -o "app/layout/variable_list_dialog.py"
pyside6-uic "ui/VariableEditDialog.ui" -o "app/layout/variable_edit_dialog.py"
