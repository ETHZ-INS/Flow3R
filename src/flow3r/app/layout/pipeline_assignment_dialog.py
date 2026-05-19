# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PipelineAssignmentDialog.ui'
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
    QFrame, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QToolButton, QTreeView,
    QVBoxLayout, QWidget)

class Ui_PipelineAssignmentDialog(object):
    def setupUi(self, PipelineAssignmentDialog):
        if not PipelineAssignmentDialog.objectName():
            PipelineAssignmentDialog.setObjectName(u"PipelineAssignmentDialog")
        PipelineAssignmentDialog.resize(400, 313)
        self.verticalLayout = QVBoxLayout(PipelineAssignmentDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(PipelineAssignmentDialog)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label)

        self.tree_inputs = QTreeView(PipelineAssignmentDialog)
        self.tree_inputs.setObjectName(u"tree_inputs")

        self.verticalLayout.addWidget(self.tree_inputs)

        self.frame = QFrame(PipelineAssignmentDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_add_pipeline = QToolButton(self.frame)
        self.btn_add_pipeline.setObjectName(u"btn_add_pipeline")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_add_pipeline.sizePolicy().hasHeightForWidth())
        self.btn_add_pipeline.setSizePolicy(sizePolicy1)
        self.btn_add_pipeline.setFocusPolicy(Qt.StrongFocus)
        self.btn_add_pipeline.setPopupMode(QToolButton.MenuButtonPopup)
        self.btn_add_pipeline.setArrowType(Qt.NoArrow)

        self.horizontalLayout.addWidget(self.btn_add_pipeline)

        self.btn_remove_pipeline = QPushButton(self.frame)
        self.btn_remove_pipeline.setObjectName(u"btn_remove_pipeline")

        self.horizontalLayout.addWidget(self.btn_remove_pipeline)


        self.verticalLayout.addWidget(self.frame)

        self.buttonBox = QDialogButtonBox(PipelineAssignmentDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(PipelineAssignmentDialog)
        self.buttonBox.accepted.connect(PipelineAssignmentDialog.accept)
        self.buttonBox.rejected.connect(PipelineAssignmentDialog.reject)

        QMetaObject.connectSlotsByName(PipelineAssignmentDialog)
    # setupUi

    def retranslateUi(self, PipelineAssignmentDialog):
        PipelineAssignmentDialog.setWindowTitle(QCoreApplication.translate("PipelineAssignmentDialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("PipelineAssignmentDialog", u"### Group Pipelines", None))
        self.btn_add_pipeline.setText(QCoreApplication.translate("PipelineAssignmentDialog", u"Add Pipeline", None))
        self.btn_remove_pipeline.setText(QCoreApplication.translate("PipelineAssignmentDialog", u"Remove Pipeline", None))
    # retranslateUi

