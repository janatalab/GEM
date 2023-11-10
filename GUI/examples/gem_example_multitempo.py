'''
Example presets file for use in GEM experiments.

Authors: Lauren Fink, Scottie Alexander, Petr Janata
Contact: pjanata@ucdavis.edu
Repository link: https://github.com/janatalab/GEM
'''
import sys, os, re

# Deal with adding the requisite GEM GUI modules to the path
if not os.environ.get('GEMROOT', None):
    # Try to get the GEM path from this module's path.
    p = re.compile('.*/GEM/')
    m = p.match(os.path.join(os.path.abspath(os.path.curdir), __file__))
    if m:
        os.environ['GEMROOT'] = m.group(0)

sys.path.append(os.path.join(os.environ['GEMROOT'],'GUI'))

from GEMGUI import GEMGUI
from GEMIO import get_metronome_port

# Indicate the serial# of the metronome Arduino.
# This is used to search for the correct port information
metronome_serial_num = "9543731333535131D171"

# Define experimental presets
presets = {
    # metronome serial port info
    "serial": {"port": get_metronome_port(serial_num=metronome_serial_num), "baud_rate": 115200, "timeout": 5},

    # beginning of output file string for output data files
    "filename": "GEM_example",

    # directory for output data
    "data_dir": "/Users/" + os.environ['USER'] + "/Desktop/GEM_data/demo_data/",

    # path to GEMConstants.h
    "hfile": os.path.join(os.environ['GEMROOT'],"GEM/GEMConstants.h"),

    # number of players in the experiment. NB: all 4 tapper Arduinos can remain attached to metronome Arduino
    "tappers_requested": 2,

    # metronome adaptivity levels to be used
    "metronome_alpha": [0, .3, 1],

    # tempo of the metronome; unit: beats-per-minute
    "metronome_tempo": [80, 120.0, 150],

    # number of repetitions for each alpha value
    "repeats": 1,

    # number of metronome clicks
    "windows": 20,

    # audio feedback condition; NB: at present, only "hear_metronome" available.
    # Future releases will allow for all variations on hearing self, metronome,
    # and others in the experiment.
    "audio_feedback": ["hear_metronome"],

    # algorithm used in adapting metronome. NB: at present, only "average" is
    # available. Future releases will incorporate additional heurstic options.
    "metronome_heuristic": ["average"],

    # Are we testing in spoof mode. Default = False
    # "spoof_mode": False,

    # Are we connecting to a Group Session in PyEnsemble for post-run data collection, e.g. surveys. Default = False
    # "connect_pyensemble": False,
}


# Run the experiment through the GUI
if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
