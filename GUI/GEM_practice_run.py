'''
Practice run presets used in GEM experiments.

Authors: Lauren Fink, Scottie Alexander, Petr Janata
Contact: pjanata@ucdavis.edu
Repository link: https://github.com/janatalab/GEM
'''

from GEMGUI import GEMGUI
import os
import serial.tools.list_ports

# Define path to Arduino directory
rootpath = "/Users/" + os.environ['USER'] + "/Documents/Arduino/"

# Define a unique identifier for the usb device used to connect the master
# Arduino. This could be something like "Arduino", though on our UC Davis
# GEM system, we use a usb adapter from the Arduino to the computer that has an
# ID of "Generic CDC".
master_port_str = "Generic CDC"

def get_master_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        # Check for ID of usb device used to connect Arduino
        if master_port_str in p[1]:
            pid = str(p)
            return pid.split(' ')[0]

# Get master Arduino port ID
master_port = get_master_port()

# Define experimental presets
presets = {
    # master serial port info
    "serial": {"port": master_port, "baud_rate": 115200, "timeout": 5},

    # beginning of output file string for output data files
    "filename": "GEM_practice",

    # directory for output data
    "data_dir": "/Users/" + os.environ['USER'] +        "/Desktop/GEM_data/practice_runs/",

    # path to GEMConstants.h
    "hfile": rootpath + "GEM/GEM/GEMConstants.h",

    # number of players in the experiment. NB: all 4 slaves Arduinos can still be attached to master
    "slaves_requested": 4,

    # metronome adaptivity levels to be used
    "metronome_alpha": 0,

    # tempo of the metronome; unit: beats-per-minute
    "metronome_tempo": 120.0,

    # number of repetitions for each alpha value
    "repeats": 3,

    # number of metronome clicks
    "windows": 26,

    # audio feedback condition; NB: at present, only "hear_metronome" available.
    # Future releases will allow for all variations on hearing self, metronome,
    # and others in the experiment.
    "audio_feedback": ["hear_metronome"],

    # algorithm used in adapting metronome. NB: at present, only "average" is
    # available. Future releases will incorporate additional heurstic options.
    "metronome_heuristic": ["average"]
}


# Run the experiment through the GUI
if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
