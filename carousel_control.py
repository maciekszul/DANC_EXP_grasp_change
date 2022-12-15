import time
import numpy as np
from pyfirmata2 import Arduino
import warnings

warnings.filterwarnings(
    action="ignore",
    category=UserWarning
)



class Carousel:
    def __init__(self, sampling_rate=100, port="auto", motor=[3, 4, 5, 6], flap=2):
        self.sampling_rate = sampling_rate
        if port == "auto":
            self.PORT = Arduino.AUTODETECT
            self.board = Arduino(self.PORT)
        else:
            self.PORT = port
            self.board = Arduino(self.PORT)
        self.board.samplingOn(1000 / sampling_rate)
        self.gpios = {
            "motor": motor,
            "flap": flap
        }

    def set_sleep_time(self, sleep_time):
        self.sleep_time = sleep_time


    def init_led(self, led_pin="d:11:p", rec_pin="a:0:i"):
        self.ir_led = self.board.get_pin(led_pin)
        self.ir_led.write(True)
        self.ir_rec = self.board.get_pin(rec_pin)
        self.ir_rec.enable_reporting()


    def ir(self):
        return self.ir_rec.read()
    
    def ir_test(self, t=2, true_output=False):

        if true_output:
            start_time = time.time()
            while time.time() - start_time <= t:
                signal = self.ir()
                print(signal)                    
                time.sleep(0.2)
            return signal
        else:
            print(
                "{} s infrared sensor test. If there is an object between two\n".format(t) +
                "LEDs there should be no bars indicating strength of the signal.\n" +
                ":|||||||||||||||||||||||||||||||||    ->    good signal\n" +
                ":                                     ->    bad signal or blocked sensor\n"
                )
            time
            start_time = time.time()
            while time.time() - start_time <= t:
                try:
                    signal = self.ir()
                    if signal != None:
                        signal = int(signal*300)
                        print(":" + "|"*signal)
                    time.sleep(0.2)
                except KeyboardInterrupt:
                    break

    
    def all_valves_off(self):
        for ix in self.gpios["motor"]:
            self.board.digital[ix].write(0)
        self.board.digital[self.gpios["flap"]].write(0)
    
    def valve_on(self, ix):
        self.board.digital[self.gpios["motor"][ix]].write(1)

    def flap_up(self):
        self.board.digital[self.gpios["flap"]].write(1)
    
    def flap_down(self):
        self.board.digital[self.gpios["flap"]].write(0)
    
    def blow(self, ix):
        self.all_valves_off()
        self.valve_on(ix)
        time.sleep(self.sleep_time)
        self.all_valves_off()
    
    def stop_all(self):
        self.ir_led.write(0)
        self.ir_rec.disable_reporting()

class Counter():
    def __init__(self, total_steps=36, stops=[0, 6, 12, 18, 24, 30], gpios=4):
        self.pos_range = list(range(total_steps))
        self.total_steps = total_steps
        self.stops = np.array(stops)
        self.pos = 0
        self.valve_ix = 0
        self.gpios = gpios
        self.calibration = False
    
    def set_pos(self, calib_step, calib_valve_ix):
        self.pos = calib_step
        self.valve_ix = calib_valve_ix
        self.calibration = True

    def step_fwd(self):
        self.valve_ix += 1
        self.pos += 1
        if self.valve_ix == self.gpios:
            self.valve_ix = 0
        if self.pos == self.total_steps:
            self.pos = 0
        return self.valve_ix
    
    def step_back(self):
        self.valve_ix -= 1
        self.pos -= 1
        if self.valve_ix == -1:
            self.valve_ix = self.gpios - 1
        if self.pos == -1:
            self.pos = self.pos_range[-1]
        return self.valve_ix
    
    def in_stop(self):
        return self.pos in self.stops
    

    def generate_run(self, reps):
        if reps % 2 == 0:
            positions = np.tile(self.stops, reps)
            iters = 0
            while True:
                iters += 1
                print(iters, end="\r")
                np.random.shuffle(positions)
                if all(positions[:-1] != positions[1:]):
                    break
            cues = np.zeros(positions.shape)
            for pos in self.stops:
                pos_ix = np.where(positions == pos)[0]
                sub_cues = np.hstack([
                    np.ones(int(pos_ix.shape[0]/2)),
                    np.zeros(int(pos_ix.shape[0]/2))
                ])
                while True:
                    iters += 1
                    print(iters, end="\r")
                    np.random.shuffle(sub_cues)
                    if all(sub_cues[:-1] != sub_cues[1:]):
                        break
                cues[pos_ix] = sub_cues
            trial_sequence = np.vstack([positions, cues]).transpose()
            trial_sequence = np.vstack([
                np.append(trial_sequence[:,0], trial_sequence[-1,0]),
                np.insert(trial_sequence[:,1], 0, trial_sequence[0,1])
            ]).transpose()
            return trial_sequence.astype(int)
        else:
            print("{} repetitions, has to be an odd number".format(reps))
        


