from typing import Callable

from PySide6.QtWidgets import QWidget

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.settings.abc.settings_menu import ISettingsMenu
from aaaflow3r.plugins.pose_estimation.settings.pose_estimation_models.widget import PoseEstimationModelsSettingsWidget


class PoseEstimationModelsSettingsMenu(ISettingsMenu):
    @property
    def name(self) -> str:
        return "Pose Estimation Models"

    @property
    def path(self) -> tuple[str, ...]:
        return "Pose Estimation", "Pose Estimation Models"

    @property
    def widget_factory(self) -> Callable[[IAppContext, QWidget], PoseEstimationModelsSettingsWidget]:
        return PoseEstimationModelsSettingsWidget
