# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'RecordingConfigurationDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLayout, QLineEdit, QPushButton,
    QSizePolicy, QTimeEdit, QVBoxLayout, QWidget)

class Ui_RecordingConfigurationDialog(object):
    def setupUi(self, RecordingConfigurationDialog):
        if not RecordingConfigurationDialog.objectName():
            RecordingConfigurationDialog.setObjectName(u"RecordingConfigurationDialog")
        RecordingConfigurationDialog.resize(400, 200)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RecordingConfigurationDialog.sizePolicy().hasHeightForWidth())
        RecordingConfigurationDialog.setSizePolicy(sizePolicy)
        RecordingConfigurationDialog.setMinimumSize(QSize(400, 200))
        RecordingConfigurationDialog.setMaximumSize(QSize(400, 200))
        RecordingConfigurationDialog.setModal(False)
        self.verticalLayout = QVBoxLayout(RecordingConfigurationDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.frame = QFrame(RecordingConfigurationDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.dpd_recording = QComboBox(self.frame)
        self.dpd_recording.addItem("")
        self.dpd_recording.setObjectName(u"dpd_recording")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.dpd_recording)

        self.line = QFrame(self.frame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.formLayout.setWidget(1, QFormLayout.SpanningRole, self.line)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_3)

        self.txt_recording_name = QLineEdit(self.frame)
        self.txt_recording_name.setObjectName(u"txt_recording_name")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.txt_recording_name)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_2)

        self.dpd_recording_mode = QComboBox(self.frame)
        self.dpd_recording_mode.addItem("")
        self.dpd_recording_mode.addItem("")
        self.dpd_recording_mode.setObjectName(u"dpd_recording_mode")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.dpd_recording_mode)

        self.lbl_tme_duration = QLabel(self.frame)
        self.lbl_tme_duration.setObjectName(u"lbl_tme_duration")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.lbl_tme_duration)

        self.tme_duration = QTimeEdit(self.frame)
        self.tme_duration.setObjectName(u"tme_duration")
        self.tme_duration.setInputMethodHints(Qt.ImhPreferNumbers|Qt.ImhTime)
        self.tme_duration.setTimeSpec(Qt.LocalTime)
        self.tme_duration.setTime(QTime(0, 10, 0))

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.tme_duration)


        self.verticalLayout.addWidget(self.frame)

        self.frame_3 = QFrame(RecordingConfigurationDialog)
        self.frame_3.setObjectName(u"frame_3")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy1)
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btn_add_recording = QPushButton(self.frame_3)
        self.btn_add_recording.setObjectName(u"btn_add_recording")

        self.horizontalLayout_2.addWidget(self.btn_add_recording)

        self.btn_remove_recording = QPushButton(self.frame_3)
        self.btn_remove_recording.setObjectName(u"btn_remove_recording")

        self.horizontalLayout_2.addWidget(self.btn_remove_recording)


        self.verticalLayout.addWidget(self.frame_3)

        self.btnbox_buttons = QDialogButtonBox(RecordingConfigurationDialog)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(RecordingConfigurationDialog)
        self.btnbox_buttons.accepted.connect(RecordingConfigurationDialog.accept)
        self.btnbox_buttons.rejected.connect(RecordingConfigurationDialog.reject)

        QMetaObject.connectSlotsByName(RecordingConfigurationDialog)
    # setupUi

    def retranslateUi(self, RecordingConfigurationDialog):
        RecordingConfigurationDialog.setWindowTitle(QCoreApplication.translate("RecordingConfigurationDialog", u"Configure Recording", None))
        self.label.setText(QCoreApplication.translate("RecordingConfigurationDialog", u"Camera Group:", None))
        self.dpd_recording.setItemText(0, QCoreApplication.translate("RecordingConfigurationDialog", u"Default", None))

        self.label_3.setText(QCoreApplication.translate("RecordingConfigurationDialog", u"Name:", None))
        self.label_2.setText(QCoreApplication.translate("RecordingConfigurationDialog", u"Recording Mode:", None))
        self.dpd_recording_mode.setItemText(0, QCoreApplication.translate("RecordingConfigurationDialog", u"Timed", None))
        self.dpd_recording_mode.setItemText(1, QCoreApplication.translate("RecordingConfigurationDialog", u"Manual", None))

        self.lbl_tme_duration.setText(QCoreApplication.translate("RecordingConfigurationDialog", u"Duration:", None))
        self.tme_duration.setDisplayFormat(QCoreApplication.translate("RecordingConfigurationDialog", u"HH'h' mm'm' ss.zzz's'", None))
        self.btn_add_recording.setText(QCoreApplication.translate("RecordingConfigurationDialog", u"Add Group", None))
        self.btn_remove_recording.setText(QCoreApplication.translate("RecordingConfigurationDialog", u"Remove Group", None))
    # retranslateUi

