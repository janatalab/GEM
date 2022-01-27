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

import tkinter
from tkinter import Tk, Label, Button, Entry, StringVar, Frame, OptionMenu, Text
from tkinter.messagebox import showerror, askyesno
from threading import Timer
from datetime import date, datetime
from copy import copy
import numpy as np
import time
import os
import re
import requests
import json

import pdb

from GEMIO import GEMDataFile, GEMAcquisition
from GEMITC import ITC

def get_date():
    return date.today().strftime("%Y%m%d")

def get_time():
    return datetime.now().strftime("%H:%M:%S")

def hours_since_trump():
    now = time.time()
    now_hr = now - np.fmod(now, 60**2)
    now_str = "%06d" % int((now_hr - 1484910000) / (60**2))
    return now_str

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
                item.grid(row=self.krow+1, column=col, pady = 3, sticky="NW")
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
        #self.entry["state"] = tkinter.DISABLED
        self.entry["state"] = "readonly"

    def enable(self):
        self.entry["state"] = tkinter.NORMAL

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
            self.change_state(self.labels.index(label), tkinter.DISABLED)

    def enable(self, label):
        if label in self.labels:
            self.change_state(self.labels.index(label), tkinter.NORMAL)

    def change_state(self, k, state):
        self.btn[k]["state"] = state

# ==============================================================================
# Class for viewing data received from Arduino
class DataViewer(GEMGUIComponent):
    def __init__(self, parent):
        GEMGUIComponent.__init__(self, parent, 1)

        self.set_title("Data Viewer")

        dv = Text(self, height=20, width=45, borderwidth=2)
        dv.insert(tkinter.INSERT,
        "Hello!\n\nSubject id format:\n{} followed by the subject's initials and a digit if needed.\n\nData will appear here...".format(parent.hst)
        )
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
        self["dv"].delete(1.0, tkinter.END)

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
        spec = {"Start Run": self.start_run, "Abort Run": self.abort_run}
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
        self["runsleft"].disable()
        self.counter = self.nruns

        self.time_remaining = 0

        self.running = False

    # --------------------------------------------------------------------------
    def check_user_input(self):

        exp_id = self.parent.basic_info.get_experimenter()
        if not exp_id:
            showerror("Missing Experimenter ID", "Please enter an experimenter ID")
            return False

        pat = re.compile(r"^\d{6}[a-z]{2,3}\d?$")

        ids = self.parent.basic_info.get_subjids()
        pad_ids = self.parent.basic_info.get_padids()

        k = 1
        for id in ids:
            if not id:
                showerror("Missing Subject ID", "Please enter an ID for all subjects")
                return False

            if not self.parent.use_pyensemble:
                if pat.match(id) is None:
                    hst = self.parent.hst
                    bi = self.parent.basic_info
                    bi["subjid-" + str(k)].set_text(hst)

                    showerror("Invalid Subject ID", "Please append the subject's initials to the number: '" + hst + "'")
                    return False

        # Make sure we have pad IDs
        unique_padids = []
        for p in pad_ids:
            if not p:
                showerror("Missing Pad ID", "Please enter a pad for all subjects")
                return False

            if p not in unique_padids:
                unique_padids.append(p)

        if len(pad_ids) != len(unique_padids):
            showerror("Non-unique pad IDs", "Please enter a unique pad# for each subject")
            return False

        return True

    # --------------------------------------------------------------------------
    def start_run(self):

        if not self.check_user_input():
            return

        if self.parent.use_pyensemble:
            if not self.parent.group_session.pyensemble["initialized_experiment"]:
                showerror("PyEnsemble Error","Experiment not initialized!")
                return

        # if this is the first run, init the data file and write the file header
        if self.counter == self.nruns:
            data_file = self.parent.init_data_file()
            if isinstance(data_file, str):
                return

            # first run, disable editing of text boxes
            self.parent.basic_info.disable();

        else:
            data_file = self.parent.data_file

        # disable start button
        self["ss"].disable("Start")

        # Get current run number
        krun = self.nruns - self.counter

        # Put our trial parameters into a dictionary
        params = {
                "run_number": krun+1,
                "start_time": get_time(),
                "alpha": self.parent.alphas[krun]
            }

        # If connected to PyEnsemble, initialize the trial
        if self.parent.use_pyensemble:
            # Initialize the trial
            initialized = self.parent.group_session.initialize_trial(params)

            if not initialized:
                return

            # Pause to give clients a chance to update and prepare for the trial
            # Should probably make this a preset somewhere, but for now use 2.5 seconds
            pre_start_pause = 2.5
            time.sleep(pre_start_pause)

            # Signal to PyEnsemble that we are in the running state
            self.parent.group_session.start_trial()

        # write run header
        data_file.write_header(krun, params)

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

            if self.parent.use_pyensemble:
                self.parent.group_session.end_trial()

    # --------------------------------------------------------------------------
    def end_run(self):
        self.clean_up()
        self.counter -= 1
        self["runsleft"].set_text(str(self.counter))

        if self.counter < 1:
            self["ss"].disable("Start")

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


        # Heading for this component of GUI
        self.set_title("Basic Information")

        if not parent.use_pyensemble:
            # Text box to enter experimenter initials
            self.add_row("experimenter", TextBoxGroup(self, "Experimenter ID:", 9))

            # Add subject text boxes
            hrs = hours_since_trump()
            for k in range(0, nsubj):
                id_str = str(k+1)

                subid_id = "subjid-" + id_str
                subid_tbg = TextBoxGroup(self, "Subject " + id_str + " ID:", 12, hrs)

                padid_id = subid_id + "-pad"
                padid_tbg = TextBoxGroup(self, "Pad#:", 1, k+1)

                self.add_row([subid_id, padid_id], [subid_tbg, padid_tbg])

            self.nsubj = nsubj
        else:
            self.nsubj = 0

    def get_subjids(self):
        ids = list()
        if self.nsubj:
            for k in range(0, self.nsubj):
                ids.append(self["subjid-" + str(k+1)].get_text())

        return ids

    def get_padids(self):
        ids = list()
        if self.nsubj:
            for k in range(0, self.nsubj):
                ids.append(self["subjid-" + str(k+1) + "-pad"].get_text())

        return ids

    def get_experimenter(self):
        return self["experimenter"].get_text()

    def disable(self):
        for k in range(0, self.nsubj):
            self["subjid-" + str(k+1)].disable()
            self["subjid-" + str(k+1) + "-pad"].disable()

        self["experimenter"].disable()




