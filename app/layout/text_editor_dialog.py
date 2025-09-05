# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TextEditorDialog.ui'
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
    QDialogButtonBox, QFrame, QHBoxLayout, QLabel,
    QListView, QSizePolicy, QVBoxLayout, QWidget)

from app.widgets.variable_text_widget import VariableTextWidget

class Ui_TextEditorDialog(object):
    def setupUi(self, TextEditorDialog):
        if not TextEditorDialog.objectName():
            TextEditorDialog.setObjectName(u"TextEditorDialog")
        TextEditorDialog.resize(695, 300)
        self.verticalLayout = QVBoxLayout(TextEditorDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(TextEditorDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.lbl_name = QLabel(self.frame)
        self.lbl_name.setObjectName(u"lbl_name")

        self.verticalLayout_2.addWidget(self.lbl_name)

        self.txt_value = VariableTextWidget(self.frame)
        self.txt_value.setObjectName(u"txt_value")

        self.verticalLayout_2.addWidget(self.txt_value)

        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_2.addWidget(self.frame_2)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setTextFormat(Qt.MarkdownText)

        self.verticalLayout_2.addWidget(self.label_2)

        self.lst_variables = QListView(self.frame)
        self.lst_variables.setObjectName(u"lst_variables")
        self.lst_variables.setFrameShape(QFrame.StyledPanel)
        self.lst_variables.setDragEnabled(True)
        self.lst_variables.setDragDropOverwriteMode(True)
        self.lst_variables.setDragDropMode(QAbstractItemView.DragOnly)

        self.verticalLayout_2.addWidget(self.lst_variables)


        self.verticalLayout.addWidget(self.frame)

        self.buttonBox = QDialogButtonBox(TextEditorDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(TextEditorDialog)
        self.buttonBox.accepted.connect(TextEditorDialog.accept)
        self.buttonBox.rejected.connect(TextEditorDialog.reject)

        QMetaObject.connectSlotsByName(TextEditorDialog)
    # setupUi

    def retranslateUi(self, TextEditorDialog):
        TextEditorDialog.setWindowTitle(QCoreApplication.translate("TextEditorDialog", u"Edit Path", None))
        self.lbl_name.setText(QCoreApplication.translate("TextEditorDialog", u"Path:", None))
        self.label.setText(QCoreApplication.translate("TextEditorDialog", u"Variables:", None))
        self.label_2.setText(QCoreApplication.translate("TextEditorDialog", u"<em>Double click or drag & drop</em>", None))
    # retranslateUi

