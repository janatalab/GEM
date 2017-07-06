#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Basic Graphical User Interface (GUI) for GEM experiments
# Most parameters loaded from GEM_presets file so user has very little to enter
# Run gem_example.py to view current GUI

# LF TODO: 
# Decode incoming bytes on the fly
# -- this is where we will compare ECC window count to master window count
# Check user imput for completeness
# Reformat output file to be human-readable
# Update countdown clock to start at appropriate time
# Implement Error handling
# Implement audio feedback conditions
# --- send message to experimenter about what to do
# Set slave sound from ECC - this might have to wait until v2

import Tkinter
from Tkinter import Tk, Label, Button, Entry, StringVar, Frame, OptionMenu, Text
import numpy as np
from datetime import date, datetime
from threading import Timer, Lock, Condition
from copy import copy
import os

import serial
from time import time

from GEMIO import GEMDataFile, GEMAcquisition


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
        self.writeToViewer("Click at [" + x + ", " + y + "]")

    # --------------------------------------------------------------------------
    def draw(self):
        # delete what is in data viewer now
        self["dv"]["state"] = "normal"
        self["dv"].delete(1.0, Tkinter.END)

        # write to data viewer
        self["dv"].insert("end", self.buffer)
        self["dv"]["state"] = "disabled"

    # --------------------------------------------------------------------------
    def writeToViewer(self, msg):
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

        # TODO: implement set-up button and appropriate callback?

        # Start and Escape buttons
        spec = {"Start": self.start_run, "Abort": self.abort_run}
        self.add_row("ss", ButtonGroup(self, spec, 39))

        # Time remaining in run countdown
        self.add_row("timeleft", TextBoxGroup(self,"Time Remaining (this Run):", 5))
        self["timeleft"].set_text(self.format_time(self.parent["run_duration"]))
        self["timeleft"].disable()

        self.nruns = len(self.parent.alphas)
        self.add_row("runsleft", TextBoxGroup(self, "Number of Runs Remaining:", 3))
        self["runsleft"].set_text(str(self.nruns))
        self.counter = self.nruns

    # --------------------------------------------------------------------------
    def initArduino(self):
        # send everything to Arduino
        self.parent.show("Ready to Jam!")

        # check user input for correctness (really subj/experimenter ids)
        # wait on master to tell us that everything is ready, then enable the
        # start button

        # if everything checks out, we can spwan the data acq thread so that
        # we are ready for incoming data as soon as

        # Inititalize Arduino button
        # Callback for this button should send all info to Arduino AND open file
        # to write experiment data

    # --------------------------------------------------------------------------
    def start_run(self):
        # disable start button
        self["ss"].disable("Start")

        # if this is the first run, init the data file and write the file header
        if self.counter == self.nruns:

            data_dir = os.path.join(self.parent["data_dir"], get_date())
            if not os.path.exists(data_dir):
                os.mkdir(data_dir)

            bi = self.parent.basic_info

            d = copy(self.parent.presets)
            d["subject_ids"] = bi.get_subjids()
            d["experimenter_id"] = bi.get_experimenter()
            d["date"] = get_date()
            d["time"] = get_time()

            # added subid1 to filename - LF
            filepath = os.path.join(data_dir, self.parent["filename"] + d["subject_ids"][0] +".gdf")

            #TODO add conditional about this path already existing (in GEMIO?)
            self.data_file = GEMDataFile(filepath)

            self.data_file.write_file_header(d, self.nruns)

        # Get current run number
        self.currRun = self.nruns - self.counter

        # write run header
        self.data_file.write_header(
            {
                "run_number": self.currRun,
                "start_time": get_time()
            }
        )

        # Get alpha value for this run & save to presets
        # so we can use it in thread
        self.parent.presets["currAlpha"] = self.parent.alphas[self.currRun]

        # class for communicating with the IO thread for this run
        self.itc = ITC(self.parent.data_viewer)

        print("created ITC object")

        # the actual IO thread
        self.acq = GEMAcquisition(self.itc,
            self.data_file.filepath,
            self.parent.presets
        )
        self.acq.start()
        print("spawned thread")

        self.parent.register_cleanup("abort_run", self.close_request)

        # begin countdown clock (in python)
        self.time_remaining = self.parent["run_duration"]
        self.update_countdown()

    # --------------------------------------------------------------------------
    def close_request(self):
        # tell parent not to close the window (forces user to click abort first)
        return False

    # --------------------------------------------------------------------------
    def abort_run(self):
        self.itc.done()
        self.clean_up()

    # --------------------------------------------------------------------------
    def clean_up(self):
        self.acq.join()
        self.timer.cancel()
        self["timeleft"].set_text("00:00")
        self.parent.unregister_cleanup("abort_run")
        self["ss"].enable("Start")

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
    def update_countdown(self):
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

        #TODO start this only once GEM_START has been sent

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
# Inter-thread-communicator
class ITC:
    def __init__(self, viewer):
        self.viewer_lock = Lock()
        self.done_lock = Lock()
        self.isdone = False
        self.viewer = viewer

    def send_message(self, msg):
        self.viewer_lock.acquire()
        self.viewer.writeToViewer("[REC]: Received %d bytes!" % msg)
        self.viewer_lock.release()

    def done(self):
        self.done_lock.acquire()
        self.isdone = True
        self.done_lock.release()

    def check_done(self):
        self.done_lock.acquire()
        ret = self.isdone
        self.done_lock.release()
        return ret

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
        self.get_IOI()

        # Window title
        self.root.title("GEM Arduino acquisition system")
        self.grid()

        self.cleanup = dict()

        # Add relevant modules
        self.basic_info = BasicInfo(self, self.presets["slaves_requested"])
        self.exp_control = ExperimentControl(self)
        self.data_viewer = DataViewer(self)

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

    def get_IOI(self):
        self.presets["ioi"] = int(60000 / self["metronome_tempo"])

    def randomize_alphas(self):
        self.alphas = np.repeat(self["metronome_alpha"], self["repeats"])
        np.random.shuffle(self.alphas)

    def show(self, msg):
        self.data_viewer.writeToViewer(msg)

    def on_close(self):
        doclose = True
        for f in self.cleanup.values():
            doclose = f() and doclose

        if doclose:
            self.root.destroy()


# ==============================================================================
# if __name__ == "__main__":
#     g = GEMGUI()
#     g.mainloop()

#print("You entered \"%s\"" % g.basic_info["experimenter"].get_text())
