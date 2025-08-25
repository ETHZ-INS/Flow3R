# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'CameraGroupListDialog.ui'
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

class Ui_CameraGroupListDialog(object):
    def setupUi(self, CameraGroupListDialog):
        if not CameraGroupListDialog.objectName():
            CameraGroupListDialog.setObjectName(u"CameraGroupListDialog")
        CameraGroupListDialog.resize(423, 414)
        self.verticalLayout = QVBoxLayout(CameraGroupListDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(CameraGroupListDialog)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label)

        self.lst_groups = QListView(CameraGroupListDialog)
        self.lst_groups.setObjectName(u"lst_groups")
        self.lst_groups.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lst_groups.setDefaultDropAction(Qt.CopyAction)
        self.lst_groups.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout.addWidget(self.lst_groups)

        self.frm_camera_list_buttons = QFrame(CameraGroupListDialog)
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
        self.btn_remove = QPushButton(self.frm_camera_list_buttons)
        self.btn_remove.setObjectName(u"btn_remove")

        self.gridLayout.addWidget(self.btn_remove, 0, 2, 1, 1)

        self.btn_add = QPushButton(self.frm_camera_list_buttons)
        self.btn_add.setObjectName(u"btn_add")

        self.gridLayout.addWidget(self.btn_add, 0, 0, 1, 1)

        self.btn_edit = QPushButton(self.frm_camera_list_buttons)
        self.btn_edit.setObjectName(u"btn_edit")

        self.gridLayout.addWidget(self.btn_edit, 1, 0, 1, 1)


        self.verticalLayout.addWidget(self.frm_camera_list_buttons)

        self.buttonBox = QDialogButtonBox(CameraGroupListDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(CameraGroupListDialog)
        self.buttonBox.accepted.connect(CameraGroupListDialog.accept)
        self.buttonBox.rejected.connect(CameraGroupListDialog.reject)

        QMetaObject.connectSlotsByName(CameraGroupListDialog)
    # setupUi

    def retranslateUi(self, CameraGroupListDialog):
        CameraGroupListDialog.setWindowTitle(QCoreApplication.translate("CameraGroupListDialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("CameraGroupListDialog", u"### Camera Groups", None))
        self.btn_remove.setText(QCoreApplication.translate("CameraGroupListDialog", u"Remove Group", None))
        self.btn_add.setText(QCoreApplication.translate("CameraGroupListDialog", u"Add Group", None))
        self.btn_edit.setText(QCoreApplication.translate("CameraGroupListDialog", u"Edit Group", None))
    # retranslateUi

