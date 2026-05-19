from copy import deepcopy
from typing import Optional, List

from PySide6 import QtWidgets
from PySide6.QtCore import (
    QAbstractListModel, Qt, QModelIndex, QSize, QRect, Signal,
    QByteArray, QDataStream, QIODevice, QMimeData,
)
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QStyle, QMenu

from flow3r.app.config.app_config import AppConfig
from flow3r.app.controller.controller import Controller
from flow3r.app.layout.placeholder_list_dialog import Ui_PlaceholderListDialog
from flow3r.app.widgets.placeholder_edit_dialog import PlaceholderEditDialog

from flow3r.app.config.placeholder_config import PlaceholderConfig


class PlaceholderListModel(QAbstractListModel):
    PlaceholderRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2

    _MIME_TYPE = "application/x-placeholder-row"

    reordered = Signal(list)  # list[str] of placeholder ids in new order

    def __init__(self):
        super().__init__()
        self._placeholders: List[PlaceholderConfig] = []

    # ...existing code...

    def flags(self, index):
        base = super().flags(index)
        if index.isValid():
            return base | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled
        return base | Qt.ItemFlag.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.DropAction.MoveAction

    def mimeTypes(self):
        return [self._MIME_TYPE]

    def mimeData(self, indexes):
        mime = QMimeData()
        buf = QByteArray()
        stream = QDataStream(buf, QIODevice.OpenModeFlag.WriteOnly)
        stream.writeInt32(indexes[0].row())
        mime.setData(self._MIME_TYPE, buf)
        return mime

    def dropMimeData(self, mime, action, row, column, parent):
        if action == Qt.DropAction.IgnoreAction:
            return True
        if not mime.hasFormat(self._MIME_TYPE):
            return False

        buf = mime.data(self._MIME_TYPE)
        stream = QDataStream(buf, QIODevice.OpenModeFlag.ReadOnly)
        src_row = stream.readInt32()

        # -1 means "drop onto empty area" → append to end
        dst_row = self.rowCount() if (row == -1 and not parent.isValid()) else (
            parent.row() if row == -1 else row
        )

        if src_row == dst_row or src_row + 1 == dst_row:
            return False  # no-op

        item = self._placeholders[src_row]
        adjusted_dst = dst_row if dst_row <= src_row else dst_row - 1

        self.beginResetModel()
        self._placeholders.pop(src_row)
        self._placeholders.insert(adjusted_dst, item)
        self.endResetModel()

        self.reordered.emit([p.id for p in self._placeholders])
        return True

    def rowCount(self, parent=None):
        return len(self._placeholders)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._placeholders):
            return None

        placeholder = self._placeholders[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return placeholder.name
        elif role == self.PlaceholderRole:
            return placeholder
        elif role == self.NameRole:
            return placeholder.name

        return None

    def find_row_by_placeholder_id(self, placeholder_id: str) -> int | None:
        for row, placeholder in enumerate(self._placeholders):
            if placeholder.id == placeholder_id:
                return row
        return None

    def _config_snapshot(self, config: AppConfig):
        if not self._placeholders:
            self.beginResetModel()
            self._placeholders = list(config.placeholders.values())
            self.endResetModel()

    def _placeholder_added(self, placeholder_config: PlaceholderConfig):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._placeholders.append(placeholder_config)
        self.endInsertRows()

    def _placeholder_updated(self, placeholder_config: PlaceholderConfig):
        row = self.find_row_by_placeholder_id(placeholder_config.id)
        if row is None:
            self._placeholder_added(placeholder_config)
            return

        index = self.createIndex(row, 0)

        self._placeholders[row] = placeholder_config
        self.dataChanged.emit(index, index)

    def _placeholder_removed(self, placeholder_id: str):
        row = self.find_row_by_placeholder_id(placeholder_id)
        if row is None:
            return

        self.beginRemoveRows(QModelIndex(), row, row)
        del self._placeholders[row]
        self.endRemoveRows()

    def roleNames(self):
        return {
            self.PlaceholderRole: b'placeholder',
            self.NameRole: b'name'
        }


class PlaceholderDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(0, max(28, option.fontMetrics.height() + 10))

    def paint(self, painter: QPainter, option, index):
        # Draw selection background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        placeholder_name = index.data(PlaceholderListModel.NameRole)

        # Common geometry
        margin = 10
        r = option.rect
        name_rect = QRect(r.left() + margin, r.top(), r.width() - 2 * margin, r.height())

        # Text color depends on selection
        if option.state & QStyle.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())

        # Draw name (elided if too long)
        name_elided = option.fontMetrics.elidedText(placeholder_name, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignVCenter | Qt.AlignLeft, name_elided)

        # Focus rect
        if option.state & QStyle.State_HasFocus:
            option2 = option  # reuse
            option2.state = option.state
            option.widget.style().drawPrimitive(QStyle.PE_FrameFocusRect, option2, painter, option.widget)


