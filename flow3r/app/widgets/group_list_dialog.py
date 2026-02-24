from copy import deepcopy
from typing import Optional, List

from PySide6 import QtWidgets
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QSize, QRect, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QStyle, QMenu

from flow3r.app.config.app_config import AppConfig
from flow3r.app.config.group_config import GroupConfig
from flow3r.app.controller.controller import Controller
from flow3r.app.layout.group_list_dialog import Ui_GroupListDialog
from flow3r.app.widgets.group_edit_dialog import GroupEditDialog
from flow3r.app.widgets.pipeline_assignment_dialog import PipelineAssignmentDialog


class GroupListModel(QAbstractListModel):
    GroupRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self):
        super().__init__()

        self._groups: List[GroupConfig] = []

    def rowCount(self, parent=None):
        return len(self._groups)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._groups):
            return None

        group = self._groups[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return group.name
        elif role == self.GroupRole:
            return group
        elif role == self.NameRole:
            return group.name

        return None

    def find_row_by_group_id(self, group_id: str) -> int | None:
        for row, group in enumerate(self._groups):
            if group.id == group_id:
                return row
        return None

    def _config_snapshot(self, config: AppConfig):
        if not self._groups:
            self.beginResetModel()
            self._groups = list(config.groups.values())
            self.endResetModel()

    def _group_added(self, group_config: GroupConfig):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._groups.append(group_config)
        self.endInsertRows()

    def _group_updated(self, group_config: GroupConfig):
        row = self.find_row_by_group_id(group_config.id)
        if row is None:
            self._group_added(group_config)
            return

        index = self.createIndex(row, 0)

        self._groups[row] = group_config
        self.dataChanged.emit(index, index)

    def _group_removed(self, group_id: str):
        row = self.find_row_by_group_id(group_id)
        if row is None:
            return

        self.beginRemoveRows(QModelIndex(), row, row)
        del self._groups[row]
        self.endRemoveRows()

    def roleNames(self):
        return {
            self.GroupRole: b'group',
            self.NameRole: b'name'
        }


class GroupDelegate(QStyledItemDelegate):
    """Paints 'name' on the left and hosts a right-aligned QComboBox editor."""
    def __init__(self):
        super().__init__()
        self._config: Optional[AppConfig] = None
        self._longest_pipeline_name_width = None

    def set_config(self, config: AppConfig):
        self._config = config
        self._longest_pipeline_name_width = None

    def sizeHint(self, option, index):
        return QSize(0, max(28, option.fontMetrics.height() + 10))

    def paint(self, painter: QPainter, option, index):
        # Draw selection background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        if self._longest_pipeline_name_width is None:
            pipeline_names = list(p.name for p in self._config.pipelines.values())
            self._longest_pipeline_name_width = painter.fontMetrics().horizontalAdvance("Default")
            for pipeline_name in pipeline_names:
                width = painter.fontMetrics().horizontalAdvance(pipeline_name)
                if width > self._longest_pipeline_name_width:
                    self._longest_pipeline_name_width = width

        group = index.data(GroupListModel.GroupRole)
        group_name = group.name
        pipeline_id = group.pipeline_id
        if pipeline_id is None:
            pipeline_name = ""
        else:
            pipeline = self._config.pipelines.get(pipeline_id)
            if pipeline is None:
                pipeline_name = "Unknown"
            else:
                pipeline_name = pipeline.name

        # Common geometry
        margin = 10
        pipeline_name_w = self._longest_pipeline_name_width + 2 * margin

        r = option.rect
        name_rect = QRect(r.left() + margin, r.top(), r.width() - pipeline_name_w - 2 * margin, r.height())
        pipeline_rect = QRect(r.right() - pipeline_name_w - margin + 1, r.top(), pipeline_name_w, r.height())

        # Text color depends on selection
        if option.state & QStyle.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())

        # Draw name (elided if too long)
        name_elided = option.fontMetrics.elidedText(group_name, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignVCenter | Qt.AlignLeft, name_elided)

        pipeline_name_elided = option.fontMetrics.elidedText(pipeline_name, Qt.ElideRight, pipeline_rect.width())
        painter.drawText(pipeline_rect, Qt.AlignVCenter | Qt.AlignRight, pipeline_name_elided)

        # Focus rect
        if option.state & QStyle.State_HasFocus:
            option2 = option  # reuse
            option2.state = option.state
            option.widget.style().drawPrimitive(QStyle.PE_FrameFocusRect, option2, painter, option.widget)


