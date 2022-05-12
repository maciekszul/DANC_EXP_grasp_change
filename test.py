from psychopy import core
from psychopy import visual
from psychopy import monitors

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

core.wait(2)
win.close()
core.quit()