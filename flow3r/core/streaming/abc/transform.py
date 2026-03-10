from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, Protocol

import reactivex as rx
from reactivex import operators as ops
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
    after one-time setup(desc_in).
    """

    @abstractmethod
    def infer_descriptor(self, desc_in: TDescIn) -> TDescOut:
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
        desc1 = stream.descriptor.pipe(
            ops.take(1),
            ops.replay(buffer_size=1),
            ops.ref_count(),
        )

        out_desc = desc1.pipe(
            ops.map(self.infer_descriptor),
            ops.replay(buffer_size=1),
            ops.ref_count(),
        )

        # Gate the data transform until setup completes.
        def data_factory(observer, _sched=None):
            closed = False
            data_sub: Optional[DisposableBase] = None
            desc_sub: Optional[DisposableBase] = None

            def cleanup_once():
                print("cleanup_once")
                nonlocal closed, data_sub, desc_sub
                if closed:
                    return
                closed = True

                if data_sub is not None:
                    data_sub.dispose()
                    data_sub = None
                if desc_sub is not None:
                    desc_sub.dispose()
                    desc_sub = None

                print("cleanup_once almost done")

                try:
                    self.cleanup()
                except Exception:
                    pass

            def on_desc(desc_in: TDescIn):
                nonlocal data_sub
                if closed:
                    return
                try:
                    self.setup(desc_in)
                except Exception as exc:
                    try:
                        observer.on_error(exc)
                    finally:
                        cleanup_once()
                    return

                try:
                    out = self.transform_observable(stream.observable)
                except Exception as exc:
                    try:
                        observer.on_error(exc)
                    finally:
                        cleanup_once()
                    return

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

                data_sub = out.subscribe(_on_next, _on_error, _on_completed)

            def on_desc_error(exc: Exception):
                try:
                    observer.on_error(exc)
                finally:
                    cleanup_once()

            desc_sub = desc1.subscribe(on_desc, on_desc_error)
            return Disposable(cleanup_once)

        out_data = rx.create(data_factory)
        return Stream(descriptor=out_desc, observable=out_data)
