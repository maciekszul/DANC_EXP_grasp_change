import os
os.environ["FOR_DISABLE_CONSOLE_CTRL_HANDLER"] = "1"
import socket
import os.path as op
import pandas as pd
import numpy as np
import warnings
import files
import json
from datetime import datetime
from functions import secondary_prompt
from carousel_control import Carousel, Counter, Mover
from unittest.mock import MagicMock
from psychopy import core
from psychopy import visual
from psychopy import monitors
from psychopy import gui
from psychopy import parallel
from psychopy import event

warnings.filterwarnings("ignore")

os.system("")

trm_red = "\33[41m"
trm_green = "\33[42m"
trm_yellow = "\33[43m"
trm_blue = "\33[44m"
trm_end = "\33[0m"

# EXPERIMENT SETTINGS from JSON file

with open("exp_settings.json") as json_file:
    params = json.load(json_file)

carousel_on = params["flap"]
parallel_on = params["parallel"]
tcp_func_on = params["tcp"]
reps_am = params["reps_per_block"]
init_time = params["init_time"] # initial wait for the exp
dump_dur = params["dump_dur"] # post trial
time_step = params["time_step"]
grasp_dur = params["grasp_dur"]
output_folder = params["output_folder"]
which_monitor = params["monitor"]
instructions = params["instructions"]

# prompt and subject data
sub_info = {
    "ID": "ADD_SUBJECT"
}

prompt = gui.DlgFromDict(
    dictionary=sub_info, 
    title="SUBJECT"
)

subject_id = sub_info["ID"]
files.make_folder(op.join(os.getcwd(), output_folder))
output_path = op.join(os.getcwd(), output_folder, subject_id)
files.make_folder(output_path)
exp_info = secondary_prompt(subject_id, output_path)

prompt = gui.DlgFromDict(
    dictionary=exp_info, 
    title="MORE INFO"
)

subject_id = exp_info["ID"]
age = exp_info["age"]
gender = exp_info["gender (m/f/o)"]
block = exp_info["block"]
block_str = str(block).zfill(3)


# data logging
timestamp = str(datetime.timestamp(datetime.now()))

data_log = {
    "ID": [],
    "age": [],
    "gender": [],
    "block": [],
    "trial": [],
    "prep_start": [],
    "flap_start": [],
    "grasp_start": [],
    "dump_start": [],
    "init_start": [],
    "cue": [],
    "cue_cat": [],
    "carousel_pos": [],
    "flap_trigger": [],
    "grasp_trigger": [],
    "dump_trigger": [],
    "vid_dump_duration": [],
    "vid_rec_duration": []
}

cue_cat = {
    0: "natural",
    1: "uncomfortable"
}


# CAROUSEL CONTROL #############################################################
if carousel_on:
    carousel = Carousel(port="COM3") # COM3 only in meg
    carousel.set_sleep_time(time_step)
    carousel.init_led()
    carousel.ir_test()
    carousel.all_valves_off()
    counter = Counter()
    mover = Mover()
    mover.add_classes(carousel, counter)
    mover.calibration() # calibration
    trial_sequence = counter.generate_run(reps_am)
    print(trm_green + "CAROUSEL CONTROL ESTABLISHED" + trm_end)
else:
    print(trm_red + "RUNNING WITHOUT CAROUSEL CONTROL" + trm_end)
    counter = Counter()
    trial_sequence = counter.generate_run(reps_am)
    mover = MagicMock()
    carousel = MagicMock()

trial_am = counter.stops.shape[0] * reps_am
################################################################################


# PARALLEL PORT ################################################################
def trigger(send_bit):
    print("trigger", send_bit, "no port")

if parallel_on:
    try:
        port = parallel.ParallelPort(address=0x3FE8)
        def trigger(send_bit):
            port.setData(send_bit)
            core.wait(0.004)
            port.setData(0)

        print(trm_green + "PARALLEL PORT CONNECTION ESTABLISHED" + trm_end)

    except:
        print("no parallel port detected")
        while True:
            pp_dd = input("continue? (y/n)")
            if pp_dd == "y":
                break
            elif pp_dd == "n":
                core.quit()
            else:
                continue

else:
    print(trm_red + "RUNNING WITHOUT PARALLEL PORT" + trm_end)
