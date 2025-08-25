from dataclasses import field, dataclass
from typing import Any, ClassVar

from app.config.config_base import ConfigBase


@dataclass
class VariableConfig(ConfigBase):
    VARIABLE_TYPES: ClassVar[dict] = {
        'int': "Integer",
        'decimal': "Decimal",
        'text': "Text",
        'bool': "Checkbox",
        'duration': "Duration",
        'folder': "Folder Path",
        'file': "File Path",
        'choice': "Choice (Dropdown)"
    }

    variable_name: str
    variable_type: str = 'text'
    persistent: bool = False
    default_value: Any = None
    description: str = ''
    choice_values: list = field(default_factory=list)

    def _extra_to_dict(self) -> dict:
        return {
            "variable_name": self.variable_name,
            "variable_type": self.variable_type,
            "persistent": self.persistent,
            "default_value": self.default_value,
            "description": self.description,
            "choice_values": self.choice_values
        }

    @classmethod
    def _extra_from_dict(cls, data: dict) -> dict:
        return {
            "variable_name": data["variable_name"],
            "variable_type": data.get("variable_type", cls.variable_type),
            "persistent": data.get("persistent", cls.persistent),
            "default_value": data.get("default_value", cls.default_value),
            "description": data.get("description", cls.description),
            "choice_values": data.get("choice_values") or []
        }


class VariableConfigList(ConfigBase):
    variables: dict = {}

    def _extra_to_dict(self) -> dict:
        return {
            "variables": {var_name: var.to_dict() for var_name, var in self.variables.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data: dict) -> dict:
        return {
            "variables": {var_name: VariableConfig.from_dict(var_data) for var_name, var_data in data.get("variables", {}).items()}
        }
