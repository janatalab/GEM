from GEMGUI import GEMGUI

presets = {
    "com_port": "/dev/ttyACM0",
    "data_dir": "<data_dir>",
    "sound_dir": "<sound_dir>",
    "slaves_requested": 3, #NB: only 3 slaves working in Davis rig
    "master_sound": "",
    "slave_sound":  [
                        "",
                        "",
                        ""
                    ],
    "metronome_alpha": [0, 0.25, 0.5, 0.75, 1],
    "metronome_tempo": 110,
    "repeats": 2,
    "run_duration": 90
}

if __name__ == "__main__":
    g = GEMGUI(presets)
    g.mainloop()
