import uuid
from dataclasses import field, dataclass
from typing import Any, ClassVar, Dict

from app.config.config_base import ConfigBase


@dataclass
class VariableConfig(ConfigBase):
    VARIABLE_TYPES: ClassVar[dict] = {
        'int': "Integer",
        'decimal': "Decimal Number",
        'text': "Text",
        'bool': "Checkbox",
        'duration': "Duration",
        'folder': "Folder Path",
        'file': "File Path",
        'choice': "Choice (Dropdown)"
    }

    SCOPE_OPTIONS: ClassVar[dict] = {
        "project": "One value for the entire Project",
        "group": "One value per group",
        "camera": "One value per camera"
    }

    PERSISTENCE_OPTIONS: ClassVar[dict] = {
        "forever": "Remember forever (when you save the project)",
        "session": "Remember until the application is closed",
        "recording": "Reset after each recording"
    }

    variable_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    variable_name: str = 'new_variable'
    variable_label: str = 'New Variable'
    variable_type: str = 'text'
    example_value: str = "Hello World"
    scope: str = 'project'
    persistence: str = 'recording'
    show_in_controls: bool = False
    description: str = ''
    choice_values: list = field(default_factory=list)

    def _extra_to_dict(self) -> dict:
        return {
            "variable_id": self.variable_id,
            "variable_name": self.variable_name,
            "variable_label": self.variable_label,
            "variable_type": self.variable_type,
            "example_value": self.example_value,
            "scope": self.scope,
            "persistence": self.persistence,
            "show_in_controls": self.show_in_controls,
            "description": self.description,
            "choice_values": self.choice_values
        }

    @classmethod
    def _extra_from_dict(cls, data: dict) -> dict:
        return {
            "variable_id": data.get("variable_id", uuid.uuid4().hex),
            "variable_name": data["variable_name"],
            "variable_label": data.get("variable_label", cls.variable_label),
            "variable_type": data.get("variable_type", cls.variable_type),
            "example_value": data.get("example_value", cls.example_value),
            "scope": data.get("scope", cls.scope),
            "persistence": data.get("persistence", cls.persistence),
            "show_in_controls": data.get("show_in_controls", cls.show_in_controls),
            "description": data.get("description", cls.description),
            "choice_values": data.get("choice_values") or []
        }


@dataclass
class VariableConfigList(ConfigBase):
    variables: Dict[str, VariableConfig] = field(default_factory=dict)

    def _extra_to_dict(self) -> dict:
        return {
            "variables": {var_name: var.to_dict() for var_name, var in self.variables.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data: dict) -> dict:
        return {
            "variables": {var_name: VariableConfig.from_dict(var_data) for var_name, var_data in data.get("variables", {}).items()}
        }


@dataclass
class VariableValue(ConfigBase):
    variable_id: str
    value: Any = None

    def _extra_to_dict(self) -> dict:
        return {
            "variable_id": self.variable_id,
            "value": self.value
        }

    @classmethod
    def _extra_from_dict(cls, data: dict) -> dict:
        return {
            "variable_id": data["variable_id"],
            "value": data.get("value", None)
        }
