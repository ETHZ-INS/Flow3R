from PySide6.QtCore import QObject, Signal


class ConfigChangeError(Exception):
    pass


class ConfigChangeReply(QObject):
    finished = Signal(bool, object)  # ok, error
