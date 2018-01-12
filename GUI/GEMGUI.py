#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
# Basic Graphical User Interface (GUI) for GEM experiments.
#   - run gem_example.py to view the GUI

# LF TODO:
# Write out alpha value on each run to .gdf file; also need to write individual
# run headers to .json file
# Implement Error handling on master side (e.g. couldn't find audio file)
# --- not a huge priority
# Implement audio feedback conditions
# --- send message to experimenter about what to do
# Set slave sound from ECC
# --- this should wait until v2
'''

import Tkinter
from Tkinter import Tk, Label, Button, Entry, StringVar, Frame, OptionMenu, Text
from tkMessageBox import showerror
from threading import Timer
from datetime import date, datetime
from copy import copy
import numpy as np
import os

from GEMIO import GEMDataFile, GEMAcquisition
from GEMITC import ITC

def get_date():
    return date.today().strftime("%Y%m%d")

def get_time():
    return datetime.now().strftime("%H:%M:%S")

# ==============================================================================
# Class of general utilities for constructing core aspects of GUI components
class GEMGUIComponent(Frame):
    def __init__(self, parent, ncol):
        Frame.__init__(self, parent)
        self.grid(pady = 15, sticky = "NW")
        #self.grid_rowconfigure(0, weight=1)
        #self.grid_columnconfigure(0, weight=1)
        self.ncol = ncol
        self.krow = 1

        self.components = dict()

    # Add title
    def set_title(self, title):
        self.title = Label(self, text=title, font=("Helvetica", 22))
        self.title.grid(row=0, columnspan=self.ncol, pady=5, sticky="NW")

    # Add row
    def add_row(self, tags, items):
        if isinstance(items, list):
            col = 0
            for (item, tag) in zip(items, tags):
                self.components[tag] = item
                item.grid(row=self.krow, column=col, pady = 3, sticky="NW")
                col += 1

            self.krow += 1
        else:
            self.components[tags] = items
            items.grid(row=self.krow+1, columnspan=self.ncol, pady = 3, sticky="NW")
            self.krow += 1

    # get entry
    def __getitem__(self, k):
        return self.components[k]

# ==============================================================================
# HELPER classes
# ==============================================================================
# Class to create text (left) next to dropdown menu (right)
class DropDown(OptionMenu):
    def __init__(self, master, status, *options):
        self.var = StringVar(master)
        self.var.set(status)
        OptionMenu.__init__(self, master, self.var, *options)


# ==============================================================================
# class to create text (left) and text box (right)
# text box will be filled with user's entry
class TextBoxGroup(Frame):
    def __init__(self, parent, label, width=5, *defaultEntry):
        Frame.__init__(self, parent)
        self.grid()

        self.text = label
        self.width = width
        self.label = Label(self, text=self.text)
        self.label.grid(row=0, column=0, pady=3)

        self.resp = StringVar(value=defaultEntry)

        self.entry = Entry(self, width=width, textvariable=self.resp)
        self.entry.grid(row=0, column=1, pady=3)

    def get_text(self):
        return self.resp.get()

    def set_text(self, txt):
        self.resp.set(txt)

    def disable(self):
        #self.entry["state"] = Tkinter.DISABLED
        self.entry["state"] = "readonly"

    def enable(self):
        self.entry["state"] = Tkinter.NORMAL

# ==============================================================================
# class to create text (left) and button (right)
class TextButtonGroup(Frame):
    def __init__(self, parent, text, label, callback, width=5):
        Frame.__init__(self, parent)
        self.grid()

        self.width = width
        self.text = Label(self, text=text)
        self.text.grid(row=0, column=0, pady = 3)

        self.button = Button(self, text=label, command=callback)
        self.button.grid(row=0, column=1)

# ==============================================================================
# class to create two buttons side-by-side
class ButtonGroup(Frame):
    def __init__(self, parent, btnspec, spacex):
        Frame.__init__(self, parent)
        self.grid()
        self.btn = list()
        self.labels = list()
        k = 0

        for label in btnspec.keys():
            self.btn.append(Button(self, text=label, command=btnspec[label]))
            self.btn[k].grid(row=0, column=k, padx = spacex, pady = 3)
            self.labels.append(label)
            k += 1

    def disable(self, label):
        if label in self.labels:
            self.change_state(self.labels.index(label), Tkinter.DISABLED)

    def enable(self, label):
        if label in self.labels:
            self.change_state(self.labels.index(label), Tkinter.NORMAL)

    def change_state(self, k, state):
        self.btn[k]["state"] = state

# ==============================================================================
# Class for viewing data received from Arduino
class DataViewer(GEMGUIComponent):
    def __init__(self, parent):
        GEMGUIComponent.__init__(self, parent, 1)

        self.set_title("Data Viewer")

        dv = Text(self, height=20, width=45, borderwidth=2)
        dv.insert(Tkinter.INSERT, "Hello!\n\nData from Arduino will appear here\n")
        dv['state'] = 'disabled'
        self.add_row("dv", dv)

        dv.bind("<Button-1>", self.callback)
        self.nline = 0
        self.buffer = ""

    # --------------------------------------------------------------------------
    def callback(self, event):
        x = str(event.x)
        y = str(event.y)
        self.show("Click at [" + x + ", " + y + "]")

    # --------------------------------------------------------------------------
    def draw(self):
        # delete what is in data viewer now
        self["dv"]["state"] = "normal"
        self["dv"].delete(1.0, Tkinter.END)

        # write to data viewer
        self["dv"].insert("end", self.buffer)
        self["dv"]["state"] = "disabled"

    # --------------------------------------------------------------------------
    def show(self, msg):
        if isinstance(msg, int):
            msg = "[REC]: %d bytes from arduino" % msg

        if self.buffer and self.nline >= 20:
            self.buffer = self.buffer[self.buffer.find('\n')+1:]

        self.nline += 1
        self.buffer += msg

        if not self.buffer.endswith('\n'):
            self.buffer += '\n'

        self.draw()

# ==============================================================================
# Class for controlling experiment and receiving data
class ExperimentControl(GEMGUIComponent):
    def __init__(self, parent):
        GEMGUIComponent.__init__(self, parent, 1)
        self.parent = parent

        self.set_title("Experiment Control Panel")

        # Start and Escape buttons
        spec = {"Start": self.start_run, "Abort": self.abort_run}
        self.add_row("ss", ButtonGroup(self, spec, 39))

        # Time remaining in run countdown
        self.add_row("timeleft", TextBoxGroup(self,
            "Time Remaining (this Run):", 5))
        self["timeleft"].set_text(self.format_time(self.parent["run_duration"]))
        self["timeleft"].disable()

        self.nruns = len(self.parent.alphas)
        self.add_row("runsleft", TextBoxGroup(self,
            "Number of Runs Remaining:", 3))

        self["runsleft"].set_text(str(self.nruns))
        self.counter = self.nruns

        self.time_remaining = 0

        self.running = False

    # --------------------------------------------------------------------------
    def check_user_input(self):

        exp_id = self.parent.basic_info.get_experimenter()
        if not exp_id:
            showerror("Missing Experimenter ID", "Please enter an experimenter ID")
            return False

        ids = self.parent.basic_info.get_subjids()
        for id in ids:
            if not id:
                showerror("Missing Subject ID", "Please enter an ID for all subjects")
                return False

        return True

    # --------------------------------------------------------------------------
    def start_run(self):

        if not self.check_user_input():
            return

        # disable start button
        self["ss"].disable("Start")

        # if this is the first run, init the data file and write the file header
        if self.counter == self.nruns:
            data_file = self.parent.init_data_file()
        else:
            data_file = self.parent.data_file

        # Get current run number
        krun = self.nruns - self.counter

        # write run header
        data_file.write_header(krun,
            {
                "run_number": krun,
                "start_time": get_time(),
                "alpha": self.parent.alphas[krun]
            }
        )

        # the actual IO thread
        self.acq = GEMAcquisition(data_file,
            self.parent.itc,
            self.parent.presets,
            self.parent.alphas[krun]
        )

        # make sure the itc is in the not-done state
        self.parent.itc.set_done(False)

        self.parent.unregister_cleanup("itc_thread")
        self.parent.register_cleanup("abort_run", self.close_request)

        # begin countdown clock (in python)
        self.time_remaining = self.parent["run_duration"]

        # starting thread is the last thing we should do
        self.acq.start()
        print("spawned thread")

        self.running = True

    # --------------------------------------------------------------------------
    def close_request(self):
        # tell parent not to close the window (forces user to click abort first)
        return False

    # --------------------------------------------------------------------------
    def abort_run(self):
        print("Calling itc.set_done()")
        self.parent.itc.set_done(True)
        self.clean_up()

    # --------------------------------------------------------------------------
    def clean_up(self):
        print("Asking IO thread to terminate")
        if self.running:
            self.acq.join()
            self.timer.cancel()
            self.time_remaining = 0
            self["timeleft"].set_text("00:00")
            self.parent.unregister_cleanup("abort_run")
            self.parent.register_cleanup("itc_thread", self.parent.itc.close)
            self["ss"].enable("Start")

            self.running = False

    # --------------------------------------------------------------------------
    def end_run(self):
        self.clean_up()
        self.counter -= 1
        self["runsleft"].set_text(str(self.counter))

    # --------------------------------------------------------------------------
    def format_time(self, t):
        mins, secs = divmod(int(np.floor(t)), 60)
        return "{:02d}:{:02d}".format(mins, secs)

    # --------------------------------------------------------------------------
    # NOTE: msg is just a placeholder for registering as an ITC listener
    def update_countdown(self, msg=""):
        self["timeleft"].set_text(self.format_time(self.time_remaining))

        if self.time_remaining > 0:
            # timer only gets called every ~2 seconds, so decrement
            # time_remaining by 2 and reset the timer
            self.time_remaining -= 2
            if self.time_remaining < 0:
                self.time_remaining = 0
            self.timer = Timer(2.0, self.update_countdown)
            self.timer.start()
        else:
            self.end_run()

# ==============================================================================
# Class to collect basic info required for GEM experiments
class BasicInfo(GEMGUIComponent):
    def __init__(self, parent, nsubj):
        GEMGUIComponent.__init__(self, parent, 1)

        # Heading for this componenet of GUI
        self.set_title("Basic Information")

        # Text box to enter experimenter initials
        self.add_row("experimenter", TextBoxGroup(self, "Experimenter ID:", 9))

        for k in range(0, nsubj):
            id = str(k+1)
            self.add_row("subjid-" + id, TextBoxGroup(self, "Subject " + id + " ID:", 12))

        self.nsubj = nsubj

    def get_subjids(self):
        ids = list()
        for k in range(0, self.nsubj):
            ids.append(self["subjid-" + str(k+1)].get_text())

        return ids

    def get_experimenter(self):
        return self["experimenter"].get_text()

# ==============================================================================
# Build Main GUI
# ==============================================================================
class GEMGUI(Frame):
    def __init__(self, presets):
        self.root = Tk()
        Frame.__init__(self, self.root)

        self.presets = presets
        self.presets["run_duration"] = self["windows"] / self["metronome_tempo"] * 60.0

        self.randomize_alphas()
        self.get_ioi()

        # Window title
        self.root.title("GEM Arduino acquisition system")
        self.grid()

        self.cleanup = dict()

        # Add relevant modules
        self.basic_info = BasicInfo(self, self.presets["slaves_requested"])
        self.exp_control = ExperimentControl(self)
        self.data_viewer = DataViewer(self)


        # thread for passing messages between IO thread and GUI, making this a
        # seperate thread prevents the IO thread from getting blocked when
        # trying to send messages
        self.itc = ITC()

        # register the data_viewer to receive messages on signal "data_viewer"
        self.itc.register_listener("data_viewer",
            self.data_viewer.show)

        # register ExperimentControl.update_countdown method as a listener for
        # run_start signals
        self.itc.register_listener("run_start",
            self.exp_control.update_countdown)

        print("starting ITC thread")
        self.itc.start()

        # make sure we close the ITC thread has a chance to clean up when the
        # app closes
        self.register_cleanup("itc_thread", self.itc.close)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def __getitem__(self, key):
        if key in self.presets:
            return self.presets[key]
        else:
            raise Exception("No key \"" + str(key) + "\" in presets!")

    def register_cleanup(self, k, f):
        self.cleanup[k] = f

    def unregister_cleanup(self, k):
        if k in self.cleanup:
            self.cleanup.pop(k)

    def get_ioi(self):
        self.presets["ioi"] = int(60000 / self["metronome_tempo"])

    def randomize_alphas(self):
        self.alphas = np.repeat(self["metronome_alpha"], self["repeats"])
        np.random.shuffle(self.alphas)

        # TODO: need to save random list and write to header and ideally to
        # output file; otherwise, don't know what alpha value corresponds to
        # which run...

    def on_close(self):
        doclose = True
        for f in self.cleanup.values():
            doclose = f() and doclose

        if doclose:
            self.root.destroy()

    def init_data_file(self):
        data_dir = os.path.join(self["data_dir"], get_date())
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        d = copy(self.presets)
        d["subject_ids"] = self.basic_info.get_subjids()
        d["experimenter_id"] = self.basic_info.get_experimenter()
        d["date"] = get_date()
        d["time"] = get_time()

        # all randomized alpha values for each run to the gdf fileheader
        d["alpha_order"] = list(self.alphas)

        # create file name from presets and subids
        filepath = os.path.join(data_dir, self["filename"] + "-" +
            "_".join(d["subject_ids"]) + ".gdf")

        nruns = len(self.alphas)

        #TODO add conditional about this path already existing (in GEMIO?)
        self.data_file = GEMDataFile(filepath, nruns)
        self.data_file.write_file_header(d, nruns)

        return self.data_file


# ==============================================================================
# if __name__ == "__main__":
#     g = GEMGUI()
#     g.mainloop()

#print("You entered \"%s\"" % g.basic_info["experimenter"].get_text())