# ==============================================================================
# Class for controlling experiment and receiving data
class GroupSession(GEMGUIComponent):
    def __init__(self, parent):
        GEMGUIComponent.__init__(self, parent, 1)
        self.parent = parent

        # Heading for this component of GUI
        self.set_title("PyEnsemble Group Session")

        # Create a dict for maintaining PyEnsemble information
        self.pyensemble = {"initialized_experiment": False}

        # Define PyEnsemble endpoints
        self.pyensemble.update({
            'urls': {
                "connect": "/group/session/attach/experimenter/",
                "update": "/group/session/participants/get/",
                "init_experiment": "/experiments/gem_control/control/experiment/init/",
                "end_experiment": "/experiments/gem_control/control/experiment/end/",
                "init_trial": "/experiments/gem_control/control/trial/init/",
                "start_trial": "/experiments/gem_control/control/trial/start/",
                "end_trial": "/experiments/gem_control/control/trial/end/",
            }
        })

        # Text box to enter the server URL
        self.add_row("server", TextBoxGroup(self, "Server:", 36))
        self["server"].set_text(self.parent["pyensemble_server"])
        self.add_row("username", TextBoxGroup(self, "User:", 15))
        self.add_row("password", TextBoxGroup(self, "Password", 15))
        self.components["password"].entry["show"] = '*'

        # Text box to enter the experimenter code
        self.add_row("experimenter_code", TextBoxGroup(self, "Experimenter Code:", 4))

        # Text box to enter the session status
        # status = Text(self, height=1, width=20, borderwidth=2)
        # self.add_row("status", status)

        # Buttons
        self.add_row("buttons", ButtonGroup(self, {"Connect": self.connect_server, "Update": self.update, "Initialize": self.initialize_experiment}, 40))

        # Add participant list viewer
        dv = Text(self, height=6, width=45, borderwidth=2)
        dv.insert(tkinter.INSERT, "Participants:\n")
        dv['state'] = 'disabled'
        self.add_row("dv", dv)


    # Bind this session to the server
    def connect_server(self):
        success = False

        # Get the requisite inputs
        server = self["server"].get_text()
        if not server:
            showerror("Missing PyEnsemble Server", "Please enter a PyEnsemble server")
            return
        self.pyensemble.update({'server': server})

        username = self["username"].get_text()
        if not username:
            showerror("Missing username", "Please enter a PyEnsemble username")
            return

        password = self["password"].get_text()
        if not password:
            showerror("Missing password", "Please enter a PyEnsemble password")
            return

        # Initialize a session object
        s = requests.Session()

        # Cache the session object
        self.pyensemble.update({"session": s})

        # Construct the server URL
        url = server + self.pyensemble["urls"]["connect"]

        # Access the URL
        resp = s.get(url)
        if not resp.ok:
            showerror("Problem fetching form")

        # Check whether it is a login form
        p = re.compile('name="username"')
        match = p.search(resp.text)

        if match:
            # Login and redirect to the target url
            resp = s.post(resp.url, {
                'username': username, 
                'password': password, 
                'csrfmiddlewaretoken': s.cookies['csrftoken']
                })

        # Check whether we are being prompted for the experimenter code
        p = re.compile('name="experimenter_code"')
        match = p.search(resp.text)

        if match:
            # Get the experimenter code from our value field
            experimenter_code = self["experimenter_code"].get_text()

            if not experimenter_code:
                showerror("Missing Session Experimenter Code", "Please enter a session experimenter code")
                return

            # Connect to the group session
            resp = s.post(url, {
                'experimenter_code': experimenter_code, 
                'csrfmiddlewaretoken': s.cookies['csrftoken']
                })

            # Check for success
            if resp.ok:
                # Check to see whether we redirected to the status page
                p = re.compile('id="groupsession_status"')
                if p.search(resp.text):
                    success = True
                else:
                    p = re.compile("The ticket matching this code has expired")
                    if p.search(resp.text):
                        showerror("PyEnsemble Error","Group session ticket has expired")

        
        if success:
            # Disable the button
            self['buttons'].disable("Connect")

            # Update the experimenter field in the basic info
            if "experimenter" not in self.parent.basic_info.components.keys():
                basic_info = self.parent.basic_info
                tbg = TextBoxGroup(basic_info, "Experimenter ID:", 9)
                tbg.set_text(username)
                basic_info.add_row("experimenter", tbg)

            # Update our participant list
            self.update()
        else:
            showerror("PyEnsemble Error","Unable to attach to group session")


    # Update our bound participant list
    def update(self):
        url = self.pyensemble["server"]+self.pyensemble["urls"]["update"]
        
        resp = self.pyensemble["session"].get(url)
        if not resp.ok:
            showerror("PyEnsemble Error","Unable to update participant list")

        # Get our basic_info section
        basic_info = self.parent.basic_info

        # Extract our participant info
        sinfo = resp.json()
        subjects = sinfo.keys()

        # Update the BasicInfo section
        # pdb.set_trace()

        # Get the existing subject IDs
        subids = basic_info.get_subjids()
        nsubs = len(subids)

        # Create necessary entries in the basic_info section
        for s in subjects:
            # Check whether an entry already exists
            if s in subids:
                continue

            # Create the entry
            nsubs += 1
            subid_id = "subjid-"+str(nsubs)
            subid_tbg = TextBoxGroup(basic_info, "Subject " + str(nsubs) + " ID:", 12)
            subid_tbg.set_text(s)

            padid_id = subid_id+"-pad"
            padid_tbg = TextBoxGroup(basic_info, "Pad#:", 1)

            # basic_info.add_row(subid_id, tbg)
            basic_info.add_row([subid_id, padid_id], [subid_tbg, padid_tbg])

        # Update
        msg = "Subjects:\n"
        for k, v in sinfo.items():
            msg += f"{k}: {v['first']} {v['last']}\n"

        # delete what is in data viewer now
        self["dv"]["state"] = "normal"
        self["dv"].delete(1.0, tkinter.END)

        # write to data viewer
        self["dv"].insert("end", msg)
        self["dv"]["state"] = "disabled"

        self.parent.basic_info.nsubj = nsubs  

    def initialize_experiment(self):
        url = self.pyensemble["server"]+self.pyensemble["urls"]["init_experiment"]
        
        # Get our session object
        s = self.pyensemble["session"]

        # GET the form
        resp = s.get(url)

        # Fill out the form
        data = {"csrfmiddlewaretoken": s.cookies["csrftoken"]}
        data.update({
            "slaves_requested": self.parent.presets["slaves_requested"],
            "metronome_alpha": self.parent.presets["metronome_alpha"],
            "metronome_tempo": self.parent.presets["metronome_tempo"],
            "repeats": self.parent.presets["repeats"],
            "windows": self.parent.presets["windows"],
            "audio_feedback": self.parent.presets["audio_feedback"],
            "trial_generator": "fully_random"  ,
            })

        # POST the form
        resp = s.post(resp.url, data)

        # Check for indications of an error in the response
        p = re.compile("error")

        if not resp.ok or p.search(resp.text):
            showerror("PyEnsemble Error","Failed to initialize experiment!")
            return

        self.pyensemble["initialized_experiment"] = True

        # Disable the Update and Initialize buttons
        self['buttons'].disable("Update")
        self['buttons'].disable("Initialize")
        
    def end_experiment(self):
        url = self.pyensemble["server"]+self.pyensemble["urls"]["end_experiment"]

        s = self.pyensemble["session"]
        resp = s.get(url)


    def initialize_trial(self, params):
        url = self.pyensemble["server"]+self.pyensemble["urls"]["init_trial"]

        # Grab our session object
        s = self.pyensemble["session"]     

        # Get our form
        resp = s.get(url)

        # Create our payload
        data = {"csrfmiddlewaretoken": s.cookies["csrftoken"]}

        # Set our trial number
        data.update({"trial_num": params["run_number"]})

        # Set our params
        data.update({"params": json.dumps({
                "alpha": params["alpha"],
                "tempo": self.parent.presets["metronome_tempo"],
                "start_time": params["start_time"],
            })
        })

        # Post our form
        resp = s.post(resp.url, data)

        p = re.compile("error")
        if not resp.ok or p.search(resp.text):
            showerror("PyEnsemble Error","Failed to initialize trial!")
            pdb.set_trace()
            return False

        return True

    def start_trial(self):
        url = self.pyensemble["server"]+self.pyensemble["urls"]["start_trial"]

        # Grab our session object
        s = self.pyensemble["session"]     

        # Call our endpoint
        resp = s.get(url)

        if not resp.ok:
            showerror("PyEnsemble Error","Failed to start trial!")

    def end_trial(self):
        url = self.pyensemble["server"]+self.pyensemble["urls"]["end_trial"]

        # Grab our session object
        s = self.pyensemble["session"]     

        # Call our endpoint
        resp = s.get(url)

