from concurrent.futures import Future
from copy import deepcopy

from PySide6 import QtWidgets
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QSize, QRect
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QStyle, QMessageBox

from app.config.group_config import GroupConfig
from app.layout.camera_group_list_dialog import Ui_CameraGroupListDialog
from app.controller import Controller
from app.thread_bound_callable import thread_bound
from app.widgets.camera_group_edit_dialog import CameraGroupEditDialog


class CameraGroupListModel(QAbstractListModel):
    CameraGroupRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        self.controller.group_added.connect(self._camera_group_added)
        self.controller.recording_updated.connect(self._camera_group_updated)
        self.controller.group_removed.connect(self._camera_group_removed)

        self.config = self.controller.get_config()
        self.camera_groups = sorted(self.config.groups.values(), key=lambda x: (not x.is_default, x.recording_name))

    def rowCount(self, parent=None):
        return len(self.camera_groups)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self.camera_groups):
            return None

        camera_group = self.camera_groups[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return camera_group.recording_name
        elif role == self.CameraGroupRole:
            return camera_group
        elif role == self.NameRole:
            return camera_group.recording_name

        return None

    def find_row_by_group_id(self, group_id: str) -> int | None:
        for row, camera_group in enumerate(self.camera_groups):
            if camera_group.group_id == group_id:
                return row
        return None

    def _camera_group_added(self, camera_group_config: GroupConfig):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.camera_groups.append(camera_group_config)
        self.endInsertRows()

    def _camera_group_updated(self, camera_group_config: GroupConfig):
        row = self.find_row_by_group_id(camera_group_config.group_id)
        if row is None:
            self._camera_group_added(camera_group_config)
            return

        index = self.createIndex(row, 0)

        self.camera_groups[row] = camera_group_config
        self.dataChanged.emit(index, index)

    def _camera_group_removed(self, group_id: str):
        row = self.find_row_by_group_id(group_id)
        if row is None:
            return

        self.beginRemoveRows(QModelIndex(), row, row)
        del self.camera_groups[row]
        self.endRemoveRows()

    def refresh(self):
        self.beginResetModel()
        self.config = self.controller.get_config()
        self.camera_groups = sorted(self.config.groups.values(), key=lambda x: (not x.is_default, x.recording_name))
        self.endResetModel()

    def roleNames(self):
        return {
            self.CameraGroupRole: b'camera_group',
            self.NameRole: b'name'
        }


class CameraGroupDelegate(QStyledItemDelegate):
    """Paints 'name' on the left and hosts a right-aligned QComboBox editor."""
    def sizeHint(self, option, index):
        return QSize(0, max(28, option.fontMetrics.height() + 10))

    def paint(self, painter: QPainter, option, index):
        group_name = index.data(CameraGroupListModel.NameRole)

        # Draw selection background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Common geometry
        margin = 10
        recording_name_w = 0
        r = option.rect
        name_rect = QRect(r.left() + margin, r.top(), r.width() - recording_name_w - 2 * margin, r.height())
        recording_rect = QRect(r.right() - recording_name_w - margin + 1, r.top(), recording_name_w, r.height())

        # Text color depends on selection
        if option.state & QStyle.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())

        # Draw name (elided if too long)
        name_elided = option.fontMetrics.elidedText(group_name, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignVCenter | Qt.AlignLeft, name_elided)

        #recording_name_elided = option.fontMetrics.elidedText(recording_name, Qt.ElideRight, recording_rect.width())
        #painter.drawText(recording_rect, Qt.AlignVCenter | Qt.AlignRight, recording_name_elided)

        # Focus rect
        if option.state & QStyle.State_HasFocus:
            option2 = option  # reuse
            option2.state = option.state
            option.widget.style().drawPrimitive(QStyle.PE_FrameFocusRect, option2, painter, option.widget)


class CameraGroupListDialog(Ui_CameraGroupListDialog, QDialog):
    def __init__(self, controller: Controller, su_mode: bool = False, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self.su_mode = su_mode

        self.camera_group_list_model = CameraGroupListModel(controller)
        self.lst_groups.setModel(self.camera_group_list_model)
        self.lst_groups.setItemDelegate(CameraGroupDelegate())

        self.lst_groups.selectionModel().selectionChanged.connect(self.selected_camera_changed)
        self.btn_add.clicked.connect(self.add_group)
        self.btn_remove.clicked.connect(self.remove_group)
        self.btn_edit.clicked.connect(self.edit_group)

        self.lst_groups.doubleClicked.connect(self.edit_group)

        self.selected_camera_changed()

    def update_btn_add(self):
        visible = self.su_mode or not self.camera_group_list_model.config.is_locked("groups")
        self.btn_add.setVisible(visible)

    def update_btn_remove(self):
        visible = self.su_mode or not self.camera_group_list_model.config.is_locked("groups")
        self.btn_remove.setVisible(visible)

        index = self.lst_groups.currentIndex()
        if not index.isValid():
            self.btn_remove.setEnabled(False)
            return

        row = index.row()
        camera_group = self.camera_group_list_model.camera_groups[row]

        if camera_group.is_default or (not self.su_mode and camera_group.is_locked("self")):
            self.btn_remove.setEnabled(False)
            return

        self.btn_remove.setEnabled(True)

    def update_btn_edit(self):
        index = self.lst_groups.currentIndex()
        if not index.isValid():
            self.btn_edit.setEnabled(False)
            return
        self.btn_edit.setEnabled(True)

    def selected_camera_changed(self):
        self.update_btn_add()
        self.update_btn_remove()
        self.update_btn_edit()

    def remove_group(self):
        index = self.lst_groups.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        camera_group = self.camera_group_list_model.camera_groups[row]

        if self._confirm_remove_group(camera_group.recording_name):
            fut = self.controller.remove_group.future(camera_group.group_id)
            fut.add_done_callback(self._remove_group_result.future)

    def _confirm_remove_group(self, group_name: str) -> bool:
        msb = QtWidgets.QMessageBox()
        msb.setWindowTitle("Remove Camera")
        msb.setText(f"Are you sure you want to remove camera '{group_name}'?")
        msb.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msb.setInformativeText("This action cannot be undone.")
        msb.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msb.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        return msb.exec_() == QtWidgets.QMessageBox.StandardButton.Yes

    @thread_bound(timeout_ms=2000)
    def _remove_group_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error Removing Group", str(fut.exception()))

    def add_group(self):
        dialog = CameraGroupEditDialog(self.controller)
        dialog.setWindowTitle("Add Camera Group")
        dialog.exec()

    def edit_group(self):
        index = self.lst_groups.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        group_config = self.camera_group_list_model.camera_groups[row]

        dialog = CameraGroupEditDialog(self.controller, group=group_config)
        dialog.setWindowTitle("Edit Camera Group")
        dialog.exec()
