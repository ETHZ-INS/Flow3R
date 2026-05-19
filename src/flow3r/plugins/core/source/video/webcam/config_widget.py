from PySide6.QtWidgets import (
    QSpinBox, QFormLayout, QCheckBox, QComboBox, QWidget, QHBoxLayout, QLabel
)

from flow3r.core.widgets.config_widget import IConfigWidget
from flow3r.plugins.core.source.video.webcam.config import (
    WebcamSourceConfig, FrameSizeSetting, FRAME_SIZE_PRESETS
)
from flow3r.plugins.core.util.list_webcams import list_webcams


class WebcamSourceConfigWidget(IConfigWidget):
    def __init__(self, config: WebcamSourceConfig, parent=None):
        super().__init__(parent)

        self.config = config

        webcams = list_webcams()

        self.dpd_device = QComboBox(self)
        for webcam in webcams:
            self.dpd_device.addItem(webcam.name, webcam.path)

        self.chb_grayscale = QCheckBox()
        self.chb_grayscale.setChecked(self.config.grayscale)

        # Frame size dropdown
        self.dpd_frame_size = QComboBox(self)
        self.dpd_frame_size.addItem("Default", FrameSizeSetting.DEFAULT)
        for w, h in FRAME_SIZE_PRESETS:
            self.dpd_frame_size.addItem(f"{w} × {h}", (w, h))
        self.dpd_frame_size.addItem("Custom…", FrameSizeSetting.CUSTOM)

        # Custom size spinboxes (shown only when Custom is selected)
        self.wgt_custom_size = QWidget(self)
        custom_layout = QHBoxLayout(self.wgt_custom_size)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        self.spb_width = QSpinBox()
        self.spb_width.setRange(1, 99999)
        self.spb_width.setSuffix(" px")
        self.spb_height = QSpinBox()
        self.spb_height.setRange(1, 99999)
        self.spb_height.setSuffix(" px")
        custom_layout.addWidget(self.spb_width)
        custom_layout.addWidget(QLabel("×"))
        custom_layout.addWidget(self.spb_height)

        self.layout = QFormLayout(self)
        self.layout.addRow("Device", self.dpd_device)
        self.layout.addRow("Grayscale", self.chb_grayscale)
        self.layout.addRow("Frame Size", self.dpd_frame_size)
        self.layout.addRow("", self.wgt_custom_size)
        self.setLayout(self.layout)

        # Restore state from config
        self._restore_frame_size()

        self.dpd_device.currentTextChanged.connect(self._device_changed)
        self.chb_grayscale.stateChanged.connect(self._grayscale_changed)
        self.dpd_frame_size.currentIndexChanged.connect(self._frame_size_changed)
        self.spb_width.valueChanged.connect(self._custom_size_changed)
        self.spb_height.valueChanged.connect(self._custom_size_changed)

    def _restore_frame_size(self):
        setting = self.config.frame_size_setting
        if setting == FrameSizeSetting.DEFAULT:
            self.dpd_frame_size.setCurrentIndex(0)
        elif setting == FrameSizeSetting.PRESET and self.config.frame_size_preset:
            idx = self.dpd_frame_size.findData(self.config.frame_size_preset)
            if idx >= 0:
                self.dpd_frame_size.setCurrentIndex(idx)
        elif setting == FrameSizeSetting.CUSTOM:
            self.dpd_frame_size.setCurrentIndex(self.dpd_frame_size.count() - 1)
            if self.config.frame_size_custom:
                self.spb_width.setValue(self.config.frame_size_custom[0])
                self.spb_height.setValue(self.config.frame_size_custom[1])
        self._update_custom_visibility()

    def _update_custom_visibility(self):
        data = self.dpd_frame_size.currentData()
        self.wgt_custom_size.setVisible(data == FrameSizeSetting.CUSTOM)

    def get_config(self) -> WebcamSourceConfig:
        return self.config

    def _device_changed(self):
        self.config.device_path = self.dpd_device.currentData()

    def _grayscale_changed(self, value: int):
        self.config.grayscale = value != 0

    def _frame_size_changed(self):
        data = self.dpd_frame_size.currentData()
        if data == FrameSizeSetting.DEFAULT:
            self.config.frame_size_setting = FrameSizeSetting.DEFAULT
            self.config.frame_size_preset = None
        elif data == FrameSizeSetting.CUSTOM:
            self.config.frame_size_setting = FrameSizeSetting.CUSTOM
            self._custom_size_changed()
        else:
            # It's a (w, h) tuple preset
            self.config.frame_size_setting = FrameSizeSetting.PRESET
            self.config.frame_size_preset = data
        self._update_custom_visibility()

    def _custom_size_changed(self):
        self.config.frame_size_custom = (self.spb_width.value(), self.spb_height.value())
