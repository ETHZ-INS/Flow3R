import os
import sys
from pathlib import Path

import av
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


if __name__ == "__main__":
    import logging
    _startup_logger = logging.getLogger("flow3r")

    bundle_dir = Path(getattr(sys, '_MEIPASS', os.getcwd()))
    res_folder = Path(os.path.abspath(os.path.join(bundle_dir, 'flow3r/app/res')))

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
    core_plugin = CorePlugin()
    core_plugin.initialize(api)

    _startup_logger.info("Flow3R application starting")
    window = MainWindow(api)
    window.setWindowTitle("Flow3R")
    window.show()

    exit_code = app.exec()
    _startup_logger.info("Flow3R application exiting (code %d)", exit_code)
    sys.exit(exit_code)
