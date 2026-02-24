from copy import deepcopy
from typing import Optional, List

from PySide6 import QtWidgets
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QSize, QRect, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QStyle

from flow3r.app.config.app_config import AppConfig
from flow3r.app.controller.controller import Controller
from flow3r.app.layout.pipeline_list_dialog import Ui_PipelineListDialog
from flow3r.app.widgets.pipeline_config_dialog import PipelineConfigDialog
from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.pipeline.pipeline_config import PipelineConfig


class PipelineListModel(QAbstractListModel):
    PipelineRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self):
        super().__init__()

        self._pipelines: List[PipelineConfig] = []

    def rowCount(self, parent=None):
        return len(self._pipelines)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._pipelines):
            return None

        pipeline = self._pipelines[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return pipeline.name
        elif role == self.PipelineRole:
            return pipeline
        elif role == self.NameRole:
            return pipeline.name

        return None

    def find_row_by_pipeline_id(self, pipeline_id: str) -> int | None:
        for row, pipeline in enumerate(self._pipelines):
            if pipeline.id == pipeline_id:
                return row
        return None

    def _config_snapshot(self, config: AppConfig):
        if not self._pipelines:
            self.beginResetModel()
            self._pipelines = list(config.pipelines.values())
            self.endResetModel()

    def _pipeline_added(self, pipeline_config: PipelineConfig):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._pipelines.append(pipeline_config)
        self.endInsertRows()

    def _pipeline_updated(self, pipeline_config: PipelineConfig):
        row = self.find_row_by_pipeline_id(pipeline_config.id)
        if row is None:
            self._pipeline_added(pipeline_config)
            return

        index = self.createIndex(row, 0)

        self._pipelines[row] = pipeline_config
        self.dataChanged.emit(index, index)

    def _pipeline_removed(self, pipeline_id: str):
        row = self.find_row_by_pipeline_id(pipeline_id)
        if row is None:
            return

        self.beginRemoveRows(QModelIndex(), row, row)
        del self._pipelines[row]
        self.endRemoveRows()

    def roleNames(self):
        return {
            self.PipelineRole: b'pipeline',
            self.NameRole: b'name'
        }


class PipelineDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(0, max(28, option.fontMetrics.height() + 10))

    def paint(self, painter: QPainter, option, index):
        # Draw selection background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        pipeline = index.data(PipelineListModel.PipelineRole)
        pipeline_name = pipeline.name

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
        name_elided = option.fontMetrics.elidedText(pipeline_name, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignVCenter | Qt.AlignLeft, name_elided)

        # Focus rect
        if option.state & QStyle.State_HasFocus:
            option2 = option  # reuse
            option2.state = option.state
            option.widget.style().drawPrimitive(QStyle.PE_FrameFocusRect, option2, painter, option.widget)


class PipelineListDialog(Ui_PipelineListDialog, QDialog):
    config_snapshot_requested = Signal()

    pipeline_added = Signal(PipelineConfig)
    pipeline_edited = Signal(PipelineConfig)
    pipeline_removed = Signal(str)

    def __init__(self, app_context: IAppContext, controller: Controller, pipeline_types, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.app_context = app_context
        self.controller = controller
        self.pipeline_types = pipeline_types

        self.pipeline_list_model = PipelineListModel()
        self.pipeline_delegate = PipelineDelegate()

        self.lst_pipelines.setModel(self.pipeline_list_model)
        self.lst_pipelines.setItemDelegate(self.pipeline_delegate)

        self.lst_pipelines.selectionModel().selectionChanged.connect(self._selected_pipeline_changed)

        self.config_snapshot_requested.connect(self.controller.send_config_snapshot)

        self.controller.config_snapshot.connect(self.pipeline_list_model._config_snapshot)

        self.controller.pipeline_added.connect(self.pipeline_list_model._pipeline_added)
        self.controller.pipeline_changed.connect(self.pipeline_list_model._pipeline_updated)
        self.controller.pipeline_removed.connect(self.pipeline_list_model._pipeline_removed)

        self.pipeline_added.connect(self.controller.add_pipeline)
        self.pipeline_edited.connect(self.controller.edit_pipeline)
        self.pipeline_removed.connect(self.controller.remove_pipeline)

        self.btn_add.clicked.connect(self.add_pipeline)
        self.btn_edit.clicked.connect(self.edit_pipeline)
        self.lst_pipelines.doubleClicked.connect(self.edit_pipeline)
        self.btn_remove.clicked.connect(self.remove_pipeline)

        self.config_snapshot_requested.emit()

        self._selected_pipeline_changed()

    def update_btn_remove(self):
        index = self.lst_pipelines.currentIndex()
        if not index.isValid():
            self.btn_remove.setEnabled(False)
            return
        self.btn_remove.setEnabled(True)

    def update_btn_edit(self):
        index = self.lst_pipelines.currentIndex()
        if not index.isValid():
            self.btn_edit.setEnabled(False)
            return
        self.btn_edit.setEnabled(True)

    def _selected_pipeline_changed(self):
        self.update_btn_remove()
        self.update_btn_edit()

    def add_pipeline(self):
        pipeline_config = PipelineConfig()
        dialog = PipelineConfigDialog(self.app_context, self.pipeline_types, pipeline_config)
        dialog.setWindowTitle("Add Pipeline")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.pipeline_added.emit(pipeline_config)

    def edit_pipeline(self):
        index = self.lst_pipelines.currentIndex()
        if not index.isValid():
            return

        pipeline = deepcopy(index.data(PipelineListModel.PipelineRole))
        dialog = PipelineConfigDialog(self.app_context, self.pipeline_types, pipeline)
        dialog.setWindowTitle("Edit Pipeline")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.pipeline_edited.emit(pipeline)

    def remove_pipeline(self):
        index = self.lst_pipelines.currentIndex()
        if not index.isValid():
            return

        pipeline = index.data(PipelineListModel.PipelineRole)

        if self._confirm_remove_pipeline(pipeline.name):
            self.pipeline_removed.emit(pipeline.id)

    def _confirm_remove_pipeline(self, pipeline_name: str) -> bool:
        msb = QtWidgets.QMessageBox()
        msb.setWindowTitle("Remove Pipeline")
        msb.setText(f"Are you sure you want to remove pipeline '{pipeline_name}'?")
        msb.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msb.setInformativeText("This action cannot be undone.")
        msb.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msb.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        return msb.exec_() == QtWidgets.QMessageBox.StandardButton.Yes
