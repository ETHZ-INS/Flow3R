# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PlaceholderListDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialog,
    QDialogButtonBox, QFrame, QGridLayout, QLabel,
    QListView, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_PlaceholderListDialog(object):
    def setupUi(self, PlaceholderListDialog):
        if not PlaceholderListDialog.objectName():
            PlaceholderListDialog.setObjectName(u"PlaceholderListDialog")
        PlaceholderListDialog.resize(423, 414)
        self.verticalLayout = QVBoxLayout(PlaceholderListDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(PlaceholderListDialog)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label)

        self.lst_placeholders = QListView(PlaceholderListDialog)
        self.lst_placeholders.setObjectName(u"lst_placeholders")
        self.lst_placeholders.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lst_placeholders.setDefaultDropAction(Qt.CopyAction)
        self.lst_placeholders.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout.addWidget(self.lst_placeholders)

        self.frm_buttons = QFrame(PlaceholderListDialog)
        self.frm_buttons.setObjectName(u"frm_buttons")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frm_buttons.sizePolicy().hasHeightForWidth())
        self.frm_buttons.setSizePolicy(sizePolicy)
        self.frm_buttons.setFrameShape(QFrame.NoFrame)
        self.frm_buttons.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.frm_buttons)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_edit = QPushButton(self.frm_buttons)
        self.btn_edit.setObjectName(u"btn_edit")

        self.gridLayout.addWidget(self.btn_edit, 1, 0, 1, 1)

        self.btn_add = QPushButton(self.frm_buttons)
        self.btn_add.setObjectName(u"btn_add")

        self.gridLayout.addWidget(self.btn_add, 0, 0, 1, 1)

        self.btn_remove = QPushButton(self.frm_buttons)
        self.btn_remove.setObjectName(u"btn_remove")

        self.gridLayout.addWidget(self.btn_remove, 0, 2, 1, 1)


        self.verticalLayout.addWidget(self.frm_buttons)

        self.buttonBox = QDialogButtonBox(PlaceholderListDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(PlaceholderListDialog)
        self.buttonBox.accepted.connect(PlaceholderListDialog.accept)
        self.buttonBox.rejected.connect(PlaceholderListDialog.reject)

        QMetaObject.connectSlotsByName(PlaceholderListDialog)
    # setupUi

    def retranslateUi(self, PlaceholderListDialog):
        PlaceholderListDialog.setWindowTitle(QCoreApplication.translate("PlaceholderListDialog", u"Placeholders", None))
        self.label.setText(QCoreApplication.translate("PlaceholderListDialog", u"### Placeholders", None))
        self.btn_edit.setText(QCoreApplication.translate("PlaceholderListDialog", u"Edit Placeholder", None))
        self.btn_add.setText(QCoreApplication.translate("PlaceholderListDialog", u"Add Placeholder", None))
        self.btn_remove.setText(QCoreApplication.translate("PlaceholderListDialog", u"Remove Placeholder", None))
    # retranslateUi

