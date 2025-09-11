from dataclasses import dataclass, field


class RecordingStateBase:
    pass

class RecordingState:
    @dataclass
    class Running(RecordingStateBase): ...

    @dataclass
    class Ready(RecordingStateBase): ...

    @dataclass
    class NotReady(RecordingStateBase):
        reason: str = "Not ready"

    @dataclass
    class Error(RecordingStateBase):
        message: str = "Error"

    @dataclass
    class MissingInfo(NotReady):
        message: str = "Missing info"
        missing_placeholders: list = field(default_factory=list)

    @dataclass
    class InvalidPlaceholders(Error):
        message: str = "Invalid placeholders"
        invalid_placeholders: list = field(default_factory=list)

    @dataclass
    class CircularDependency(Error):
        message: str = "Circular dependency"
