from PySide6.QtWidgets import QWidget, QSpinBox, QFormLayout

from aaaflow3r.plugins.core.source.audio.microphone.config import MicrophoneSourceConfig


class MicrophoneSourceConfigWidget(QWidget):
    def __init__(self, config: MicrophoneSourceConfig, parent=None):
        super().__init__(parent)

        self.config = config

        self.spn_device = QSpinBox()
        self.spn_device.setRange(0, 1000)
        self.spn_device.setValue(self.config.device_index)

        self.layout = QFormLayout(self)
        self.layout.addRow("Device", self.spn_device)
        self.setLayout(self.layout)

        self.spn_device.valueChanged.connect(self._device_changed)

    def _device_changed(self, value: int):
        self.config.device_index = value
