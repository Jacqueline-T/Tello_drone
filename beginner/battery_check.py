from djitellopy import Tello

t = Tello()
t.connect(wait_for_state=False)
print(t.query_battery())
