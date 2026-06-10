import cv2
import cv2.aruco as aruco
from collections import deque, Counter
from djitellopy import Tello
import time

def main():
    # --- Connect and start stream ---
    t = Tello()
    t.connect(wait_for_state=False)
    t.streamon()
    print("Stream on")
    time.sleep(2)

    cap = cv2.VideoCapture("udp://0.0.0.0:12345?overrun_nonfatal=1&fifo_size=5000000", cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("Error: Could not open stream.")
        t.streamoff()
        t.end()
        return

    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    parameters = aruco.DetectorParameters()
    parameters.adaptiveThreshWinSizeMin = 3
    parameters.adaptiveThreshWinSizeMax = 23
    parameters.adaptiveThreshWinSizeStep = 4
    parameters.minMarkerPerimeterRate = 0.05
    parameters.maxMarkerPerimeterRate = 4.0
    parameters.polygonalApproxAccuracyRate = 0.05
    parameters.errorCorrectionRate = 0.3
    parameters.minCornerDistanceRate = 0.05
    parameters.minDistanceToBorder = 3
    parameters.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX
    parameters.adaptiveThreshConstant = 7
    parameters.minOtsuStdDev = 5.0

    print("Press 'q' to quit.")
    history = deque(maxlen=5)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("No frame received")
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        if ids is not None:
            history.append(int(ids.flatten()[0]))
        else:
            history.append(None)

        stable_id = None
        if len(history) == 5:
            most_common, count = Counter(history).most_common(1)[0]
            if count >= 3 and most_common is not None:
                stable_id = most_common

        if stable_id is not None:
            aruco.drawDetectedMarkers(frame, corners, ids)
            cv2.putText(frame, f"Stable ID: {stable_id}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)
            print(f"Stable marker ID: {stable_id}")
        else:
            cv2.putText(frame, "No stable marker", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("ArUco Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    t.streamoff()
    t.end()

if __name__ == "__main__":
    main()
