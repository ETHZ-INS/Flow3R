# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'CameraGroupEditDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDateTimeEdit,
    QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QLabel, QLayout, QLineEdit, QSizePolicy,
    QSpacerItem, QTimeEdit, QVBoxLayout, QWidget)

class Ui_CameraGroupEditDialog(object):
    def setupUi(self, CameraGroupEditDialog):
        if not CameraGroupEditDialog.objectName():
            CameraGroupEditDialog.setObjectName(u"CameraGroupEditDialog")
        CameraGroupEditDialog.resize(400, 177)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(CameraGroupEditDialog.sizePolicy().hasHeightForWidth())
        CameraGroupEditDialog.setSizePolicy(sizePolicy)
        CameraGroupEditDialog.setMinimumSize(QSize(0, 0))
        CameraGroupEditDialog.setMaximumSize(QSize(16777215, 16777215))
        CameraGroupEditDialog.setModal(False)
        self.verticalLayout = QVBoxLayout(CameraGroupEditDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.label = QLabel(CameraGroupEditDialog)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label)

        self.frm_recording_configuration = QFrame(CameraGroupEditDialog)
        self.frm_recording_configuration.setObjectName(u"frm_recording_configuration")
        self.frm_recording_configuration.setFrameShape(QFrame.StyledPanel)
        self.frm_recording_configuration.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frm_recording_configuration)
        self.formLayout.setObjectName(u"formLayout")
        self.label_3 = QLabel(self.frm_recording_configuration)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.txt_recording_name = QLineEdit(self.frm_recording_configuration)
        self.txt_recording_name.setObjectName(u"txt_recording_name")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.txt_recording_name)

        self.label_2 = QLabel(self.frm_recording_configuration)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.dpd_recording_mode = QComboBox(self.frm_recording_configuration)
        self.dpd_recording_mode.addItem("")
        self.dpd_recording_mode.addItem("")
        self.dpd_recording_mode.setObjectName(u"dpd_recording_mode")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.dpd_recording_mode)

        self.lbl_tme_duration = QLabel(self.frm_recording_configuration)
        self.lbl_tme_duration.setObjectName(u"lbl_tme_duration")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.lbl_tme_duration)

        self.tme_duration = QTimeEdit(self.frm_recording_configuration)
        self.tme_duration.setObjectName(u"tme_duration")
        self.tme_duration.setDateTime(QDateTime(QDate(2000, 12, 31), QTime(22, 10, 0)))
        self.tme_duration.setMaximumTime(QTime(23, 59, 0))
        self.tme_duration.setCurrentSection(QDateTimeEdit.HourSection)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.tme_duration)


        self.verticalLayout.addWidget(self.frm_recording_configuration)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.btnbox_buttons = QDialogButtonBox(CameraGroupEditDialog)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(CameraGroupEditDialog)
        self.btnbox_buttons.accepted.connect(CameraGroupEditDialog.accept)
        self.btnbox_buttons.rejected.connect(CameraGroupEditDialog.reject)

        QMetaObject.connectSlotsByName(CameraGroupEditDialog)
    # setupUi

    def retranslateUi(self, CameraGroupEditDialog):
        CameraGroupEditDialog.setWindowTitle(QCoreApplication.translate("CameraGroupEditDialog", u"Configure Recording", None))
        self.label.setText(QCoreApplication.translate("CameraGroupEditDialog", u"### Camera Group Settings", None))
        self.label_3.setText(QCoreApplication.translate("CameraGroupEditDialog", u"Name:", None))
        self.txt_recording_name.setText(QCoreApplication.translate("CameraGroupEditDialog", u"Group 1", None))
        self.label_2.setText(QCoreApplication.translate("CameraGroupEditDialog", u"Recording Mode:", None))
        self.dpd_recording_mode.setItemText(0, QCoreApplication.translate("CameraGroupEditDialog", u"Timed", None))
        self.dpd_recording_mode.setItemText(1, QCoreApplication.translate("CameraGroupEditDialog", u"Manual", None))

        self.lbl_tme_duration.setText(QCoreApplication.translate("CameraGroupEditDialog", u"Duration:", None))
        self.tme_duration.setDisplayFormat(QCoreApplication.translate("CameraGroupEditDialog", u"HH'h' mm'm' ss.zzz's'", None))
    # retranslateUi

