# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PlaceholderEditDialog.ui'
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
    QLabel, QLayout, QLineEdit, QSizePolicy,
    QSpacerItem, QTextEdit, QVBoxLayout, QWidget)

class Ui_PlaceholderEditDialog(object):
    def setupUi(self, PlaceholderEditDialog):
        if not PlaceholderEditDialog.objectName():
            PlaceholderEditDialog.setObjectName(u"PlaceholderEditDialog")
        PlaceholderEditDialog.resize(500, 295)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PlaceholderEditDialog.sizePolicy().hasHeightForWidth())
        PlaceholderEditDialog.setSizePolicy(sizePolicy)
        PlaceholderEditDialog.setMinimumSize(QSize(0, 0))
        PlaceholderEditDialog.setMaximumSize(QSize(16777215, 16777215))
        PlaceholderEditDialog.setModal(False)
        self.verticalLayout = QVBoxLayout(PlaceholderEditDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.label = QLabel(PlaceholderEditDialog)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label)

        self.frm_placeholder_configuration = QFrame(PlaceholderEditDialog)
        self.frm_placeholder_configuration.setObjectName(u"frm_placeholder_configuration")
        self.frm_placeholder_configuration.setFrameShape(QFrame.StyledPanel)
        self.frm_placeholder_configuration.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frm_placeholder_configuration)
        self.formLayout.setObjectName(u"formLayout")
        self.label_3 = QLabel(self.frm_placeholder_configuration)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.txt_name = QLineEdit(self.frm_placeholder_configuration)
        self.txt_name.setObjectName(u"txt_name")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.txt_name)

        self.label_2 = QLabel(self.frm_placeholder_configuration)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.dpd_type = QComboBox(self.frm_placeholder_configuration)
        self.dpd_type.addItem("")
        self.dpd_type.addItem("")
        self.dpd_type.addItem("")
        self.dpd_type.setObjectName(u"dpd_type")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.dpd_type)

        self.lbl_tme_duration = QLabel(self.frm_placeholder_configuration)
        self.lbl_tme_duration.setObjectName(u"lbl_tme_duration")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.lbl_tme_duration)

        self.txt_label = QLineEdit(self.frm_placeholder_configuration)
        self.txt_label.setObjectName(u"txt_label")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.txt_label)

        self.label_4 = QLabel(self.frm_placeholder_configuration)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_4)

        self.chb_global = QCheckBox(self.frm_placeholder_configuration)
        self.chb_global.setObjectName(u"chb_global")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.chb_global)

        self.label_5 = QLabel(self.frm_placeholder_configuration)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_5)

        self.txt_description = QTextEdit(self.frm_placeholder_configuration)
        self.txt_description.setObjectName(u"txt_description")
        self.txt_description.setMinimumSize(QSize(0, 40))

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.txt_description)

        self.label_6 = QLabel(self.frm_placeholder_configuration)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_6)

        self.chb_constant = QCheckBox(self.frm_placeholder_configuration)
        self.chb_constant.setObjectName(u"chb_constant")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.chb_constant)

        self.label_7 = QLabel(self.frm_placeholder_configuration)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_7)

        self.txt_value = QLineEdit(self.frm_placeholder_configuration)
        self.txt_value.setObjectName(u"txt_value")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.txt_value)


        self.verticalLayout.addWidget(self.frm_placeholder_configuration)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.btnbox_buttons = QDialogButtonBox(PlaceholderEditDialog)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(PlaceholderEditDialog)
        self.btnbox_buttons.accepted.connect(PlaceholderEditDialog.accept)
        self.btnbox_buttons.rejected.connect(PlaceholderEditDialog.reject)

        QMetaObject.connectSlotsByName(PlaceholderEditDialog)
    # setupUi

    def retranslateUi(self, PlaceholderEditDialog):
        PlaceholderEditDialog.setWindowTitle(QCoreApplication.translate("PlaceholderEditDialog", u"Configure Group", None))
        self.label.setText(QCoreApplication.translate("PlaceholderEditDialog", u"### Placeholder Settings", None))
        self.label_3.setText(QCoreApplication.translate("PlaceholderEditDialog", u"Name:", None))
        self.txt_name.setText(QCoreApplication.translate("PlaceholderEditDialog", u"new_placeholder", None))
        self.label_2.setText(QCoreApplication.translate("PlaceholderEditDialog", u"Type:", None))
        self.dpd_type.setItemText(0, QCoreApplication.translate("PlaceholderEditDialog", u"Text", None))
        self.dpd_type.setItemText(1, QCoreApplication.translate("PlaceholderEditDialog", u"Folder Path", None))
        self.dpd_type.setItemText(2, QCoreApplication.translate("PlaceholderEditDialog", u"File Path", None))

        self.lbl_tme_duration.setText(QCoreApplication.translate("PlaceholderEditDialog", u"Label:", None))
        self.txt_label.setText(QCoreApplication.translate("PlaceholderEditDialog", u"New Placeholder", None))
        self.label_4.setText(QCoreApplication.translate("PlaceholderEditDialog", u"Global:", None))
        self.chb_global.setText("")
        self.label_5.setText(QCoreApplication.translate("PlaceholderEditDialog", u"Description:", None))
        self.label_6.setText(QCoreApplication.translate("PlaceholderEditDialog", u"Constant:", None))
        self.chb_constant.setText("")
        self.label_7.setText(QCoreApplication.translate("PlaceholderEditDialog", u"Value:", None))
    # retranslateUi

