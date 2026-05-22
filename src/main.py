import os
import sys
from importlib.resources import files
from pathlib import Path

import av

from flow3r.core.plugin.plugin import IPlugin

av.logging.set_level(av.logging.ERROR)

# ── Logging must be set up before any other Flow3R imports ────────────────────
from flow3r.logger import setup_logging as _setup_logging
LOCAL_APPDATA = os.environ.get("LOCALAPPDATA")
LOG_DIR = Path(LOCAL_APPDATA) / "ETH3RHub" / "Flow3R" / "logs" if LOCAL_APPDATA else None
_setup_logging(log_dir=LOG_DIR)

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from flow3r.app.api.plugins.plugins import PluginAPI
from flow3r.app.widgets.main_window import MainWindow
from flow3r.plugins.core.plugin import CorePlugin

os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = "-8"
os.environ['PYLON_CAMEMU'] = "2"

PLUGIN_GROUP = "flow3r.plugins"


if __name__ == "__main__":
    import logging
    _startup_logger = logging.getLogger("flow3r")

    project_file = None
    if len(sys.argv) > 1:
        _startup_logger.info("Command line arguments: %s", sys.argv[1:])
        try:
            project_file = Path(sys.argv[1])
        except Exception as e:
            _startup_logger.warning("Failed to parse project file argument: %s", e)
            project_file = None

        if not project_file.is_file():
            _startup_logger.warning("Provided project file %s does not exist or is not a file", project_file)
            project_file = None

    res_folder = files("flow3r.app.res")

    _excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        _startup_logger.critical(
            "Unhandled exception", exc_info=(exctype, value, traceback)
        )
        _excepthook(exctype, value, traceback)

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(res_folder / "flow3r.png")))
    app.setStyleSheet(Path(str(res_folder / "style.qss")).read_text())

    api = PluginAPI()
    loaded_plugins: list[IPlugin] = []

    core_plugin = CorePlugin()
    core_plugin.initialize(api)
    loaded_plugins.append(core_plugin)

    from importlib.metadata import entry_points

    for ep in entry_points(group=PLUGIN_GROUP):
        plugin_cls = ep.load()
        plugin = plugin_cls()

        if not isinstance(plugin, IPlugin):
            raise TypeError(
                f"Entry point {ep.name!r} did not provide an IPlugin instance"
            )

        _startup_logger.info("Loading plugin %s", plugin.name)
        plugin.initialize(api)
        loaded_plugins.append(plugin)

    _startup_logger.info("Flow3R application starting")
    window = MainWindow(api, config_file=project_file)
    window.setWindowTitle("Flow3R")
    window.show()

    exit_code = app.exec()
    _startup_logger.info("Flow3R application exiting (code %d)", exit_code)
    sys.exit(exit_code)
