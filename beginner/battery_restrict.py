from djitellopy import Tello

if __name__ == '__main__':
    t = Tello()                         # Same as tl_drone = robot.Drone()
    t.connect(wait_for_state=False)     # Same as tl_drone.initialize()

    # Get battery status
    battery = t.query_battery()
    print("Drone battery soc: {}%".format(battery))

    # Check if battery is sufficient for flight
    if battery <= 10:
        print("Battery too low for flight. Please recharge.")
        t.end()  # Ends the connection to the drone
    else:
        print("Battery sufficient for flight. You can take off.")
        t.end()
