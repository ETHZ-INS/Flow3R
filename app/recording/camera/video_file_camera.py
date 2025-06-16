import cv2

from app.recording.camera.camera import Camera


class VideoFileCamera(Camera):
    def __init__(self, video_file_path, loop=False):
        self.video_file_path = video_file_path
        self.loop = loop
        self.vc = cv2.VideoCapture(str(video_file_path))

        self.frame_index = 0

    def reset(self):
        self.vc.release()
        self.vc = cv2.VideoCapture(str(self.video_file_path))
        self.frame_index = 0

    def grab_frame(self):
        ret, frame = self.vc.read()
        if not ret:
            if self.loop and not self.frame_index == 0:
                self.reset()
                frame = self.grab_frame()
            else:
                frame = None

        frame_index = self.frame_index
        self.frame_index += 1
        return frame
