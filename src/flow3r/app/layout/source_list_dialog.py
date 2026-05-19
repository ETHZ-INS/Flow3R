# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'SourceListDialog.ui'
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

class Ui_SourceListDialog(object):
    def setupUi(self, SourceListDialog):
        if not SourceListDialog.objectName():
            SourceListDialog.setObjectName(u"SourceListDialog")
        SourceListDialog.resize(423, 414)
        self.verticalLayout = QVBoxLayout(SourceListDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(SourceListDialog)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label)

        self.lst_sources = QListView(SourceListDialog)
        self.lst_sources.setObjectName(u"lst_sources")
        self.lst_sources.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lst_sources.setDefaultDropAction(Qt.CopyAction)
        self.lst_sources.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout.addWidget(self.lst_sources)

        self.frm_camera_list_buttons = QFrame(SourceListDialog)
        self.frm_camera_list_buttons.setObjectName(u"frm_camera_list_buttons")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frm_camera_list_buttons.sizePolicy().hasHeightForWidth())
        self.frm_camera_list_buttons.setSizePolicy(sizePolicy)
        self.frm_camera_list_buttons.setFrameShape(QFrame.NoFrame)
        self.frm_camera_list_buttons.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.frm_camera_list_buttons)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_deactivate = QPushButton(self.frm_camera_list_buttons)
        self.btn_deactivate.setObjectName(u"btn_deactivate")

        self.gridLayout.addWidget(self.btn_deactivate, 1, 2, 1, 1)

        self.btn_edit = QPushButton(self.frm_camera_list_buttons)
        self.btn_edit.setObjectName(u"btn_edit")

        self.gridLayout.addWidget(self.btn_edit, 1, 0, 1, 1)

        self.btn_add = QPushButton(self.frm_camera_list_buttons)
        self.btn_add.setObjectName(u"btn_add")

        self.gridLayout.addWidget(self.btn_add, 0, 0, 1, 1)

        self.btn_remove = QPushButton(self.frm_camera_list_buttons)
        self.btn_remove.setObjectName(u"btn_remove")

        self.gridLayout.addWidget(self.btn_remove, 0, 2, 1, 1)


        self.verticalLayout.addWidget(self.frm_camera_list_buttons)

        self.buttonBox = QDialogButtonBox(SourceListDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(SourceListDialog)
        self.buttonBox.accepted.connect(SourceListDialog.accept)
        self.buttonBox.rejected.connect(SourceListDialog.reject)

        QMetaObject.connectSlotsByName(SourceListDialog)
    # setupUi

    def retranslateUi(self, SourceListDialog):
        SourceListDialog.setWindowTitle(QCoreApplication.translate("SourceListDialog", u"Sources", None))
        self.label.setText(QCoreApplication.translate("SourceListDialog", u"### Sources", None))
        self.btn_deactivate.setText(QCoreApplication.translate("SourceListDialog", u"Deactivate Source", None))
        self.btn_edit.setText(QCoreApplication.translate("SourceListDialog", u"Edit Source", None))
        self.btn_add.setText(QCoreApplication.translate("SourceListDialog", u"Add Source", None))
        self.btn_remove.setText(QCoreApplication.translate("SourceListDialog", u"Remove Source", None))
    # retranslateUi

