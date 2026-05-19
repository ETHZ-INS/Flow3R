from dataclasses import dataclass
from typing import List

from cv2_enumerate_cameras import enumerate_cameras
import cv2


@dataclass
class WebcamDevice:
    index: int
    name: str
    path: str


def list_webcams() -> List[WebcamDevice]:
    webcams = []
    for cam in enumerate_cameras(cv2.CAP_DSHOW):
        if cam.path is None:
            continue
        webcams.append(WebcamDevice(index=cam.index, name=cam.name, path="@device_pnp_" + cam.path))
    return webcams
