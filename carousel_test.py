from carousel_control import Carousel, Counter, Mover
import numpy as np
import time

# init
carousel = Carousel()
carousel.set_sleep_time(0.15)
carousel.init_led()
carousel.ir_test()
carousel.all_valves_off()

counter = Counter()
# counter.set_pos(30, 2) # fake calibration

mover = Mover()
mover.add_classes(carousel, counter)
mover.calibration()

# moving to different positions
trials = np.tile(counter.stops, 10)
np.random.shuffle(trials)

for target in trials:
    mover.move_to_target(target)
    time.sleep(1)
    print("\n")


carousel.all_valves_off()
carousel.stop_all()