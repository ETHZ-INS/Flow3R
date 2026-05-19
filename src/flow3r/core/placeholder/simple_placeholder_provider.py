from typing import Any, Dict

from flow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider


class SimplePlaceholderProvider(IPlaceholderProvider):
    def __init__(self, values: Dict[str, Any]):
        self._values = values

    def get_placeholder_values(self) -> Dict[str, Any]:
        return self._values
