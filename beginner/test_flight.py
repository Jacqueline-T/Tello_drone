from djitellopy import Tello
import time

t = Tello()
t.connect(wait_for_state=False)

print("Battery:", t.query_battery())

t.takeoff()

print("Hovering...")
time.sleep(5)

t.land()

t.end()