class GroupListDialog(Ui_GroupListDialog, QDialog):
    config_snapshot_requested = Signal()

    group_added = Signal(GroupConfig)
    group_edited = Signal(GroupConfig)
    group_removed = Signal(str)

    pipeline_assignment_changed = Signal(str, object, object)  # group_id, pipeline_ids, source_mapping

    def __init__(self, controller: Controller, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self._config: Optional[AppConfig] = None

        self.group_list_model = GroupListModel()
        self.group_delegate = GroupDelegate()

        self.lst_groups.setModel(self.group_list_model)
        self.lst_groups.setItemDelegate(self.group_delegate)

        self.lst_groups.selectionModel().selectionChanged.connect(self._selected_group_changed)
        self.lst_groups.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lst_groups.customContextMenuRequested.connect(self._show_context_menu)

        self.config_snapshot_requested.connect(self.controller.send_config_snapshot)

        self.controller.config_snapshot.connect(self.group_list_model._config_snapshot)
        self.controller.config_snapshot.connect(self.group_delegate.set_config)
        self.controller.config_changed.connect(self.group_delegate.set_config)
        self.controller.config_snapshot.connect(self.set_config)
        self.controller.config_changed.connect(self.set_config)

        self.controller.group_added.connect(self.group_list_model._group_added)
        self.controller.group_changed.connect(self.group_list_model._group_updated)
        self.controller.group_removed.connect(self.group_list_model._group_removed)

        self.group_added.connect(self.controller.add_group)
        self.group_edited.connect(self.controller.edit_group)
        self.group_removed.connect(self.controller.remove_group)

        self.pipeline_assignment_changed.connect(self.controller.set_pipeline_assignment)

        self.btn_add.clicked.connect(self.add_group)
        self.btn_edit.clicked.connect(self.edit_group)
        self.lst_groups.doubleClicked.connect(self.edit_group)
        self.btn_remove.clicked.connect(self.remove_group)
        self.btn_configure_pipelines.clicked.connect(self.configure_pipelines)

        self.config_snapshot_requested.emit()

        self._selected_group_changed()

    def set_config(self, config: AppConfig):
        self._config = config

    def update_btn_remove(self):
        index = self.lst_groups.currentIndex()
        if not index.isValid():
            self.btn_remove.setEnabled(False)
            return
        self.btn_remove.setEnabled(True)

    def update_btn_edit(self):
        index = self.lst_groups.currentIndex()
        if not index.isValid():
            self.btn_edit.setEnabled(False)
            return
        self.btn_edit.setEnabled(True)

    def update_btn_configure_pipelines(self):
        index = self.lst_groups.currentIndex()
        if not index.isValid():
            self.btn_edit.setEnabled(False)
            return
        self.btn_configure_pipelines.setEnabled(True)

    def _selected_group_changed(self):
        self.update_btn_remove()
        self.update_btn_edit()
        self.update_btn_configure_pipelines()

    def add_group(self):
        group_config = GroupConfig()
        dialog = GroupEditDialog(group_config)
        dialog.setWindowTitle("Add Group")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.group_added.emit(group_config)

    def edit_group(self):
        index = self.lst_groups.currentIndex()
        if not index.isValid():
            return

        group = deepcopy(index.data(GroupListModel.GroupRole))
        dialog = GroupEditDialog(group)
        dialog.setWindowTitle("Edit Group")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.group_edited.emit(group)

    def remove_group(self):
        index = self.lst_groups.currentIndex()
        if not index.isValid():
            return

        group = index.data(GroupListModel.GroupRole)

        if self._confirm_remove_group(group.name):
            self.group_removed.emit(group.id)

    def _confirm_remove_group(self, group_name: str) -> bool:
        msb = QtWidgets.QMessageBox()
        msb.setWindowTitle("Remove Camera")
        msb.setText(f"Are you sure you want to remove camera '{group_name}'?")
        msb.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msb.setInformativeText("This action cannot be undone.")
        msb.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msb.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        return msb.exec_() == QtWidgets.QMessageBox.StandardButton.Yes

    def assign_pipeline_to_group(self, group_id: str, pipeline_id: str):
        group_config = self._config.groups.get(group_id)
        group_config.pipeline_ids.add(pipeline_id)

        dialog = PipelineAssignmentDialog(group_config, self._config.sources, self._config.pipelines)
        res = dialog.exec()
        if res == QDialog.DialogCode.Accepted:
            self.pipeline_assignment_changed.emit(group_id, group_config.pipeline_ids, group_config.source_mapping)

    def configure_pipelines(self):
        index = self.lst_groups.currentIndex()
        if not index.isValid():
            return

        group_config = index.data(GroupListModel.GroupRole)
        dialog = PipelineAssignmentDialog(group_config, self._config.sources, self._config.pipelines)
        dialog.setWindowTitle("Configure Pipelines")
        res = dialog.exec()
        if res == QDialog.DialogCode.Accepted:
            self.pipeline_assignment_changed.emit(group_config.id, group_config.pipeline_ids, group_config.source_mapping)

    def _show_context_menu(self, pos):
        idx = self.lst_groups.indexAt(pos)
        menu = QMenu(self.lst_groups)

        if not idx.isValid():
            return

        self.lst_groups.setCurrentIndex(idx)

        group = self.group_list_model.data(idx, GroupListModel.GroupRole)

        #act_toggle = None
        #if not camera.is_locked("activated"):
        #    act_toggle = menu.addAction("Deactivate" if camera else "Activate")

        act_set_pipeline = menu.addMenu("Set processing pipeline")
        act = act_set_pipeline.addAction("No Pipeline")
        act.setData(None)

        pipelines = sorted(self._config.pipelines.values(), key=lambda x: x.name)
        for pipeline in pipelines:
            act = act_set_pipeline.addAction(pipeline.name)
            act.setData(pipeline.id)

        chosen = menu.exec(self.lst_groups.viewport().mapToGlobal(pos))
        if not chosen:
            return

        if chosen.parent() == act_set_pipeline:
            pipeline_id = chosen.data()
            self.assign_pipeline_to_group(group.id, pipeline_id)