################################################################################


# TCP COMMS ####################################################################
tcp_on = False
if tcp_func_on:
    tcp_yn = input("Do you want a TCP connection? (y/n)")
    if tcp_yn == "y":
        tcp_on = True
        # TCP_IP = "169.254.226.95"
        TCP_IP = "100.1.1.3"
        TCP_PORT = 5005
        buffer_size = 1024

        # setting up the connection
        print("waiting for the video computer to init")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(999)
        s.bind((TCP_IP, TCP_PORT))
        s.listen(1)
        conn, addr = s.accept()

        print("CONNECTION ADDRESS:", addr)

        # waiting for the client to initialize and connect
        while True:
            data = conn.recv(buffer_size)
            if data.decode() == "connected":
                print(trm_green + "video PC ready and connected" + trm_end)
                break
    else:
        print(trm_red + "RUNNING WITHOUT TCP CONNECTION" + trm_end)
        pass
else:
    print(trm_red + "RUNNING WITHOUT TCP CONNECTION" + trm_end)
################################################################################


def exp_abort():
    message_finish = "abort"
    if tcp_on:
        conn.send(message_finish.encode())
    win.close()
    carousel.stop_all()
    core.quit()



# monitor settings
monitors_ = {
    "office": [1920, 1080, 52.70, 29.64, 56],
    "meg": [1920, 1080, 52.70, 29.64, 56]
}

mon = monitors.Monitor("default")
w_px, h_px, w_cm, h_cm, d_cm = monitors_[which_monitor]
mon.setWidth(w_cm)
mon.setDistance(d_cm)
mon.setSizePix((w_px, h_px))

win = visual.Window(
    [w_px, h_px],
    monitor=mon,
    units="deg",
    color="#000000",
    fullscr=True,
    allowGUI=False,
    winType="pyglet"
)

win.mouseVisible = False

framerate = win.getActualFrameRate(
    nIdentical=10,
    nMaxFrames=200,
    nWarmUpFrames=10,
    threshold=1
)

print("recorded framerate:", framerate)



# creating visual objects
cue = visual.Circle(
    win,
    radius=4,
    edges=40,
    units="deg",
    fillColor="red",
    lineColor="red",
    pos=(0, 0)
)

text_stim = visual.TextStim(
    win,
    text="",
    height=0.5,
    color="white",
    pos=(-17, 13),
    anchorHoriz="center", 
    anchorVert="center"
)

# EXPERIMENT STARTS ############################################################
for text in instructions:
    text_stim.text = text
    text_stim.draw()
    win.flip()
    event.waitKeys(
        maxWait=60, 
        keyList=["space"], 
        modifiers=False, 
        timeStamped=False
    )

text_stim.text = ""
text_stim.draw()
win.flip()
trigger(252)
core.wait(2)

cue.fillColor = "red"
cue.lineColor = "red"
cue.draw()
trigger(10)
init_start = win.flip()

# initial wait and positioning of the carousel
init_wait = core.StaticPeriod()
init_wait.start(init_time)
timer = core.CountdownTimer(init_time - 0.1)
mover.move_to_target(trial_sequence[0, 0]) # initial position of the carousel
while timer.getTime() > 0:
    if event.getKeys(keyList=["escape"], timeStamped=False):
        exp_abort()
init_wait.complete()


