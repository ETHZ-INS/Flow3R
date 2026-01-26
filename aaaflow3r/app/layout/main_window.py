# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindow.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QMainWindow,
    QMenu, QMenuBar, QPlainTextEdit, QSizePolicy,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_WelfareRecorder(object):
    def setupUi(self, WelfareRecorder):
        if not WelfareRecorder.objectName():
            WelfareRecorder.setObjectName(u"WelfareRecorder")
        WelfareRecorder.resize(800, 569)
        WelfareRecorder.setDockOptions(QMainWindow.AllowNestedDocks|QMainWindow.AllowTabbedDocks|QMainWindow.AnimatedDocks)
        WelfareRecorder.setUnifiedTitleAndToolBarOnMac(False)
        self.action_configure_recordings = QAction(WelfareRecorder)
        self.action_configure_recordings.setObjectName(u"action_configure_recordings")
        self.action_add_pipeline = QAction(WelfareRecorder)
        self.action_add_pipeline.setObjectName(u"action_add_pipeline")
        self.action_load_project = QAction(WelfareRecorder)
        self.action_load_project.setObjectName(u"action_load_project")
        self.action_save_project = QAction(WelfareRecorder)
        self.action_save_project.setObjectName(u"action_save_project")
        self.action_save_project_as = QAction(WelfareRecorder)
        self.action_save_project_as.setObjectName(u"action_save_project_as")
        self.action_add_camera = QAction(WelfareRecorder)
        self.action_add_camera.setObjectName(u"action_add_camera")
        self.action_configure_cameras = QAction(WelfareRecorder)
        self.action_configure_cameras.setObjectName(u"action_configure_cameras")
        self.action_add_camera_group = QAction(WelfareRecorder)
        self.action_add_camera_group.setObjectName(u"action_add_camera_group")
        self.action_configure_camera_groups = QAction(WelfareRecorder)
        self.action_configure_camera_groups.setObjectName(u"action_configure_camera_groups")
        self.action_add_placeholder = QAction(WelfareRecorder)
        self.action_add_placeholder.setObjectName(u"action_add_placeholder")
        self.action_configure_placeholders = QAction(WelfareRecorder)
        self.action_configure_placeholders.setObjectName(u"action_configure_placeholders")
        self.action_configure_pipelines = QAction(WelfareRecorder)
        self.action_configure_pipelines.setObjectName(u"action_configure_pipelines")
        self.action_enable_superuser_mode = QAction(WelfareRecorder)
        self.action_enable_superuser_mode.setObjectName(u"action_enable_superuser_mode")
        self.centralwidget = QWidget(WelfareRecorder)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frm_dock_window = QFrame(self.centralwidget)
        self.frm_dock_window.setObjectName(u"frm_dock_window")
        self.frm_dock_window.setFrameShape(QFrame.StyledPanel)
        self.frm_dock_window.setFrameShadow(QFrame.Raised)

        self.verticalLayout.addWidget(self.frm_dock_window)

        self.frm_recordings = QFrame(self.centralwidget)
        self.frm_recordings.setObjectName(u"frm_recordings")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frm_recordings.sizePolicy().hasHeightForWidth())
        self.frm_recordings.setSizePolicy(sizePolicy)
        self.frm_recordings.setFrameShape(QFrame.NoFrame)
        self.frm_recordings.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frm_recordings)
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.frm_recordings)

        self.frm_footer = QFrame(self.centralwidget)
        self.frm_footer.setObjectName(u"frm_footer")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frm_footer.sizePolicy().hasHeightForWidth())
        self.frm_footer.setSizePolicy(sizePolicy1)
        self.frm_footer.setMinimumSize(QSize(0, 65))
        self.frm_footer.setMaximumSize(QSize(16777215, 65))
        self.frm_footer.setStyleSheet(u"")
        self.frm_footer.setFrameShape(QFrame.StyledPanel)
        self.frm_footer.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frm_footer)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.txt_log = QPlainTextEdit(self.frm_footer)
        self.txt_log.setObjectName(u"txt_log")
        self.txt_log.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.txt_log.setUndoRedoEnabled(False)
        self.txt_log.setTextInteractionFlags(Qt.NoTextInteraction)

        self.horizontalLayout_4.addWidget(self.txt_log)


        self.verticalLayout.addWidget(self.frm_footer)

        WelfareRecorder.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(WelfareRecorder)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuCameras = QMenu(self.menubar)
        self.menuCameras.setObjectName(u"menuCameras")
        self.menuProcessing = QMenu(self.menubar)
        self.menuProcessing.setObjectName(u"menuProcessing")
        self.menuVariables = QMenu(self.menubar)
        self.menuVariables.setObjectName(u"menuVariables")
        WelfareRecorder.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(WelfareRecorder)
        self.statusbar.setObjectName(u"statusbar")
        WelfareRecorder.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuCameras.menuAction())
        self.menubar.addAction(self.menuProcessing.menuAction())
        self.menubar.addAction(self.menuVariables.menuAction())
        self.menuFile.addAction(self.action_load_project)
        self.menuFile.addAction(self.action_save_project)
        self.menuFile.addAction(self.action_save_project_as)
        self.menuFile.addAction(self.action_enable_superuser_mode)
        self.menuCameras.addAction(self.action_configure_cameras)
        self.menuCameras.addAction(self.action_configure_camera_groups)
        self.menuCameras.addAction(self.action_add_camera)
        self.menuCameras.addAction(self.action_add_camera_group)
        self.menuProcessing.addAction(self.action_configure_pipelines)
        self.menuProcessing.addAction(self.action_add_pipeline)
        self.menuVariables.addAction(self.action_configure_placeholders)
        self.menuVariables.addAction(self.action_add_placeholder)

        self.retranslateUi(WelfareRecorder)

        QMetaObject.connectSlotsByName(WelfareRecorder)
    # setupUi

    def retranslateUi(self, WelfareRecorder):
        WelfareRecorder.setWindowTitle(QCoreApplication.translate("WelfareRecorder", u"Welfar3Recorder", None))
        self.action_configure_recordings.setText(QCoreApplication.translate("WelfareRecorder", u"Configure Recording", None))
        self.action_add_pipeline.setText(QCoreApplication.translate("WelfareRecorder", u"Add Processing Pipeline", None))
        self.action_load_project.setText(QCoreApplication.translate("WelfareRecorder", u"Load Project...", None))
        self.action_save_project.setText(QCoreApplication.translate("WelfareRecorder", u"Save Project", None))
        self.action_save_project_as.setText(QCoreApplication.translate("WelfareRecorder", u"Save Project As...", None))
        self.action_add_camera.setText(QCoreApplication.translate("WelfareRecorder", u"Add Camera", None))
        self.action_configure_cameras.setText(QCoreApplication.translate("WelfareRecorder", u"Cameras...", None))
        self.action_add_camera_group.setText(QCoreApplication.translate("WelfareRecorder", u"Add Camera Group", None))
        self.action_configure_camera_groups.setText(QCoreApplication.translate("WelfareRecorder", u"Camera Groups...", None))
        self.action_add_placeholder.setText(QCoreApplication.translate("WelfareRecorder", u"Add Placeholder", None))
        self.action_configure_placeholders.setText(QCoreApplication.translate("WelfareRecorder", u"Placeholders...", None))
        self.action_configure_pipelines.setText(QCoreApplication.translate("WelfareRecorder", u"Processing Pipelines...", None))
        self.action_enable_superuser_mode.setText(QCoreApplication.translate("WelfareRecorder", u"Enable Superuser Mode", None))
        self.menuFile.setTitle(QCoreApplication.translate("WelfareRecorder", u"File", None))
        self.menuCameras.setTitle(QCoreApplication.translate("WelfareRecorder", u"Cameras", None))
        self.menuProcessing.setTitle(QCoreApplication.translate("WelfareRecorder", u"Processing", None))
        self.menuVariables.setTitle(QCoreApplication.translate("WelfareRecorder", u"Placeholders", None))
    # retranslateUi

