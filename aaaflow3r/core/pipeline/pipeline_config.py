import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class PipelineConfig:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Pipeline"
    pipeline_type: str = "Record Video"
    sub_configs: Dict[str, Any] = field(default_factory=dict)

    @property
    def active_config(self) -> Any:
        return self.sub_configs[self.pipeline_type]

    def get_sub_config(self, pipeline_type: str) -> Optional[Any]:
        return self.sub_configs.get(pipeline_type)

    def set_sub_config(self, pipeline_type: str, config: Any):
        self.sub_configs[pipeline_type] = config
