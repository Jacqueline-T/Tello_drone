from djitellopy import Tello
import cv2
import time

# ---------------------------
# Connect to Tello
# ---------------------------
t = Tello()
t.connect(wait_for_state=False)

battery = t.get_battery()
print(f"Battery: {battery}%")

t.streamon()
time.sleep(2)

cap = cv2.VideoCapture("udp://0.0.0.0:11111", cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Failed to open stream")
    t.streamoff()
    t.end()
    exit()

# ---------------------------
# ArUco setup
# ---------------------------
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
aruco_params = cv2.aruco.DetectorParameters()

detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

print("ArUco detection active — press ESC to quit")

# ---------------------------
# Main loop
# ---------------------------
while True:
    ret, frame = cap.read()

    if not ret or frame is None:
        continue

    frame = cv2.resize(frame, (480, 360))

    # Detect markers
    corners, ids, rejected = detector.detectMarkers(frame)

    # Draw results if detected
    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        for i in range(len(ids)):
            marker_id = ids[i][0]
            cv2.putText(
                frame,
                f"ID: {marker_id}",
                (20, 40 + i * 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
    else:
        cv2.putText(
            frame,
            "No ArUco marker detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )

    cv2.imshow("Tello ArUco Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

# ---------------------------
# Cleanup
# ---------------------------
cap.release()
cv2.destroyAllWindows()
t.streamoff()
t.end()
