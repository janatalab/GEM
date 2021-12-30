'''
Presets for use in single player GEM pilot experiment.

This experiment involves solo tapper with adaptive metronome, as in Fairhurst, Janata, and Keller (2013) but adds tap audio feedback.

    IV: alpha value
    DV: std asynchrony; subjective ratings
    Instructions: Listen to first 2 metronome tones and then synchronize

Authors: Lauren Fink, Scottie Alexander, Petr Janata
Contact: pjanata@ucdavis.edu
Repository link: https://github.com/janatalab/GEM
'''

from GEMGUI import GEMGUI
import os
import serial.tools.list_ports

def get_master_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        # Check for ID of usb adapter we use to connect Arduino
        if "Generic CDC" in p[1]:
            pid = str(p)
            return pid.split(' ')[0]

master_port = get_master_port()

rootpath = "/Users/" + os.environ['USER'] + "/Documents/Arduino/"

presets = {
    "serial": {"port": master_port, "baud_rate": 115200, "timeout": 5},
    "filename": "GEM_1player_hearSelf",
    "data_dir": "/Users/" + os.environ['USER'] +        "/Desktop/GEM_data/1person_GEM_hearSelf/",
    "hfile": rootpath + "GEM/GEM/GEMConstants.h",
    "slaves_requested": 1,
    "metronome_alpha": [0, 0.25, 0.5, 0.75, 1],
    "metronome_tempo": 120.0, #units: beats-per-minute
    "repeats": 10, #10, #number of rounds at each alpha; Fairhurst was 12
    "windows": 26, #26, #number of metronome clicks; Fairhurst = 24
    "audio_feedback": ["hear_self"],
    "metronome_heuristic": ["average"]
}

if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
