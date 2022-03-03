'''
Script that will play metronome until user clicks abort.
For use in letting participants adjust volume of tap sound relative to metronome through their headphones, before starting experiment.

Authors: Lauren Fink, Scottie Alexander, Petr Janata
Contact: pjanata@ucdavis.edu
Repository link: https://github.com/janatalab/GEM
'''

from GEMGUI import GEMGUI
import os
import serial.tools.list_ports

# Define path to Arduino directory
rootpath = "/Users/" + os.environ['USER'] + "/Documents/Arduino/"

# Define a unique identifier for the usb device used to connect the metronome
# Arduino. This could be something like "Arduino", though on our UC Davis
# GEM system, we use a usb adapter from the Arduino to the computer that has an ID of "Generic CDC".
metronome_port_str = "Generic CDC"

def get_metronome_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        # Check for ID of usb device used to connect Arduino
        if metronome_port_str in p[1]:
            pid = str(p)
            return pid.split(' ')[0]

# Get metronome Arduino port ID
metronome_port = get_metronome_port()

# Define experimental presets
presets = {
    # metronome serial port info
    "serial": {"port": metronome_port, "baud_rate": 115200, "timeout": 5},

    # beginning of output file string for output data files
    "filename": "GEM_volume",

    # directory for output data
    "data_dir": "/Users/" + os.environ['USER'] + "/Desktop/GEM_data/volume_trial/",

    # path to GEMConstants.h
    "hfile": rootpath + "GEM/GEM/GEMConstants.h",

    # number of players in the experiment. NB: all 4 tapper Arduinos should still be attached to metronome
    "tappers_requested": 1, # don't care about participant IDs since this is just for adjusting volume

    # metronome adaptivity levels to be used
    "metronome_alpha": 0,

    # tempo of the metronome; unit: beats-per-minute
    "metronome_tempo": 120.0,

    # number of repetitions for each alpha value
    "repeats": 3,

    # number of metronome clicks
    "windows": 300,

    # Future releases will allow for all variations on hearing self, metronome, and others in the experiment.
    "audio_feedback": ["hear_metronome_and_self"],

    # algorithm used in adapting metronome. NB: at present, only "average" is available. Future releases will incorporate additional heurstic options.
    "metronome_heuristic": ["average"]
}


# Run the experiment through the GUI
if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
