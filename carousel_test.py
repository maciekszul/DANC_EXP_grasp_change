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
trial_sequence = counter.generate_run(2)

print(trial_sequence)

for trial, target in enumerate(trial_sequence[:-1,0]):
    print("trial", trial+1, "cue", trial_sequence[trial, 1])
    mover.move_to_target(target)
    carousel.flap_up()
    time.sleep(1)
    carousel.flap_down()
    print("\n")




carousel.all_valves_off()
carousel.stop_all()