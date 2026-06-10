from djitellopy import Tello
import cv2
import time

# Initialize and connect
tello = Tello()
tello.connect()

# Turn on video streaming
tello.streamon()
frame_read = tello.get_frame_read()

# Take off
tello.takeoff()
time.sleep(2)

print("Initiating circular trajectory")

# Circular trajectory using rc control
for _ in range(72):
    # Move while yawing to create a circle
    tello.send_rc_control(30, 0, 0, 40)

    # Show the live feed at the same time
    frame = frame_read.frame
    cv2.imshow("Tello Live Feed", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    time.sleep(0.2)

# Stop movement
tello.send_rc_control(0, 0, 0, 0)
time.sleep(1)

# Land
tello.land()

# Cleanup
tello.streamoff()
tello.end()
cv2.destroyAllWindows()

print("Flight complete")
