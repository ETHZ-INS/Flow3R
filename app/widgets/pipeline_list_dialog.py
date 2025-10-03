from concurrent.futures import Future
from typing import List

from PySide6 import QtWidgets
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QSize, QRect
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QStyle, QMessageBox

from app.config.pipeline_config import PipelineConfig
from app.controller import Controller
from app.layout.pipeline_list_dialog import Ui_PipelineListDialog
from app.thread_bound_callable import thread_bound
from app.widgets.pipeline_edit_dialog import PipelineEditDialog


class PipelineListModel(QAbstractListModel):
    PipelineRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        self.controller.pipeline_added.connect(self._pipeline_added)
        self.controller.pipeline_updated.connect(self._pipeline_updated)
        self.controller.pipeline_removed.connect(self._pipeline_removed)

        self.config = self.controller.get_config()
        self.pipelines: List[PipelineConfig] = sorted(self.config.pipelines.values(), key=lambda x: (not x.is_default, x.pipeline_name))

    def rowCount(self, parent=None):
        return len(self.pipelines)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self.pipelines):
            return None

        pipeline = self.pipelines[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return pipeline.pipeline_name
        elif role == self.PipelineRole:
            return pipeline
        elif role == self.NameRole:
            return pipeline.pipeline_name

        return None

    def find_row_by_id(self, pipeline_id: str) -> int | None:
        for row, pipeline in enumerate(self.pipelines):
            if pipeline.pipeline_id == pipeline_id:
                return row
        return None

    def _pipeline_added(self, pipeline_config: PipelineConfig):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.pipelines.append(pipeline_config)
        self.endInsertRows()

    def _pipeline_updated(self, pipeline_config: PipelineConfig):
        row = self.find_row_by_id(pipeline_config.pipeline_id)
        if row is None:
            self._pipeline_added(pipeline_config)
            return

        index = self.createIndex(row, 0)

        self.pipelines[row] = pipeline_config
        self.dataChanged.emit(index, index)

    def _pipeline_removed(self, pipeline_id: str):
        row = self.find_row_by_id(pipeline_id)
        if row is None:
            return

        self.beginRemoveRows(QModelIndex(), row, row)
        del self.pipelines[row]
        self.endRemoveRows()

    def refresh(self):
        self.beginResetModel()
        self.config = self.controller.get_config()
        self.pipelines = sorted(self.config.pipelines.values(), key=lambda x: (not x.is_default, x.pipeline_name))
        self.endResetModel()

    def roleNames(self):
        return {
            self.PipelineRole: b'pipeline',
            self.NameRole: b'name'
        }


class PipelineDelegate(QStyledItemDelegate):
    """Paints 'name' on the left and hosts a right-aligned QComboBox editor."""
    def sizeHint(self, option, index):
        return QSize(0, max(28, option.fontMetrics.height() + 10))

    def paint(self, painter: QPainter, option, index):
        pipeline_name = index.data(PipelineListModel.NameRole)

        # Draw selection background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Common geometry
        margin = 10
        pipeline_name_w = 0
        r = option.rect
        name_rect = QRect(r.left() + margin, r.top(), r.width() - pipeline_name_w - 2 * margin, r.height())
        pipeline_rect = QRect(r.right() - pipeline_name_w - margin + 1, r.top(), pipeline_name_w, r.height())

        # Text color depends on selection
        if option.state & QStyle.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())

        # Draw name (elided if too long)
        name_elided = option.fontMetrics.elidedText(pipeline_name, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignVCenter | Qt.AlignLeft, name_elided)

        #pipeline_name_elided = option.fontMetrics.elidedText(pipeline_name, Qt.ElideRight, pipeline_rect.width())
        #painter.drawText(pipeline_rect, Qt.AlignVCenter | Qt.AlignRight, pipeline_name_elided)

        # Focus rect
        if option.state & QStyle.StateFlag.State_HasFocus:
            option2 = option  # reuse
            option2.state = option.state
            option.widget.style().drawPrimitive(QStyle.PE_FrameFocusRect, option2, painter, option.widget)


class PipelineListDialog(Ui_PipelineListDialog, QDialog):
    def __init__(self, controller: Controller, su_mode: bool = False, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self.su_mode = su_mode

        self.list_model = PipelineListModel(controller)
        self.lst_pipelines.setModel(self.list_model)
        self.lst_pipelines.setItemDelegate(PipelineDelegate())

        self.lst_pipelines.selectionModel().selectionChanged.connect(self.selected_camera_changed)
        self.btn_add.clicked.connect(self.add_pipeline)
        self.btn_remove.clicked.connect(self.remove_pipeline)
        self.btn_edit.clicked.connect(self.edit_pipeline)

        self.lst_pipelines.doubleClicked.connect(self.edit_pipeline)

        self.selected_camera_changed()

    def update_btn_add(self):
        visible = self.su_mode or not self.list_model.config.is_locked("pipelines")
        self.btn_add.setVisible(visible)

    def update_btn_remove(self):
        visible = self.su_mode or not self.list_model.config.is_locked("pipelines")
        self.btn_remove.setVisible(visible)

        index = self.lst_pipelines.currentIndex()
        if not index.isValid():
            self.btn_remove.setEnabled(False)
            return

        row = index.row()
        pipeline = self.list_model.pipelines[row]

        if pipeline.is_default or (not self.su_mode and pipeline.is_locked("self")):
            self.btn_remove.setEnabled(False)
            return

        self.btn_remove.setEnabled(True)

    def update_btn_edit(self):
        index = self.lst_pipelines.currentIndex()
        if not index.isValid():
            self.btn_edit.setEnabled(False)
            return
        self.btn_edit.setEnabled(True)

    def selected_camera_changed(self):
        self.update_btn_add()
        self.update_btn_remove()
        self.update_btn_edit()

    def remove_pipeline(self):
        index = self.lst_pipelines.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        pipeline = self.list_model.pipelines[row]

        if self._confirm_remove(pipeline.pipeline_name):
            fut = self.controller.remove_pipeline.future(pipeline.pipeline_id)
            fut.add_done_callback(self._remove_pipeline_result.future)

    def _confirm_remove(self, pipeline_name: str) -> bool:
        msb = QtWidgets.QMessageBox()
        msb.setWindowTitle("Remove Camera")
        msb.setText(f"Are you sure you want to remove pipeline '{pipeline_name}'?")
        msb.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msb.setInformativeText("This action cannot be undone.")
        msb.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msb.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        return msb.exec_() == QtWidgets.QMessageBox.StandardButton.Yes

    @thread_bound(timeout_ms=2000)
    def _remove_pipeline_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error Removing Pipeline", str(fut.exception()))

    def add_pipeline(self):
        dialog = PipelineEditDialog(self.controller)
        dialog.setWindowTitle("Add Pipeline")
        dialog.exec()

    def edit_pipeline(self):
        index = self.lst_pipelines.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        pipeline = self.list_model.pipelines[row]

        dialog = PipelineEditDialog(self.controller, pipeline=pipeline)
        dialog.setWindowTitle("Edit Pipeline")
        dialog.exec()
