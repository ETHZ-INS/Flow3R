import re
from typing import Dict, Literal

PLACEHOLDER_PATTERN = re.compile(r"{([a-zA-Z_][a-zA-Z0-9_]*)}")


class PlaceholderResolutionError(Exception):
    pass


class MissingPlaceholderError(PlaceholderResolutionError):
    def __init__(self, message: str, placeholder_name: str):
        super().__init__(message)
        self.placeholder_name = placeholder_name


class CyclicPlaceholderError(PlaceholderResolutionError):
    pass


def resolve_placeholders(
    placeholders: Dict[str, str],
    *,
    on_missing: Literal["raise", "keep", "empty"] = "raise",
) -> Dict[str, str]:
    """Resolve all ``{name}`` references in *placeholders* values.

    Parameters
    ----------
    placeholders:
        A flat ``{name: raw_value}`` dict where values may themselves contain
        ``{other_name}`` references.
    on_missing:
        What to do when a referenced name has no entry in *placeholders*:

        * ``"raise"`` (default) – raise :exc:`MissingPlaceholderError`.
        * ``"keep"``            – leave the original ``{name}`` token in place.
        * ``"empty"``           – substitute an empty string.

    Raises
    ------
    MissingPlaceholderError
        When *on_missing* is ``"raise"`` and a referenced name is absent.
    CyclicPlaceholderError
        On a circular reference, regardless of *on_missing*.
    """
    resolved: Dict[str, str] = {}
    visiting: set[str] = set()

    def resolve_one(name: str) -> str:
        if name in resolved:
            return resolved[name]

        if name in visiting:
            cycle = " -> ".join(list(visiting) + [name])
            raise CyclicPlaceholderError(f"Cyclic reference detected: {cycle}")

        if name not in placeholders:
            if on_missing == "raise":
                raise MissingPlaceholderError(f"Missing placeholder: {name}", name)
            elif on_missing == "keep":
                return "{" + name + "}"
            else:  # "empty"
                return ""

        visiting.add(name)
        raw_value = placeholders[name]

        def replace_match(match: re.Match[str]) -> str:
            return resolve_one(match.group(1))

        final_value = PLACEHOLDER_PATTERN.sub(replace_match, raw_value)

        visiting.remove(name)
        resolved[name] = final_value
        return final_value

    for key in placeholders:
        resolve_one(key)

    return resolved
