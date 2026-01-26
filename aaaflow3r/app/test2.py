import time

import cv2

vc = cv2.VideoCapture("test.mp4")

while True:
    ret, frame = vc.read()
    if not ret:
        break
    cv2.imshow("test", frame)
    cv2.waitKey(1)
    time.sleep(1)


vc.release()
cv2.destroyAllWindows()