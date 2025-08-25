# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'CameraPreviewDialog.ui'
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
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

class Ui_CameraPreviewDialog(object):
    def setupUi(self, CameraPreviewDialog):
        if not CameraPreviewDialog.objectName():
            CameraPreviewDialog.setObjectName(u"CameraPreviewDialog")
        CameraPreviewDialog.resize(400, 300)
        self.verticalLayout = QVBoxLayout(CameraPreviewDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(CameraPreviewDialog)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(50, 50))
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.buttonBox = QDialogButtonBox(CameraPreviewDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(CameraPreviewDialog)
        self.buttonBox.accepted.connect(CameraPreviewDialog.accept)
        self.buttonBox.rejected.connect(CameraPreviewDialog.reject)

        QMetaObject.connectSlotsByName(CameraPreviewDialog)
    # setupUi

    def retranslateUi(self, CameraPreviewDialog):
        CameraPreviewDialog.setWindowTitle(QCoreApplication.translate("CameraPreviewDialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("CameraPreviewDialog", u"Loading preview...", None))
    # retranslateUi

