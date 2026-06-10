from djitellopy import Tello
import time

t = Tello()
t.connect(wait_for_state=False)

battery = t.get_battery()
print(f"Battery: {battery}%")

if battery <= 25:
    print("Battery too low.")
    t.end()
    exit()

t.takeoff()
print("Hovering for 10 seconds...")

time.sleep(10)

print("Landing...")
t.land()
t.end()
print("Done.")
