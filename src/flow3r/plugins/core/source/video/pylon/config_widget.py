from typing import List

from PySide6.QtWidgets import QFormLayout, QComboBox
from pypylon import pylon

from flow3r.core.widgets.config_widget import IConfigWidget
from flow3r.core.widgets.path_input import PathWidget
from flow3r.plugins.core.source.video.pylon.config import PylonCameraSourceConfig


def get_available_pylon_devices() -> List[str]:
    devices = list(pylon.TlFactory.GetInstance().EnumerateDevices())
    return [device.GetSerialNumber() for device in devices]


class PylonCameraSourceConfigWidget(IConfigWidget):
    def __init__(self, config: PylonCameraSourceConfig, parent=None):
        super().__init__(parent)

        self.config = config

        self.dpd_device = QComboBox(self)
        available_cameras = get_available_pylon_devices()
        self.dpd_device.addItem("")  # Add empty option for no selection
        for camera in available_cameras:
            self.dpd_device.addItem(camera)
        self.dpd_device.setCurrentText(self.config.device or "")

        self.txt_config_file = PathWidget(mode="file")
        self.txt_config_file.set_path(self.config.config_file or "")

        self.layout = QFormLayout(self)
        self.layout.addRow("Device", self.dpd_device)
        self.layout.addRow("Config File", self.txt_config_file)
        self.setLayout(self.layout)

        self.dpd_device.currentTextChanged.connect(self._device_changed)
        self.txt_config_file.path_changed.connect(self._config_file_changed)

    def get_config(self) -> PylonCameraSourceConfig:
        return self.config

    def _device_changed(self, value: str):
        self.config.device = value

    def _config_file_changed(self):
        self.config.config_file = self.txt_config_file.get_path() or None
