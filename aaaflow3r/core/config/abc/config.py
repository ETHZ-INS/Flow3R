from typing import Protocol


class IConfig(Protocol):
    def is_locked(self, name: str) -> bool: ...
