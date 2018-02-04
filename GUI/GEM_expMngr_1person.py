'''
Presets for use in single player GEM pilot experiment.

This experiment involves solo tapper with adaptive metronome to make
sure that we can replicate the single-tapper results of Fairhurst, Janata, and
Keller, 2012, with the GEM system.

    IV: alpha value
    DV: std asynchrony; sunjective ratings
    Instructions: Listen to first 2 metronome tones and then synchronize

Authors: Lauren Fink, Scottie Alexander, Petr Janata
Contact: pjanata@ucdavis.edu
Repository link: https://github.com/janatalab/GEM
'''

from GEMGUI import GEMGUI
import os

rootpath = "/Users/" + os.environ['USER'] + "/Documents/Arduino/"

presets = {
    "serial": {"port": "/dev/cu.usbmodem1451111", "baud_rate": 115200, "timeout": 5},
    "filename": "GEM_1playerPilot",
    "data_dir": "/Users/janatalab/Documents/Arduino/Data", #TODO: change on lab computer
    "hfile": rootpath + "GEM/GEM/GEMConstants.h",
    "slaves_requested": 1,
    "metronome_alpha": [0, 0.25, 0.5, 0.75, 1],
    "metronome_tempo": 120.0, #units: beats-per-minute
    "repeats": 1,#10, #fairhurst was 12
    "windows": 20, #26, #number of windows
    "audio_feedback": ["hear_metronome"],
    "metronome_heuristic": ["average"]
}

if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
