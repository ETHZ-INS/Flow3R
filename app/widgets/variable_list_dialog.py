from concurrent.futures import Future
from copy import deepcopy

from PySide6 import QtWidgets
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QSize, QRect
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QStyle, QMessageBox

from app.config.variable_config import VariableConfig
from app.controller import Controller
from app.layout.variable_list_dialog import Ui_VariableListDialog
from app.thread_bound_callable import thread_bound
from app.widgets.variable_edit_dialog import VariableEditDialog


class VariableListModel(QAbstractListModel):
    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        self.controller.variable_added.connect(self._variable_added)
        self.controller.variable_updated.connect(self._variable_updated)
        self.controller.variable_removed.connect(self._variable_removed)

        self.variable_config_list = deepcopy(self.controller.config.variable_config_list)
        self.variable_configs = sorted(self.variable_config_list.variables.values(), key=lambda x: x.variable_label)

    def rowCount(self, parent=None):
        return len(self.variable_configs)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self.variable_configs):
            return None

        variable_config = self.variable_configs[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return variable_config.variable_label

        return None

    def find_row_by_variable_id(self, variable_id: str) -> int | None:
        for row, variable_config in enumerate(self.variable_configs):
            if variable_config.variable_id == variable_id:
                return row
        return None

    def _variable_added(self, variable_config: VariableConfig):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.variable_configs.append(variable_config)
        self.endInsertRows()

    def _variable_updated(self, variable_config: VariableConfig):
        row = self.find_row_by_variable_id(variable_config.variable_id)
        if row is None:
            self._variable_added(variable_config)
            return

        index = self.createIndex(row, 0)

        self.variable_configs[row] = variable_config
        self.dataChanged.emit(index, index)

    def _variable_removed(self, variable_id: str):
        row = self.find_row_by_variable_id(variable_id)
        if row is None:
            return

        self.beginRemoveRows(QModelIndex(), row, row)
        del self.variable_configs[row]
        self.endRemoveRows()

    def refresh(self):
        self.beginResetModel()
        self.variable_config_list = deepcopy(self.controller.config.variable_config_list)
        self.variable_configs = sorted(self.variable_config_list.variables.values(), key=lambda x: x.variable_label)
        self.endResetModel()


class VariableDelegate(QStyledItemDelegate):
    """Paints 'name' on the left and hosts a right-aligned QComboBox editor."""
    def sizeHint(self, option, index):
        return QSize(0, max(28, option.fontMetrics.height() + 10))

    def paint(self, painter: QPainter, option, index):
        variable_label = index.data()

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
        name_elided = option.fontMetrics.elidedText(variable_label, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignVCenter | Qt.AlignLeft, name_elided)

        #recording_name_elided = option.fontMetrics.elidedText(recording_name, Qt.ElideRight, recording_rect.width())
        #painter.drawText(recording_rect, Qt.AlignVCenter | Qt.AlignRight, recording_name_elided)

        # Focus rect
        if option.state & QStyle.State_HasFocus:
            option2 = option  # reuse
            option2.state = option.state
            option.widget.style().drawPrimitive(QStyle.PE_FrameFocusRect, option2, painter, option.widget)


class VariableListDialog(Ui_VariableListDialog, QDialog):
    def __init__(self, controller: Controller, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self.list_model = VariableListModel(controller)
        self.lst_variables.setModel(self.list_model)
        self.lst_variables.setItemDelegate(VariableDelegate())

        self.lst_variables.selectionModel().selectionChanged.connect(self.selected_variable_changed)
        self.btn_add.clicked.connect(self.add_variable)
        self.btn_remove.clicked.connect(self.remove_variable)
        self.btn_edit.clicked.connect(self.edit_variable)

        self.lst_variables.doubleClicked.connect(self.edit_variable)

        self.selected_variable_changed()

    def update_btn_add(self):
        if self.list_model.variable_config_list.is_locked("variables"):
            self.btn_add.setVisible(False)

    def update_btn_remove(self):
        if self.list_model.variable_config_list.is_locked("variables"):
            self.btn_remove.setVisible(False)

        index = self.lst_variables.currentIndex()
        if not index.isValid():
            self.btn_remove.setEnabled(False)
            return

        row = index.row()
        variable_config = self.list_model.variable_configs[row]

        if variable_config.is_locked("self"):
            self.btn_remove.setEnabled(False)
            return

        self.btn_remove.setEnabled(True)

    def update_btn_edit(self):
        index = self.lst_variables.currentIndex()
        if not index.isValid():
            self.btn_edit.setEnabled(False)
            return
        self.btn_edit.setEnabled(True)

    def selected_variable_changed(self):
        self.update_btn_add()
        self.update_btn_remove()
        self.update_btn_edit()

    def remove_variable(self):
        index = self.lst_variables.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        variable_config = self.list_model.variable_configs[row]

        if self._confirm_remove_variable(variable_config.variable_label):
            fut = self.controller.remove_variable.future(variable_config.variable_id)
            fut.add_done_callback(self._remove_variable_result.future)

    def _confirm_remove_variable(self, variable_label: str) -> bool:
        msb = QtWidgets.QMessageBox()
        msb.setWindowTitle("Remove Variable")
        msb.setText(f"Are you sure you want to remove variable '{variable_label}'?")
        msb.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msb.setInformativeText("This action cannot be undone.")
        msb.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msb.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        return msb.exec_() == QtWidgets.QMessageBox.StandardButton.Yes

    @thread_bound(timeout_ms=2000)
    def _remove_variable_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error Removing Variable", str(fut.exception()))
        res = fut.result()
        if not res.success:
            QMessageBox.critical(self, "Error Removing Variable", res.message)

    def add_variable(self):
        dialog = VariableEditDialog(self.controller)
        dialog.setWindowTitle("Add Variable")
        dialog.exec()

    def edit_variable(self):
        index = self.lst_variables.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        variable_config = self.list_model.variable_configs[row]

        dialog = VariableEditDialog(self.controller, variable_config=variable_config)
        dialog.setWindowTitle("Edit Variable")
        dialog.exec()
