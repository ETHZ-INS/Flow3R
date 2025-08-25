# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'VariablePreparationDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_VariablePreparationDialog(object):
    def setupUi(self, VariablePreparationDialog):
        if not VariablePreparationDialog.objectName():
            VariablePreparationDialog.setObjectName(u"VariablePreparationDialog")
        VariablePreparationDialog.resize(423, 414)
        self.verticalLayout = QVBoxLayout(VariablePreparationDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(VariablePreparationDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.frm_variables = QWidget()
        self.frm_variables.setObjectName(u"frm_variables")
        self.frm_variables.setGeometry(QRect(0, 0, 403, 364))
        self.formLayout = QFormLayout(self.frm_variables)
        self.formLayout.setObjectName(u"formLayout")
        self.scrollArea.setWidget(self.frm_variables)

        self.verticalLayout.addWidget(self.scrollArea)

        self.buttonBox = QDialogButtonBox(VariablePreparationDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(VariablePreparationDialog)
        self.buttonBox.rejected.connect(VariablePreparationDialog.reject)
        self.buttonBox.accepted.connect(VariablePreparationDialog.accept)

        QMetaObject.connectSlotsByName(VariablePreparationDialog)
    # setupUi

    def retranslateUi(self, VariablePreparationDialog):
        VariablePreparationDialog.setWindowTitle(QCoreApplication.translate("VariablePreparationDialog", u"Dialog", None))
    # retranslateUi