# ==============================================================================
# Build Main GUI
# ==============================================================================
class GEMGUI(Frame):
    def __init__(self, presets):
        self.root = Tk()
        Frame.__init__(self, self.root)

        self.hst = hours_since_trump()

        self.presets = presets
        self.presets["run_duration"] = self["windows"] / self["metronome_tempo"] * 60.0

        self.randomize_alphas()
        self.get_ioi()

        # Window title
        self.root.title("GEM Arduino acquisition system")
        self.grid()

        # Initialize a dictionary for registering cleanup actions
        self.cleanup = dict()

        # Determine whether we are connecting with PyEnsemble
        self.use_pyensemble = False
        if self.presets.get("connect_pyensemble", False):
            self.use_pyensemble = True

        # Add relevant modules
        self.basic_info = BasicInfo(self, self.presets["slaves_requested"])

        # Add PyEnsemble components if requested
        if self.use_pyensemble:
            self.group_session = GroupSession(self)
            # self.register_cleanup("pyensemble", self.group_session.end_experiment)

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

        if os.path.exists(filepath):
            if not askyesno("Overwrite file", "The data file already exists, overwrite?"):
                return ""

        nruns = len(self.alphas)

        #TODO add conditional about this path already existing (in GEMIO?)
        self.data_file = GEMDataFile(filepath, nruns)
        self.data_file.write_file_header(d, nruns)

        return self.data_file

# ==============================================================================
