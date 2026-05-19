from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass(kw_only=True, frozen=True)
class SessionStateBase:
    recording_number: int
    duration: Optional[float] = None

@dataclass(kw_only=True, frozen=True)
class Started(SessionStateBase):
    start_time: datetime

@dataclass(kw_only=True, frozen=True)
class AcquisitionFinished:
    stop_time: datetime

@dataclass(kw_only=True, frozen=True)
class ProcessingFinished:
    end_time: datetime

@dataclass(kw_only=True, frozen=True)
class Running(Started): pass

@dataclass(kw_only=True, frozen=True)
class FinishingRecording(Started, AcquisitionFinished): pass

@dataclass(kw_only=True, frozen=True)
class FinishingProcessing(Started, AcquisitionFinished):
    processing_progress: float = 1.0

@dataclass(kw_only=True, frozen=True)
class Ready(SessionStateBase):
    files: List[Path] = field(default_factory=list)
    #non_empty_folders: List[Path] = field(default_factory=list)

@dataclass(kw_only=True, frozen=True)
class StartFailed(SessionStateBase):
    message: str = "Recording could not be started"
    files: List[Path] = field(default_factory=list)

@dataclass(kw_only=True, frozen=True)
class Finished(Started, AcquisitionFinished, ProcessingFinished): pass

@dataclass(kw_only=True, frozen=True)
class NotReady(SessionStateBase):
    reason: str = "Not ready"

@dataclass(kw_only=True, frozen=True)
class Error(SessionStateBase):
    message: str = "Error"

@dataclass(kw_only=True, frozen=True)
class MissingPlaceholder(NotReady):
    message: str = "Missing placeholder"
    placeholder_name: str = ""

@dataclass(kw_only=True, frozen=True)
class ConfigError(Error):
    message: str = "Configuration error"
    location: List[str] = field(default_factory=list)

@dataclass(kw_only=True, frozen=True)
class InvalidPlaceholders(Error):
    message: str = "Invalid placeholders"
    invalid_placeholders: List[str] = field(default_factory=list)

@dataclass(kw_only=True, frozen=True)
class CircularDependency(Error):
    message: str = "Circular dependency"
