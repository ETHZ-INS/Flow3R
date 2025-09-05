# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'VariableTextWidget.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QToolButton, QVBoxLayout, QWidget)

from app.widgets.placeholder_line_edit import PlaceholderLineEdit

class Ui_VariableTextWidget(object):
    def setupUi(self, VariableTextWidget):
        if not VariableTextWidget.objectName():
            VariableTextWidget.setObjectName(u"VariableTextWidget")
        VariableTextWidget.resize(400, 44)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(VariableTextWidget.sizePolicy().hasHeightForWidth())
        VariableTextWidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(VariableTextWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(VariableTextWidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.txt_value = PlaceholderLineEdit(self.frame)
        self.txt_value.setObjectName(u"txt_value")

        self.horizontalLayout.addWidget(self.txt_value)

        self.btn_select_file = QToolButton(self.frame)
        self.btn_select_file.setObjectName(u"btn_select_file")
        icon = QIcon()
        iconThemeName = u"folder-open"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u"../../../anaconda3/envs/GrimaceRecorder/Lib/site-packages/qt6_applications/Qt/bin", QSize(), QIcon.Normal, QIcon.Off)

        self.btn_select_file.setIcon(icon)

        self.horizontalLayout.addWidget(self.btn_select_file)

        self.btn_editor = QToolButton(self.frame)
        self.btn_editor.setObjectName(u"btn_editor")

        self.horizontalLayout.addWidget(self.btn_editor)


        self.verticalLayout.addWidget(self.frame)

        self.lbl_preview = QLabel(VariableTextWidget)
        self.lbl_preview.setObjectName(u"lbl_preview")

        self.verticalLayout.addWidget(self.lbl_preview)


        self.retranslateUi(VariableTextWidget)

        QMetaObject.connectSlotsByName(VariableTextWidget)
    # setupUi

    def retranslateUi(self, VariableTextWidget):
        VariableTextWidget.setWindowTitle(QCoreApplication.translate("VariableTextWidget", u"Form", None))
        self.btn_select_file.setText(QCoreApplication.translate("VariableTextWidget", u"...", None))
        self.btn_editor.setText(QCoreApplication.translate("VariableTextWidget", u"{v}", None))
        self.lbl_preview.setText(QCoreApplication.translate("VariableTextWidget", u"Preview:", None))
    # retranslateUi

