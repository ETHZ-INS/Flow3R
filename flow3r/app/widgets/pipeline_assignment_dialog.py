from typing import Dict, Optional, List, Any, Set

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, QTimer, QSize
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QComboBox, QAbstractItemView, QApplication, QMenu

from flow3r.app.config.group_config import GroupConfig
from flow3r.app.layout.pipeline_assignment_dialog import Ui_PipelineAssignmentDialog
from flow3r.app.config.pipeline_config import PipelineConfig
from flow3r.app.config.source_config import SourceConfig


# ----- Tree nodes -----
class RootNode:
    def __init__(self):
        self.name = "root"
        self.parent = None
        self.children: List[PipelineNode] = []

    def row(self) -> int:
        return 0

class PipelineNode:
    def __init__(self, name: str, pipeline_id: str, parent: RootNode):
        self.name = name
        self.pipeline_id = pipeline_id
        self.parent = parent
        self.children: List[InputNode] = []

    def row(self) -> int:
        return self.parent.children.index(self)


class InputNode:
    def __init__(self, name: str, optional: bool, parent: PipelineNode):
        self.name = name
        self.optional = optional
        self.parent = parent
        self.source_id: Optional[str] = None

    def row(self) -> int:
        return self.parent.children.index(self)


# ----- Model -----
class MappingModel(QAbstractItemModel):
    COL_NAME = 0
    COL_SOURCE = 1

    def __init__(self, pipeline_configs: Dict[str, PipelineConfig], source_configs: Dict[str, SourceConfig],
                 pipeline_ids: Set[str], source_mapping: Dict[str, Dict[str, str]]):
        super().__init__()
        self.pipeline_configs = pipeline_configs
        # Prefer stable IDs internally; show names in UI.
        self.sources: Dict[str, str] = {sc.id: sc.name for sc in source_configs.values()}

        self.pipeline_ids = pipeline_ids
        self.source_mapping = source_mapping

        self.root = RootNode()
        self._pipeline_nodes: Dict[str, PipelineNode] = {}  # pipeline_id -> Node
        self._input_nodes: Dict[str, InputNode] = {}

        for pipeline_id in pipeline_ids:
            pipeline_config = self.pipeline_configs[pipeline_id]

            pipeline_node = PipelineNode(pipeline_config.name, pipeline_id=pipeline_config.id, parent=self.root)
            self.root.children.append(pipeline_node)
            self._pipeline_nodes[pipeline_id] = pipeline_node

            # Build child input nodes (no beginInsertRows needed; parent row is not yet "visible")
            for input_name in pipeline_config.active_config.inputs:
                input_node = InputNode(input_name, optional=False, parent=pipeline_node)
                if pipeline_id in source_mapping:
                    input_node.source_id = source_mapping[pipeline_id].get(input_name)
                pipeline_node.children.append(input_node)

            for input_name in pipeline_config.active_config.optional_inputs:
                input_node = InputNode(input_name, optional=True, parent=pipeline_node)
                if pipeline_id in source_mapping:
                    input_node.source_id = source_mapping[pipeline_id].get(input_name)
                pipeline_node.children.append(input_node)


    # ---------- required Qt model methods ----------
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        node = parent.internalPointer() if parent.isValid() else self.root
        if isinstance(node, InputNode):
            return 0
        return len(node.children)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return ["Pipeline/Input", "Source"][section]
        return None

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_node = parent.internalPointer() if parent.isValid() else self.root
        child = parent_node.children[row]
        return self.createIndex(row, column, child)

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
        parent_node = node.parent
        if parent_node is None or parent_node is self.root:
            return QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        node = index.internalPointer()
        col = index.column()

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if col == self.COL_NAME:
                name = node.name
                if isinstance(node, InputNode) and node.optional:
                    name += " (opt.)"
                return name
            if col == self.COL_SOURCE:
                if not isinstance(node, InputNode):
                    return ""

                if node.source_id is None:
                    return ""

                return self.sources.get(node.source_id, "")

        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        node = index.internalPointer()
        col = index.column()

        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if isinstance(node, InputNode) and col == self.COL_SOURCE:
            f |= Qt.ItemIsEditable
        return f

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid():
            return False
        node = index.internalPointer()

        if isinstance(node, InputNode) and index.column() == self.COL_SOURCE:
            # Here, store a source_id (recommended). Your delegate can provide IDs.
            pipeline_id = node.parent.pipeline_id
            if pipeline_id not in self.source_mapping:
                self.source_mapping[pipeline_id] = {}
            self.source_mapping[pipeline_id][node.name] = value or None

            node.source_id = value or None
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        return False

    # ---------- public API ----------
    def enabled_pipelines(self) -> List[str]:
        return list(self._pipeline_nodes.keys())

    def add_pipeline(self, pipeline_id: str) -> bool:
        """Enable a pipeline (show it in the tree). Returns True if added."""
        if pipeline_id in self._pipeline_nodes:
            return False
        cfg = self.pipeline_configs[pipeline_id]

        self.pipeline_ids.add(pipeline_id)

        # Choose insertion row. Here: append at end.
        insert_row = len(self.root.children)
        self.beginInsertRows(QModelIndex(), insert_row, insert_row)

        pipeline_node = PipelineNode(cfg.name, pipeline_id=pipeline_id, parent=self.root)
        self.root.children.insert(insert_row, pipeline_node)
        self._pipeline_nodes[pipeline_id] = pipeline_node

        # Build child input nodes (no beginInsertRows needed; parent row is not yet "visible")
        for input_name in cfg.active_config.inputs:
            input_node = InputNode(input_name, optional=False, parent=pipeline_node)
            pipeline_node.children.append(input_node)

        for input_name in cfg.active_config.optional_inputs:
            input_node = InputNode(input_name, optional=True, parent=pipeline_node)
            pipeline_node.children.append(input_node)

        self.endInsertRows()
        return True

    def remove_pipeline(self, pipeline_id: str) -> bool:
        """Disable a pipeline (hide it). Returns True if removed."""
        pnode = self._pipeline_nodes.get(pipeline_id)
        if pnode is None:
            return False

        self.pipeline_ids.remove(pipeline_id)

        row = pnode.row()
        self.beginRemoveRows(QModelIndex(), row, row)

        del self.root.children[row]
        del self._pipeline_nodes[pipeline_id]

        self.endRemoveRows()
        return True


