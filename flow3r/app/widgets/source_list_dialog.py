from copy import deepcopy
from typing import Optional, List

from PySide6 import QtWidgets
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QSize, QRect, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QStyle, QMenu

from flow3r.app.config.app_config import AppConfig
from flow3r.app.controller.controller import Controller
from flow3r.app.layout.source_list_dialog import Ui_SourceListDialog
from flow3r.app.widgets.source_config_dialog import SourceConfigDialog

from flow3r.app.config.source_config import SourceConfig


class SourceListModel(QAbstractListModel):
    SourceRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self):
        super().__init__()

        self._sources: List[SourceConfig] = []

    def rowCount(self, parent=None):
        return len(self._sources)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._sources):
            return None

        source = self._sources[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return source.name
        elif role == self.SourceRole:
            return source
        elif role == self.NameRole:
            return source.name

        return None

    def find_row_by_source_id(self, source_id: str) -> int | None:
        for row, source in enumerate(self._sources):
            if source.id == source_id:
                return row
        return None

    def _config_snapshot(self, config: AppConfig):
        if not self._sources:
            self.beginResetModel()
            self._sources = list(config.sources.values())
            self.endResetModel()

    def _source_added(self, source_config: SourceConfig):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._sources.append(source_config)
        self.endInsertRows()

    def _source_updated(self, source_config: SourceConfig):
        row = self.find_row_by_source_id(source_config.id)
        if row is None:
            self._source_added(source_config)
            return

        index = self.createIndex(row, 0)

        self._sources[row] = source_config
        self.dataChanged.emit(index, index)

    def _source_removed(self, source_id: str):
        row = self.find_row_by_source_id(source_id)
        if row is None:
            return

        self.beginRemoveRows(QModelIndex(), row, row)
        del self._sources[row]
        self.endRemoveRows()

    def roleNames(self):
        return {
            self.SourceRole: b'source',
            self.NameRole: b'name'
        }


class SourceDelegate(QStyledItemDelegate):
    """Paints 'name' on the left and hosts a right-aligned QComboBox editor."""
    def __init__(self):
        super().__init__()
        self._config: Optional[AppConfig] = None
        self._longest_group_name_width = None

    def set_config(self, config: AppConfig):
        self._config = config
        self._longest_group_name_width = None

    def sizeHint(self, option, index):
        return QSize(0, max(28, option.fontMetrics.height() + 10))

    def paint(self, painter: QPainter, option, index):
        # Draw selection background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        if self._longest_group_name_width is None:
            group_names = list(p.name for p in self._config.groups.values())
            self._longest_group_name_width = painter.fontMetrics().horizontalAdvance("Default")
            for group_name in group_names:
                width = painter.fontMetrics().horizontalAdvance(group_name)
                if width > self._longest_group_name_width:
                    self._longest_group_name_width = width

        source = index.data(SourceListModel.SourceRole)
        source_name = source.name
        group_id = source.group_id
        if group_id is None:
            group_name = ""
        else:
            group = self._config.groups.get(group_id)
            if group is None:
                group_name = "Unknown"
            else:
                group_name = group.name

        # Common geometry
        margin = 10
        group_name_w = self._longest_group_name_width + 2 * margin

        r = option.rect
        name_rect = QRect(r.left() + margin, r.top(), r.width() - group_name_w - 2 * margin, r.height())
        group_rect = QRect(r.right() - group_name_w - margin + 1, r.top(), group_name_w, r.height())

        # Text color depends on selection
        if option.state & QStyle.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())

        # Draw name (elided if too long)
        name_elided = option.fontMetrics.elidedText(source_name, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignVCenter | Qt.AlignLeft, name_elided)

        group_name_elided = option.fontMetrics.elidedText(group_name, Qt.ElideRight, group_rect.width())
        painter.drawText(group_rect, Qt.AlignVCenter | Qt.AlignRight, group_name_elided)

        # Focus rect
        if option.state & QStyle.State_HasFocus:
            option2 = option  # reuse
            option2.state = option.state
            option.widget.style().drawPrimitive(QStyle.PE_FrameFocusRect, option2, painter, option.widget)


