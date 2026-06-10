from djitellopy import Tello
import time

# =========================================================
# Connect
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
# Takeoff
# =========================================================
t.takeoff()
print("Taking off...")
time.sleep(3)  # stabilise after takeoff

# =========================================================
# Trajectory
# All movements are slow to keep ArUco visible to Drone 2
# =========================================================

# Move forward slowly
print("Moving forward...")
t.move_forward(50)   # 50 cm
time.sleep(2)

# Slide left
print("Moving left...")
t.move_left(40)      # 40 cm
time.sleep(2)

# Slide right 
print("Moving right...")
t.move_right(80)     # 40 cm
time.sleep(2)

# Slide left (back to centre)
print("Moving left...")
t.move_left(40)      # 40 cm
time.sleep(2)

# Move back to start
print("Moving back...")
t.move_back(50)      # 50 cm
time.sleep(2)

# =========================================================
# Land
# =========================================================
print("Landing...")
t.land()
t.end()
print("Done.")
