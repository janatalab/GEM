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
    check_devices = ["DEV_METRONOME","DEV_TAPPER_1","DEV_TAPPER_2","DEV_TAPPER_3","DEV_TAPPER_4"]
    device_sounds = {}

    with GEMIOManager(presets["serial"], None, False) as io:
        # allow some time for handshake!
        io.com.readline()

        for device in check_devices:
            print(f"Fetching sounds for {device}")

            # Send the request to list available sounds for the metronome
            msg = constants["LIST_AVAILABLE_SOUNDS"] + constants[device]
            print(f"Sending message: {msg}")
            io.send(msg)

            # Listen for the response
            done = False
            response = b""

            while (not done):
                n = io.available()
                if n > 0:
                    # print(f"Reading {n} bytes")
                    response += io.com.read(n)

                    # print(f"Cumulative response: {response}")

                    # Check whether we've received the termination code
                    if response.endswith(constants["GEM_REQUEST_ACK"]):
                        done = True

            # Convert to bytearray
            response = bytearray(response[:-1])

            if not len(response):
                continue

            # Check whether this is GEM_DTP_SND_LIST packet
            if response.startswith(constants["GEM_DTP_SND_LIST"]):
                # Slice our response
                response = response[1:]

                actual_device = None
                for k,v in constants.items():
                    if isinstance(v, bytes) and response.startswith(v):
                        actual_device = k
                        response = response[1:]
                        break

                # Make sure it is for the requested device
                if actual_device != device:
                    ValueError(f"Device mismatch: Expected {device}, got {actual_device}")

            # pdb.set_trace()
            print(f"Sounds on device: {device}")
            sounds = []
            for s in response.split(b"\x00"):
                if s:
                    soundname = bytes(s).decode('utf-8')
                    sounds.append(soundname)
                    print(f"{soundname}")

            device_sounds.update({device:sounds})

    return device_sounds

