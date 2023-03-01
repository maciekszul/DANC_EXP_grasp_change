from carousel_control import Carousel, Counter, Mover
import numpy as np
import time

# init
carousel = Carousel(port="COM3") # COM3 only in meg
carousel.set_sleep_time(0.2)
carousel.init_led()
carousel.ir_test()
carousel.all_valves_off()

counter = Counter()
# counter.set_pos(30, 2) # fake calibration

mover = Mover()
mover.add_classes(carousel, counter)
mover.calibration()

# moving to different positions
trial_sequence = counter.generate_run(2)

print(trial_sequence)

for trial, (target, cond) in enumerate(trial_sequence[:-2]):

    mover.move_to_target(target)
    time.sleep(1)
    mover.signal_at_stops()
    carousel.flap_up()
    time.sleep(3)
    carousel.flap_down()
    time.sleep(2)
    print("\n")




carousel.all_valves_off()
carousel.stop_all()