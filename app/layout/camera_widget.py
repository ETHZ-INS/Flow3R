# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'CameraWidget.ui'
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
from PySide6.QtWidgets import (QApplication, QDockWidget, QFrame, QLabel,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_CameraWidget(object):
    def setupUi(self, CameraWidget):
        if not CameraWidget.objectName():
            CameraWidget.setObjectName(u"CameraWidget")
        CameraWidget.resize(400, 230)
        CameraWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        CameraWidget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frm_content = QFrame(self.dockWidgetContents)
        self.frm_content.setObjectName(u"frm_content")
        self.frm_content.setFrameShape(QFrame.StyledPanel)
        self.frm_content.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frm_content)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(self.frm_content)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.RichText)
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.label)


        self.verticalLayout.addWidget(self.frm_content)

        CameraWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(CameraWidget)

        QMetaObject.connectSlotsByName(CameraWidget)
    # setupUi

    def retranslateUi(self, CameraWidget):
        CameraWidget.setWindowTitle(QCoreApplication.translate("CameraWidget", u"DockWidget", None))
        self.label.setText(QCoreApplication.translate("CameraWidget", u"Camera not Configured", None))
    # retranslateUi

