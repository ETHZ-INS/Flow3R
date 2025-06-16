# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'WelfareRecorder.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QVBoxLayout, QWidget)

class Ui_WelfareRecorder(object):
    def setupUi(self, WelfareRecorder):
        if not WelfareRecorder.objectName():
            WelfareRecorder.setObjectName(u"WelfareRecorder")
        WelfareRecorder.resize(800, 600)
        WelfareRecorder.setDockOptions(QMainWindow.AllowNestedDocks|QMainWindow.AllowTabbedDocks|QMainWindow.AnimatedDocks)
        WelfareRecorder.setUnifiedTitleAndToolBarOnMac(False)
        self.action_configure_cameras = QAction(WelfareRecorder)
        self.action_configure_cameras.setObjectName(u"action_configure_cameras")
        self.centralwidget = QWidget(WelfareRecorder)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QSize(0, 60))
        self.frame.setMaximumSize(QSize(16777215, 60))
        self.frame.setStyleSheet(u"")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, 9, 9, -1)
        self.frame_7 = QFrame(self.frame)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setMinimumSize(QSize(250, 0))
        self.frame_7.setMaximumSize(QSize(200, 16777215))
        self.frame_7.setFrameShape(QFrame.NoFrame)
        self.frame_7.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.frame_7)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.btn_record = QPushButton(self.frame_7)
        self.btn_record.setObjectName(u"btn_record")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_record.sizePolicy().hasHeightForWidth())
        self.btn_record.setSizePolicy(sizePolicy1)
        self.btn_record.setMinimumSize(QSize(100, 0))

        self.horizontalLayout_5.addWidget(self.btn_record)

        self.chb_identifier = QCheckBox(self.frame_7)
        self.chb_identifier.setObjectName(u"chb_identifier")
        self.chb_identifier.setChecked(True)

        self.horizontalLayout_5.addWidget(self.chb_identifier)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)


        self.horizontalLayout_4.addWidget(self.frame_7)

        self.lbl_message = QLabel(self.frame)
        self.lbl_message.setObjectName(u"lbl_message")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lbl_message.sizePolicy().hasHeightForWidth())
        self.lbl_message.setSizePolicy(sizePolicy2)
        self.lbl_message.setTextFormat(Qt.MarkdownText)
        self.lbl_message.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_4.addWidget(self.lbl_message)

        self.lbl_time = QLabel(self.frame)
        self.lbl_time.setObjectName(u"lbl_time")
        sizePolicy1.setHeightForWidth(self.lbl_time.sizePolicy().hasHeightForWidth())
        self.lbl_time.setSizePolicy(sizePolicy1)
        self.lbl_time.setMinimumSize(QSize(250, 0))
        self.lbl_time.setMaximumSize(QSize(200, 16777215))
        self.lbl_time.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.lbl_time)


        self.verticalLayout.addWidget(self.frame)

        WelfareRecorder.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(WelfareRecorder)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuRecording = QMenu(self.menubar)
        self.menuRecording.setObjectName(u"menuRecording")
        WelfareRecorder.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(WelfareRecorder)
        self.statusbar.setObjectName(u"statusbar")
        WelfareRecorder.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuRecording.menuAction())
        self.menuRecording.addAction(self.action_configure_cameras)

        self.retranslateUi(WelfareRecorder)

        QMetaObject.connectSlotsByName(WelfareRecorder)
    # setupUi

    def retranslateUi(self, WelfareRecorder):
        WelfareRecorder.setWindowTitle(QCoreApplication.translate("WelfareRecorder", u"Welfar3Recorder", None))
        self.action_configure_cameras.setText(QCoreApplication.translate("WelfareRecorder", u"Configure Cameras", None))
#if QT_CONFIG(tooltip)
        self.btn_record.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.btn_record.setText(QCoreApplication.translate("WelfareRecorder", u"Start Recording", None))
        self.chb_identifier.setText(QCoreApplication.translate("WelfareRecorder", u"Ask for Identifier", None))
        self.lbl_message.setText(QCoreApplication.translate("WelfareRecorder", u"Ready to record", None))
        self.lbl_time.setText(QCoreApplication.translate("WelfareRecorder", u"00:00:00", None))
        self.menuFile.setTitle(QCoreApplication.translate("WelfareRecorder", u"File", None))
        self.menuRecording.setTitle(QCoreApplication.translate("WelfareRecorder", u"Recording", None))
    # retranslateUi

