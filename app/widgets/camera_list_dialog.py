from concurrent.futures import Future
from copy import deepcopy

from PySide6 import QtWidgets
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QSize, QRect
from PySide6.QtGui import QFont, QPainter
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QStyle, QMenu, QMessageBox

from app.config.camera_config import CameraConfig
from app.layout.camera_list_dialog import Ui_CameraListDialog
from app.controller import Controller
from app.thread_bound_callable import thread_bound
from app.widgets.camera_edit_dialog import CameraEditDialog


class CameraListModel(QAbstractListModel):
    CameraRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2
    ActiveRole = Qt.ItemDataRole.UserRole + 3
    RecordingIDRole = Qt.ItemDataRole.UserRole + 4
    GroupNameRole = Qt.ItemDataRole.UserRole + 5
    PipelineIDRole = Qt.ItemDataRole.UserRole + 6
    PipelineNameRole = Qt.ItemDataRole.UserRole + 7

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        self.controller.camera_added.connect(self._camera_added)
        self.controller.camera_updated.connect(self._camera_updated)
        self.controller.camera_removed.connect(self._camera_removed)

        self.config = deepcopy(self.controller.config)

    def rowCount(self, parent=None):
        return len(self.config.cameras)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self.config.cameras):
            return None

        camera_id = list(self.config.cameras.keys())[index.row()]
        camera = self.config.cameras[camera_id]

        if role == Qt.ItemDataRole.DisplayRole:
            return camera.camera_name
        elif role == Qt.ItemDataRole.FontRole:
            font = QFont()
            font.setPointSize(15)
            font.setStrikeOut(not camera.activated)
            return font
        elif role == self.CameraRole:
            return camera
        elif role == self.NameRole:
            return camera.camera_name
        elif role == self.ActiveRole:
            return camera.activated
        elif role == self.RecordingIDRole:
            return camera.recording_id if camera.recording_id else None
        elif role == self.GroupNameRole:
            recording = self.config.groups[camera.recording_id] if camera.recording_id else None
            if recording:
                return recording.recording_name
            else:
                return ""
        elif role == self.PipelineIDRole:
            return camera.pipeline_id if camera.pipeline_id else None
        elif role == self.PipelineNameRole:
            pipeline = self.config.pipelines[camera.pipeline_id] if camera.pipeline_id else None
            if pipeline:
                return pipeline.pipeline_name
            else:
                return "Default"

        return None

    def _camera_added(self, camera_config: CameraConfig):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.config.cameras[camera_config.camera_id] = camera_config
        self.endInsertRows()

    def _camera_updated(self, camera_config: CameraConfig):
        if camera_config.camera_id not in self.config.cameras:
            self._camera_added(camera_config)
            return

        row = list(self.config.cameras.keys()).index(camera_config.camera_id)
        index = self.createIndex(row, 0)

        self.config.cameras[camera_config.camera_id] = camera_config
        self.dataChanged.emit(index, index)

    def _camera_removed(self, camera_id: str):
        if camera_id not in self.config.cameras:
            return

        row = list(self.config.cameras.keys()).index(camera_id)
        self.beginRemoveRows(QModelIndex(), row, row)
        del self.config.cameras[camera_id]
        self.endRemoveRows()

    def refresh(self):
        self.beginResetModel()
        self.config = deepcopy(self.controller.config)
        self.endResetModel()

    def roleNames(self):
        return { self.NameRole: b"name", self.ActiveRole: b"active" }


class CameraDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, group_names=None, pipeline_names=None):
        super().__init__(parent)
        self.group_names = group_names or []
        self.pipeline_names = pipeline_names or []

        self.longest_group_name_width = None
        self.longest_pipeline_name_width = None

    """Paints 'name' on the left and hosts a right-aligned QComboBox editor."""
    def sizeHint(self, option, index):
        return QSize(0, max(28, option.fontMetrics.height() + 10))

    def paint(self, painter: QPainter, option, index):

        # Draw selection background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        if self.longest_group_name_width is None:
            self.longest_group_name_width = painter.fontMetrics().horizontalAdvance("Default")
            for group_name in self.group_names:
                width = painter.fontMetrics().horizontalAdvance(group_name)
                if width > self.longest_group_name_width:
                    self.longest_group_name_width = width

        if self.longest_pipeline_name_width is None:
            self.longest_pipeline_name_width = painter.fontMetrics().horizontalAdvance("Default")
            for pipeline_name in self.pipeline_names:
                width = painter.fontMetrics().horizontalAdvance(pipeline_name)
                if width > self.longest_pipeline_name_width:
                    self.longest_pipeline_name_width = width

        name = index.data(CameraListModel.NameRole)
        active = index.data(CameraListModel.ActiveRole)
        group_name = index.data(CameraListModel.GroupNameRole)
        pipeline_name = index.data(CameraListModel.PipelineNameRole)

        # Common geometry
        margin = 10

        group_name_w = self.longest_group_name_width + 2 * margin
        pipeline_name_w = self.longest_pipeline_name_width + 2 * margin

        r = option.rect
        name_rect = QRect(r.left() + margin, r.top(), r.width() - group_name_w - pipeline_name_w - 3 * margin, r.height())
        recording_rect = QRect(r.right() - pipeline_name_w - group_name_w - 2 * margin, r.top(), group_name_w, r.height())
        pipeline_rect = QRect(r.right() - pipeline_name_w - margin, r.top(), pipeline_name_w, r.height())

        # Text color depends on selection
        if option.state & QStyle.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())

        font = option.font
        font.setStrikeOut(not active)
        painter.setFont(font)

        # Draw name (elided if too long)
        name_elided = option.fontMetrics.elidedText(name, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignVCenter | Qt.AlignLeft, name_elided)

        recording_name_elided = option.fontMetrics.elidedText(group_name, Qt.ElideRight, recording_rect.width())
        painter.drawText(recording_rect, Qt.AlignVCenter | Qt.AlignRight, recording_name_elided)

        pipeline_name_elided = option.fontMetrics.elidedText(pipeline_name, Qt.ElideRight, pipeline_rect.width())
        painter.drawText(pipeline_rect, Qt.AlignVCenter | Qt.AlignRight, pipeline_name_elided)

        # Focus rect
        if option.state & QStyle.State_HasFocus:
            option2 = option  # reuse
            option2.state = option.state
            option.widget.style().drawPrimitive(QStyle.PE_FrameFocusRect, option2, painter, option.widget)


