from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QSizePolicy

from flow3r.app.controller.placeholder_resolver import CyclicPlaceholderError, resolve_placeholders
from flow3r.core.placeholder.placeholder_formatter import PlaceholderFormatter


class PlaceholderLabel(QLabel):
    """A QLabel that resolves ``{placeholder}`` tokens in a template string.

    The label never manages its own visibility — that is left to the parent.
    Instead it emits :attr:`content_changed` with ``True`` when there is
    resolved text to display and ``False`` when there is nothing (no service,
    no placeholder tokens, or an empty template).  Parents that want
    auto-hide behaviour can connect::

        label.content_changed.connect(label.setVisible)
    """

    content_changed = Signal(bool)  # True = has content, False = empty / no service

    def __init__(
        self,
        template: str = "",
        prefix: str = "Preview: ",
        service=None,
        parent=None,
    ):
        super().__init__(parent)
        self._template: str = template
        self._prefix: str = prefix
        self._service = None

        # Default styling — matches the existing preview label appearance
        self.setStyleSheet("color: palette(mid); font-size: 10px;")
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        if service is not None:
            self.set_service(service)
        else:
            self._render()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_template(self, template: str) -> None:
        """Set the template string and re-render."""
        self._template = template
        self._render()

    def set_service(self, service) -> None:
        """Connect to an ``IPlaceholderService``.

        Disconnects any previously connected service, connects to
        ``service.changed``, and performs an immediate render using
        ``service.values``.
        """
        self._disconnect_service()
        self._service = service
        if service is not None:
            service.changed.connect(self._on_service_changed)
        self._render()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _disconnect_service(self) -> None:
        if self._service is not None:
            try:
                self._service.changed.disconnect(self._on_service_changed)
            except RuntimeError:
                pass  # already disconnected
            self._service = None

    def _on_service_changed(self) -> None:
        self._render()

    def _render(self) -> None:
        if self._service is None:
            super().setText("")
            self.content_changed.emit(False)
            return

        formatter = PlaceholderFormatter(self._template)
        if not formatter.get_placeholder_names():
            super().setText("")
            self.content_changed.emit(False)
            return

        try:
            resolved = resolve_placeholders(
                {k: str(v) for k, v in self._service.values.items()},
                on_missing="keep",
            )
        except CyclicPlaceholderError:
            resolved = {k: str(v) for k, v in self._service.values.items()}

        preview = formatter.format(**resolved)
        super().setText(f"{self._prefix}{preview}")
        self.content_changed.emit(True)

