# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PipelineEditDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QFrame, QGridLayout, QLabel,
    QLineEdit, QSizePolicy, QSpacerItem, QToolButton,
    QVBoxLayout, QWidget)

class Ui_PipelineEditDialog(object):
    def setupUi(self, PipelineEditDialog):
        if not PipelineEditDialog.objectName():
            PipelineEditDialog.setObjectName(u"PipelineEditDialog")
        PipelineEditDialog.resize(357, 261)
        self.verticalLayout = QVBoxLayout(PipelineEditDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_4 = QLabel(PipelineEditDialog)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label_4)

        self.frm_configuration = QFrame(PipelineEditDialog)
        self.frm_configuration.setObjectName(u"frm_configuration")
        self.frm_configuration.setFrameShape(QFrame.StyledPanel)
        self.frm_configuration.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.frm_configuration)
        self.gridLayout.setObjectName(u"gridLayout")
        self.chb_grimace = QCheckBox(self.frm_configuration)
        self.chb_grimace.setObjectName(u"chb_grimace")

        self.gridLayout.addWidget(self.chb_grimace, 5, 0, 1, 1)

        self.btn_configure_save_video = QToolButton(self.frm_configuration)
        self.btn_configure_save_video.setObjectName(u"btn_configure_save_video")

        self.gridLayout.addWidget(self.btn_configure_save_video, 1, 1, 1, 1)

        self.lbl_live_heatmap_hint = QLabel(self.frm_configuration)
        self.lbl_live_heatmap_hint.setObjectName(u"lbl_live_heatmap_hint")

        self.gridLayout.addWidget(self.lbl_live_heatmap_hint, 3, 2, 1, 1)

        self.chb_pose_estimation = QCheckBox(self.frm_configuration)
        self.chb_pose_estimation.setObjectName(u"chb_pose_estimation")

        self.gridLayout.addWidget(self.chb_pose_estimation, 2, 0, 1, 1)

        self.chb_welfare_analysis = QCheckBox(self.frm_configuration)
        self.chb_welfare_analysis.setObjectName(u"chb_welfare_analysis")

        self.gridLayout.addWidget(self.chb_welfare_analysis, 4, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 1, 2, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 6, 0, 1, 1)

        self.btn_configure_grimace = QToolButton(self.frm_configuration)
        self.btn_configure_grimace.setObjectName(u"btn_configure_grimace")

        self.gridLayout.addWidget(self.btn_configure_grimace, 5, 1, 1, 1)

        self.btn_configure_live_heatmap = QToolButton(self.frm_configuration)
        self.btn_configure_live_heatmap.setObjectName(u"btn_configure_live_heatmap")

        self.gridLayout.addWidget(self.btn_configure_live_heatmap, 3, 1, 1, 1)

        self.btn_configure_welfare_analysis = QToolButton(self.frm_configuration)
        self.btn_configure_welfare_analysis.setObjectName(u"btn_configure_welfare_analysis")

        self.gridLayout.addWidget(self.btn_configure_welfare_analysis, 4, 1, 1, 1)

        self.btn_configure_pose_estimation = QToolButton(self.frm_configuration)
        self.btn_configure_pose_estimation.setObjectName(u"btn_configure_pose_estimation")

        self.gridLayout.addWidget(self.btn_configure_pose_estimation, 2, 1, 1, 1)

        self.lbl_welfare_analysis_hint = QLabel(self.frm_configuration)
        self.lbl_welfare_analysis_hint.setObjectName(u"lbl_welfare_analysis_hint")

        self.gridLayout.addWidget(self.lbl_welfare_analysis_hint, 4, 2, 1, 1)

        self.chb_live_heatmap = QCheckBox(self.frm_configuration)
        self.chb_live_heatmap.setObjectName(u"chb_live_heatmap")

        self.gridLayout.addWidget(self.chb_live_heatmap, 3, 0, 1, 1)

        self.chb_save_video = QCheckBox(self.frm_configuration)
        self.chb_save_video.setObjectName(u"chb_save_video")
        self.chb_save_video.setChecked(True)

        self.gridLayout.addWidget(self.chb_save_video, 1, 0, 1, 1)

        self.label_3 = QLabel(self.frm_configuration)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)

        self.txt_name = QLineEdit(self.frm_configuration)
        self.txt_name.setObjectName(u"txt_name")

        self.gridLayout.addWidget(self.txt_name, 0, 1, 1, 2)


        self.verticalLayout.addWidget(self.frm_configuration)

        self.buttonBox = QDialogButtonBox(PipelineEditDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(PipelineEditDialog)
        self.buttonBox.accepted.connect(PipelineEditDialog.accept)
        self.buttonBox.rejected.connect(PipelineEditDialog.reject)

        QMetaObject.connectSlotsByName(PipelineEditDialog)
    # setupUi

    def retranslateUi(self, PipelineEditDialog):
        PipelineEditDialog.setWindowTitle(QCoreApplication.translate("PipelineEditDialog", u"Configure Processing Steps", None))
        self.label_4.setText(QCoreApplication.translate("PipelineEditDialog", u"### Pipeline Settings", None))
        self.chb_grimace.setText(QCoreApplication.translate("PipelineEditDialog", u"Grimace Scoring", None))
        self.btn_configure_save_video.setText(QCoreApplication.translate("PipelineEditDialog", u"...", None))
        self.lbl_live_heatmap_hint.setText(QCoreApplication.translate("PipelineEditDialog", u"Requires: Pose Estimation", None))
        self.chb_pose_estimation.setText(QCoreApplication.translate("PipelineEditDialog", u"Pose Estimation", None))
        self.chb_welfare_analysis.setText(QCoreApplication.translate("PipelineEditDialog", u"Welfare Analysis", None))
        self.btn_configure_grimace.setText(QCoreApplication.translate("PipelineEditDialog", u"...", None))
        self.btn_configure_live_heatmap.setText(QCoreApplication.translate("PipelineEditDialog", u"...", None))
        self.btn_configure_welfare_analysis.setText(QCoreApplication.translate("PipelineEditDialog", u"...", None))
        self.btn_configure_pose_estimation.setText(QCoreApplication.translate("PipelineEditDialog", u"...", None))
        self.lbl_welfare_analysis_hint.setText(QCoreApplication.translate("PipelineEditDialog", u"Requires: Pose Estimation", None))
        self.chb_live_heatmap.setText(QCoreApplication.translate("PipelineEditDialog", u"Live Heatmap", None))
        self.chb_save_video.setText(QCoreApplication.translate("PipelineEditDialog", u"Save Video File", None))
        self.label_3.setText(QCoreApplication.translate("PipelineEditDialog", u"Name:", None))
    # retranslateUi