class SourceListDialog(Ui_SourceListDialog, QDialog):
    config_snapshot_requested = Signal()

    source_added = Signal(SourceConfig)
    source_edited = Signal(SourceConfig)
    source_removed = Signal(str)

    group_assigned_to_source = Signal(str, object)  # source_id, group_id
    pipeline_assigned_to_source = Signal(str, object)  # source_id, pipeline_id

    def __init__(self, controller: Controller, source_types, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self.source_types = source_types
        self._config: Optional[AppConfig] = None

        self.btn_deactivate.setVisible(False)

        self.source_list_model = SourceListModel()
        self.source_delegate = SourceDelegate()

        self.lst_sources.setModel(self.source_list_model)
        self.lst_sources.setItemDelegate(self.source_delegate)

        self.lst_sources.selectionModel().selectionChanged.connect(self._selected_source_changed)
        self.lst_sources.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lst_sources.customContextMenuRequested.connect(self._show_context_menu)

        self.config_snapshot_requested.connect(self.controller.send_config_snapshot)

        self.controller.config_snapshot.connect(self.source_list_model._config_snapshot)
        self.controller.config_snapshot.connect(self.source_delegate.set_config)
        self.controller.config_changed.connect(self.source_delegate.set_config)
        self.controller.config_snapshot.connect(self.set_config)
        self.controller.config_changed.connect(self.set_config)

        self.controller.source_added.connect(self.source_list_model._source_added)
        self.controller.source_changed.connect(self.source_list_model._source_updated)
        self.controller.source_removed.connect(self.source_list_model._source_removed)

        self.source_added.connect(self.controller.add_source)
        self.source_edited.connect(self.controller.edit_source)
        self.source_removed.connect(self.controller.remove_source)

        self.group_assigned_to_source.connect(self.controller.assign_group)
        self.pipeline_assigned_to_source.connect(self.controller.assign_pipeline_to_source)

        self.btn_add.clicked.connect(self.add_source)
        self.btn_edit.clicked.connect(self.edit_source)
        self.lst_sources.doubleClicked.connect(self.edit_source)
        self.btn_remove.clicked.connect(self.remove_source)

        self.config_snapshot_requested.emit()

        self._selected_source_changed()

    def set_config(self, config: AppConfig):
        self._config = config

    def update_btn_remove(self):
        index = self.lst_sources.currentIndex()
        if not index.isValid():
            self.btn_remove.setEnabled(False)
            return
        self.btn_remove.setEnabled(True)

    def update_btn_edit(self):
        index = self.lst_sources.currentIndex()
        if not index.isValid():
            self.btn_edit.setEnabled(False)
            return
        self.btn_edit.setEnabled(True)

    def _selected_source_changed(self):
        self.update_btn_remove()
        self.update_btn_edit()

    def add_source(self):
        source_config = SourceConfig()
        dialog = SourceConfigDialog(self.source_types, source_config)
        dialog.setWindowTitle("Add Source")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.source_added.emit(source_config)

    def edit_source(self):
        index = self.lst_sources.currentIndex()
        if not index.isValid():
            return

        source = deepcopy(index.data(SourceListModel.SourceRole))
        dialog = SourceConfigDialog(self.source_types, source)
        dialog.setWindowTitle("Edit Source")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.source_edited.emit(source)

    def remove_source(self):
        index = self.lst_sources.currentIndex()
        if not index.isValid():
            return

        source = index.data(SourceListModel.SourceRole)

        if self._confirm_remove_source(source.name):
            self.source_removed.emit(source.id)

    def _confirm_remove_source(self, source_name: str) -> bool:
        msb = QtWidgets.QMessageBox()
        msb.setWindowTitle("Remove Camera")
        msb.setText(f"Are you sure you want to remove camera '{source_name}'?")
        msb.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msb.setInformativeText("This action cannot be undone.")
        msb.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msb.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        return msb.exec_() == QtWidgets.QMessageBox.StandardButton.Yes

    def assign_group_to_source(self, source_id: str, group_id: str):
        self.group_assigned_to_source.emit(source_id, group_id)

    def assign_pipeline_to_source(self, source_id: str, pipeline_id: str):
        self.pipeline_assigned_to_source.emit(source_id, pipeline_id)

    def _show_context_menu(self, pos):
        idx = self.lst_sources.indexAt(pos)
        menu = QMenu(self.lst_sources)
        menu.setToolTipsVisible(True)

        if not idx.isValid():
            return

        self.lst_sources.setCurrentIndex(idx)

        source = self.source_list_model.data(idx, SourceListModel.SourceRole)

        #act_toggle = None
        #if not camera.is_locked("activated"):
        #    act_toggle = menu.addAction("Deactivate" if camera else "Activate")

        act_set_group = menu.addMenu("Assign to Group")
        act = act_set_group.addAction("Individual (no group)")
        act.setData(None)

        groups = sorted(self._config.groups.values(), key=lambda x: x.name)
        for group in groups:
            act = act_set_group.addAction(group.name)
            act.setData(group.id)

        act_set_pipeline = menu.addMenu("Assign Pipeline")
        act_set_pipeline.setToolTipsVisible(True)
        if source.group_id is not None:
            act_set_pipeline.setEnabled(False)
            act_set_pipeline.menuAction().setToolTip("Pipelines cannot be assigned to sources that are part of a group. Assign it to the group instead.")
        else:
            act = act_set_pipeline.addAction("Default (no pipeline)")
            act.setData(None)

            pipelines = sorted(self._config.pipelines.values(), key=lambda x: x.name)
            for pipeline in pipelines:
                act = act_set_pipeline.addAction(pipeline.name)
                act.setData(pipeline.id)
                if len(pipeline.active_config.inputs) != 1:
                    act.setEnabled(False)
                    act.setToolTip("Pipelines with multiple inputs cannot be assigned to sources. Create a group instead.")
                    #act.setToolTipsVisible(True)

        chosen = menu.exec(self.lst_sources.viewport().mapToGlobal(pos))
        if not chosen:
            return

        if chosen.parent() == act_set_group:
            group_id = chosen.data()
            self.assign_group_to_source(source.id, group_id)
        elif chosen.parent() == act_set_pipeline:
            pipeline_id = chosen.data()
            self.assign_pipeline_to_source(source.id, pipeline_id)
