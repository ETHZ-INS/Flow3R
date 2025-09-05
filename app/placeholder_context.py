from dataclasses import dataclass, field
from typing import Dict, Any, List

from app.config.variable_config import VariableConfig
from app.placeholder_formatter import PlaceholderFormatter


@dataclass
class ResolvedValue:
    value: Any = None
    is_set: bool = False
    missing_dependencies: List[str] = field(default_factory=list)
    circular_dependencies: bool = False


class PlaceholderContext:
    def __init__(self, values: Dict[str, Any]):
        self._values = values
        self._resolved = {}

    def dependencies(self, var_name: str, path: List[str] = None) -> set[str]:
        if path is None:
            path = []

        if var_name in path:
            return set()

        if var_name not in self._values or self._values[var_name] is None:
            return set()

        dependencies = set()

        var_value = self._values[var_name]
        if isinstance(var_value, str):
            template = PlaceholderFormatter(var_value)
            direct_dependencies = template.get_placeholders()
            dependencies.update(direct_dependencies)
            for dep in direct_dependencies:
                dependencies.update(self.dependencies(dep, path + [var_name]))

        return dependencies

    def resolve(self, var_name: str, path: List[str] = None):
        if path is None:
            path = []

        if var_name in self._resolved:
            return self._resolved[var_name]

        if var_name in path:
            self._resolved[var_name] = ResolvedValue(circular_dependencies=True)
            return self._resolved[var_name]

        if var_name not in self._values or self._values[var_name] is None:
            self._resolved[var_name] = ResolvedValue(is_set=False)
            return self._resolved[var_name]

        var_value = self._values[var_name]
        missing_dependencies = []
        if isinstance(var_value, str):
            template = PlaceholderFormatter(var_value)
            dependencies = template.get_placeholders()

            if dependencies:
                dependency_values = {dep: self.resolve(dep, path + [var_name]) for dep in dependencies}

                if any(val.circular_dependencies for val in dependency_values.values()):
                    self._resolved[var_name] = ResolvedValue(circular_dependencies=True)
                    return self._resolved[var_name]

                missing_dependencies = [dep for dep, val in dependency_values.items() if not val.is_set]
                missing_dependencies += [dep for val in dependency_values.values() for dep in val.missing_dependencies if dep not in missing_dependencies]
                var_value = template.format(**{dep: val.value for dep, val in dependency_values.items() if val.is_set})

        self._resolved[var_name] = ResolvedValue(value=var_value, is_set=True, missing_dependencies=missing_dependencies)
        return self._resolved[var_name]

    def format(self, value: str) -> str:
        template = PlaceholderFormatter(value)
        dependencies = template.get_placeholders()
        dependency_values = {dep: self.resolve(dep) for dep in dependencies if dep in self._values}
        return template.format(**{dep: val.value for dep, val in dependency_values.items() if val.is_set})