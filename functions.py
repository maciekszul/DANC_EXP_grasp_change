import time
import numpy as np

def blow(valve_ix, sleep_time, gpios, board):
    for ix in gpios:
        board.digital[ix].write(0)
    board.digital[valve_ix].write(1)
    time.sleep(sleep_time)
    for ix in gpios:
        board.digital[ix].write(0)


def on(valve_ix, board):
    board.digital[valve_ix].write(1)


def forward(pos, valve):
    pos += 1
    valve += 1
    if pos == 36:
        pos = 0
    if valve == 4:
        valve = 0
    return pos, valve


def backward(pos, valve):
    pos -= 1
    valve -= 1
    if pos == -1:
        pos = 35
    if valve == -1:
        valve = 3
    return pos, valve


def calibration(pos, valve, positions, ir_rec_pin, gpios, time_step, board):
    pd = ir_rec_pin.read()
    while pd == None:
        pd = ir_rec_pin.read()

    pos = 0
    valve = 0
    while True:
        pos, valve = forward(pos, valve)
        blow(gpios[valve], time_step, gpios, board)
        pd = ir_rec_pin.read()
        if pd < 0.01:
            break
        print("calibration step", pos, pd)
    on(gpios[valve], board)
    pos_init = input("Which position? \n{} ".format(positions))
    for i in positions:
        if str(i) in str(pos_init):
            pos_init = i
    return int(pos_init), valve


def generate_run(tar_positions, tr_am):
    ch_am = int(np.ceil(tr_am/tar_positions.shape[0]))
    conds = np.tile(tar_positions, ch_am)
    while True:
        np.random.shuffle(conds)
        if np.mean(conds[1:] == conds[:-1]) == 0:
            break
    conds = conds[:tr_am]
    p = np.unique(conds, return_counts=True)
    cues = np.zeros(conds.shape)
    for cnd, cnt  in zip(p[0], p[1]):
        ch_cue = np.hstack([np.zeros(int(cnt/2)), np.ones(int(cnt/2))])
        while True:
            np.random.shuffle(ch_cue)
            if np.mean(ch_cue[1:] == ch_cue[:-1]) == 0:
                break
        ixs = np.where(conds == cnd)[0]
        cues[ixs] = ch_cue
    return np.vstack([conds, cues]).transpose()


def generate_steps(init_pos, target, all_pos):
    rom = np.tile(all_pos, 2)
    pos_ixs = np.where(all_pos == init_pos)[0]
    dist_tars = []
    for pos_ix in pos_ixs:
        tar_ix = np.where(rom == target)[0]
        dist_tar = tar_ix - pos_ix
        dist_tars.append(dist_tar)
    dist_tars = np.array(dist_tars).flatten()
    closest_ix = np.argmin(np.abs(dist_tars))
    steps = np.min(np.abs(dist_tars[closest_ix]))
    direction = np.sign(dist_tars[closest_ix])
    return steps, direction
