import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SourceConfig:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Source"
    group_id: Optional[str] = None
    active: bool = True
    source_type: str = "Webcam"
    sub_configs: Dict[str, Any] = field(default_factory=dict)

    @property
    def active_config(self) -> Any:
        return self.sub_configs[self.source_type]

    def get_sub_config(self, source_type: str) -> Optional[Any]:
        return self.sub_configs.get(source_type)

    def set_sub_config(self, source_type: str, config: Any):
        self.sub_configs[source_type] = config

    @property
    def implicit_group_id(self) -> str:
        return self.group_id if self.group_id is not None else self.id
