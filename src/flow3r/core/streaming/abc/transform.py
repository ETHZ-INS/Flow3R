from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Protocol

import reactivex as rx
from reactivex.abc import DisposableBase
from reactivex.disposable import Disposable

from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream

TDescIn = TypeVar("TDescIn")
TDataIn = TypeVar("TDataIn")
TDescOut = TypeVar("TDescOut")
TDataOut = TypeVar("TDataOut")


class ITransform(Protocol[TDescIn, TDataIn, TDescOut, TDataOut]):
    def pipe(self, stream: IStream[TDescIn, TDataIn]) -> Stream[TDescOut, TDataOut]: ...


class Transform(Generic[TDescIn, TDataIn, TDescOut, TDataOut], ABC):
    """
    Transform base that supports arbitrary cardinality:
      Observable[TIn] -> Observable[TOut]

    with a simple, non-reactive format:
      Stream.format: TDescIn

    Lifecycle:
    1. setup(input_format)
    2. infer output format
    3. build transformed observable
    4. cleanup() on completion/error/dispose
    """

    @abstractmethod
    def infer_format(self, desc_in: TDescIn) -> TDescOut:
        ...

    def setup(self, desc_in: TDescIn) -> None:
        return None

    @abstractmethod
    def transform_observable(self, obs: rx.Observable[TDataIn]) -> rx.Observable[TDataOut]:
        """
        Implement the data path as an Rx transform.
        This can batch, drop, expand, reorder, etc.
        """
        ...

    def cleanup(self) -> None:
        return None

    def pipe(self, stream: IStream[TDescIn, TDataIn]) -> Stream[TDescOut, TDataOut]:
        desc_in = stream.format

        try:
            # Perform one-time setup eagerly before data starts flowing.
            self.setup(desc_in)

            # Infer output format eagerly as well.
            out_desc = self.infer_format(desc_in)

            # Build the transformed data observable once.
            out = self.transform_observable(stream.data)
        except Exception as exc:
            out_desc = None
            out = rx.throw(exc)

        def data_factory(observer, _sched=None):
            closed = False
            data_sub: DisposableBase | None = None

            def cleanup_once():
                nonlocal closed, data_sub
                if closed:
                    return
                closed = True

                if data_sub is not None:
                    data_sub.dispose()
                    data_sub = None

                try:
                    self.cleanup()
                except Exception:
                    pass

            def _on_next(x: TDataOut):
                if not closed:
                    observer.on_next(x)

            def _on_error(exc: Exception):
                try:
                    observer.on_error(exc)
                finally:
                    cleanup_once()

            def _on_completed():
                try:
                    observer.on_completed()
                finally:
                    cleanup_once()

            try:
                data_sub = out.subscribe(_on_next, _on_error, _on_completed, scheduler=_sched)
            except Exception as exc:
                try:
                    observer.on_error(exc)
                finally:
                    cleanup_once()

            return Disposable(cleanup_once)

        out_data = rx.create(data_factory)
        return Stream(format=out_desc, data=out_data)
