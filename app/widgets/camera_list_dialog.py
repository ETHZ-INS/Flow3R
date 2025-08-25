from concurrent.futures import Future
from copy import deepcopy

from PySide6 import QtWidgets
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QThread, QSize, QRect
from PySide6.QtGui import QFont, QPainter, QColor
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QStyle, QComboBox, QMenu, QMessageBox

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
    RecordingNameRole = Qt.ItemDataRole.UserRole + 5

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        self.controller.camera_added.connect(self._camera_added)
        self.controller.camera_updated.connect(self._camera_updated)
        self.controller.camera_removed.connect(self._camera_removed)

        self.camera_config_list = deepcopy(self.controller.config.camera_config_list)
        self.recording_config_list = deepcopy(self.controller.config.recording_config_list)

    def rowCount(self, parent=None):
        return len(self.camera_config_list.cameras)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self.camera_config_list.cameras):
            return None

        camera_id = list(self.camera_config_list.cameras.keys())[index.row()]
        camera = self.camera_config_list.cameras[camera_id]

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
        elif role == self.RecordingNameRole:
            recording_id = camera.recording_id
            recording = self.controller.config.recording_config_list.recordings.get(recording_id) if recording_id else None
            if recording:
                return recording.recording_name
            else:
                return ""

        return None

    def _camera_added(self, camera_config: CameraConfig):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.camera_config_list.cameras[camera_config.camera_id] = camera_config
        self.endInsertRows()

    def _camera_updated(self, camera_config: CameraConfig):
        if camera_config.camera_id not in self.camera_config_list.cameras:
            self._camera_added(camera_config)
            return

        row = list(self.camera_config_list.cameras.keys()).index(camera_config.camera_id)
        index = self.createIndex(row, 0)

        self.camera_config_list.cameras[camera_config.camera_id] = camera_config
        self.dataChanged.emit(index, index)

    def _camera_removed(self, camera_id: str):
        if camera_id not in self.camera_config_list.cameras:
            return

        row = list(self.camera_config_list.cameras.keys()).index(camera_id)
        self.beginRemoveRows(QModelIndex(), row, row)
        del self.camera_config_list.cameras[camera_id]
        self.endRemoveRows()

    def refresh(self):
        self.beginResetModel()
        self.camera_config_list = deepcopy(self.controller.config.camera_config_list.cameras)
        self.recording_config_list = deepcopy(self.controller.config.recording_config_list)
        self.endResetModel()

    def roleNames(self):
        return { self.NameRole: b"name", self.ActiveRole: b"active" }


class CameraDelegate(QStyledItemDelegate):
    """Paints 'name' on the left and hosts a right-aligned QComboBox editor."""
    def sizeHint(self, option, index):
        return QSize(0, max(28, option.fontMetrics.height() + 10))

    def paint(self, painter: QPainter, option, index):
        name = index.data(CameraListModel.NameRole)
        active = index.data(CameraListModel.ActiveRole)
        recording_name = index.data(CameraListModel.RecordingNameRole)

        # Draw selection background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Common geometry
        margin = 10
        recording_name_w = painter.fontMetrics().horizontalAdvance("Recording Name") + 2 * margin
        r = option.rect
        name_rect = QRect(r.left() + margin, r.top(), r.width() - recording_name_w - 2 * margin, r.height())
        recording_rect = QRect(r.right() - recording_name_w - margin + 1, r.top(), recording_name_w, r.height())

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

        recording_name_elided = option.fontMetrics.elidedText(recording_name, Qt.ElideRight, recording_rect.width())
        painter.drawText(recording_rect, Qt.AlignVCenter | Qt.AlignRight, recording_name_elided)

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
        self.lst_cameras.setItemDelegate(CameraDelegate())

        # Enable custom context menu and wire it up
        self.lst_cameras.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        def show_menu(pos):
            idx = self.lst_cameras.indexAt(pos)
            menu = QMenu(self.lst_cameras)

            if not idx.isValid():
                return

            row = idx.row()
            # Select the row that was right-clicked (nice UX)
            self.lst_cameras.setCurrentIndex(idx)

            camera = self.camera_list_model.data(idx, CameraListModel.CameraRole)
            active = bool(self.camera_list_model.data(idx, CameraListModel.ActiveRole))

            act_toggle = None
            if not camera.is_locked("activated"):
                act_toggle = menu.addAction("Deactivate" if active else "Activate")

            act_add_group = None
            if not camera.is_locked("recording_id"):
                act_add_group = menu.addMenu("Assign to group")

                camera_groups = sorted(self.controller.config.recording_config_list.recordings.values(),
                                        key=lambda x: (not x.is_default, x.recording_name))
                for camera_group in camera_groups:
                    act = act_add_group.addAction(camera_group.recording_name)
                    if camera_group.is_default:
                        act.setData(None)
                    else:
                        act.setData(camera_group.recording_id)

            chosen = menu.exec(self.lst_cameras.viewport().mapToGlobal(pos))
            if not chosen:
                return

            if chosen == act_toggle:
                self.toggle_activate_camera()
            elif chosen.parent() == act_add_group:
                print("Assigning to group")
                recording_id = chosen.data()
                print(f"Recording ID: {recording_id}")
                camera_id = list(self.controller.config.camera_config_list.cameras.keys())[row]
                self.assign_camera_to_group(camera_id, recording_id)

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
        if self.camera_list_model.camera_config_list.is_locked("cameras"):
            self.btn_add_camera.setVisible(False)

    def update_btn_remove_camera(self):
        if self.camera_list_model.camera_config_list.is_locked("cameras"):
            self.btn_remove_camera.setVisible(False)

        index = self.lst_cameras.currentIndex()
        if not index.isValid():
            self.btn_remove_camera.setEnabled(False)
            return

        row = index.row()
        camera_id = list(self.camera_list_model.camera_config_list.cameras.keys())[row]
        camera = self.camera_list_model.camera_config_list.cameras[camera_id]

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
        camera_id = list(self.camera_list_model.camera_config_list.cameras.keys())[row]
        camera = self.camera_list_model.camera_config_list.cameras[camera_id]

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

        camera_id = list(self.controller.config.camera_config_list.cameras.keys())[row]
        camera = self.controller.config.camera_config_list.cameras[camera_id]

        self.controller.set_camera_activated.future(camera_id, not camera.activated)

    def remove_camera(self):
        index = self.lst_cameras.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        camera_id = list(self.controller.config.camera_config_list.cameras.keys())[row]
        camera = self.controller.config.camera_config_list.cameras[camera_id]

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
        camera_id = list(self.controller.config.camera_config_list.cameras.keys())[row]
        camera_config = self.controller.config.camera_config_list.cameras[camera_id]

        dialog = CameraEditDialog(self.controller, camera_config=camera_config)
        dialog.setWindowTitle("Edit Camera")
        dialog.exec()

    def assign_camera_to_group(self, camera_id: str, recording_id: str):
        fut = self.controller.assign_camera_to_recording.future(camera_id, recording_id)
        fut.add_done_callback(self._assign_camera_result.future)

    @thread_bound(timeout_ms=2000)
    def _assign_camera_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error Assigning Camera Group", str(fut.exception()))
            return
        res = fut.result()
        if not res.success:
            QMessageBox.critical(self, "Error Assigning Camera Group", res.message)
            return

    def _camera_activated(self, *_):
        print("Camera activated")
        self.update_btn_deactivate_camera()
