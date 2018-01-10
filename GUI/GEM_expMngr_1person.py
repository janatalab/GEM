#
# Presets for use in single player version of GEM
#
# This experiment involves solo tapper with virtual metronome to make
# sure that we can replicate the single-tapper results of Fairhurst, Janata, &
# Keller, 2012 with the GEM system.
#
# Experimental conditions:
# - varying alpha values
# - audio_feedback (with vs. without hearing oneself. One always hears metronome)


from GEMGUI import GEMGUI
import serial
from time import time

presets = {
    "serial": {"port": "/dev/cu.usbmodem1421", "baud_rate": 115200, "timeout": 5},
    "filename": "GEM_1playerData_",
    "data_dir": "/Users/laurenfink/Documents/Arduino/",
    # "sound_dir": "<sound_dir>",
    "slaves_requested": 1, 
    #"master_sound": "1.WAV",
    # "slave_sound": "1.WAV",
    "metronome_alpha": [0, 0.25, 0.5, 0.75, 1],
    "metronome_tempo": 100.0, #units: beats-per-minute
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
