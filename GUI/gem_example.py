from GEMGUI import GEMGUI

presets = {
    "serial": {"port": "/dev/cu.usbmodem1421", "baud_rate": 115200, "timeout": 5},
    "filename": "data",
    "data_dir": "/Users/laurenfink/Documents/Arduino/",
    # "sound_dir": "<sound_dir>",
    "slaves_requested": 3, #NB: only 3 slaves working in Davis rig
    #"master_sound": "1.WAV",
    # "slave_sound":  [
    #                     "1.WAV",
    #                     "1.WAV",
    #                     "1.WAV"
    #                 ],
    "metronome_alpha": [0, 0.25, 0.5, 0.75, 1],
    "metronome_tempo": 110, #units: beats-per-minute
    "repeats": 2,
    "windows": 55 #number of windows (55 -> ~100 second runs)
}

if __name__ == "__main__":
    g = GEMGUI(presets)
    g.mainloop()
