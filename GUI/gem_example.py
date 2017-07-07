from GEMGUI import GEMGUI
import serial
from time import time

presets = {
    "serial": {"port": "/dev/cu.usbmodem1421", "baud_rate": 115200, "timeout": 5},
    "filename": "GEM_data_",
    "data_dir": "/Users/laurenfink/Documents/Arduino/",
    "hfile": "/Users/laurenfink/Documents/Arduino/GEM/GEM/GEMConstants.h",
    # "sound_dir": "<sound_dir>",
    "slaves_requested": 3, #NB: only 3 slaves working in Davis rig
    #"master_sound": "1.WAV",
    # "slave_sound":  [
    #                     "1.WAV",
    #                     "1.WAV",
    #                     "1.WAV"
    #                 ],
    "metronome_alpha": [0.0, 0.25, 0.5, 0.75, 1.0],
    "metronome_tempo": 150.0, #units: beats-per-minute
    "repeats": 2.0,
    "windows": 50.0, #number of windows

    # TODO: deal with audio_feedback
    # control the master sound, send message to experimenter through data viewer
    # run trials blocked by audio feeback. randomize order of audio feedback
    "audio_feedback": ["hear_none", "hear_self", "hear_all"],
    "metronome_heuristic": ["average"] # more to come

}


if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
