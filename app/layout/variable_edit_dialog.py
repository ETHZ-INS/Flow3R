# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'VariableEditDialog.ui'
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

class Ui_VariableEditDialog(object):
    def setupUi(self, VariableEditDialog):
        if not VariableEditDialog.objectName():
            VariableEditDialog.setObjectName(u"VariableEditDialog")
        VariableEditDialog.resize(400, 359)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(VariableEditDialog.sizePolicy().hasHeightForWidth())
        VariableEditDialog.setSizePolicy(sizePolicy)
        VariableEditDialog.setMinimumSize(QSize(0, 0))
        VariableEditDialog.setMaximumSize(QSize(16777215, 16777215))
        VariableEditDialog.setModal(False)
        self.verticalLayout = QVBoxLayout(VariableEditDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.label = QLabel(VariableEditDialog)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label)

        self.frm_configuration = QFrame(VariableEditDialog)
        self.frm_configuration.setObjectName(u"frm_configuration")
        self.frm_configuration.setFrameShape(QFrame.StyledPanel)
        self.frm_configuration.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frm_configuration)
        self.formLayout.setObjectName(u"formLayout")
        self.label_3 = QLabel(self.frm_configuration)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.txt_name = QLineEdit(self.frm_configuration)
        self.txt_name.setObjectName(u"txt_name")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.txt_name)

        self.label_4 = QLabel(self.frm_configuration)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_4)

        self.txt_label = QLineEdit(self.frm_configuration)
        self.txt_label.setObjectName(u"txt_label")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.txt_label)

        self.label_2 = QLabel(self.frm_configuration)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.dpd_variable_type = QComboBox(self.frm_configuration)
        self.dpd_variable_type.addItem("")
        self.dpd_variable_type.setObjectName(u"dpd_variable_type")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.dpd_variable_type)

        self.label_8 = QLabel(self.frm_configuration)
        self.label_8.setObjectName(u"label_8")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_8)

        self.dpd_scope = QComboBox(self.frm_configuration)
        self.dpd_scope.addItem("")
        self.dpd_scope.addItem("")
        self.dpd_scope.addItem("")
        self.dpd_scope.setObjectName(u"dpd_scope")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.dpd_scope)

        self.label_6 = QLabel(self.frm_configuration)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_6)

        self.dpd_persistence = QComboBox(self.frm_configuration)
        self.dpd_persistence.addItem("")
        self.dpd_persistence.addItem("")
        self.dpd_persistence.addItem("")
        self.dpd_persistence.setObjectName(u"dpd_persistence")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.dpd_persistence)

        self.label_5 = QLabel(self.frm_configuration)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_5)

        self.txt_description = QTextEdit(self.frm_configuration)
        self.txt_description.setObjectName(u"txt_description")
        self.txt_description.setMaximumSize(QSize(16777215, 70))

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.txt_description)

        self.label_7 = QLabel(self.frm_configuration)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_7)

        self.txt_example_value = QLineEdit(self.frm_configuration)
        self.txt_example_value.setObjectName(u"txt_example_value")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.txt_example_value)

        self.label_9 = QLabel(self.frm_configuration)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.label_9)

        self.chb_preview = QCheckBox(self.frm_configuration)
        self.chb_preview.setObjectName(u"chb_preview")

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.chb_preview)


        self.verticalLayout.addWidget(self.frm_configuration)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.btnbox_buttons = QDialogButtonBox(VariableEditDialog)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(VariableEditDialog)
        self.btnbox_buttons.accepted.connect(VariableEditDialog.accept)
        self.btnbox_buttons.rejected.connect(VariableEditDialog.reject)

        QMetaObject.connectSlotsByName(VariableEditDialog)
    # setupUi

    def retranslateUi(self, VariableEditDialog):
        VariableEditDialog.setWindowTitle(QCoreApplication.translate("VariableEditDialog", u"Configure Variable", None))
        self.label.setText(QCoreApplication.translate("VariableEditDialog", u"### Placeholder Settings", None))
        self.label_3.setText(QCoreApplication.translate("VariableEditDialog", u"Name:", None))
        self.txt_name.setText(QCoreApplication.translate("VariableEditDialog", u"animal_id", None))
        self.label_4.setText(QCoreApplication.translate("VariableEditDialog", u"Label:", None))
        self.txt_label.setText(QCoreApplication.translate("VariableEditDialog", u"Animal ID", None))
        self.label_2.setText(QCoreApplication.translate("VariableEditDialog", u"Type:", None))
        self.dpd_variable_type.setItemText(0, QCoreApplication.translate("VariableEditDialog", u"Text", None))

        self.label_8.setText(QCoreApplication.translate("VariableEditDialog", u"Scope:", None))
        self.dpd_scope.setItemText(0, QCoreApplication.translate("VariableEditDialog", u"Per Camera", None))
        self.dpd_scope.setItemText(1, QCoreApplication.translate("VariableEditDialog", u"Per Group", None))
        self.dpd_scope.setItemText(2, QCoreApplication.translate("VariableEditDialog", u"Global", None))

        self.label_6.setText(QCoreApplication.translate("VariableEditDialog", u"Persistence:", None))
        self.dpd_persistence.setItemText(0, QCoreApplication.translate("VariableEditDialog", u"Clear after every recording", None))
        self.dpd_persistence.setItemText(1, QCoreApplication.translate("VariableEditDialog", u"Remember until application is closed", None))
        self.dpd_persistence.setItemText(2, QCoreApplication.translate("VariableEditDialog", u"Remember forever", None))

        self.label_5.setText(QCoreApplication.translate("VariableEditDialog", u"Description:", None))
        self.label_7.setText(QCoreApplication.translate("VariableEditDialog", u"Example Value:", None))
        self.txt_example_value.setText(QCoreApplication.translate("VariableEditDialog", u"a3001", None))
        self.label_9.setText(QCoreApplication.translate("VariableEditDialog", u"Show Preview:", None))
        self.chb_preview.setText("")
    # retranslateUi

