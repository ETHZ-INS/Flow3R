from typing import Any

from aaaflow3r.core.streaming.abc.sink import Sink


class DoNothingSink(Sink[Any, Any]):
    def setup(self, desc: Any) -> None:
        pass

    def on_next(self, item: Any) -> None:
        pass

    def cleanup(self) -> None:
        pass