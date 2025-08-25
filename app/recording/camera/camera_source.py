import rx


class CameraSource:
    def get_frame_dimensions(self) -> tuple[int, int, int]:
        raise NotImplementedError

    def get_fps(self) -> float:
        raise NotImplementedError

    @property
    def stream(self) -> rx.core.Observable:
        raise NotImplementedError

    def is_closed(self) -> bool:
        raise NotImplementedError

    def wait(self, timeout=None):
        raise NotImplementedError