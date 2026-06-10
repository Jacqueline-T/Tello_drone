from djitellopy import Tello

t = Tello()
t.connect()

print("SDK:", t.query_sdk_version())
print("Battery:", t.query_battery())

t.end()
