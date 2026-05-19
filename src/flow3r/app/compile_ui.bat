:: The pyside6-uic command is provided by the pyside6 Python module, so the command needs to be executed inside the conda environment
call conda activate GrimaceRecorder
echo Compiling Main Window...
pyside6-uic "ui/MainWindow.ui" -o "layout/main_window.py"
echo Compiling Widgets...
pyside6-uic "ui/RecordingControlsWidget.ui" -o "layout/recording_controls_widget.py"
echo Compiling Dialogs...
pyside6-uic "ui/SourceListDialog.ui" -o "layout/source_list_dialog.py"
pyside6-uic "ui/GroupListDialog.ui" -o "layout/group_list_dialog.py"
pyside6-uic "ui/GroupEditDialog.ui" -o "layout/group_edit_dialog.py"
pyside6-uic "ui/PipelineAssignmentDialog.ui" -o "layout/pipeline_assignment_dialog.py"
pyside6-uic "ui/PipelineListDialog.ui" -o "layout/pipeline_list_dialog.py"
pyside6-uic "ui/PlaceholderEditDialog.ui" -o "layout/placeholder_edit_dialog.py"
pyside6-uic "ui/PlaceholderListDialog.ui" -o "layout/placeholder_list_dialog.py"
