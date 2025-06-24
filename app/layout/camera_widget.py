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
from PySide6.QtWidgets import (QApplication, QDockWidget, QFrame, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_CameraWidget(object):
    def setupUi(self, CameraWidget):
        if not CameraWidget.objectName():
            CameraWidget.setObjectName(u"CameraWidget")
        CameraWidget.resize(400, 279)
        CameraWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        CameraWidget.setAllowedAreas(Qt.TopDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame_2 = QFrame(self.dockWidgetContents)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(self.frame_2)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.label)

        self.frame = QFrame(self.frame_2)
        self.frame.setObjectName(u"frame")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QSize(0, 20))
        self.frame.setMaximumSize(QSize(16777215, 16777215))
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_start = QPushButton(self.frame)
        self.btn_start.setObjectName(u"btn_start")
        self.btn_start.setMinimumSize(QSize(0, 0))

        self.horizontalLayout.addWidget(self.btn_start)

        self.horizontalSpacer = QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.lbl_time = QLabel(self.frame)
        self.lbl_time.setObjectName(u"lbl_time")
        sizePolicy.setHeightForWidth(self.lbl_time.sizePolicy().hasHeightForWidth())
        self.lbl_time.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.lbl_time)


        self.verticalLayout_2.addWidget(self.frame)


        self.verticalLayout.addWidget(self.frame_2)

        CameraWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(CameraWidget)

        QMetaObject.connectSlotsByName(CameraWidget)
    # setupUi

    def retranslateUi(self, CameraWidget):
        CameraWidget.setWindowTitle(QCoreApplication.translate("CameraWidget", u"DockWidget", None))
        self.label.setText(QCoreApplication.translate("CameraWidget", u"Camera not Configured", None))
        self.btn_start.setText(QCoreApplication.translate("CameraWidget", u"Start", None))
        self.lbl_time.setText(QCoreApplication.translate("CameraWidget", u"00:00:00", None))
    # retranslateUi

