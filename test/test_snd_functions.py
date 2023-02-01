# test_snd_functions.py

import sys, os, re
from time import sleep

import pdb

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
    with GEMIOManager(presets["serial"], None, False) as io:
        # allow some time for handshake!
        response = b""

        response += io.com.readline()

        done = False
        attempts = 0
        while (not done):
            n = io.available()
            if n > 0:
                print(f"Reading {n} bytes")
                response += io.com.read(n)

                # print(f"Cumulative response: {response}")

            sleep(2)
            attempts += 1

            if attempts > 3:
                done = True

        print(response.decode('utf-8'))

        pdb.set_trace()

        # Send the request to list available sounds for the metronome
        msg = constants["LIST_AVAILABLE_SOUNDS"] + constants["DEV_METRONOME"]
        print(f"Sending message: {msg}")
        io.send(msg)

        # Listen for the response
        done = False
        response = b""

        while (not done):
            n = io.available()
            if n > 0:
                print(f"Reading {n} bytes")
                response += io.com.read(n)

                print(f"Cumulative response: {response}")

                # Check whether we've received the termination code
                pdb.set_trace()
                response.endswith(constants["GEM_REQUEST_ACK"])


