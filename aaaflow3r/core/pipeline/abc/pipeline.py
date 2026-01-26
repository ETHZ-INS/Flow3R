from typing import Protocol, List, Any, TypeVar

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.streaming.abc.stream import IStream

TConfig = TypeVar("TConfig")


class IPipeline(Protocol[TConfig]):
    def configure(self, app_context: IAppContext, config: TConfig): ...
    def build(self, app_context: IAppContext, sources: List[IStream]) -> Any: ...  # TODO: Decide on return type (interface for start/stop etc.)
    def dispose(self): ...
