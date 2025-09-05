from copy import deepcopy

from PySide6.QtWidgets import QDialog

from app.analysis.pose_estimation.yolo_pose_model import YoloPoseModel
from app.config.pose_estimation_config import PoseEstimationConfig, PoseEstimationModelConfig
from app.layout.pose_estimation_configuration_dialog import Ui_PoseEstimationConfigurationDialog
from app.controller import Controller


# TODO: I need a way to globally add external models and use them in multiple PoseEstimation nodes. Or do i?

class PoseEstimationConfigurationDialog(Ui_PoseEstimationConfigurationDialog, QDialog):
    def __init__(self, controller: Controller, config: PoseEstimationConfig, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self.config = deepcopy(config)

        if len(self.config.models) < 1:
            model = PoseEstimationModelConfig()
            self.config.models[model.model_id] = model

        self.dpd_model.clear()
        for model_id, model in self.config.models.items():
            self.dpd_model.addItem(model.name, model_id)
        self.dpd_model.setCurrentIndex(0)

        self.dpd_select_model.clear()
        for model_name in self.controller.config.INTERNAL_MODELS:
            self.dpd_select_model.addItem(model_name)
        self.dpd_select_model.setCurrentIndex(0)

        self.dpd_device.clear()
        self.dpd_device.addItem("CPU", "cpu")
        self.dpd_device.addItem("GPU (CUDA)", "cuda")

        self.current_model = self.config.models[self.dpd_model.currentData()]

        self.dpd_model.currentIndexChanged.connect(self.current_model_changed)
        self.dpd_select_model.currentTextChanged.connect(self.selected_model_changed)
        self.dpd_device.currentIndexChanged.connect(self.device_changed)
        self.btn_add_model.clicked.connect(self.add_model)
        self.btn_remove_model.clicked.connect(self.remove_model)

        self.chb_save_file.stateChanged.connect(self.save_to_file_changed)
        self.txt_save_file.textChanged.connect(self.save_file_changed)

        self.current_model_changed()
        self.update_form()

    def update_form(self):
        if self.current_model.internal_model_name:
            self.dpd_select_model.setCurrentText(self.current_model.internal_model_name)
        else:
            self.dpd_select_model.setCurrentIndex(-1)

        self.dpd_device.setCurrentIndex(self.dpd_device.findData(self.current_model.device))
        self.lbl_tracked_instance_types.setText("\n".join(self.get_tracked_instances()))

        self.btn_remove_model.setEnabled(len(self.config.models) > 1)

    def current_model_changed(self):
        model_id = self.dpd_model.currentData()
        if model_id is None:
            model_id = list(self.config.models.keys())[0]

        self.current_model = self.config.models.get(model_id)
        self.update_form()

    def selected_model_changed(self):
        self.current_model.internal_model_name = self.dpd_select_model.currentText()
        self.current_model.model_folder = self.controller.config.INTERNAL_MODELS.get(self.current_model.internal_model_name, None)
        self.dpd_model.setItemText(self.dpd_model.currentIndex(), self.current_model.name)
        self.update_form()

    def device_changed(self):
        self.current_model.device = self.dpd_device.currentData()
        self.dpd_model.setItemText(self.dpd_model.currentIndex(), self.current_model.name)
        self.update_form()

    def add_model(self):
        model = PoseEstimationModelConfig()
        self.config.models[model.model_id] = model
        self.dpd_model.addItem(model.name, model.model_id)
        self.dpd_model.setCurrentIndex(self.dpd_model.findData(model.model_id))
        self.current_model_changed()

    def remove_model(self):
        model_id = self.dpd_model.currentData()
        if model_id is None or len(self.config.models) <= 1:
            return

        del self.config.models[model_id]
        self.dpd_model.removeItem(self.dpd_model.currentIndex())

        self.dpd_model.setCurrentIndex(0)
        self.current_model_changed()

    def save_to_file_changed(self):
        self.config.save_to_file = self.chb_save_file.isChecked()

    def save_file_changed(self):
        self.config.save_file = self.txt_save_file.text()

    def get_tracked_instances(self):
        instance_type_names = []
        for model_config in self.config.models.values():
            model_folder = model_config.model_folder
            if model_folder is None or not model_folder.exists():
                continue
            instance_types = YoloPoseModel.load_instance_types(model_folder)
            instance_type_names.extend([instance_type.name for instance_type in instance_types])
        return instance_type_names
