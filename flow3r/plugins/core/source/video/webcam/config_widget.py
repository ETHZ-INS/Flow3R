from PySide6.QtWidgets import QWidget, QLineEdit, QSpinBox, QFormLayout, QCheckBox

from flow3r.plugins.core.source.video.webcam.config import WebcamSourceConfig


class WebcamSourceConfigWidget(QWidget):
    def __init__(self, config: WebcamSourceConfig, parent=None):
        super().__init__(parent)

        self.config = config

        self.spn_device = QSpinBox()
        self.spn_device.setRange(0, 1000)
        self.spn_device.setValue(self.config.device_index)

        self.chb_grayscale = QCheckBox()
        self.chb_grayscale.setChecked(self.config.grayscale)

        self.layout = QFormLayout(self)
        self.layout.addRow("Device", self.spn_device)
        self.layout.addRow("Grayscale", self.chb_grayscale)
        self.setLayout(self.layout)

        self.spn_device.valueChanged.connect(self._device_changed)
        self.chb_grayscale.stateChanged.connect(self._grayscale_changed)

    def _device_changed(self, value: int):
        self.config.device_index = value

    def _grayscale_changed(self, value: int):
        self.config.grayscale = value != 0
