from typing import Protocol, Any, Dict


class IPlaceholderProvider(Protocol):
    def get_placeholder_values(self) -> Dict[str, Any]: ...
