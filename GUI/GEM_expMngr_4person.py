'''
Presets for use in 4-player GEM pilot experiment.

This experiment involves four tappers with an adaptive metronome to extend the
findings of Fairhurst, Janata, and Keller (2012) to group settings.

    IV: alpha value
    DV: individual std asynchronies, group std asynchs, subjective ratings
    Instruction: Listen to first 2 metronome tones and then synchronize

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
    "filename": "GEM_4playerData",
    "data_dir": rootpath + "Data/",
    "hfile": rootpath + "GEM/GEM/GEMConstants.h",
    "slaves_requested": 4,
    "metronome_alpha": [0, 0.4, 1],
    "metronome_tempo": 120.0, #units: beats-per-minute
    "repeats": 5,
    "windows": 120, #number of windows # TODO wants 1 min rounds then short pause
    "audio_feedback": ["hear_metronome"],
    "metronome_heuristic": ["average"]
}

if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
