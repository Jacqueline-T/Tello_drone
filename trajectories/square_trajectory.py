'''
Robomaster                                     Djitellopy
tl_flight.forward(distance=100)                t.move_forward(100)
tl_flight.backward(distance=100)               t.move_back(100)
tl_flight.up(distance=40)                      t.move_up(40)
tl_flight.left(distance=80)                    t.move_left(80)
tl_flight.right(distance=80)                   t.move_right(80)
tl_flight.down(distance=40)                    t.move_down(40)
tl_flight.rotate(angle=180)                    t.rotate_clockwise(180)
tl_flight.rotate(angle=-180)                   t.rotate_counter_clockwise(180)
'''

from djitellopy import Tello

if __name__ == '__main__':
    t = Tello()                         
    t.connect(wait_for_state=False)     

    t.takeoff()
    t.move_up(50)

    # Square trajectory
    for _ in range(4):
        t.move_forward(100)
        t.rotate_clockwise(90)

    #t.move_forward(100)
    #t.move_back(100)
    #t.move_up(40)
    #t.move_left(80)
    #t.move_right(80)
    #t.move_down(40)
    #t.rotate_clockwise(180)
    #t.rotate_counter_clockwise(180)

    t.move_down(50)
    t.land()
    t.end()

