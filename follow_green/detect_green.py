from djitellopy import Tello
import time
import cv2
import numpy as np
import threading
import os


os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
# and for the h264 warnings, add this flag to the capture:


# --- Green detection function ---
def detect_green(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)


    lower_green = np.array([45, 80, 80])
    upper_green = np.array([75, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)


    kernel = np.ones((5, 5), np.uint8)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_CLOSE, kernel)


    green_pixels = np.sum(mask_green > 0)
    threshold = 500


    return "green" if green_pixels > threshold else "none", mask_green




# --- Connect and start stream ---
t = Tello()
t.connect(wait_for_state=False)
t.streamon()
print("Stream on")
time.sleep(2)  # give stream time to stabilize


# --- Open UDP stream with OpenCV ---
cap = cv2.VideoCapture("udp://0.0.0.0:12345?overrun_nonfatal=1&fifo_size=5000000", cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)


if not cap.isOpened():
    print("Failed to open stream")
    t.streamoff()
    t.end()
    exit()


print("Stream opened — press ESC to quit")


while True:
    ret, frame = cap.read()


    if not ret or frame is None:
        print("No frame received")
        continue


    state, mask = detect_green(frame)


    # Draw detection result on frame
    color = (0, 255, 0) if state == "green" else (0, 0, 255)
    cv2.putText(frame, state, (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)


    # Show both the live feed and the green mask
    cv2.imshow("Tello Camera", frame)
    cv2.imshow("Green Mask", mask)


    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        break


cap.release()
cv2.destroyAllWindows()
t.streamoff()
t.end()
