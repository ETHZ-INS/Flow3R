from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

import reactivex as rx
from reactivex.disposable import Disposable

from aaaflow3r.core.streaming.abc.transform import Transform

TDescIn = TypeVar("TDescIn")
TDataIn = TypeVar("TDataIn")
TDescOut = TypeVar("TDescOut")
TDataOut = TypeVar("TDataOut")


class FinalizeTransform(Transform[TDescIn, TDataIn, TDescOut, TDataOut], ABC):
    """
    Specialized transform:
      - processes each input item (side effects / accumulation)
      - emits exactly one output item when input completes
      - then completes

    Optional: can also finalize on disposal.
    """

    def __init__(self, *, finalize_on_dispose: bool = False):
        super().__init__()
        self._finalize_on_dispose = finalize_on_dispose

    def begin(self, desc_in: TDescIn) -> None:
        """Optional hook: run after setup(desc_in) but before first item. Default no-op."""
        return None

    @abstractmethod
    def on_item(self, item: TDataIn) -> None:
        """Called for each input item."""
        ...

    @abstractmethod
    def finalize(self) -> TDataOut:
        """Called once when upstream completes (or on dispose if enabled). Must return exactly one output."""
        ...

    def on_upstream_error(self, exc: Exception) -> None:
        """Optional hook on upstream error (default no-op)."""
        return None

    def transform_observable(self, obs: rx.Observable[TDataIn]) -> rx.Observable[TDataOut]:
        finalize_on_dispose = self._finalize_on_dispose

        def factory(observer, _sched=None):
            closed = False
            done = False
            sub = None

            def emit_once_and_complete():
                nonlocal done
                if done:
                    return
                done = True
                try:
                    result = self.finalize()
                    observer.on_next(result)
                    observer.on_completed()
                except Exception as exc:
                    observer.on_error(exc)

            def cleanup_inner():
                nonlocal closed, sub
                if closed:
                    return
                closed = True
                if sub is not None:
                    sub.dispose()

                if finalize_on_dispose:
                    emit_once_and_complete()

            def _on_next(x: TDataIn):
                if closed:
                    return
                try:
                    self.on_item(x)
                except Exception as exc:
                    # propagate error; do not emit result
                    observer.on_error(exc)
                    cleanup_inner()

            def _on_error(exc: Exception):
                try:
                    self.on_upstream_error(exc)
                finally:
                    observer.on_error(exc)
                    cleanup_inner()

            def _on_completed():
                try:
                    emit_once_and_complete()
                finally:
                    cleanup_inner()

            sub = obs.subscribe(_on_next, _on_error, _on_completed)
            return Disposable(cleanup_inner)

        return rx.create(factory)