# experiment loop
# for details, read: carousel_control.Counter.generate_run()
for trial_ix, (target_pos, trial_cue) in enumerate(trial_sequence[1:]):
    trial_msg = "\n{} block: {} | trial: {}/{}".format(subject_id, block, trial_ix+1, trial_am)
    print(trm_blue + trial_msg + trm_end)

    # wait before the onset of the trial
    cue.fillColor = "red"
    cue.lineColor = "red"
    cue.draw()
    prep_dur = np.random.uniform(0.0, 0.5)
    prep_start = win.flip()
    prep_wait = core.StaticPeriod()
    timer = core.CountdownTimer(prep_dur - 0.1)
    prep_wait.start(prep_dur)
    while timer.getTime() > 0:
        if event.getKeys(keyList=["escape"], timeStamped=False):
            exp_abort()
    prep_wait.complete()

    # prep + flap open
    cue.fillColor = "red"
    cue.lineColor = "red"
    cue.draw()
    flap_dur = np.random.uniform(0.5, 1.0)
    flap_start = win.flip()
    flap_trigger = int(target_pos+50*trial_cue+5)

    message_start = "{}_{}_{}_start_{}".format(subject_id, block_str, trial_ix, timestamp)
    print("tcp msg:", message_start)
    if tcp_on:
        conn.send(message_start.encode())
    
    carousel.flap_down()
    print(trm_green + "flap open and recording video" + trm_end)
    
    trigger(flap_trigger)
    
    flap_wait = core.StaticPeriod()
    timer = core.CountdownTimer(flap_dur - 0.1)
    flap_wait.start(flap_dur)
    while timer.getTime() > 0:
        if event.getKeys(keyList=["escape"], timeStamped=False):
            exp_abort()
    flap_wait.complete()
    
    # grasp prep + action cue
    if trial_cue == 0:
        cue_colour = "#0000FF"
    elif trial_cue == 1:
        cue_colour = "#FF00FF"

    cue.fillColor = cue_colour
    cue.lineColor = cue_colour
    cue.draw()
    grasp_start = win.flip()
    print(trm_yellow + "CUE" + trm_end)
    grasp_trigger = int(2*target_pos+50+50*trial_cue+5)
    trigger(grasp_trigger)
    grasp_wait = core.StaticPeriod()
    timer = core.CountdownTimer(grasp_dur - 0.1)
    grasp_wait.start(grasp_dur)
    while timer.getTime() > 0:
        if event.getKeys(keyList=["escape"], timeStamped=False):
            exp_abort()
    grasp_wait.complete()
    
    # flap up
    cue.fillColor = "red"
    cue.lineColor = "red"
    cue.draw()
    carousel.flap_up()
    print(trm_red + "flap closed" + trm_end)
    
    message_stop = "{}_{}_{}_stop_{}".format(subject_id, block_str, trial_ix, timestamp)
    print("tcp msg:", message_stop)
    if tcp_on:
        conn.send(message_stop.encode())

    # ITI aka DUMP PERIOD aka move the carousel
    dump_start = win.flip()
    dump_trigger = int(3*target_pos+100+50*trial_cue+5)
    trigger(dump_trigger)
    dump_wait = core.StaticPeriod()
    timer = core.CountdownTimer(dump_dur - 0.1)
    dump_wait.start(dump_dur)

    filename = "block-{}_{}_{}.csv".format(
        block_str,
        subject_id,
        timestamp
    )
    filename = op.join(output_path, filename)

    data_log["ID"].append(subject_id)
    data_log["age"].append(age)
    data_log["gender"].append(gender)
    data_log["block"].append(block)
    data_log["trial"].append(trial_ix)
    data_log["prep_start"].append(prep_start)
    data_log["flap_start"].append(flap_start)
    data_log["grasp_start"].append(grasp_start)
    data_log["dump_start"].append(dump_start)
    data_log["init_start"].append(init_start)
    data_log["cue"].append(trial_cue)
    data_log["cue_cat"].append(cue_cat[trial_cue])
    data_log["carousel_pos"].append(target_pos)
    data_log["flap_trigger"].append(flap_trigger)
    data_log["grasp_trigger"].append(grasp_trigger)
    data_log["dump_trigger"].append(dump_trigger)
    data_log["vid_dump_duration"].append(0)
    data_log["vid_rec_duration"].append(0)

    pd.DataFrame.from_dict(data_log).to_csv(filename)

    mover.move_to_target(target_pos)

    
    if tcp_on:
        while True:
            data_raw = conn.recv(buffer_size)
            data = data_raw.decode()
            if "dump" in data:
                print(data)
                break
    
    dump_wait.complete()


# END OF THE BLOCK CLEANING #

trigger(250)

message_convert = "{}_0_0_convert_{}".format(subject_id, timestamp)
print("tcp msg:", message_convert)
if tcp_on:
    conn.send(message_convert.encode())


message_exit = "{}_0_0_exit_{}".format(subject_id, timestamp)
print("tcp msg:", message_exit)
if tcp_on:
    conn.send(message_exit.encode())

carousel.stop_all()
print("carousel closed")
win.close()
print("window closed")
core.quit()

