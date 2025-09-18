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
    QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
    QWidget)

from app.widgets.variable_text_widget import VariableTextWidget

class Ui_PoseEstimationConfigurationDialog(object):
    def setupUi(self, PoseEstimationConfigurationDialog):
        if not PoseEstimationConfigurationDialog.objectName():
            PoseEstimationConfigurationDialog.setObjectName(u"PoseEstimationConfigurationDialog")
        PoseEstimationConfigurationDialog.resize(453, 143)
        self.verticalLayout = QVBoxLayout(PoseEstimationConfigurationDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_4 = QLabel(PoseEstimationConfigurationDialog)
        self.label_4.setObjectName(u"label_4")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label_4)

        self.frm_configuration = QFrame(PoseEstimationConfigurationDialog)
        self.frm_configuration.setObjectName(u"frm_configuration")
        self.frm_configuration.setFrameShape(QFrame.StyledPanel)
        self.frm_configuration.setFrameShadow(QFrame.Raised)
        self.formLayout_2 = QFormLayout(self.frm_configuration)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.chb_save_file = QCheckBox(self.frm_configuration)
        self.chb_save_file.setObjectName(u"chb_save_file")
        self.chb_save_file.setChecked(True)

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.chb_save_file)

        self.frm_pylon_config_file_2 = QFrame(self.frm_configuration)
        self.frm_pylon_config_file_2.setObjectName(u"frm_pylon_config_file_2")
        self.frm_pylon_config_file_2.setFrameShape(QFrame.NoFrame)
        self.frm_pylon_config_file_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frm_pylon_config_file_2)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.txt_save_file = VariableTextWidget(self.frm_pylon_config_file_2)
        self.txt_save_file.setObjectName(u"txt_save_file")

        self.horizontalLayout_4.addWidget(self.txt_save_file)


        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.frm_pylon_config_file_2)

        self.label = QLabel(self.frm_configuration)
        self.label.setObjectName(u"label")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label)

        self.dpd_preset = QComboBox(self.frm_configuration)
        self.dpd_preset.addItem("")
        self.dpd_preset.setObjectName(u"dpd_preset")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.dpd_preset)


        self.verticalLayout.addWidget(self.frm_configuration)

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
        self.label_4.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"### Pose Estimation Settings", None))
        self.chb_save_file.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Save to file:", None))
        self.txt_save_file.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"pose_results.csv", None))
        self.label.setText(QCoreApplication.translate("PoseEstimationConfigurationDialog", u"Preset:", None))
        self.dpd_preset.setItemText(0, QCoreApplication.translate("PoseEstimationConfigurationDialog", u"EPM", None))

    # retranslateUi

