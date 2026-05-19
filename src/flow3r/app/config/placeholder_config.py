import uuid
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Any, Type, Self, Literal

from flow3r.core.config.abc.config import ConfigBase, ITypedConfig


@dataclass
class PlaceholderConfig(ConfigBase):
    VERSION = 1

    PLACEHOLDER_TYPES: ClassVar[dict] = {
        'text': "Text",
        'folder': "Folder Path",
        'file': "File Path",
    }

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "new_placeholder"
    type: str = 'text'
    label: str = 'New Placeholder'
    is_global: bool = True
    persistence: Literal['session', 'project', 'recording'] = 'session'
    is_constant: bool = False
    constant_value: str = ''
    description: str = ''

    def _to_dict_data(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'label': self.label,
            'is_global': self.is_global,
            'persistence': self.persistence,
            'is_constant': self.is_constant,
            'constant_value': self.constant_value,
            'description': self.description,
        }

    @classmethod
    def _from_dict_data(cls, data: Dict[str, Any], type_registry: Dict[str, Type[ITypedConfig]]) -> Self:
        return cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            label=data['label'],
            is_global=data['is_global'],
            persistence=data.get('persistence', 'session'),
            is_constant=data['is_constant'],
            constant_value=data['constant_value'],
            description=data['description'],
        )
