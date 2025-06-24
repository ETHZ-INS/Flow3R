# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'HeatmapWidget.ui'
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
from PySide6.QtWidgets import (QApplication, QDockWidget, QHBoxLayout, QLabel,
    QSizePolicy, QWidget)

class Ui_HeatmapWidget(object):
    def setupUi(self, HeatmapWidget):
        if not HeatmapWidget.objectName():
            HeatmapWidget.setObjectName(u"HeatmapWidget")
        HeatmapWidget.resize(400, 300)
        HeatmapWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        HeatmapWidget.setAllowedAreas(Qt.TopDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.horizontalLayout = QHBoxLayout(self.dockWidgetContents)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.dockWidgetContents)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.label)

        HeatmapWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(HeatmapWidget)

        QMetaObject.connectSlotsByName(HeatmapWidget)
    # setupUi

    def retranslateUi(self, HeatmapWidget):
        HeatmapWidget.setWindowTitle(QCoreApplication.translate("HeatmapWidget", u"DockWidget", None))
        self.label.setText("")
    # retranslateUi

