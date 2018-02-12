'''
Presets for use in debugging.
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
    "filename": "throughput",
    "data_dir": rootpath + "Data/",
    "hfile": rootpath + "GEM/GEM/GEMConstants.h",
    "slaves_requested": 1,
    "metronome_alpha": [0],
    "metronome_tempo": 120.0, #units: beats-per-minute
    "repeats": 1,#10, #fairhurst was 12
    "windows": 20, #26, #number of windows
    "audio_feedback": ["hear_metronome"],
    "metronome_heuristic": ["average"]
}

if __name__ == "__main__":

    g = GEMGUI(presets)
    g.mainloop()
