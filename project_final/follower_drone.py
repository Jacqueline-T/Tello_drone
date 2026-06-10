from djitellopy import Tello
import cv2
import cv2.aruco as aruco
import numpy as np
import time
from collections import deque, Counter
import threading

# =========================================================
# PD gains
# =========================================================
Kp_yaw = 0.25;  Kd_yaw = 0.10
Kp_ud  = 0.30;  Kd_ud  = 0.10
Kp_fb  = 0.08;  Kd_fb  = 0.04

prev_error_yaw = 0
prev_error_ud  = 0
prev_error_fb  = 0

# =========================================================
# Height limits (cm)
# =========================================================
MAX_HEIGHT = 150
MIN_HEIGHT = 30

# =========================================================
# ArUco distance target
# =========================================================
TARGET_AREA   = 4500
AREA_DEADZONE = 800

# Frame centre
FRAME_CX = 480
FRAME_CY = 360

# =========================================================
# Lost marker timeout (seconds before landing)
# =========================================================
LOST_TIMEOUT = 5.0

# =========================================================
# ArUco setup
# =========================================================
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
parameters.adaptiveThreshWinSizeMin    = 3
parameters.adaptiveThreshWinSizeMax    = 23
parameters.adaptiveThreshWinSizeStep   = 4
parameters.minMarkerPerimeterRate      = 0.05
parameters.maxMarkerPerimeterRate      = 4.0
parameters.polygonalApproxAccuracyRate = 0.05
parameters.errorCorrectionRate         = 0.3
parameters.minCornerDistanceRate       = 0.05
parameters.minDistanceToBorder         = 3
parameters.cornerRefinementMethod      = aruco.CORNER_REFINE_SUBPIX
parameters.adaptiveThreshConstant      = 7
parameters.minOtsuStdDev               = 5.0

# =========================================================
# Threaded frame reader
# =========================================================
latest_frame = None
frame_lock   = threading.Lock()

def frame_reader(cap):
    global latest_frame
    while True:
        ret, frame = cap.read()
        if ret and frame is not None:
            with frame_lock:
                latest_frame = frame

# =========================================================
# Connect to Tello
# =========================================================
t = Tello()
t.connect(wait_for_state=False)

battery = t.get_battery()
print(f"Battery: {battery}%")

if battery <= 25:
    print("Battery too low.")
    t.end()
    exit()

# =========================================================
# Start stream
# =========================================================
t.streamon()
print("Stream on")
time.sleep(2)

cap = cv2.VideoCapture(
    "udp://0.0.0.0:12345?overrun_nonfatal=1&fifo_size=5000000",
    cv2.CAP_FFMPEG
)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Stream failed to open")
    t.streamoff()
    t.end()
    exit()

reader_thread = threading.Thread(target=frame_reader, args=(cap,), daemon=True)
reader_thread.start()

# =========================================================
# Takeoff
# =========================================================
t.takeoff()
time.sleep(2)
print("Hovering — ArUco tracking active. Press ESC to land.")

history       = deque(maxlen=5)
lost_since    = None   # timestamp when marker was last lost

try:
    while True:
        with frame_lock:
            frame = latest_frame.copy() if latest_frame is not None else None

        if frame is None:
            t.send_rc_control(0, 0, 0, 0)
            time.sleep(0.01)
            continue

        frame  = cv2.resize(frame, (960, 720))
        height = t.get_height()

        # =====================================================
        # ArUco detection
        # =====================================================
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray  = clahe.apply(gray)

        corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        if ids is not None:
            history.append(int(ids.flatten()[0]))
        else:
            history.append(None)

        stable_id = None
        if len(history) == 5:
            most_common, count = Counter(history).most_common(1)[0]
            if count >= 3 and most_common is not None:
                stable_id = most_common

        yaw_speed = 0
        ud        = 0
        fb        = 0
        mode      = "hover"

        # =====================================================
        # ArUco found
        # =====================================================
        if stable_id is not None and corners:
            lost_since = None  # reset lost timer
            mode       = "aruco"

            c    = corners[0][0]
            x0   = int(c[:, 0].min())
            y0   = int(c[:, 1].min())
            x1   = int(c[:, 0].max())
            y1   = int(c[:, 1].max())
            cx   = (x0 + x1) // 2
            cy   = (y0 + y1) // 2
            area = (x1 - x0) * (y1 - y0)

            error_yaw      = cx - FRAME_CX
            deriv_yaw      = error_yaw - prev_error_yaw
            yaw_speed      = Kp_yaw * error_yaw + Kd_yaw * deriv_yaw
            if abs(error_yaw) < 30:
                yaw_speed  = 0
            yaw_speed      = int(np.clip(yaw_speed, -30, 30))
            prev_error_yaw = error_yaw

            error_ud      = FRAME_CY - cy
            deriv_ud      = error_ud - prev_error_ud
            ud            = Kp_ud * error_ud + Kd_ud * deriv_ud
            if abs(error_ud) < 20:
                ud        = 0
            ud            = int(np.clip(ud, -40, 25))
            if height >= MAX_HEIGHT and ud > 0: ud = 0
            if height <= MIN_HEIGHT and ud < 0: ud = 0
            prev_error_ud = error_ud

            error_fb      = area - TARGET_AREA
            deriv_fb      = error_fb - prev_error_fb
            fb            = -(Kp_fb * error_fb + Kd_fb * deriv_fb)
            if abs(error_fb) < AREA_DEADZONE:
                fb        = 0
            fb            = int(np.clip(fb, -12, 12))
            prev_error_fb = error_fb

            t.send_rc_control(0, fb, ud, yaw_speed)

            aruco.drawDetectedMarkers(frame, corners, ids)
            cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 6, (255, 0, 0), -1)

        # =====================================================
        # ArUco lost
        # =====================================================
        else:
            mode = "lost"

            # Start lost timer if not already started
            if lost_since is None:
                lost_since = time.time()

            elapsed = time.time() - lost_since

            # Hover while waiting
            t.send_rc_control(0, 0, 0, 0)

            # Countdown on HUD
            remaining = max(0, LOST_TIMEOUT - elapsed)
            cv2.putText(frame, f"Marker lost — landing in {remaining:.1f}s",
                        (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Land after timeout
            if elapsed >= LOST_TIMEOUT:
                print("Marker lost for 5 seconds — landing safely.")
                break

        # =====================================================
        # HUD
        # =====================================================
        mode_colors = {"aruco": (0, 255, 0), "lost": (0, 0, 255), "hover": (0, 255, 255)}
        cv2.putText(frame, f"Mode: {mode}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_colors[mode], 2)
        cv2.putText(frame, f"yaw:{yaw_speed}  ud:{ud}  fb:{fb}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Height: {height} cm",
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Follower Drone", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

except KeyboardInterrupt:
    print("Interrupted — landing...")

finally:
    print("Landing safely...")
    t.send_rc_control(0, 0, 0, 0)
    time.sleep(0.5)
    t.land()
    cap.release()
    cv2.destroyAllWindows()
    t.streamoff()
    t.end()
    print("Landed safely.")