class PlaceholderListDialog(Ui_PlaceholderListDialog, QDialog):
    config_snapshot_requested = Signal()

    placeholder_added = Signal(PlaceholderConfig)
    placeholder_edited = Signal(PlaceholderConfig)
    placeholder_removed = Signal(str)

    def __init__(self, controller: Controller, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self._config: Optional[AppConfig] = None

        self.placeholder_list_model = PlaceholderListModel()
        self.placeholder_delegate = PlaceholderDelegate()

        self.lst_placeholders.setModel(self.placeholder_list_model)
        self.lst_placeholders.setItemDelegate(self.placeholder_delegate)
        self.lst_placeholders.setDragEnabled(True)
        self.lst_placeholders.setAcceptDrops(True)
        self.lst_placeholders.setDropIndicatorShown(True)
        self.lst_placeholders.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.lst_placeholders.setDefaultDropAction(Qt.DropAction.MoveAction)

        self.lst_placeholders.selectionModel().selectionChanged.connect(self._selected_placeholder_changed)
        self.lst_placeholders.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.config_snapshot_requested.connect(self.controller.send_config_snapshot)

        self.controller.config_snapshot.connect(self.placeholder_list_model._config_snapshot)
        self.controller.config_snapshot.connect(self.set_config)
        self.controller.config_changed.connect(self.set_config)

        self.controller.placeholder_added.connect(self.placeholder_list_model._placeholder_added)
        self.controller.placeholder_changed.connect(self.placeholder_list_model._placeholder_updated)
        self.controller.placeholder_removed.connect(self.placeholder_list_model._placeholder_removed)

        self.placeholder_added.connect(self.controller.add_placeholder)
        self.placeholder_edited.connect(self.controller.edit_placeholder)
        self.placeholder_removed.connect(self.controller.remove_placeholder)
        self.placeholder_list_model.reordered.connect(self.controller.reorder_placeholders)

        self.btn_add.clicked.connect(self.add_placeholder)
        self.btn_edit.clicked.connect(self.edit_placeholder)
        self.lst_placeholders.doubleClicked.connect(self.edit_placeholder)
        self.btn_remove.clicked.connect(self.remove_placeholder)

        self.config_snapshot_requested.emit()

        self._selected_placeholder_changed()

    def set_config(self, config: AppConfig):
        self._config = config

    def update_btn_remove(self):
        index = self.lst_placeholders.currentIndex()
        if not index.isValid():
            self.btn_remove.setEnabled(False)
            return
        self.btn_remove.setEnabled(True)

    def update_btn_edit(self):
        index = self.lst_placeholders.currentIndex()
        if not index.isValid():
            self.btn_edit.setEnabled(False)
            return
        self.btn_edit.setEnabled(True)

    def _selected_placeholder_changed(self):
        self.update_btn_remove()
        self.update_btn_edit()

    def add_placeholder(self):
        placeholder_config = PlaceholderConfig()
        dialog = PlaceholderEditDialog(placeholder_config)
        dialog.setWindowTitle("Add Placeholder")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.placeholder_added.emit(placeholder_config)

    def edit_placeholder(self):
        index = self.lst_placeholders.currentIndex()
        if not index.isValid():
            return

        placeholder_config = deepcopy(index.data(PlaceholderListModel.PlaceholderRole))
        dialog = PlaceholderEditDialog(placeholder_config)
        dialog.setWindowTitle("Edit Placeholder")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.placeholder_edited.emit(placeholder_config)

    def remove_placeholder(self):
        index = self.lst_placeholders.currentIndex()
        if not index.isValid():
            return

        placeholder = index.data(PlaceholderListModel.PlaceholderRole)

        if self._confirm_remove_placeholder(placeholder.name):
            self.placeholder_removed.emit(placeholder.id)

    def _confirm_remove_placeholder(self, placeholder_name: str) -> bool:
        msb = QtWidgets.QMessageBox()
        msb.setWindowTitle("Remove Camera")
        msb.setText(f"Are you sure you want to remove camera '{placeholder_name}'?")
        msb.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msb.setInformativeText("This action cannot be undone.")
        msb.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msb.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        return msb.exec_() == QtWidgets.QMessageBox.StandardButton.Yes
