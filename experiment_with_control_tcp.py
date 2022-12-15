import socket
import os
import os.path as op
import time
import pandas as pd
import numpy as np
import files
import json
from pyfirmata2 import Arduino
from psychopy import core
from psychopy import visual
from psychopy import monitors
from psychopy import gui
from psychopy import event
from psychopy import parallel
from datetime import datetime
from carousel_control import Carousel, Counter, Mover

import warnings

warnings.filterwarnings("ignore")

exp_beginning = core.getTime() # time

############### EXPERIMENT SETTINGS ###################

with open("exp_settings.json") as json_file:
    params = json.load(json_file)

# exp timing from JSON file
reps_am = params["reps_per_run"]
init_time = params["init_time"] # initial wait for the exp
dump_dur = params["dump_dur"] # post trial
grasp_dur = params["grasp_dur"]
output_folder = params["output_folder"]
which_monitor = params["monitor"]

# prompt about ses and subj

sub_info = {
    "ID": "sub-666"
}

prompt = gui.DlgFromDict(
    dictionary=sub_info, 
    title="SUBJECT"
)

subject_id = sub_info["ID"]
files.make_folder(op.join(os.getcwd(), output_folder))
output_path = op.join(os.getcwd(), output_folder, subject_id)
files.make_folder(output_path)
#### the trickery to get the data ###
all_the_files = files.get_files(output_path, "run", ".csv")[2]
all_the_files.sort()
try:
    last_file = all_the_files[-1]
    dem_data = pd.read_csv(last_file)
    age_prev = dem_data.age.unique()[0]
    gender_prev = dem_data.gender.unique()[0]
    run_prev = dem_data.run.unique()[0]
    exp_info = {
        "ID": subject_id,
        "age": age_prev,
        "gender (m/f/o)": gender_prev,
        "run": run_prev + 1
    }
except:
    exp_info = {
        "ID": subject_id,
        "age": "ADD_AGE",
        "gender (m/f/o)": "ADD_GENDER",
        "run": 0
    }

prompt = gui.DlgFromDict(
    dictionary=exp_info, 
    title="OTHER DATA"
)


subject_id = exp_info["ID"]
age = exp_info["age"]
gender = exp_info["gender (m/f/o)"]
run = exp_info["run"]

instructions = params["instructions"]

# data logging
timestamp = str(datetime.timestamp(datetime.now()))

# motor parameters
carousel = Carousel()
carousel.set_sleep_time(0.15)
carousel.init_led()
carousel.ir_test()
carousel.all_valves_off()

counter = Counter()

mover = Mover()
mover.add_classes(carousel, counter)
mover.calibration()
############### EXPERIMENT SETTINGS ###################
trial_am = counter.stops.shape[0] * reps_am
########### generating the trial sequence #############
trial_sequence = counter.generate_run(reps_am)

############ the parallel port triggering #############
try:
    port = parallel.ParallelPort(address=0x3FE8)
    def trigger(send_bit):
        port.setData(send_bit)
        core.wait(0.004)
        port.setData(0)

except:
    print("no parallel port detected")
    while True:
        pp_dd = input("continue? (y/n)")
        if pp_dd == "y":
            break
        if pp_dd == "n":
            core.quit()
        else:
            continue

    port = []
    def trigger(send_bit):
        print("trigger", send_bit, "no port")

############ the parallel port triggering #############

################### TCP CONNECTION ####################
tcp_yn = ("Do you want a TCP connection? (y/n)")
tcp_on = False
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
            print("video PC ready and connected")
            break
else:
    pass

################## monitor settings ###################
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
################## monitor settings ###################

###################### objects ########################

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

###################### objects ########################

