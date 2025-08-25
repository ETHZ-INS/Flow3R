# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PoseEstimationConfigurationDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QToolButton, QVBoxLayout, QWidget)

class Ui_PoseEstimationConfigurationDialog(object):
    def setupUi(self, PoseEstimationConfigurationDialog):
        if not PoseEstimationConfigurationDialog.objectName():
            PoseEstimationConfigurationDialog.setObjectName(u"PoseEstimationConfigurationDialog")
        PoseEstimationConfigurationDialog.resize(453, 369)
        self.verticalLayout = QVBoxLayout(PoseEstimationConfigurationDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_4 = QLabel(PoseEstimationConfigurationDialog)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout.addWidget(self.label_4)

        self.frm_pose_estimation = QFrame(PoseEstimationConfigurationDialog)
        self.frm_pose_estimation.setObjectName(u"frm_pose_estimation")
        self.frm_pose_estimation.setFrameShape(QFrame.StyledPanel)
        self.frm_pose_estimation.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frm_pose_estimation)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.frm_pose_estimation)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.dpd_model = QComboBox(self.frm_pose_estimation)
        self.dpd_model.addItem("")
        self.dpd_model.setObjectName(u"dpd_model")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.dpd_model)

        self.line = QFrame(self.frm_pose_estimation)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.formLayout.setWidget(1, QFormLayout.SpanningRole, self.line)

        self.dpd_select_model = QComboBox(self.frm_pose_estimation)
        self.dpd_select_model.addItem("")
        self.dpd_select_model.setObjectName(u"dpd_select_model")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.dpd_select_model)

        self.label_2 = QLabel(self.frm_pose_estimation)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_2)

        self.dpd_device = QComboBox(self.frm_pose_estimation)
        self.dpd_device.addItem("")
        self.dpd_device.setObjectName(u"dpd_device")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.dpd_device)

        self.label_6 = QLabel(self.frm_pose_estimation)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_6)


        self.verticalLayout.addWidget(self.frm_pose_estimation)

        self.frame_3 = QFrame(PoseEstimationConfigurationDialog)
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
        self.btn_add_model = QPushButton(self.frame_3)
        self.btn_add_model.setObjectName(u"btn_add_model")

        self.horizontalLayout_2.addWidget(self.btn_add_model)

        self.btn_remove_model = QPushButton(self.frame_3)
        self.btn_remove_model.setObjectName(u"btn_remove_model")

        self.horizontalLayout_2.addWidget(self.btn_remove_model)


        self.verticalLayout.addWidget(self.frame_3)

        self.label_5 = QLabel(PoseEstimationConfigurationDialog)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout.addWidget(self.label_5)

        self.frame = QFrame(PoseEstimationConfigurationDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.formLayout_2 = QFormLayout(self.frame)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.chb_save_file = QCheckBox(self.frame)
        self.chb_save_file.setObjectName(u"chb_save_file")
        self.chb_save_file.setChecked(True)

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.chb_save_file)

        self.frm_pylon_config_file_2 = QFrame(self.frame)
        self.frm_pylon_config_file_2.setObjectName(u"frm_pylon_config_file_2")
        self.frm_pylon_config_file_2.setFrameShape(QFrame.NoFrame)
        self.frm_pylon_config_file_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frm_pylon_config_file_2)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.txt_save_file = QLineEdit(self.frm_pylon_config_file_2)
        self.txt_save_file.setObjectName(u"txt_save_file")

        self.horizontalLayout_4.addWidget(self.txt_save_file)

        self.btn_select_save_file = QToolButton(self.frm_pylon_config_file_2)
        self.btn_select_save_file.setObjectName(u"btn_select_save_file")

        self.horizontalLayout_4.addWidget(self.btn_select_save_file)


        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.frm_pylon_config_file_2)


        self.verticalLayout.addWidget(self.frame)

        self.label_3 = QLabel(PoseEstimationConfigurationDialog)
        self.label_3.setObjectName(u"label_3")
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.label_3)

        self.lbl_tracked_instance_types = QLabel(PoseEstimationConfigurationDialog)
        self.lbl_tracked_instance_types.setObjectName(u"lbl_tracked_instance_types")

        self.verticalLayout.addWidget(self.lbl_tracked_instance_types)

        self.buttonbox = QDialogButtonBox(PoseEstimationConfigurationDialog)
        self.buttonbox.setObjectName(u"buttonbox")
        self.buttonbox.setOrientation(Qt.Horizontal)
        self.buttonbox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonbox)


        self.retranslateUi(PoseEstimationConfigurationDialog)
        self.buttonbox.accepted.connect(PoseEstimationConfigurationDialog.accept)
        self.buttonbox.rejected.connect(PoseEstimationConfigurationDialog.reject)

        QMetaObject.connectSlotsByName(PoseEstimationConfigurationDialog)
    # setupUi

    def retranslateUi(self, PoseEstimationConfigurationDialog):
        PoseEstimationConfigurationDialog.setWindowTitle(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Configure Pose Estimation", None))
        self.label_4.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Pose Estimation Models", None))
        self.label.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Model:", None))
        self.dpd_model.setItemText(0, QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Bohacek Lab Mouse Model", None))

        self.dpd_select_model.setItemText(0, QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Bohacek Lab Mouse Model", None))

        self.label_2.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Computation Device:", None))
        self.dpd_device.setItemText(0, QCoreApplication.translate("PoseEstimationConfigurationDialog", u"CPU", None))

        self.label_6.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Select Model:", None))
        self.btn_add_model.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Add Model", None))
        self.btn_remove_model.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Remove Model", None))
        self.label_5.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Results", None))
        self.chb_save_file.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Save to file:", None))
        self.txt_save_file.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"{base_folder}/{recording_name}/{camera_name}_pose_results.csv", None))
        self.btn_select_save_file.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"...", None))
        self.label_3.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Tracked Instance Types:", None))
        self.lbl_tracked_instance_types.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"mouse_top", None))
    # retranslateUi

