from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set

from PySide6.QtCore import QObject, Signal

from flow3r.app.config.app_config import AppConfig


class ConfigChangeError(Exception):
    pass


class ConfigChangeReply(QObject):
    finished = Signal(bool, object)  # ok, error


@dataclass
class Transaction:
    """Wraps a mutable draft config and per-transaction flags.

    Yielded by ``Controller.transaction()``.  Callers edit ``tx.config`` as
    usual and set any flags they need before the ``with`` block exits.
    """

    config: AppConfig

    # Group IDs whose running recordings should also receive the updated
    # recording_duration when it changes in this transaction.
    # Populated by ``edit_group(..., propagate_duration=True)``.
    propagate_duration_group_ids: Set[str] = field(default_factory=set)