class CameraListDialog(Ui_CameraListDialog, QDialog):
    def __init__(self, controller: Controller, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self.camera_list_model = CameraListModel(controller)
        self.lst_cameras.setModel(self.camera_list_model)

        group_names = [g.recording_name for g in self.camera_list_model.config.groups.values() if not g.is_default]
        pipeline_names = [p.pipeline_name for p in self.camera_list_model.config.pipelines.values()]
        self.lst_cameras.setItemDelegate(CameraDelegate(self.lst_cameras, group_names=group_names, pipeline_names=pipeline_names))

        # Enable custom context menu and wire it up
        self.lst_cameras.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        def show_menu(pos):
            idx = self.lst_cameras.indexAt(pos)
            menu = QMenu(self.lst_cameras)

            if not idx.isValid():
                return

            row = idx.row()
            self.lst_cameras.setCurrentIndex(idx)

            camera = self.camera_list_model.data(idx, CameraListModel.CameraRole)
            active = bool(self.camera_list_model.data(idx, CameraListModel.ActiveRole))

            act_toggle = None
            if not camera.is_locked("activated"):
                act_toggle = menu.addAction("Deactivate" if active else "Activate")

            act_add_group = None
            if not camera.is_locked("recording_id"):
                act_add_group = menu.addMenu("Assign to group")

                camera_groups = sorted(self.camera_list_model.config.groups.values(),
                                        key=lambda x: (not x.is_default, x.recording_name))
                for camera_group in camera_groups:
                    act = act_add_group.addAction(camera_group.recording_name)
                    if camera_group.is_default:
                        act.setData(None)
                    else:
                        act.setData(camera_group.recording_id)

            act_add_pipeline = None
            if not camera.is_locked("pipeline_id"):
                act_add_pipeline = menu.addMenu("Set processing pipeline")

                pipelines = sorted(self.camera_list_model.config.pipelines.values(),
                                      key=lambda x: (not x.is_default, x.pipeline_name))
                for pipeline in pipelines:
                     act = act_add_pipeline.addAction(pipeline.pipeline_name)
                     if pipeline.is_default:
                           act.setData(None)
                     else:
                           act.setData(pipeline.pipeline_id)

            chosen = menu.exec(self.lst_cameras.viewport().mapToGlobal(pos))
            if not chosen:
                return

            if chosen == act_toggle:
                self.toggle_activate_camera()
            elif chosen.parent() == act_add_group:
                print("Assigning to group")
                recording_id = chosen.data()
                print(f"Recording ID: {recording_id}")
                camera_id = list(self.camera_list_model.config.cameras.keys())[row]
                self.assign_camera_to_group(camera_id, recording_id)
            elif chosen.parent() == act_add_pipeline:
                print("Setting processing pipeline")
                pipeline_id = chosen.data()
                print(f"Pipeline ID: {pipeline_id}")
                camera_id = list(self.camera_list_model.config.cameras.keys())[row]
                self.assign_camera_to_pipeline(camera_id, pipeline_id)

        self.lst_cameras.customContextMenuRequested.connect(show_menu)

        self.controller.camera_activated.connect(self._camera_activated)
        self.lst_cameras.selectionModel().selectionChanged.connect(self.selected_camera_changed)
        self.btn_add_camera.clicked.connect(self.add_camera)
        self.btn_remove_camera.clicked.connect(self.remove_camera)
        self.btn_edit_camera.clicked.connect(self.edit_camera)
        self.btn_deactivate_camera.clicked.connect(self.toggle_activate_camera)

        self.lst_cameras.doubleClicked.connect(self.edit_camera)

        self.selected_camera_changed()

    def update_btn_add_camera(self):
        if self.camera_list_model.config.is_locked("cameras"):
            self.btn_add_camera.setVisible(False)

    def update_btn_remove_camera(self):
        if self.camera_list_model.config.is_locked("cameras"):
            self.btn_remove_camera.setVisible(False)

        index = self.lst_cameras.currentIndex()
        if not index.isValid():
            self.btn_remove_camera.setEnabled(False)
            return

        row = index.row()
        camera_id = list(self.camera_list_model.config.cameras.keys())[row]
        camera = self.camera_list_model.config.cameras[camera_id]

        if camera.is_locked("self"):
            self.btn_remove_camera.setEnabled(False)
            return

        self.btn_remove_camera.setEnabled(True)

    def update_btn_edit_camera(self):
        index = self.lst_cameras.currentIndex()
        if not index.isValid():
            self.btn_edit_camera.setEnabled(False)
            return
        self.btn_edit_camera.setEnabled(True)

    def update_btn_deactivate_camera(self):
        index = self.lst_cameras.currentIndex()
        if not index.isValid():
            self.btn_deactivate_camera.setEnabled(False)
            return

        row = index.row()
        camera_id = list(self.camera_list_model.config.cameras.keys())[row]
        camera = self.camera_list_model.config.cameras[camera_id]

        if camera.is_locked("activated"):
            self.btn_deactivate_camera.setEnabled(False)
            return

        self.btn_deactivate_camera.setEnabled(True)
        if camera.activated:
            self.btn_deactivate_camera.setText("Deactivate Camera")
        else:
            self.btn_deactivate_camera.setText("Activate Camera")

    def selected_camera_changed(self):
        self.update_btn_add_camera()
        self.update_btn_remove_camera()
        self.update_btn_edit_camera()
        self.update_btn_deactivate_camera()

    def toggle_activate_camera(self):
        index = self.lst_cameras.currentIndex()
        if not index.isValid():
            return

        row = index.row()

        camera_id = list(self.controller.config.cameras.keys())[row]
        camera = self.controller.config.cameras[camera_id]

        self.controller.set_camera_activated.future(camera_id, not camera.activated)

    def remove_camera(self):
        index = self.lst_cameras.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        camera_id = list(self.controller.config.cameras.keys())[row]
        camera = self.controller.config.cameras[camera_id]

        if self._confirm_remove_camera(camera.camera_name):
            fut = self.controller.remove_camera.future(camera_id)
            fut.add_done_callback(self._remove_camera_result.future)

    def _confirm_remove_camera(self, camera_name: str) -> bool:
        msb = QtWidgets.QMessageBox()
        msb.setWindowTitle("Remove Camera")
        msb.setText(f"Are you sure you want to remove camera '{camera_name}'?")
        msb.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msb.setInformativeText("This action cannot be undone.")
        msb.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msb.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        ret = msb.exec_()
        return ret == QtWidgets.QMessageBox.StandardButton.Yes

    @thread_bound(timeout_ms=2000)
    def _remove_camera_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error Removing Camera", str(fut.exception()))
        res = fut.result()
        if not res.success:
            QMessageBox.critical(self, "Error Removing Camera", res.message)

    def add_camera(self):
        dialog = CameraEditDialog(self.controller)
        dialog.setWindowTitle("Add Camera")
        dialog.exec()

    def edit_camera(self):
        index = self.lst_cameras.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        camera_id = list(self.controller.config.cameras.keys())[row]
        camera_config = self.controller.config.cameras[camera_id]

        dialog = CameraEditDialog(self.controller, camera_config=camera_config)
        dialog.setWindowTitle("Edit Camera")
        dialog.exec()

    def assign_camera_to_group(self, camera_id: str, recording_id: str):
        fut = self.controller.assign_camera_to_group.future(camera_id, recording_id)
        fut.add_done_callback(self._assign_group_result.future)

    @thread_bound(timeout_ms=2000)
    def _assign_group_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error Assigning Camera Group", str(fut.exception()))
            return
        res = fut.result()
        if not res.success:
            QMessageBox.critical(self, "Error Assigning Camera Group", res.message)
            return

    def assign_camera_to_pipeline(self, camera_id: str, pipeline_id: str):
        fut = self.controller.assign_camera_to_pipeline.future(camera_id, pipeline_id)
        fut.add_done_callback(self._assign_pipeline_result.future)

    @thread_bound(timeout_ms=2000)
    def _assign_pipeline_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error Assigning Processing Pipeline", str(fut.exception()))
            return
        res = fut.result()
        if not res.success:
            QMessageBox.critical(self, "Error Assigning Processing Pipeline", res.message)
            return

    def _camera_activated(self, *_):
        print("Camera activated")
        self.update_btn_deactivate_camera()
