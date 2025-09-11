# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'CameraEditDialog.ui'
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
    QSpacerItem, QSpinBox, QToolButton, QVBoxLayout,
    QWidget)

class Ui_CameraEditDialog(object):
    def setupUi(self, CameraEditDialog):
        if not CameraEditDialog.objectName():
            CameraEditDialog.setObjectName(u"CameraEditDialog")
        CameraEditDialog.resize(400, 341)
        self.verticalLayout = QVBoxLayout(CameraEditDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_4 = QLabel(CameraEditDialog)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label_4)

        self.frm_camera_config = QFrame(CameraEditDialog)
        self.frm_camera_config.setObjectName(u"frm_camera_config")
        self.frm_camera_config.setFrameShape(QFrame.StyledPanel)
        self.frm_camera_config.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frm_camera_config)
        self.formLayout.setObjectName(u"formLayout")
        self.label_2 = QLabel(self.frm_camera_config)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.txt_camera_name = QLineEdit(self.frm_camera_config)
        self.txt_camera_name.setObjectName(u"txt_camera_name")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.txt_camera_name)

        self.label = QLabel(self.frm_camera_config)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label)

        self.dpd_group = QComboBox(self.frm_camera_config)
        self.dpd_group.addItem("")
        self.dpd_group.setObjectName(u"dpd_group")
        self.dpd_group.setEditable(False)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.dpd_group)

        self.label_3 = QLabel(self.frm_camera_config)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.dpd_camera_type = QComboBox(self.frm_camera_config)
        self.dpd_camera_type.addItem("")
        self.dpd_camera_type.addItem("")
        self.dpd_camera_type.setObjectName(u"dpd_camera_type")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.dpd_camera_type)

        self.lbl_dpd_pylon_device = QLabel(self.frm_camera_config)
        self.lbl_dpd_pylon_device.setObjectName(u"lbl_dpd_pylon_device")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.lbl_dpd_pylon_device)

        self.dpd_pylon_device = QComboBox(self.frm_camera_config)
        self.dpd_pylon_device.setObjectName(u"dpd_pylon_device")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.dpd_pylon_device)

        self.lbl_spn_webcam_device = QLabel(self.frm_camera_config)
        self.lbl_spn_webcam_device.setObjectName(u"lbl_spn_webcam_device")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.lbl_spn_webcam_device)

        self.spn_webcam_device = QSpinBox(self.frm_camera_config)
        self.spn_webcam_device.setObjectName(u"spn_webcam_device")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.spn_webcam_device)

        self.lbl_frm_video_file = QLabel(self.frm_camera_config)
        self.lbl_frm_video_file.setObjectName(u"lbl_frm_video_file")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.lbl_frm_video_file)

        self.frm_video_file = QFrame(self.frm_camera_config)
        self.frm_video_file.setObjectName(u"frm_video_file")
        self.frm_video_file.setFrameShape(QFrame.NoFrame)
        self.frm_video_file.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frm_video_file)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.lbl_video_file = QLabel(self.frm_video_file)
        self.lbl_video_file.setObjectName(u"lbl_video_file")
        self.lbl_video_file.setMargin(0)
        self.lbl_video_file.setIndent(5)

        self.horizontalLayout_2.addWidget(self.lbl_video_file)

        self.btn_select_video_file = QToolButton(self.frm_video_file)
        self.btn_select_video_file.setObjectName(u"btn_select_video_file")
        icon = QIcon(QIcon.fromTheme(u"folder-open"))
        self.btn_select_video_file.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.btn_select_video_file)


        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.frm_video_file)

        self.label_5 = QLabel(self.frm_camera_config)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_5)

        self.frm_pylon_config_file = QFrame(self.frm_camera_config)
        self.frm_pylon_config_file.setObjectName(u"frm_pylon_config_file")
        self.frm_pylon_config_file.setFrameShape(QFrame.NoFrame)
        self.frm_pylon_config_file.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frm_pylon_config_file)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.lbl_pylon_config_file = QLabel(self.frm_pylon_config_file)
        self.lbl_pylon_config_file.setObjectName(u"lbl_pylon_config_file")
        self.lbl_pylon_config_file.setMargin(0)
        self.lbl_pylon_config_file.setIndent(5)

        self.horizontalLayout_4.addWidget(self.lbl_pylon_config_file)

        self.btn_select_pylon_config_file = QToolButton(self.frm_pylon_config_file)
        self.btn_select_pylon_config_file.setObjectName(u"btn_select_pylon_config_file")
        self.btn_select_pylon_config_file.setIcon(icon)

        self.horizontalLayout_4.addWidget(self.btn_select_pylon_config_file)


        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.frm_pylon_config_file)

        self.btn_test_camera = QPushButton(self.frm_camera_config)
        self.btn_test_camera.setObjectName(u"btn_test_camera")

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.btn_test_camera)


        self.verticalLayout.addWidget(self.frm_camera_config)

        self.lbl_status = QLabel(CameraEditDialog)
        self.lbl_status.setObjectName(u"lbl_status")
        self.lbl_status.setTextFormat(Qt.RichText)

        self.verticalLayout.addWidget(self.lbl_status)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(CameraEditDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(CameraEditDialog)
        self.buttonBox.accepted.connect(CameraEditDialog.accept)
        self.buttonBox.rejected.connect(CameraEditDialog.reject)

        QMetaObject.connectSlotsByName(CameraEditDialog)
    # setupUi

    def retranslateUi(self, CameraEditDialog):
        CameraEditDialog.setWindowTitle(QCoreApplication.translate("CameraEditDialog", u"Dialog", None))
        self.label_4.setText(QCoreApplication.translate("CameraEditDialog", u"### Camera Settings", None))
        self.label_2.setText(QCoreApplication.translate("CameraEditDialog", u"Name:", None))
        self.txt_camera_name.setText(QCoreApplication.translate("CameraEditDialog", u"Camera 1", None))
        self.label.setText(QCoreApplication.translate("CameraEditDialog", u"Group:", None))
        self.dpd_group.setItemText(0, QCoreApplication.translate("CameraEditDialog", u"Individual (Default)", None))

        self.dpd_group.setPlaceholderText("")
        self.label_3.setText(QCoreApplication.translate("CameraEditDialog", u"Camera Type:", None))
        self.dpd_camera_type.setItemText(0, QCoreApplication.translate("CameraEditDialog", u"Pylon", None))
        self.dpd_camera_type.setItemText(1, QCoreApplication.translate("CameraEditDialog", u"Video File", None))

        self.lbl_dpd_pylon_device.setText(QCoreApplication.translate("CameraEditDialog", u"Device:", None))
        self.lbl_spn_webcam_device.setText(QCoreApplication.translate("CameraEditDialog", u"Device:", None))
        self.lbl_frm_video_file.setText(QCoreApplication.translate("CameraEditDialog", u"File:", None))
        self.lbl_video_file.setText(QCoreApplication.translate("CameraEditDialog", u"No file selected", None))
        self.btn_select_video_file.setText(QCoreApplication.translate("CameraEditDialog", u"...", None))
        self.label_5.setText(QCoreApplication.translate("CameraEditDialog", u"Config File:", None))
        self.lbl_pylon_config_file.setText(QCoreApplication.translate("CameraEditDialog", u"No file selected", None))
        self.btn_select_pylon_config_file.setText(QCoreApplication.translate("CameraEditDialog", u"...", None))
        self.btn_test_camera.setText(QCoreApplication.translate("CameraEditDialog", u"Preview", None))
        self.lbl_status.setText("")
    # retranslateUi

