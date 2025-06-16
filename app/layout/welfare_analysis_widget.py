# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'WelfareAnalysisWidget.ui'
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
from PySide6.QtWidgets import (QApplication, QDockWidget, QLabel, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_WelfareAnalysisWidget(object):
    def setupUi(self, WelfareAnalysisWidget):
        if not WelfareAnalysisWidget.objectName():
            WelfareAnalysisWidget.setObjectName(u"WelfareAnalysisWidget")
        WelfareAnalysisWidget.resize(400, 300)
        WelfareAnalysisWidget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.dockWidgetContents)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        WelfareAnalysisWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(WelfareAnalysisWidget)

        QMetaObject.connectSlotsByName(WelfareAnalysisWidget)
    # setupUi

    def retranslateUi(self, WelfareAnalysisWidget):
        WelfareAnalysisWidget.setWindowTitle(QCoreApplication.translate("WelfareAnalysisWidget", u"Welfare Analysis", None))
        self.label.setText(QCoreApplication.translate("WelfareAnalysisWidget", u"# Your mouse is: Happy", None))
    # retranslateUi

