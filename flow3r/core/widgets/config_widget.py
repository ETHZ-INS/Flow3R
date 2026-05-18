from abc import abstractmethod
from typing import TypeVar

from PySide6.QtWidgets import QWidget

TConfig = TypeVar("TConfig")


class IConfigWidget(QWidget):
    """Base class for all config widgets.

    Instead of mutating the config object directly, widgets should implement
    ``get_config()`` to return the current config state when requested.
    The dialog calls ``get_config()`` on ``accept()`` to retrieve the result.

    For simple widgets that already mutate the config in real-time, ``get_config()``
    can simply ``return self.config``. For more complex cases (e.g. a text editor
    that deserialises back to a new object), ``get_config()`` can return a freshly
    constructed config without needing to mutate the original.
    """

    @abstractmethod
    def get_config(self) -> object:
        """Return the current config represented by this widget."""
        ...
