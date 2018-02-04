'''
Presets for use in debugging.
'''

from GEMGUI import GEMGUI
import os

rootpath = "/Users/" + os.environ['USER'] + "/Documents/Arduino/"

presets = {
    "serial": {"port": "/dev/cu.usbmodem1451111", "baud_rate": 115200, "timeout": 5},
    "filename": "throughput",
    "data_dir": rootpath + "Data/", #TODO: change on lab computer
    "hfile": rootpath + "GEM/GEM/GEMConstants.h",
    "slaves_requested": 1,
    "metronome_alpha": [0],
    "metronome_tempo": 120.0, #units: beats-per-minute
    "repeats": 1,#10, #fairhurst was 12
    "windows": 20, #26, #number of windows
    "audio_feedback": ["hear_metronome"],
    "metronome_heuristic": ["average"]
}

if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