class Mover():
    def __init_(self):
        """
        None - if not defined 
        """
        self.null = "null"
    
    def add_classes(self, carousel, counter):
        self.carousel = carousel
        self.counter = counter


    def calibration(self):
        while True:
            signal = self.carousel.ir()
            if signal > 0.005:
                self.carousel.blow(self.counter.step_fwd())
            elif signal < 0.005:
                self.carousel.valve_on(self.counter.valve_ix)
                calib_pos = input("Position of a carousel: ")
                self.counter.set_pos(int(calib_pos), self.counter.valve_ix)
                break
                

    def move_to_target(self, target, printing=True):
        pos = self.counter.pos
        stop = target
        step_range_pos = np.hstack([
            np.arange(pos - 35, pos),
            np.arange(pos, pos+36)
        ])
        below = np.where((step_range_pos < 0))[0]
        above = np.where((step_range_pos >= 36))[0]
        step_range_pos[below] = step_range_pos[below] + 36
        step_range_pos[above] = step_range_pos[above] - 36
        curr_ix = np.where(step_range_pos==pos)[0][0]
        target_ixs = np.where(step_range_pos==stop)[0]
        target_steps = target_ixs - curr_ix
        choice = target_steps[np.argmin(np.abs(target_steps))]
        direction = np.sign(choice)
        steps = np.abs(choice)

        dir_lab = "none"
        if direction == 1:
            dir_lab = "forwards"
        elif direction == -1:
            dir_lab = "backwards"

        if printing:
            print(
                "dir:{} curr_pos: {} target pos: {} steps: {}/{}".format(
                    dir_lab, self.counter.pos, target, 0, steps
                )
            )
        for _click in range(steps):
            if direction == 1:
                self.carousel.blow(self.counter.step_fwd())
            elif direction == -1:
                self.carousel.blow(self.counter.step_back())
            
            if printing:
                print(
                    "dir:{} curr_pos: {} target pos: {} steps: {}/{}".format(
                        dir_lab, self.counter.pos, target, _click + 1, steps
                    )
                )
        
        if dir_lab == "none":
            for _click in range(3):
                self.carousel.blow(self.counter.step_fwd())
                dir_lab = "forwards"
                if printing:
                    print(
                        "FAKE MOVE: dir:{} curr_pos: {} target pos: {} steps: {}/{}".format(
                            dir_lab, self.counter.pos, target, _click + 1, 6
                        )
                    )
            for _click in range(3):
                self.carousel.blow(self.counter.step_back())
                dir_lab = "backwards"
                if printing:
                    print(
                        "FAKE MOVE: dir:{} curr_pos: {} target pos: {} steps: {}/{}".format(
                            dir_lab, self.counter.pos, target, _click + 4, 6
                        )
                    )
        self.carousel.valve_on(self.counter.valve_ix)