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

rootpath = "/Users/" + os.environ['USER'] + "/Documents/Arduino/"

presets = {
    "serial": {"port": "/dev/cu.usbmodem1441111", "baud_rate": 115200, "timeout": 5},
    "filename": "GEM_4playerData_",
    "data_dir": "/Users/janatalab/Documents/Arduino/Data",
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