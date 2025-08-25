from concurrent.futures import Future
from threading import Event
from typing import TypeVar, Generic, Callable

from PySide6.QtCore import QObject, QThread, QTimer

T = TypeVar("T")


class _ThreadBoundCallable(Generic[T]):
    def __init__(self, obj: QObject, func: Callable[..., T], timeout_ms: int | None):
        self._obj = obj
        self._func = func
        self._timeout_ms = timeout_ms

    # implicit "run": returns the raw result, blocks cross-thread
    def __call__(self, *args, **kwargs) -> T:
        # same-thread: just call it
        if QThread.currentThread() == self._obj.thread():
            return self._func(self._obj, *args, **kwargs)

        done = Event()
        res: dict[str, object] = {"val": None, "err": None}
        destroyed = {"flag": False}

        def on_destroyed(*_):
            destroyed["flag"] = True
            if res["err"] is None:
                res["err"] = RuntimeError(
                    f"{type(self._obj).__name__} was destroyed before {self._func.__name__} ran"
                )
            done.set()

        self._obj.destroyed.connect(on_destroyed)

        def task():
            try:
                res["val"] = self._func(self._obj, *args, **kwargs)
            except Exception as e:
                res["err"] = e
            finally:
                done.set()
                # best-effort cleanup
                try:
                    self._obj.destroyed.disconnect(on_destroyed)
                except Exception:
                    pass

        # queue into receiver's thread; if obj dies, Qt drops this callback
        QTimer.singleShot(0, self._obj, task)

        # block caller thread until done or timeout
        if self._timeout_ms is not None and not done.wait(self._timeout_ms / 1000.0):
            raise TimeoutError(f"{self._func.__name__} timed out after {self._timeout_ms} ms")

        # if we woke up (either completed or destroyed)
        if res["err"] is not None:
            raise res["err"]  # re-raise in caller thread
        return res["val"]  # type: ignore[return-value]

    # explicit async: always returns a Future
    def future(self, *args, **kwargs) -> Future[T]:
        fut: Future[T] = Future()

        ## same-thread: compute immediately and finish the future
        #if QThread.currentThread() == self._obj.thread():
        #    try:
        #        fut.set_result(self._func(self._obj, *args, **kwargs))
        #    except Exception as e:
        #        fut.set_exception(e)
        #    return fut

        def on_destroyed(*_):
            if not fut.done():
                fut.set_exception(RuntimeError(
                    f"{type(self._obj).__name__} was destroyed before {self._func.__name__} ran"
                ))

        self._obj.destroyed.connect(on_destroyed)

        def task():
            try:
                if fut.cancelled():
                    return
                result = self._func(self._obj, *args, **kwargs)
                fut.set_result(result)
            except Exception as e:
                import traceback
                print(f"[thread_bound_callable] error: {e}")
                traceback.print_exc()
                if not fut.done():
                    fut.set_exception(e)
            finally:
                try:
                    self._obj.destroyed.disconnect(on_destroyed)
                except Exception:
                    pass

        QTimer.singleShot(0, self._obj, task)
        return fut


def thread_bound(*, timeout_ms: int | None = None):
    """
    Decorator for QObject instance methods.

    - Call normally: obj.method(...) -> returns raw result.
      If cross-thread, the caller blocks until the result (or timeout).

    - Async path:   obj.method.future(...) -> returns a Future[T].
      If same-thread, it's already completed; otherwise it completes later.

    Notes:
      * The receiver's thread must have a running event loop for cross-thread calls.
      * Blocking in the GUI thread freezes the UI; prefer .future(...) for longer work.
    """
    def decorator(func):
        class _Descriptor:
            __name__ = getattr(func, "__name__", "thread_bound_method")
            __doc__ = func.__doc__
            def __get__(self, obj, objtype=None):
                if obj is None:
                    return func  # access via class
                return _ThreadBoundCallable(obj, func, timeout_ms)
        return _Descriptor()
    return decorator