############### DATA LOGGINGG #########################
data_log = {
    "ID": [],
    "age": [],
    "gender": [],
    "run": [],
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

############### DATA LOGGINGG #########################

####################### START #########################



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
win.flip()

trigger(252)

core.wait(2)

cue.fillColor = "red"
cue.lineColor = "red"
cue.draw()
trigger(10)
init_start = win.flip()
init_wait = core.StaticPeriod()
init_wait.start(init_time)
timer = core.CountdownTimer(init_time - 0.1)

##### first trial position #####
mover.move_to_target(trial_sequence[0, 0])
##################################

while timer.getTime() > 0:
    if event.getKeys(keyList=["escape"], timeStamped=False):
        message_finish = "exit_stop"
        if tcp_on:
            conn.send(message_finish.encode())
        win.close()
        carousel.stop_all()
        core.quit()
init_wait.complete()


for trial_ix, (target_pos, trial_cue) in enumerate(trial_sequence[1:]):
    print("\ntrial: {}/{}".format(trial_ix+1, trial_am))
    
    trial_cue = int(trial_cue)

    cue.fillColor = "red"
    cue.lineColor = "red"
    cue.draw()

    text = "PREP\ntrial:{0}\ncurrent_pos:{3}\ntarget_pos:{1}\ncue:{2}".format(trial_ix, target_pos, trial_cue, counter.pos)
    text_stim.text = text
    text_stim.draw()
    
    prep_dur = np.random.uniform(0.0, 0.5)
    prep_start = win.flip()
    prep_wait = core.StaticPeriod()
    timer = core.CountdownTimer(prep_dur - 0.1)
    prep_wait.start(prep_dur)
    
    # prep wait code ?
    
    while timer.getTime() > 0:
        if event.getKeys(keyList=["escape"], timeStamped=False):
            message_finish = "exit_stop"
            win.close()
            carousel.stop_all()
            core.quit()
    prep_wait.complete()

    # FLAP OPEN
    cue.fillColor = "red"
    cue.lineColor = "red"
    cue.draw()

    text = "FLAP\ntrial:{0}\ncurrent_pos:{3}\ntarget_pos:{1}\ncue:{2}\nFLAP IS OPEN + RECORDING".format(trial_ix, target_pos, trial_cue, counter.pos)
    text_stim.text = text
    text_stim.draw()
    
    flap_dur = np.random.uniform(0.5, 1.0)
    flap_start = win.flip()
    flap_trigger = int(target_pos+50*trial_cue+5)
    carousel.flap_up()
    trigger(flap_trigger)
    flap_wait = core.StaticPeriod()
    timer = core.CountdownTimer(flap_dur - 0.1)
    flap_wait.start(flap_dur)

    # flap wait code ?
    
    while timer.getTime() > 0:
        if event.getKeys(keyList=["escape"], timeStamped=False):
            message_finish = "exit_stop"
            win.close()
            carousel.stop_all()
            core.quit()

    flap_wait.complete()
    carousel.flap_down()

    # GRASP ONSET
    if trial_cue == 0:
        cue_colour = "#0000FF"
    elif trial_cue == 1:
        cue_colour = "#FF00FF"

    cue.fillColor = cue_colour
    cue.lineColor = cue_colour
    cue.draw()

    text = "GRASP\ntrial:{0}\ncurrent_pos:{3}\ntarget_pos:{1}\ncue:{2}\nFLAP IS OPEN + RECORDING + GRASP".format(trial_ix, target_pos, trial_cue, counter.pos)
    text_stim.text = text
    text_stim.draw()

    grasp_start = win.flip()
    grasp_trigger = int(2*target_pos+50+50*trial_cue+5)
    trigger(grasp_trigger)
    grasp_wait = core.StaticPeriod()
    
    timer = core.CountdownTimer(grasp_dur - 0.1)
    grasp_wait.start(grasp_dur)
    
    # grasp wait code ? 
    while timer.getTime() > 0:
        if event.getKeys(keyList=["escape"], timeStamped=False):
            message_finish = "exit_stop"
            win.close()
            carousel.stop_all()
            core.quit()

    grasp_wait.complete()


    # ITI
    cue.fillColor = "red"
    cue.lineColor = "red"
    cue.draw()

    text = "ITI\ntrial:{0}\ncurrent_pos:{3}\ntarget_pos:{1}\ncue:{2}".format(trial_ix, target_pos, trial_cue, counter.pos)
    text_stim.text = text
    text_stim.draw()

    dump_start = win.flip()
    dump_trigger = int(3*target_pos+100+50*trial_cue+5)
    trigger(dump_trigger)
    dump_wait = core.StaticPeriod()
    timer = core.CountdownTimer(dump_dur - 0.1)
    dump_wait.start(dump_dur)
    
    # dump wait code ?

    ## motor
    mover.move_to_target(target_pos)

    ## data
    cue_cat = {
        0: "natural",
        1: "uncomfortable"
    }

    filename = "run-{}_{}_{}.csv".format(
        str(run).zfill(3),
        subject_id,
        timestamp
    )
    filename = op.join(output_path, filename)

    data_log["ID"].append(subject_id)
    data_log["age"].append(age)
    data_log["gender"].append(gender)
    data_log["run"].append(run)
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

    while timer.getTime() > 0:
        if event.getKeys(keyList=["escape"], timeStamped=False):
            message_finish = "exit_stop"
            win.close()
            carousel.stop_all()
            core.quit()

    dump_wait.complete()


trigger(250)

win.close()
carousel.stop_all()
core.quit()