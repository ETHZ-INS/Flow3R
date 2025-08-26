# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'CameraListDialog.ui'
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

class Ui_CameraListDialog(object):
    def setupUi(self, CameraListDialog):
        if not CameraListDialog.objectName():
            CameraListDialog.setObjectName(u"CameraListDialog")
        CameraListDialog.resize(423, 414)
        self.verticalLayout = QVBoxLayout(CameraListDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(CameraListDialog)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label)

        self.lst_cameras = QListView(CameraListDialog)
        self.lst_cameras.setObjectName(u"lst_cameras")
        self.lst_cameras.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lst_cameras.setDefaultDropAction(Qt.CopyAction)
        self.lst_cameras.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout.addWidget(self.lst_cameras)

        self.frm_camera_list_buttons = QFrame(CameraListDialog)
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
        self.btn_deactivate_camera = QPushButton(self.frm_camera_list_buttons)
        self.btn_deactivate_camera.setObjectName(u"btn_deactivate_camera")

        self.gridLayout.addWidget(self.btn_deactivate_camera, 1, 2, 1, 1)

        self.btn_edit_camera = QPushButton(self.frm_camera_list_buttons)
        self.btn_edit_camera.setObjectName(u"btn_edit_camera")

        self.gridLayout.addWidget(self.btn_edit_camera, 1, 0, 1, 1)

        self.btn_add_camera = QPushButton(self.frm_camera_list_buttons)
        self.btn_add_camera.setObjectName(u"btn_add_camera")

        self.gridLayout.addWidget(self.btn_add_camera, 0, 0, 1, 1)

        self.btn_remove_camera = QPushButton(self.frm_camera_list_buttons)
        self.btn_remove_camera.setObjectName(u"btn_remove_camera")

        self.gridLayout.addWidget(self.btn_remove_camera, 0, 2, 1, 1)


        self.verticalLayout.addWidget(self.frm_camera_list_buttons)

        self.buttonBox = QDialogButtonBox(CameraListDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(CameraListDialog)
        self.buttonBox.accepted.connect(CameraListDialog.accept)
        self.buttonBox.rejected.connect(CameraListDialog.reject)

        QMetaObject.connectSlotsByName(CameraListDialog)
    # setupUi

    def retranslateUi(self, CameraListDialog):
        CameraListDialog.setWindowTitle(QCoreApplication.translate("CameraListDialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("CameraListDialog", u"### Cameras", None))
        self.btn_deactivate_camera.setText(QCoreApplication.translate("CameraListDialog", u"Deactivate Camera", None))
        self.btn_edit_camera.setText(QCoreApplication.translate("CameraListDialog", u"Edit Camera", None))
        self.btn_add_camera.setText(QCoreApplication.translate("CameraListDialog", u"Add Camera", None))
        self.btn_remove_camera.setText(QCoreApplication.translate("CameraListDialog", u"Remove Camera", None))
    # retranslateUi

