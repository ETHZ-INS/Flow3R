from dataclasses import dataclass, field
from datetime import datetime
from typing import List


class SessionStateBase:
    pass

@dataclass(kw_only=True, frozen=True)
class Started(SessionStateBase):
    start_time: datetime

@dataclass(kw_only=True, frozen=True)
class AcquisitionFinished(SessionStateBase):
    end_time: datetime

@dataclass(kw_only=True, frozen=True)
class Running(Started): pass

@dataclass(kw_only=True, frozen=True)
class FinishingRecording(Running, AcquisitionFinished): pass

@dataclass(kw_only=True, frozen=True)
class FinishingProcessing(Running, AcquisitionFinished):
    processing_progress: float = 1.0

@dataclass(kw_only=True, frozen=True)
class Ready(SessionStateBase): pass
    #existing_files: List[Path] = field(default_factory=list)
    #non_empty_folders: List[Path] = field(default_factory=list)

@dataclass(kw_only=True, frozen=True)
class Finished(Started, AcquisitionFinished): pass

@dataclass(kw_only=True, frozen=True)
class NotReady(SessionStateBase):
    reason: str = "Not ready"

@dataclass(kw_only=True, frozen=True)
class Error(SessionStateBase):
    message: str = "Error"

@dataclass(kw_only=True, frozen=True)
class MissingInfo(NotReady):
    message: str = "Missing info"
    missing_placeholders: list = field(default_factory=list)

@dataclass(kw_only=True, frozen=True)
class ConfigError(Error):
    message: str = "Configuration error"
    location: List[str] = field(default_factory=list)

@dataclass(kw_only=True, frozen=True)
class InvalidPlaceholders(Error):
    message: str = "Invalid placeholders"
    invalid_placeholders: list = field(default_factory=list)

@dataclass(kw_only=True, frozen=True)
class CircularDependency(Error):
    message: str = "Circular dependency"
