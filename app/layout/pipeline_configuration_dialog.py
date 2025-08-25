# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PipelineConfigurationDialog.ui'
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
    QGridLayout, QLabel, QSizePolicy, QSpacerItem,
    QToolButton, QVBoxLayout, QWidget)

class Ui_PipelineConfigurationDialog(object):
    def setupUi(self, PipelineConfigurationDialog):
        if not PipelineConfigurationDialog.objectName():
            PipelineConfigurationDialog.setObjectName(u"PipelineConfigurationDialog")
        PipelineConfigurationDialog.resize(357, 309)
        self.verticalLayout = QVBoxLayout(PipelineConfigurationDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frm_camera_configuration = QFrame(PipelineConfigurationDialog)
        self.frm_camera_configuration.setObjectName(u"frm_camera_configuration")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frm_camera_configuration.sizePolicy().hasHeightForWidth())
        self.frm_camera_configuration.setSizePolicy(sizePolicy)
        self.frm_camera_configuration.setFrameShape(QFrame.StyledPanel)
        self.frm_camera_configuration.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frm_camera_configuration)
        self.formLayout.setObjectName(u"formLayout")
        self.label_4 = QLabel(self.frm_camera_configuration)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.dpd_camera = QComboBox(self.frm_camera_configuration)
        self.dpd_camera.addItem("")
        self.dpd_camera.addItem("")
        self.dpd_camera.setObjectName(u"dpd_camera")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.dpd_camera)


        self.verticalLayout.addWidget(self.frm_camera_configuration)

        self.frame = QFrame(PipelineConfigurationDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.frame)
        self.gridLayout.setObjectName(u"gridLayout")
        self.btn_configure_save_video = QToolButton(self.frame)
        self.btn_configure_save_video.setObjectName(u"btn_configure_save_video")

        self.gridLayout.addWidget(self.btn_configure_save_video, 0, 1, 1, 1)

        self.btn_configure_pose_estimation = QToolButton(self.frame)
        self.btn_configure_pose_estimation.setObjectName(u"btn_configure_pose_estimation")

        self.gridLayout.addWidget(self.btn_configure_pose_estimation, 1, 1, 1, 1)

        self.chb_grimace = QCheckBox(self.frame)
        self.chb_grimace.setObjectName(u"chb_grimace")

        self.gridLayout.addWidget(self.chb_grimace, 4, 0, 1, 1)

        self.chb_pose_estimation = QCheckBox(self.frame)
        self.chb_pose_estimation.setObjectName(u"chb_pose_estimation")

        self.gridLayout.addWidget(self.chb_pose_estimation, 1, 0, 1, 1)

        self.chb_save_video = QCheckBox(self.frame)
        self.chb_save_video.setObjectName(u"chb_save_video")
        self.chb_save_video.setChecked(True)

        self.gridLayout.addWidget(self.chb_save_video, 0, 0, 1, 1)

        self.btn_configure_grimace = QToolButton(self.frame)
        self.btn_configure_grimace.setObjectName(u"btn_configure_grimace")

        self.gridLayout.addWidget(self.btn_configure_grimace, 4, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 5, 0, 1, 1)

        self.btn_configure_live_heatmap = QToolButton(self.frame)
        self.btn_configure_live_heatmap.setObjectName(u"btn_configure_live_heatmap")

        self.gridLayout.addWidget(self.btn_configure_live_heatmap, 2, 1, 1, 1)

        self.chb_live_heatmap = QCheckBox(self.frame)
        self.chb_live_heatmap.setObjectName(u"chb_live_heatmap")

        self.gridLayout.addWidget(self.chb_live_heatmap, 2, 0, 1, 1)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 2, 2, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 2, 1, 1)

        self.chb_welfare_analysis = QCheckBox(self.frame)
        self.chb_welfare_analysis.setObjectName(u"chb_welfare_analysis")

        self.gridLayout.addWidget(self.chb_welfare_analysis, 3, 0, 1, 1)

        self.btn_configure_welfare_analysis = QToolButton(self.frame)
        self.btn_configure_welfare_analysis.setObjectName(u"btn_configure_welfare_analysis")

        self.gridLayout.addWidget(self.btn_configure_welfare_analysis, 3, 1, 1, 1)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 3, 2, 1, 1)


        self.verticalLayout.addWidget(self.frame)

        self.buttonBox = QDialogButtonBox(PipelineConfigurationDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(PipelineConfigurationDialog)
        self.buttonBox.accepted.connect(PipelineConfigurationDialog.accept)
        self.buttonBox.rejected.connect(PipelineConfigurationDialog.reject)

        QMetaObject.connectSlotsByName(PipelineConfigurationDialog)
    # setupUi

    def retranslateUi(self, PipelineConfigurationDialog):
        PipelineConfigurationDialog.setWindowTitle(QCoreApplication.translate("PipelineConfigurationDialog", u"Configure Processing Steps", None))
        self.label_4.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"Camera:", None))
        self.dpd_camera.setItemText(0, QCoreApplication.translate("PipelineConfigurationDialog", u"Camera 1", None))
        self.dpd_camera.setItemText(1, QCoreApplication.translate("PipelineConfigurationDialog", u"Camera 2", None))

        self.btn_configure_save_video.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"...", None))
        self.btn_configure_pose_estimation.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"...", None))
        self.chb_grimace.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"Grimace Scoring", None))
        self.chb_pose_estimation.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"Pose Estimation", None))
        self.chb_save_video.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"Save Video File", None))
        self.btn_configure_grimace.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"...", None))
        self.btn_configure_live_heatmap.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"...", None))
        self.chb_live_heatmap.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"Live Heatmap", None))
        self.label.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"Requires: Pose Estimation", None))
        self.chb_welfare_analysis.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"Welfare Analysis", None))
        self.btn_configure_welfare_analysis.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"...", None))
        self.label_2.setText(QCoreApplication.translate("PipelineConfigurationDialog", u"Requires: Pose Estimation", None))
    # retranslateUi

