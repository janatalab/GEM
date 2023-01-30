# test_snd_functions.py

import sys, os, re

# Deal with adding the requisite GEM GUI modules to the path
if not os.environ.get('GEMROOT', None):
    # Try to get the GEM path from this module's path.
    p = re.compile('.*/GEM/')
    m = p.match(os.path.join(os.path.abspath(os.path.curdir), __file__))
    if m:
        os.environ['GEMROOT'] = m.group(0)

sys.path.append(os.path.join(os.environ['GEMROOT'],'GUI'))

from GEMIO import get_metronome_port, GEMIOManager, parse_constants

metronome_serial_num = "95536333830351317171"

presets = {
    # metronome serial port info
    "serial": {
    	"port": get_metronome_port(serial_num=metronome_serial_num), 
    	"baud_rate": 115200, 
    	"timeout": 5},
    "datafile": "./test_snd_functions.txt",
    "hfile": os.path.join(os.environ['GEMROOT'],"GEM/GEMConstants.h"),
}

# Parse our constants
constants = parse_constants(presets["hfile"])

def get_sound_lists():
	with GEMIOManager(presets["serial"], presets["datafile"], False) as io:
		# allow some time for handshake!
		io.com.readline()