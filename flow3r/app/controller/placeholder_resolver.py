import re
from typing import Dict, Set

PLACEHOLDER_PATTERN = re.compile(r"{([a-zA-Z_][a-zA-Z0-9_]*)}")


class PlaceholderResolutionError(Exception):
    pass


class MissingPlaceholderError(PlaceholderResolutionError):
    def __init__(self, message: str, placeholder_name: str):
        super().__init__(message)
        self.placeholder_name = placeholder_name


class CyclicPlaceholderError(PlaceholderResolutionError):
    pass


def resolve_placeholders(placeholders: Dict[str, str]) -> Dict[str, str]:
    resolved: Dict[str, str] = {}
    visiting: set[str] = set()

    def resolve_one(name: str) -> str:
        if name in resolved:
            return resolved[name]

        if name in visiting:
            cycle = " -> ".join(list(visiting) + [name])
            raise CyclicPlaceholderError(f"Cyclic reference detected: {cycle}")

        if name not in placeholders:
            raise MissingPlaceholderError(f"Missing placeholder: {name}", name)

        visiting.add(name)
        raw_value = placeholders[name]

        def replace_match(match: re.Match[str]) -> str:
            dependency = match.group(1)
            return resolve_one(dependency)

        final_value = PLACEHOLDER_PATTERN.sub(replace_match, raw_value)

        visiting.remove(name)
        resolved[name] = final_value
        return final_value

    for key in placeholders:
        resolve_one(key)

    return resolved
