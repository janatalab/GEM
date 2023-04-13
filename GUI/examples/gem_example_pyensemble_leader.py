'''
This is a preset file to use if all trial parameters, i.e. tempo, alpha, 
and the number of windows, are to be obtained from PyEnsemble on each trial.

This arrangement allows code written in PyEnsemble to generate arbitrary trial orders
and parameter constellations, providing for much more flexibility than the rigid
arrays of tempi and alpha levels.

It is envisioned that various parameters, such as metronome_serial_num, 
data directory and file paths could also be set in PyEnsemble, 
in a section of the Group Status page.

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

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Indicate the serial# of the metronome Arduino.
# This is used to search for the correct port information, and is unique for every setup
metronome_serial_num = "9543731333535131D171"

# Define experimental presets
presets = {
    # Are we testing in spoof mode. Default = False
    "spoof_mode": False,

    # Useful to set verify_ssl to False if debugging
    "verify_ssl": False,

    # metronome serial port info
    "serial": {"port": get_metronome_port(serial_num=metronome_serial_num), "baud_rate": 115200, "timeout": 5},

    # path to GEMConstants.h
    "hfile": os.path.join(os.environ['GEMROOT'],"GEM/GEMConstants.h"),

    # Are we connecting to a Group Session in PyEnsemble for post-run data collection, e.g. surveys.
    "parameter_source": 'pyensemble', # Are we fetching our parameters from PyEnsemble or local

    # PyEnsemble connection information (should probably be read from a site-specific config file)
    "connect_pyensemble": True,
    "pyensemble_server": "https://atonal.ucdavis.edu/gem/",

    # # beginning of output file string for output data files
    # "filename": "GEM_pyensemble_example",

    # # directory for output data
    # "data_dir": "/Users/" + os.environ['USER'] + "/Desktop/GEM_data/demo_data/",

    # # number of players in the experiment. NB: all 4 tapper Arduinos can remain attached to metronome Arduino
    # "tappers_requested": 4,

    # # metronome adaptivity levels to be used
    # "metronome_alpha": [0, .25, .75, 1],

    # # tempo of the metronome; unit: beats-per-minute
    # "metronome_tempo": 120.0,

    # # number of repetitions for each alpha value
    # "repeats": 1,

    # # number of metronome clicks
    # "windows": 20,

    # # audio feedback condition; NB: at present, only "hear_metronome" available.
    # # Future releases will allow for all variations on hearing self, metronome,
    # # and others in the experiment.
    # "audio_feedback": ["hear_metronome"],

    # # algorithm used in adapting metronome. NB: at present, only "average" is
    # # available. Future releases will incorporate additional heurstic options.
    # "metronome_heuristic": ["average"],

}


# Run the experiment through the GUI
if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
