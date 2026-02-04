from __future__ import annotations

from typing import Protocol, TypeVar
import threading

import reactivex as rx
from reactivex import Observable, Observer
from reactivex.disposable import Disposable


TData = TypeVar("TData")


class ISource(Protocol[TData]):
    def open(self) -> None: ...
    def close(self) -> None: ...
    def read(self, timeout: float) -> TData: ...


def source_observable(source: ISource[TData]) -> Observable[TData]:
    read_timeout_s = 0.5  # keep this reasonably small for responsive shutdown

    def _subscribe(observer: Observer[TData], _=None):
        stop = threading.Event()
        done = threading.Event()

        def run():
            try:
                source.open()
            except Exception as ex:
                observer.on_error(ex)
                done.set()
                return

            try:
                while not stop.is_set():
                    try:
                        item = source.read(read_timeout_s)
                        if item is None:
                            raise RuntimeError("Source returned None")
                    except Exception as ex:
                        # If we're stopping, read may throw because the device is tearing down.
                        if not stop.is_set():
                            observer.on_error(ex)
                        break

                    if stop.is_set():
                        break

                    observer.on_next(item)

                observer.on_completed()

            finally:
                try:
                    source.close()
                except Exception:
                    pass
                done.set()

        t = threading.Thread(target=run, daemon=True)
        t.start()

        def dispose():
            stop.set()
            # Wait for the acquisition thread to exit so close happens after read returns.
            # Because read uses a timeout, this should be quick.
            done.wait(timeout=1.0)

        return Disposable(dispose)

    return rx.create(_subscribe)
