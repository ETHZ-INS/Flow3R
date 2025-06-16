from PySide6.QtWidgets import QDockWidget

from app.layout.welfare_analysis_widget import Ui_WelfareAnalysisWidget


class WelfareAnalysisWidget(Ui_WelfareAnalysisWidget, QDockWidget):
    def __init__(self):
        super(WelfareAnalysisWidget, self).__init__()

        self.setupUi(self)
