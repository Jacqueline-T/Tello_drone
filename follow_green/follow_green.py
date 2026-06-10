from djitellopy import Tello
import cv2
import numpy as np
import time

# =========================================================
# PD controller gains
# =========================================================
Kp_yaw = 0.25
Kd_yaw = 0.10

Kp_z = 0.20
Kd_z = 0.08

prev_error_yaw = 0
prev_error_z = 0

# =========================================================
# HEIGHT LIMITS (cm)
# =========================================================
MAX_HEIGHT = 100
MIN_HEIGHT = 50

# =========================================================
# Green HSV range
# =========================================================
lower_green = np.array([40, 50, 50])
upper_green = np.array([80, 255, 255])

# =========================================================
# Connect to Tello
# =========================================================
t = Tello()
t.connect(wait_for_state=False)

battery = t.get_battery()
print(f"Battery: {battery}%")

# Safer battery threshold
if battery <= 25:
    print("Battery too low for safe tracking flight.")
    t.end()
    exit()

# =========================================================
# Start stream
# =========================================================
t.streamon()
time.sleep(2)

cap = cv2.VideoCapture("udp://0.0.0.0:11111", cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Stream failed to open")
    t.streamoff()
    t.end()
    exit()

# =========================================================
# Takeoff
# =========================================================
t.takeoff()
time.sleep(2)

print("Hovering — tracking active. Press ESC to land.")

try:

    while True:

        ret, frame = cap.read()

        # =================================================
        # FAILSAFE: stop movement if frame is invalid
        # =================================================
        if not ret or frame is None:
            t.send_rc_control(0, 0, 0, 0)
            continue

        frame = cv2.resize(frame, (480, 360))

        # =================================================
        # Get drone height
        # =================================================
        height = t.get_height()

        # =================================================
        # Green detection
        # =================================================
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, lower_green, upper_green)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # =================================================
        # Default hover values
        # =================================================
        yaw_speed = 0
        ud = 0

        if contours:

            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)

            # =============================================
            # Ignore tiny noisy detections
            # =============================================
            if area > 500:

                x, y, w, h = cv2.boundingRect(largest)

                cx = x + w // 2
                cy = y + h // 2

                # =========================================
                # PD Yaw Control
                # =========================================
                error_yaw = cx - 240
                derivative_yaw = error_yaw - prev_error_yaw

                yaw_speed = (
                    Kp_yaw * error_yaw
                    + Kd_yaw * derivative_yaw
                )

                # Deadzone
                if abs(error_yaw) < 20:
                    yaw_speed = 0

                # Safer yaw clamp
                yaw_speed = int(np.clip(yaw_speed, -30, 30))

                # =========================================
                # PD Height Control
                # =========================================
                error_z = 180 - cy
                derivative_z = error_z - prev_error_z

                ud = (
                    Kp_z * error_z
                    + Kd_z * derivative_z
                )

                # Deadzone
                if abs(error_z) < 15:
                    ud = 0

                # Safer vertical clamp
                ud = int(np.clip(ud, -15, 15))

                # =========================================
                # HEIGHT LIMITS
                # =========================================

                # Prevent climbing too high
                if height >= MAX_HEIGHT and ud > 0:
                    ud = 0

                # Prevent descending too low
                if height <= MIN_HEIGHT and ud < 0:
                    ud = 0

                prev_error_yaw = error_yaw
                prev_error_z = error_z

                # =========================================
                # Send RC command
                # =========================================
                t.send_rc_control(0, 0, ud, yaw_speed)

                # =========================================
                # Draw visuals
                # =========================================
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                cv2.circle(
                    frame,
                    (cx, cy),
                    5,
                    (255, 0, 0),
                    -1
                )

                cv2.putText(
                    frame,
                    f"yaw:{yaw_speed} ud:{ud}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

            else:
                # Tiny contour/noise → hover
                t.send_rc_control(0, 0, 0, 0)

                cv2.putText(
                    frame,
                    "Noise ignored",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )

        else:
            # =============================================
            # No target → hover safely
            # =============================================
            t.send_rc_control(0, 0, 0, 0)

            cv2.putText(
                frame,
                "Green not detected",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )

        # =================================================
        # Show current height
        # =================================================
        cv2.putText(
            frame,
            f"Height: {height} cm",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

        # =================================================
        # Display windows
        # =================================================
        cv2.imshow("Tello Tracking", frame)
        cv2.imshow("Green Mask", mask)

        # ESC key
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
