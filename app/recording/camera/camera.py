import numpy as np


class Camera:
    def grab_frame(self) -> np.ndarray | None:
        """
        Grabs a frame from the camera.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement grab_frame method.")