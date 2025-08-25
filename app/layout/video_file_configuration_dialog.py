# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'VideoFileConfigurationDialog.ui'
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
    QLabel, QLineEdit, QSizePolicy, QToolButton,
    QVBoxLayout, QWidget)

class Ui_VideoFileConfigurationDialog(object):
    def setupUi(self, VideoFileConfigurationDialog):
        if not VideoFileConfigurationDialog.objectName():
            VideoFileConfigurationDialog.setObjectName(u"VideoFileConfigurationDialog")
        VideoFileConfigurationDialog.resize(453, 148)
        self.verticalLayout = QVBoxLayout(VideoFileConfigurationDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(VideoFileConfigurationDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_3)

        self.lbl_filename_preview = QLabel(self.frame)
        self.lbl_filename_preview.setObjectName(u"lbl_filename_preview")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.lbl_filename_preview)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.dpd_codec = QComboBox(self.frame)
        self.dpd_codec.addItem("")
        self.dpd_codec.setObjectName(u"dpd_codec")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.dpd_codec)

        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.txt_filename = QLineEdit(self.frame_2)
        self.txt_filename.setObjectName(u"txt_filename")

        self.horizontalLayout.addWidget(self.txt_filename)

        self.toolButton = QToolButton(self.frame_2)
        self.toolButton.setObjectName(u"toolButton")

        self.horizontalLayout.addWidget(self.toolButton)


        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.frame_2)


        self.verticalLayout.addWidget(self.frame)

        self.buttonbox = QDialogButtonBox(VideoFileConfigurationDialog)
        self.buttonbox.setObjectName(u"buttonbox")
        self.buttonbox.setOrientation(Qt.Horizontal)
        self.buttonbox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonbox)


        self.retranslateUi(VideoFileConfigurationDialog)
        self.buttonbox.accepted.connect(VideoFileConfigurationDialog.accept)
        self.buttonbox.rejected.connect(VideoFileConfigurationDialog.reject)

        QMetaObject.connectSlotsByName(VideoFileConfigurationDialog)
    # setupUi

    def retranslateUi(self, VideoFileConfigurationDialog):
        VideoFileConfigurationDialog.setWindowTitle(QCoreApplication.translate("VideoFileConfigurationDialog", u"Configure Video File", None))
        self.label.setText(QCoreApplication.translate("VideoFileConfigurationDialog", u"Filename:", None))
        self.label_3.setText(QCoreApplication.translate("VideoFileConfigurationDialog", u"Preview:", None))
        self.lbl_filename_preview.setText(QCoreApplication.translate("VideoFileConfigurationDialog", u"C:/Users/Me/Recordings/recording_1/Camera 1.mp4", None))
        self.label_2.setText(QCoreApplication.translate("VideoFileConfigurationDialog", u"Video Codec:", None))
        self.dpd_codec.setItemText(0, QCoreApplication.translate("VideoFileConfigurationDialog", u"FMP4", None))

        self.txt_filename.setText(QCoreApplication.translate("VideoFileConfigurationDialog", u"{base_folder}/{recording_name}/{camera_name}.mp4", None))
        self.toolButton.setText(QCoreApplication.translate("VideoFileConfigurationDialog", u"...", None))
    # retranslateUi

