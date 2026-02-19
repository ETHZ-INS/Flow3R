from typing import Tuple, Optional, Protocol

from PySide6.QtWidgets import QWidget


class INavigatorService(Protocol):
    def open(self, path: Tuple[str, ...], parent: Optional[QWidget] = None, modal: bool = True) -> None: ...
