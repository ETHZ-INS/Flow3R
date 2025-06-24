# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'CameraConfigurationDialog.ui'
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
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QToolButton, QVBoxLayout, QWidget)

class Ui_CameraConfigurationDialog(object):
    def setupUi(self, CameraConfigurationDialog):
        if not CameraConfigurationDialog.objectName():
            CameraConfigurationDialog.setObjectName(u"CameraConfigurationDialog")
        CameraConfigurationDialog.resize(400, 288)
        self.verticalLayout = QVBoxLayout(CameraConfigurationDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(CameraConfigurationDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.dpd_camera = QComboBox(self.frame)
        self.dpd_camera.addItem("")
        self.dpd_camera.addItem("")
        self.dpd_camera.setObjectName(u"dpd_camera")

        self.formLayout.setWidget(0, QFormLayout.SpanningRole, self.dpd_camera)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.txt_camera_name = QLineEdit(self.frame)
        self.txt_camera_name.setObjectName(u"txt_camera_name")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.txt_camera_name)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label)

        self.dpd_group = QComboBox(self.frame)
        self.dpd_group.setObjectName(u"dpd_group")
        self.dpd_group.setEditable(False)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.dpd_group)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_3)

        self.dpd_camera_type = QComboBox(self.frame)
        self.dpd_camera_type.addItem("")
        self.dpd_camera_type.addItem("")
        self.dpd_camera_type.setObjectName(u"dpd_camera_type")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.dpd_camera_type)

        self.lbl_dpd_pylon_device = QLabel(self.frame)
        self.lbl_dpd_pylon_device.setObjectName(u"lbl_dpd_pylon_device")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.lbl_dpd_pylon_device)

        self.dpd_pylon_device = QComboBox(self.frame)
        self.dpd_pylon_device.setObjectName(u"dpd_pylon_device")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.dpd_pylon_device)

        self.lbl_frm_video_file = QLabel(self.frame)
        self.lbl_frm_video_file.setObjectName(u"lbl_frm_video_file")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.lbl_frm_video_file)

        self.frm_video_file = QFrame(self.frame)
        self.frm_video_file.setObjectName(u"frm_video_file")
        self.frm_video_file.setFrameShape(QFrame.StyledPanel)
        self.frm_video_file.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frm_video_file)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.lbl_video_file = QLabel(self.frm_video_file)
        self.lbl_video_file.setObjectName(u"lbl_video_file")
        self.lbl_video_file.setMargin(0)
        self.lbl_video_file.setIndent(5)

        self.horizontalLayout.addWidget(self.lbl_video_file)

        self.btn_select_video_file = QToolButton(self.frm_video_file)
        self.btn_select_video_file.setObjectName(u"btn_select_video_file")

        self.horizontalLayout.addWidget(self.btn_select_video_file)


        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.frm_video_file)


        self.verticalLayout.addWidget(self.frame)

        self.frame_3 = QFrame(CameraConfigurationDialog)
        self.frame_3.setObjectName(u"frame_3")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy)
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btn_add_camera = QPushButton(self.frame_3)
        self.btn_add_camera.setObjectName(u"btn_add_camera")

        self.horizontalLayout_2.addWidget(self.btn_add_camera)

        self.btn_remove_camera = QPushButton(self.frame_3)
        self.btn_remove_camera.setObjectName(u"btn_remove_camera")

        self.horizontalLayout_2.addWidget(self.btn_remove_camera)


        self.verticalLayout.addWidget(self.frame_3)

        self.buttonBox = QDialogButtonBox(CameraConfigurationDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(CameraConfigurationDialog)
        self.buttonBox.accepted.connect(CameraConfigurationDialog.accept)
        self.buttonBox.rejected.connect(CameraConfigurationDialog.reject)

        QMetaObject.connectSlotsByName(CameraConfigurationDialog)
    # setupUi

    def retranslateUi(self, CameraConfigurationDialog):
        CameraConfigurationDialog.setWindowTitle(QCoreApplication.translate("CameraConfigurationDialog", u"Dialog", None))
        self.dpd_camera.setItemText(0, QCoreApplication.translate("CameraConfigurationDialog", u"Camera 1", None))
        self.dpd_camera.setItemText(1, QCoreApplication.translate("CameraConfigurationDialog", u"Camera 2", None))

        self.label_2.setText(QCoreApplication.translate("CameraConfigurationDialog", u"Name:", None))
        self.label.setText(QCoreApplication.translate("CameraConfigurationDialog", u"Group:", None))
        self.dpd_group.setPlaceholderText(QCoreApplication.translate("CameraConfigurationDialog", u"individual", None))
        self.label_3.setText(QCoreApplication.translate("CameraConfigurationDialog", u"Camera Type:", None))
        self.dpd_camera_type.setItemText(0, QCoreApplication.translate("CameraConfigurationDialog", u"Pylon", None))
        self.dpd_camera_type.setItemText(1, QCoreApplication.translate("CameraConfigurationDialog", u"Video File", None))

        self.lbl_dpd_pylon_device.setText(QCoreApplication.translate("CameraConfigurationDialog", u"Device:", None))
        self.lbl_frm_video_file.setText(QCoreApplication.translate("CameraConfigurationDialog", u"File:", None))
        self.lbl_video_file.setText(QCoreApplication.translate("CameraConfigurationDialog", u"No file selected", None))
        self.btn_select_video_file.setText(QCoreApplication.translate("CameraConfigurationDialog", u"...", None))
        self.btn_add_camera.setText(QCoreApplication.translate("CameraConfigurationDialog", u"Add Camera", None))
        self.btn_remove_camera.setText(QCoreApplication.translate("CameraConfigurationDialog", u"Remove Camera", None))
    # retranslateUi

