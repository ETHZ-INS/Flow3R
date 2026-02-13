from PySide6.QtWidgets import QWidget, QSpinBox, QFormLayout

from aaaflow3r.plugins.core.source.audio.microphone.config import MicrophoneSourceConfig


class MicrophoneSourceConfigWidget(QWidget):
    def __init__(self, config: MicrophoneSourceConfig, parent=None):
        super().__init__(parent)

        self.config = config

        self.spn_device = QSpinBox()
        self.spn_device.setRange(0, 1000)
        self.spn_device.setValue(self.config.device_index)

        self.spn_sample_rate = QSpinBox()
        self.spn_sample_rate.setRange(0, 1_000_000)
        self.spn_sample_rate.setValue(self.config.sample_rate)

        self.layout = QFormLayout(self)
        self.layout.addRow("Device", self.spn_device)
        self.layout.addRow("Sample Rate", self.spn_sample_rate)
        self.setLayout(self.layout)

        self.spn_device.valueChanged.connect(self._device_changed)
        self.spn_sample_rate.valueChanged.connect(self._sample_rate_changed)

    def _device_changed(self, value: int):
        self.config.device_index = value

    def _sample_rate_changed(self, value: int):
        self.config.sample_rate = value
