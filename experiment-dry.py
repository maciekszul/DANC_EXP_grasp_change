import pyfirmata
import time
from psychopy import core
from psychopy import visual
from psychopy import monitors
from psychopy import gui
from psychopy import event
from psychopy import parallel
from datetime import datetime
import socket
import os
import os.path as op
import pandas as pd
from utilities import files


# for the future:
# - settings for TCP and port in JSON FILE
# - Hz measuring

exp_beginning = core.getTime() # time

board = pyfirmata.Arduino("COM3")

########### the parallel port triggering ############

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
#####################################################

############ TCP connection #########################
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

####################################################



monitors_ = {
    "office": [1920, 1080, 52.70, 29.64, 56]
}


which_monitor = "office"
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


cue = visual.Circle(
    win,
    radius=4,
    edges=40,
    units="deg",
    fillColor="red",
    lineColor="red",
    pos=(-15, 7)
)

############ EXPERIMENT SETTINGS ###################

trial_am = 50
init_time = 5 # initial wait for the exp
orange_time = 2 # waiting period for the trial to begin
green_time = 4 # duration of the trial
red_time = 3 # post trial
subject_id = "sub-666"
output_folder = "data"

files.make_folder(op.join(os.getcwd(), output_folder))
output_path = op.join(os.getcwd(), output_folder, subject_id)
files.make_folder(output_path)


############ DATA LOGGINGG #########################

data_log = {
    "ID": [],
    "trial": [],
    "exp_beginning": [],
    "init_start": [],
    "orange_start": [],
    "green_start": [],
    "red_start": [],
    "vid_dump_duration": [],
    "vid_rec_duration": [],
    "trial_duration": [],
    "trial_rec_diff": []
}

now = datetime.now()
timestamp = str(datetime.timestamp(now))

###### experiment start ############################


#trigger(0)
trigger(252)
cue.fillColor = "red"
cue.lineColor = "red"
cue.draw()
trigger(50)
init_start = win.flip()
red_wait = core.StaticPeriod()
red_wait.start(init_time)
timer = core.CountdownTimer(init_time - 0.1)
while timer.getTime() > 0:
    if event.getKeys(keyList=["escape"], timeStamped=False):
        message_finish = "exit_stop"
        conn.send(message_finish.encode())
        win.close()
        core.quit()
red_wait.complete()

for trial_n in range(trial_am):
    print("TRIAL:", trial_n, "|", trial_am)

    cue.fillColor = "orange"
    cue.lineColor = "orange"
    cue.draw()
    orange_start = win.flip()

    # orange light - preparation
    orange_wait = core.StaticPeriod()
    orange_wait.start(orange_time)
    timer = core.CountdownTimer(orange_time - 0.1)
    while timer.getTime() > 0:
        if event.getKeys(keyList=["escape"], timeStamped=False):
            message_finish = "exit_stop"
            conn.send(message_finish.encode())
            win.close()
            core.quit()
    cue.fillColor = "green"
    cue.lineColor = "green"
    cue.draw()
    orange_wait.complete()
    
    
    message_start = str(trial_n).zfill(4) + "_start_" + str(timestamp)
    conn.send(message_start.encode())
    trigger(100)
    green_start = win.flip() # light is turning green and waiting for the video to stop recording
    
    
    green_wait = core.StaticPeriod()
    green_wait.start(green_time)
    timer = core.CountdownTimer(green_time - 0.1)
    while timer.getTime() > 0:
        if event.getKeys(keyList=["escape"], timeStamped=False):
            message_finish = "exit_stop"
            conn.send(message_finish.encode())
            win.close()
            core.quit()
    cue.fillColor = "red"
    cue.lineColor = "red"
    cue.draw()
    green_wait.complete()
    

    # light is turning red, data dump + 
    message_stop = str(trial_n).zfill(4) + "_stop"
    conn.send(message_stop.encode())
    trigger(200)
    red_start = win.flip()

    gpios = [3, 4, 5, 6, 3, 4, 5, 6]

    for ix in gpios:
        board.digital[ix].write(0)
        board.digital[ix].write(1)
        time.sleep(0.2)
        board.digital[ix].write(0)

    dump_wait = core.StaticPeriod()
    dump_wait.start(red_time)

    # video logging
    while True:
        if event.getKeys(keyList=["escape"], timeStamped=False):
            message_finish = "exit_stop"
            conn.send(message_finish.encode())
            win.close()
            core.quit()
            
        data = conn.recv(buffer_size)
        if "dumped" in data.decode():
            dump_output = data.decode()
            x, dump_time, x, rec_time = dump_output.split("_")
            print(dump_output, "video data dumped")
            break
    
    # experiment logging
    data_log["ID"].append(subject_id)
    data_log["trial"].append(trial_n)
    data_log["exp_beginning"].append(exp_beginning)
    data_log["init_start"].append(init_start)
    data_log["orange_start"].append(orange_start)
    data_log["green_start"].append(green_start)
    data_log["red_start"].append(red_start)
    data_log["vid_dump_duration"].append(eval(dump_time))
    data_log["vid_rec_duration"].append(eval(rec_time))
    data_log["trial_duration"].append(red_start - green_start)
    data_log["trial_rec_diff"].append((red_start - green_start) - eval(rec_time))

    exp_log_filename = "_".join([
        subject_id,
        "grasp",
        timestamp + ".csv"
    ])
    exp_log_path = op.join(output_path, exp_log_filename)

    data_log_df = pd.DataFrame.from_dict(data_log)
    data_log_df.to_csv(exp_log_path, index_label=False, index=False)

    dump_outcome = dump_wait.complete()
    print("Dump within time:", bool(dump_outcome))
message_exit = "exit"
conn.send(message_exit.encode())
conn.close()

trigger(250)
win.close()
core.quit()