class SourceComboDelegate(QStyledItemDelegate):
    def __init__(self, model: MappingModel, parent=None):
        super().__init__(parent)
        self.model = model

    def createEditor(self, parent, option, index):
        node = index.internalPointer()
        if isinstance(node, InputNode) and index.column() == 1:
            cb = QComboBox(parent)
            cb.addItem("", None)
            for source_id, source_name in self.model.sources.items():
                cb.addItem(source_name, source_id)

            # Commit + close immediately on user selection
            cb.activated.connect(lambda _:
                                 (self.commitData.emit(cb),
                                  self.closeEditor.emit(cb, QStyledItemDelegate.NoHint))
                                 )

            # Open dropdown immediately (after it’s shown)
            QTimer.singleShot(0, cb.showPopup)
            return cb

        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, QComboBox):
            current = index.data(Qt.ItemDataRole.EditRole) or ""
            i = editor.findText(current)
            editor.setCurrentIndex(i if i >= 0 else 0)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentData(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def sizeHint(self, option, index):
        return QSize(0, max(28, option.fontMetrics.height() + 10))


class PipelineAssignmentDialog(Ui_PipelineAssignmentDialog, QDialog):
    def __init__(self, config: GroupConfig, source_configs: Dict[str, SourceConfig], pipeline_configs: Dict[str, PipelineConfig], parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.config = config

        self.model = MappingModel(pipeline_configs, source_configs, self.config.pipeline_ids, self.config.source_mapping)
        self.tree_inputs.setEditTriggers(QAbstractItemView.EditTrigger.CurrentChanged | QAbstractItemView.EditTrigger.SelectedClicked)
        self.tree_inputs.setModel(self.model)
        self.tree_inputs.setItemDelegate(SourceComboDelegate(self.model, self.tree_inputs))
        self.tree_inputs.expandAll()
        self.tree_inputs.setAlternatingRowColors(True)

        self.tree_inputs.selectionModel().selectionChanged.connect(self._selection_changed)

        def expand_new_rows(parent, start, end):
            for row in range(start, end + 1):
                index = self.model.index(row, 0, parent)
                self.tree_inputs.expand(index)

        self.model.rowsInserted.connect(expand_new_rows)

        add_pipeline_menu = QMenu(self)

        for pipeline_id in pipeline_configs.keys():
            pipeline_name = pipeline_configs[pipeline_id].name
            action = add_pipeline_menu.addAction(pipeline_name)
            action.setData(pipeline_id)
            action.triggered.connect(lambda checked, pid=pipeline_id: self._add_pipeline(pid))

        self.btn_add_pipeline.setMenu(add_pipeline_menu)

        self.btn_remove_pipeline.clicked.connect(self._remove_pipeline)

    def _selected_pipeline_id(self) -> Optional[str]:
        for index in self.tree_inputs.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue

            node = index.internalPointer()
            if isinstance(node, PipelineNode):
                return node.pipeline_id
        return None

    def _selection_changed(self, _selected, _deselected):
        pipeline_id = self._selected_pipeline_id()
        self.btn_remove_pipeline.setEnabled(pipeline_id is not None)

    def _add_pipeline(self, pipeline_id: str):
        model = self.tree_inputs.model()
        model.add_pipeline(pipeline_id)

    def _remove_pipeline(self):
        pipeline_id = self._selected_pipeline_id()
        if pipeline_id is None:
            return
        self.model.remove_pipeline(pipeline_id)

if __name__ == "__main__":
    from flow3r.plugins.core.source.video.webcam.config import WebcamSourceConfig
    from flow3r.plugins.core.source.audio.microphone.config import MicrophoneSourceConfig
    from flow3r.plugins.core.pipeline.record_video_with_audio.config import RecordVideoWithAudioConfig

    app = QApplication([])

    source = SourceConfig(name="Camera", source_type="Webcam")
    source.set_sub_config("Webcam", WebcamSourceConfig(device_index=0))

    source2 = SourceConfig(name="Mic", source_type="Microphone")
    source2.set_sub_config("Microphone", MicrophoneSourceConfig(device_index=0, sample_rate=48000))

    group = GroupConfig()

    pipeline = PipelineConfig(pipeline_type="Record Video with Audio")
    pipeline.set_sub_config("Record Video with Audio",
                            RecordVideoWithAudioConfig("recordings/recording_{recording_number}.mkv"))

    group.pipeline_ids = {pipeline.id}
    group.source_mapping = {}

    dialog = PipelineAssignmentDialog(group, {source.id: source, source2.id: source2}, {pipeline.id: pipeline})
    dialog.show()

    app.exec()
