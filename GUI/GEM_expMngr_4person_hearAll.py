'''
Presets for use in 4-player GEM pilot experiment.

This experiment involves four tappers with an adaptive metronome to extend the findings of Fairhurst, Janata, and Keller (2012) to group settings. Unlike the first 4 person experiment, this version allows tappers to hear both the metronome (through speaker) and the sound produced by their own taps (through headphones).

    IV: alpha value
    DV: individual std asynchronies, group std asynchs, subjective ratings
    Instructions: Listen to first 2 metronome tones and then synchronize.
    Try to maintain the initial tempo of the metronome.
    Tap with index finger of dominant hand. Look at own index finger, not other players. Vol of tap sound should be perceptually equal to that of metronome.

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
    "filename": "GEM_4playerData_hearAll",
    "data_dir": "/Users/" + os.environ['USER'] +        "/Desktop/GEM_data/4person_GEM_hearAll/",
    "hfile": rootpath + "GEM/GEM/GEMConstants.h",
    "slaves_requested": 4,
    "metronome_alpha": [0, 0.35, 0.7, 1],
    "metronome_tempo": 120.0, #units: beats-per-minute
    "repeats": 6,
    "windows": 60, # ~30 sec rounds
    "audio_feedback": ["hear_all"],
    "metronome_heuristic": ["average"]
}

if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
