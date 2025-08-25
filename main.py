import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.widgets.main_window import WelfareRecorder

config_file = None
if len(sys.argv) > 1:
    config_file = Path(sys.argv[1])
    if not config_file.exists():
        print(f"Config file {config_file} does not exist.")
        sys.exit(1)

os.environ["YOLO_VERBOSE"] = "false"
os.environ["PYLON_CAMEMU"] = "4"

app = QApplication(sys.argv)

window = WelfareRecorder(config_file)
window.show()

sys.exit(app.exec())
