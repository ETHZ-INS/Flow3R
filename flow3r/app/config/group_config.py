import uuid
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Optional, Set, Any, Type, Self

from flow3r.app.config.recording_config import RecordingConfig
from flow3r.core.config.abc.config import ConfigBase, ITypedConfig


@dataclass
class GroupConfig(ConfigBase):
    RECORDING_MODES: ClassVar[Dict[str, str]] = {
        'manual': 'Manual',
        'timed': 'Timed'
    }

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Group"
    implicit: bool = False
    active: bool = True
    recording_config: RecordingConfig = field(default_factory=RecordingConfig)
    pipeline_id: Optional[str] = None

    pipeline_ids: Set[str] = field(default_factory=set)
    source_mapping: Dict[str, Dict[str, str]] = field(default_factory=dict)  # pipeline_id -> input_name -> source_id

    def _to_dict_data(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "implicit": self.implicit,
            "active": self.active,
            "recording_config": self.recording_config.to_dict(),
            "pipeline_id": self.pipeline_id,
            "pipeline_ids": list(self.pipeline_ids),
            "source_mapping": self.source_mapping,
        }

    @classmethod
    def _from_dict_data(cls, data: Dict[str, Any], type_registry: Dict[str, Type[ITypedConfig]]) -> Self:
        recording_config = RecordingConfig.from_dict(data["recording_config"], type_registry)
        return cls(
            id=data["id"],
            name=data["name"],
            implicit=data["implicit"],
            active=data["active"],
            recording_config=recording_config,
            pipeline_id=data["pipeline_id"],
            pipeline_ids=set(data["pipeline_ids"]),
            source_mapping=data["source_mapping"],
        )
