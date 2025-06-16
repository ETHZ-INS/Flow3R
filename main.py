import sys
import os

from PySide6.QtWidgets import QApplication

from app.widgets.welfare_recorder import WelfareRecorder

print(sys.argv)

os.environ["YOLO_VERBOSE"] = "false"
os.environ["PYLON_CAMEMU"] = "2"

app = QApplication(sys.argv)

window = WelfareRecorder()
window.show()

sys.exit(app.exec())
