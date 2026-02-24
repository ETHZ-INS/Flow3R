from typing import Dict, Optional, List, Tuple, Any, Set

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, QTimer, QSize
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QComboBox, QAbstractItemView, QApplication, QStyle, QMenu
from scipy.constants import pt

from flow3r.app.config.group_config import GroupConfig
from flow3r.app.layout.pipeline_assignment_dialog import Ui_PipelineAssignmentDialog
from flow3r.core.pipeline.pipeline_config import PipelineConfig
from flow3r.core.source.source_config import SourceConfig


# ----- Tree node -----
class Node:
    def __init__(self, kind: str, name: str, parent: Optional["Node"] = None, node_id: Optional[str] = None):
        self.kind = kind            # "root" | "pipeline" | "input"
        self.name = name
        self.id = node_id           # pipeline_id for pipelines, maybe input_id for inputs
        self.parent = parent
        self.children: List[Node] = []
        self.assigned_source_id: Optional[str] = None  # store source_id or source_name (prefer source_id)

    def row(self) -> int:
        return self.parent.children.index(self) if self.parent else 0


# ----- Model -----
class MappingModel(QAbstractItemModel):
    COL_NAME = 0
    COL_SOURCE = 1

    def __init__(self, pipeline_configs: Dict[str, PipelineConfig], source_configs: Dict[str, SourceConfig],
                 pipeline_ids: Set[str], source_mapping: Dict[str, Dict[str, str]]):
        super().__init__()
        self.pipeline_configs = pipeline_configs
        # Prefer stable IDs internally; show names in UI.
        self.sources: List[Tuple[str, str]] = [(sc.id, sc.name) for sc in source_configs.values()]

        self.pipeline_ids = pipeline_ids
        self.source_mapping = source_mapping

        self.root = Node("root", "root")
        self._pipeline_nodes: Dict[str, Node] = {}  # pipeline_id -> Node

        for pipeline_id in pipeline_ids:
            cfg = self.pipeline_configs[pipeline_id]

            pnode = Node("pipeline", cfg.name, parent=self.root, node_id=pipeline_id)
            self.root.children.append(pnode)
            self._pipeline_nodes[pipeline_id] = pnode

            # Build child input nodes (no beginInsertRows needed; parent row is not yet "visible")
            for input_name in cfg.active_config.inputs():
                inode = Node("input", input_name, parent=pnode, node_id=None)
                if pipeline_id in source_mapping:
                    inode.assigned_source_id = source_mapping[pipeline_id].get(input_name)
                pnode.children.append(inode)


    # ---------- required Qt model methods ----------
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        node = parent.internalPointer() if parent.isValid() else self.root
        return len(node.children)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
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
        node: Node = index.internalPointer()
        parent_node = node.parent
        if parent_node is None or parent_node is self.root:
            return QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        node: Node = index.internalPointer()
        col = index.column()

        if role in (Qt.DisplayRole, Qt.EditRole):
            if col == self.COL_NAME:
                return node.name
            if col == self.COL_SOURCE:
                if node.kind != "input":
                    return ""
                # If you store source_id, convert to display name here:
                if node.assigned_source_id is None or node.assigned_source_id == "":
                    return ""
                # map id -> name
                for sid, sname in self.sources:
                    if sid == node.assigned_source_id:
                        return sname
                # fallback if unknown
                return ""

        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        node: Node = index.internalPointer()
        col = index.column()

        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if node.kind == "input" and col == self.COL_SOURCE:
            f |= Qt.ItemIsEditable
        return f

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        print(f"setData called with index={index.row()}/{index.column()}, value={value}, role={role}")
        if role != Qt.EditRole or not index.isValid():
            return False
        node: Node = index.internalPointer()

        if node.kind == "input" and index.column() == self.COL_SOURCE:
            # Here, store a source_id (recommended). Your delegate can provide IDs.
            print(f"assigning source {value} to input {node.name}")
            pipeline_id = node.parent.id
            if pipeline_id not in self.source_mapping:
                self.source_mapping[pipeline_id] = {}
            self.source_mapping[pipeline_id][node.name] = value or None

            node.assigned_source_id = value or None
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

        pnode = Node("pipeline", cfg.name, parent=self.root, node_id=pipeline_id)
        self.root.children.insert(insert_row, pnode)
        self._pipeline_nodes[pipeline_id] = pnode

        # Build child input nodes (no beginInsertRows needed; parent row is not yet "visible")
        for input_name in cfg.active_config.inputs():
            inode = Node("input", input_name, parent=pnode, node_id=None)
            pnode.children.append(inode)

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
        if node.kind == "input" and index.column() == 1:
            cb = QComboBox(parent)
            cb.addItem("", None)
            for source_id, source_name in self.model.sources:
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
            if node.kind == "pipeline":
                return node.id
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
