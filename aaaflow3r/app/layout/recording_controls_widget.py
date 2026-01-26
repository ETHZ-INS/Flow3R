# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'RecordingControlsWidget.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_RecordingControlsWidget(object):
    def setupUi(self, RecordingControlsWidget):
        if not RecordingControlsWidget.objectName():
            RecordingControlsWidget.setObjectName(u"RecordingControlsWidget")
        RecordingControlsWidget.resize(519, 81)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RecordingControlsWidget.sizePolicy().hasHeightForWidth())
        RecordingControlsWidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(RecordingControlsWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbl_group_name = QLabel(RecordingControlsWidget)
        self.lbl_group_name.setObjectName(u"lbl_group_name")
        sizePolicy.setHeightForWidth(self.lbl_group_name.sizePolicy().hasHeightForWidth())
        self.lbl_group_name.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.lbl_group_name)

        self.frm_preview = QFrame(RecordingControlsWidget)
        self.frm_preview.setObjectName(u"frm_preview")
        sizePolicy.setHeightForWidth(self.frm_preview.sizePolicy().hasHeightForWidth())
        self.frm_preview.setSizePolicy(sizePolicy)
        self.frm_preview.setFrameShape(QFrame.NoFrame)
        self.frm_preview.setFrameShadow(QFrame.Raised)

        self.verticalLayout.addWidget(self.frm_preview)

        self.frm_controls = QFrame(RecordingControlsWidget)
        self.frm_controls.setObjectName(u"frm_controls")
        sizePolicy.setHeightForWidth(self.frm_controls.sizePolicy().hasHeightForWidth())
        self.frm_controls.setSizePolicy(sizePolicy)
        self.frm_controls.setFrameShape(QFrame.NoFrame)
        self.frm_controls.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frm_controls)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_start = QPushButton(self.frm_controls)
        self.btn_start.setObjectName(u"btn_start")
        self.btn_start.setMinimumSize(QSize(80, 25))

        self.horizontalLayout.addWidget(self.btn_start)

        self.lbl_status = QLabel(self.frm_controls)
        self.lbl_status.setObjectName(u"lbl_status")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lbl_status.sizePolicy().hasHeightForWidth())
        self.lbl_status.setSizePolicy(sizePolicy1)
        self.lbl_status.setTextFormat(Qt.RichText)

        self.horizontalLayout.addWidget(self.lbl_status)

        self.lbl_recording_time = QLabel(self.frm_controls)
        self.lbl_recording_time.setObjectName(u"lbl_recording_time")

        self.horizontalLayout.addWidget(self.lbl_recording_time)


        self.verticalLayout.addWidget(self.frm_controls)


        self.retranslateUi(RecordingControlsWidget)

        QMetaObject.connectSlotsByName(RecordingControlsWidget)
    # setupUi

    def retranslateUi(self, RecordingControlsWidget):
        RecordingControlsWidget.setWindowTitle(QCoreApplication.translate("RecordingControlsWidget", u"Frame", None))
        self.lbl_group_name.setText(QCoreApplication.translate("RecordingControlsWidget", u"Recording 1", None))
        self.btn_start.setText(QCoreApplication.translate("RecordingControlsWidget", u"Start", None))
        self.lbl_status.setText(QCoreApplication.translate("RecordingControlsWidget", u"Ready", None))
        self.lbl_recording_time.setText(QCoreApplication.translate("RecordingControlsWidget", u"00:00:00", None))
    # retranslateUi

